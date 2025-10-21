from __future__ import annotations
import asyncio
import logging
from mcp.server.fastmcp import FastMCP

# Configure logging to write to stderr.
logging.basicConfig(level=logging.INFO)
mcp = FastMCP(name="demo")

@mcp.tool()
async def reverse_string(text: str) -> str:
    """Reverse a string of text.

    Args:
        text: The text to reverse.

    Returns:
        The reversed string.
    """
    return text[::-1]

@mcp.tool()
async def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers together.

    Args:
        a: First number (floating point).
        b: Second number (floating point).

    Returns:
        The product of a and b.
    """
    return a * b

async def serve() -> None:
    """Run the FastMCP server over STDIO."""
    await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(serve())
