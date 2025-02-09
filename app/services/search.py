from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime
import concurrent.futures
from openai import OpenAI

from ..utils.logging import log_chat
from tools.WebSearch_Tool import WebSearch_Tool
from tools.get_url_contents import get_url_contents

class SearchService:
    """Service for handling web searches and content extraction."""
    
    def __init__(self, search_client: OpenAI):
        """
        Initialize SearchService.
        
        Args:
            search_client: OpenAI client for search operations
        """
        self.search_client = search_client

    def process_url(self, result: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Process a URL to extract its content.
        
        Args:
            result: Dictionary containing URL information
        
        Returns:
            Dictionary with URL and extracted content, or None if extraction fails
        """
        url = result['url']
        content = get_url_contents(url)
        
        if content:
            return {
                'url': url,
                'content': content[:8000]  # Limit content to 8000 characters
            }
        return None

    def web_search(self, query: str) -> List[Dict[str, str]]:
        """
        Perform web search and extract content from top results.
        
        Args:
            query: Search query string
        
        Returns:
            List of dictionaries containing URL and extracted content
        """
        search_results = WebSearch_Tool(query)
        processed_results = []
        
        # Process top 2 results concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_url = {
                executor.submit(self.process_url, result): result 
                for result in search_results[:2]
            }
            
            for future in concurrent.futures.as_completed(future_to_url):
                result = future.result()
                if result:
                    processed_results.append(result)
        
        return processed_results

    def agent_search_decision(self, 
                            conversation_history: List[Dict[str, str]], 
                            disable_search: bool) -> Tuple[bool, Optional[str]]:
        """
        Decide whether to perform a web search based on conversation context.
        
        Args:
            conversation_history: List of conversation messages
            disable_search: Whether search is explicitly disabled
        
        Returns:
            Tuple of (should_search, search_query)
        """
        if disable_search:
            return False, None

        today = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M")
        
        # Prepare messages for the search decision agent
        messages = [
            {
                "role": "system",
                "content": f"""You are a Search Decision Agent.
Your task is to evaluate the user's query and determine whether a web search is necessary to provide an accurate response. To make this decision, follow these steps:
1. Analyze the query:
-Is the question seeking information that may change frequently (e.g., current events, real-time data)?  
-Does the query reference something highly specific that may not be covered comprehensively?
-Today's date is {today} and current time is {current_time}
2. Check the conversation context: 
-Does the user ask about topics previously discussed? 
-Is the query sufficiently answered by the information already available?
3. Make your decision: 
-Respond with 'SEARCH' if a web search is necessary, followed by the most effective search query without other explanation. Use the same language as the user's query. 
-Respond with 'NO SEARCH' if the query can be answered with your existing knowledge.
4. Aim for efficiency: 
- Avoid unnecessary searches for general knowledge questions. 
- Prioritize searching for time-sensitive or rapidly changing information.
- avoid unnecessary searches for current time."""
            },
            {
                "role": "user",
                "content": f"Decide if a web search is needed:\n\n{json.dumps(conversation_history, indent=2)}"
            }
        ]

        try:
            response = self.search_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=33,
                temperature=0.2
            )

            decision = response.choices[0].message.content.strip()
            
            if decision.startswith("SEARCH"):
                search_query = decision.split("SEARCH", 1)[1].strip()
                return True, search_query
            
            return False, None
            
        except Exception as e:
            log_chat("Search decision", "llama-3.3-70b-versatile", False, str(e))
            return False, None