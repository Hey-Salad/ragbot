import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Any
from rag_system import RAGSystem
from urllib.parse import urlparse
import time

class WebResearcher:
    def __init__(self):
        self.rag_system = RAGSystem()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape content from a URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Get title
            title = soup.title.string if soup.title else urlparse(url).netloc
            
            return {
                "success": True,
                "url": url,
                "title": title,
                "content": text[:10000],  # Limit to 10k chars
                "length": len(text)
            }
            
        except Exception as e:
            logging.error(f"Error scraping {url}: {str(e)}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
    
    def add_url_to_knowledge_base(self, url: str) -> str:
        """Scrape URL and add to knowledge base"""
        result = self.scrape_url(url)
        
        if not result["success"]:
            return f"Failed to scrape {url}: {result['error']}"
        
        # Add to RAG system
        metadata = {
            "source": "web",
            "url": url,
            "title": result["title"],
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        add_result = self.rag_system.add_document(result["content"], metadata)
        
        return f"✅ Added content from {result['title']}\n{add_result}\nSource: {url}"
    
    def research_topic(self, topic: str, num_sources: int = 3) -> str:
        """Research a topic using DuckDuckGo and add to knowledge base"""
        try:
            # Use DuckDuckGo Instant Answer API
            search_url = f"https://api.duckduckgo.com/?q={topic}&format=json"
            response = requests.get(search_url, timeout=10)
            data = response.json()
            
            results = []
            
            # Get abstract if available
            if data.get('Abstract'):
                metadata = {
                    "source": "duckduckgo",
                    "topic": topic,
                    "type": "abstract"
                }
                self.rag_system.add_document(data['Abstract'], metadata)
                results.append(f"Added abstract about {topic}")
            
            # Get related topics
            if data.get('RelatedTopics'):
                for item in data['RelatedTopics'][:num_sources]:
                    if isinstance(item, dict) and item.get('Text'):
                        metadata = {
                            "source": "duckduckgo",
                            "topic": topic,
                            "type": "related"
                        }
                        self.rag_system.add_document(item['Text'], metadata)
                        results.append(f"Added: {item['Text'][:50]}...")
            
            if results:
                return f"✅ Researched '{topic}':\n" + "\n".join(results)
            else:
                return f"No results found for '{topic}'"
                
        except Exception as e:
            logging.error(f"Error researching {topic}: {str(e)}")
            return f"Error researching topic: {str(e)}"
    
    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape multiple URLs and add to knowledge base"""
        results = []
        
        for url in urls:
            result = self.add_url_to_knowledge_base(url)
            results.append({"url": url, "result": result})
            time.sleep(1)  # Be polite, don't hammer servers
        
        return results