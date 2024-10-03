# tools/WebSearch_Tool.py

import os
import requests
import sys
import time
import random
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DEBUG = os.environ.get('DEBUG') == 'True'

def log_debug(message):
    if DEBUG:
        print(message)

def get_random_user_agent():
    ua = UserAgent()
    return ua.random

def WebSearch_Tool(query: str, num_results: int = 10, max_retries: int = 3):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,/;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    search_url = f"https://www.google.com/search?q={query}&num={num_results}"
    log_debug(f"Search URL: {search_url}")
    
    for attempt in range(max_retries):
        try:
            # Rotate user agents
            headers['User-Agent'] = get_random_user_agent()
            
            # Configure retry strategy
            retry_strategy = Retry(
                total=3,
                backoff_factor=0.3,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session = requests.Session()
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            # Add a random delay before each request
            time.sleep(random.uniform(1, 3))
            
            response = session.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = []
            
            for g in soup.find_all('div', class_='g'):
                anchor = g.find('a')
                title = g.find('h3').text if g.find('h3') else 'No title'
                url = anchor.get('href', 'No URL') if anchor else 'No URL'
                
                description = ''
                description_div = g.find('div', class_=['VwiC3b', 'yXK7lf'])
                if description_div:
                    description = description_div.get_text(strip=True)
                else:
                    description = g.get_text(strip=True)
                
                search_results.append({
                    'title': title,
                    'description': description,
                    'url': url
                })
            
            if DEBUG:
                print(f"Successfully retrieved {len(search_results)} search results for query: {query}")
                print(f"Search results preview: {search_results[:5]}")
            
            return search_results
        
        except requests.RequestException as e:
            error_message = f"Error performing search for query '{query}' (Attempt {attempt + 1}/{max_retries}): {str(e)}"
            if DEBUG:
                print(error_message)
            
            if attempt == max_retries - 1:
                return []
            
            # Exponential backoff
            time.sleep((2 ** attempt) + random.random())
    
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
        print("Failed to retrieve search results")
