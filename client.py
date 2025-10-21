"""Basic MCP client that uses the modern Google GenAI SDK for tool calling.

This client connects to an MCP server via STDIO, discovers its tools
and forwards natural‑language queries to Gemini.  The new Google
GenAI SDK introduces a `Client` object as the central entry point and
supports function calling directly in `generate_content`:contentReference[oaicite:11]{index=11}.
If the model decides to call a tool, the client executes the request
via MCP and sends the result back to the model as a `function_response`.
"""

from __future__ import annotations
import asyncio
import os
from contextlib import AsyncExitStack
from typing import List

from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters

from google import genai
from google.genai import types


class MCPGenAIClient:
    def __init__(self, model_name: str = "gemini-2.0-flash") -> None:
        # Initialise a GenAI client.  The new SDK picks up your API key from
        # GEMINI_API_KEY or GOOGLE_API_KEY automatically:contentReference[oaicite:12]{index=12}.
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = genai.Client()
        self.model_name = model_name
        self.exit_stack = AsyncExitStack()
        self.session: ClientSession | None = None
        self.stdio = None
        self.write = None

    async def connect(self, server_script_path: str) -> None:
        """Start the server and open an MCP session over STDIO."""
        params = StdioServerParameters(command="python", args=[server_script_path])
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()
        response = await self.session.list_tools()
        print("Connected to server with tools:", [t.name for t in response.tools])

    async def _tools_for_model(self) -> List[types.Tool]:
        """
        Convert MCP tool metadata into GenAI SDK `Tool` objects.

        Each MCP tool provides a name, description and JSON‑Schema input
        definition.  We use this metadata to create a
        `FunctionDeclaration` and wrap it inside a `Tool`.  Returning
        `Tool` instances instead of dictionaries prevents the
        `ValidationError` raised by Pydantic when raw dicts are passed
        directly into `GenerateContentConfig`:contentReference[oaicite:13]{index=13}.
        """
        assert self.session is not None
        response = await self.session.list_tools()
        tools: List[types.Tool] = []
        for tool in response.tools:
            function_decl = types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=tool.inputSchema,
            )
            tools.append(types.Tool(function_declarations=[function_decl]))
        return tools

    async def ask(self, query: str) -> str:
        """Send a query to Gemini and handle any tool calls manually."""
        assert self.session is not None
        response = await self.client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=genai.types.GenerateContentConfig(
                temperature=0,
                tools=[self.session],  # <-- built-in MCP support, auto tool-calling
                # automatic_function_calling=genai.types.AutomaticFunctionCallingConfig(disable=True),  # optional
            ),
        )
        return response.text

    async def close(self) -> None:
        await self.exit_stack.aclose()


async def main() -> None:
    client = MCPGenAIClient()
    await client.connect("server.py")
    try:
        while True:
            query = input("Ask a question (or 'quit' to exit): ")
            if query.lower() == "quit":
                break
            answer = await client.ask(query)
            print("Gemini:", answer)
    finally:
        await client.close()

if __name__ == "__main__":
    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()
    asyncio.run(main())
