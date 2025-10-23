import os
import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from google import genai
from google.genai import types

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

class MCPClient:
    def __init__(self):
        self.session : Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.gemini_client = genai.Client(api_key = api_key)

    async def connect_to_server(self, server_script_path: str) -> None:
        '''
        Cnnect to a MCP server

        Args:
            server_script_path: path to the srver file (.py or .js)
        '''
        
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")

        if not (is_python or is_js):
            raise ValueError("Server script should be .py or .js")
        
        command = "python" if is_python else "node"

        server_params = StdioServerParameters(
            command = command,
            args = [server_script_path],
            env =  None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools

        print("\nConnected to server. Tools: ", [tool.name for tool in tools])

        if "search_query" in [tool.name for tool in tools]:
            print("Testing search tool with a dummy query.")
            r = await self.session.call_tool("search_query", {"query": "site:tensorflow.org keras", "num_of_results": 3})
            print("Direct tool response:\n", r)

    async def ask_query(self, query_prompt: str) -> str:
        # print(query_prompt)
        # Send request to the model with MCP function declarations
        response = await self.gemini_client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=query_prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0,
                tools=[self.session],  # uses the session, will automatically call the tool
                # Uncomment if you **don't** want the SDK to automatically call the tool
                # automatic_function_calling=genai.types.AutomaticFunctionCallingConfig(
                #     disable=True
                # ),
            ),
        )
        return response.text
    
    async def chat_loop(self) -> None:
        '''
        Run an interactive chat loop.
        '''

        print("\nMCP Client Started.")
        print("Type your query of type 'quit' to answer")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                chat_response = await self.ask_query(query)
                print("\n" + chat_response)
            except Exception as e:
                print(f"Error: {str(e)}")

    async def cleanup(self):
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())