import requests
import dotenv
import os
import json
import logging
import httpx

from typing import Optional

class CustomGoogleSearch:
    def __init__(self):
        self.url : str = "https://www.googleapis.com/customsearch/v1"

        self.params : dict[str, str] = {
            "key" : os.getenv("CSE_API_KEY"),
            "cx" : os.getenv("CSE_ID")
            # "callback" : "hndlr"
        }

        self.headers : dict[str, str] = {
            "Accept" : "application/json"
        }

    async def call_search_on_query(self, query: str = None, num_of_results = 1) -> Optional[tuple[dict[str, str],list[dict[str, str]]]]:
        self.params["q"] = query
        self.params["num"] = num_of_results
        try:
            # response = requests.get(url=self.url, params=self.params, headers=self.headers)
            async with httpx.AsyncClient() as client:
                 response = await client.get(
                    url=self.url,
                    params=self.params,
                    headers=self.headers
                )
            if response.status_code == 200:
                response_object : dict[any, any] = response.json()
                search_info : dict[str, str] = response_object["searchInformation"] or {}
                search_items : list[dict[str, str]] = response_object["items"] or []
                return (search_info, search_items)
            
            # Return a single string (server already formats this for the user)
            try:
                j = response.json()
                err = j.get("error", {}).get("message", "")
            except Exception:
                err = response.text[:500]
            msg = f"Show following message as is to user. CSE HTTP {response.status_code}: {err}"
            logging.error(msg)
            return msg

        except Exception as err:
            msg = f"Show following message as is to user. Unknown error: {err}"
            logging.error(msg)
            return msg

def main() -> None:
    import asyncio
    async def _demo():
        searcher = CustomGoogleSearch()
        res = await searcher.call_search_on_query("cricket", 3)
        print(res)
    asyncio.run(_demo())

if __name__ == "__main__":
    dotenv.load_dotenv()
    main()


        