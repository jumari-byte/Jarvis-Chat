# tools/WebSearch_Tool.py

import os
import requests
import sys
from typing import List, Dict, Any

# Ensure these environment variables are set
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.environ.get('GOOGLE_CSE_ID')

def WebSearch_Tool(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        raise ValueError("GOOGLE_API_KEY and GOOGLE_CSE_ID must be set as environment variables")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'key': GOOGLE_API_KEY,
        'cx': GOOGLE_CSE_ID,
        'num': min(num_results, 10)  # Google API allows max 10 results per request
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        search_results = response.json()

        results = []
        for item in search_results.get('items', []):
            results.append({
                'title': item.get('title', 'No title'),
                'description': item.get('snippet', 'No description'),
                'url': item.get('link', 'No URL')
            })

        return results

    except requests.RequestException as e:
        print(f"Error performing search for query '{query}': {str(e)}")
        return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: WebSearch_Tool.py <query> [num_results]")
        sys.exit(1)

    query = sys.argv[1]
    num_results = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    results = WebSearch_Tool(query, num_results)

    if results:
        for result in results:
            print(result)
    else:
        print("No search results found or an error occurred")