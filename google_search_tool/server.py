from typing import Any, Optional
from mcp.server.fastmcp import FastMCP
from basic_request import CustomGoogleSearch

import logging
import dotenv
dotenv.load_dotenv()


# IMPORTANT: do NOT print on stdout in an MCP server.
# Send logs to stderr.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

# initialize mcp server
mcp = FastMCP("google-custom-search")

# initialize the search class
search = CustomGoogleSearch()

def format_search_results(search_info: dict[str, str], search_results: list[dict[str, str]]) -> str:
    '''
    Format search results in a readable string

    Args:
        search_info: metadata on search results
        search_results: itemized search results

    return:
        final_result_string: string creating by formatting the search results
    '''

    final_result_string = f'''
    Total results found: {search_info.get("formattedTotalResults", "unknown")}. 
    The top {len(search_results)} results are sent.
    ---------------------
    '''

    for item in search_results:
        final_result_string += f'''
        Title: {item.get("title", "")}
        Link: {item.get("link") or item.get("displayLink", "")}
        Snippet: {item.get("snippet", "")}
        ---------------------
        '''
        
    return final_result_string

@mcp.tool()
async def search_query(query: str, num_of_results: int = 1) -> Optional[str]:
    '''
    Makes a query to google search.

    Args:
        query: string to search on
        num_of_results: number of results to get

    return:
        A string containing metadata on search and top num_of_results search results
    '''
    logging.info("search_query called: %r (top %d)", query, num_of_results)
    try:
        result = await search.call_search_on_query(query, num_of_results=num_of_results)
        logging.info("call_search_on_query type: %s", type(result).__name__)
        # Handle error returns BEFORE unpacking
        if result is None:
            logging.error("call_search_on_query returned None")
            return "Show following message as is to user. Unable to run search, getting nothing!!"
        if isinstance(result, str):
            logging.error("call_search_on_query error: %s", result)
            return "Show following message as is to user. Unable to run search because: " + result

        search_info, search_results = result
        logging.info("Search meta: %s", search_info)
        return format_search_results(search_info, search_results)
    except Exception as e:
        logging.exception("Unhandled exception in search_query")
        return f"Tool crashed: {type(e).__name__}: {e}"

def main():
    # Initialize and run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()    