import requests
import dotenv
import os
import json

from typing import Optional

class CustomGoogleSearch():
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

    def call_search_on_query(self, query: str = None, num_of_results = 1) -> Optional[tuple[dict[str, str],list[dict[str, str]]]]:
        self.params["q"] = query
        self.params["num"] = num_of_results
        try:
            response = requests.get(url=self.url, params=self.params, headers=self.headers)
            if response.status_code == 200:
                response_object : dict[any, any] = response.json()
                search_info : dict[str, str] = response_object["searchInformation"]
                search_items : list[dict[str, str]] = response_object["items"]
                return (search_info, search_items)
                # for item in search_items:
                #     print(item["title"])
                #     print(item["displayLink"])
                #     print(item["snippet"])
        except Exception as err:
            print(err)

def main() -> None:
    searcher = CustomGoogleSearch()
    search_info, search_items = searcher.call_search_on_query("cricket", 10)
    for item in search_items:
        # print(item)
        print(item["title"])
        print(item["displayLink"])
        print(item["snippet"])
        print("---------------------")

if __name__ == "__main__":
    dotenv.load_dotenv()
    main()


        