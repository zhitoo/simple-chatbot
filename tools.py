from serpapi import GoogleSearch
from dotenv import load_dotenv
import os

load_dotenv()


SERPAPI_KEY = os.getenv("SERPAPI_KEY")


def serpapi_search(query: str):
    search = GoogleSearch(
        {
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 3,
            "engine": "google",
        }
    )
    results = search.get_dict()
    return results.get("organic_results", "چیزی یافت نشد")


tools = [
    {
        "type": "function",
        "function": {
            "name": "serpapi_search",
            "description": "اگر به سرچ نیاز پیدا کردی میتونی از این ابزار استفاده کنی",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "اگر برای پاسخ بهتر نیاز به سرچ داشتی از این ابزار استفاده کن",
                    }
                },
                "required": ["query"],
            },
        },
    }
]
