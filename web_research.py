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
        """Research a topic using multiple sources and add to knowledge base"""
        results = []
        
        # Try DuckDuckGo first
        try:
            search_url = f"https://api.duckduckgo.com/?q={topic}&format=json"
            response = requests.get(search_url, timeout=10)
            data = response.json()
            
            # Get abstract if available
            if data.get('Abstract'):
                metadata = {
                    "source": "duckduckgo",
                    "topic": topic,
                    "type": "abstract"
                }
                self.rag_system.add_document(data['Abstract'], metadata)
                results.append(f"✅ Added DuckDuckGo abstract")
            
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
                        results.append(f"✅ Added related info")
        except Exception as e:
            logging.error(f"DuckDuckGo error: {str(e)}")
        
        # Always try Wikipedia as it's most reliable
        try:
            wiki_result = self._search_wikipedia(topic)
            if wiki_result:
                results.append(wiki_result)
        except Exception as e:
            logging.error(f"Wikipedia error: {str(e)}")
            print(f"Wikipedia error: {str(e)}")
        
        # If still no results, try web search
        if not results:
            try:
                web_result = self._search_web(topic)
                if web_result:
                    results.append(web_result)
            except Exception as e:
                logging.error(f"Web search error: {str(e)}")
                print(f"Web search error: {str(e)}")
        
        if results:
            return f"🔍 *Researched '{topic}':*\n\n" + "\n".join(results)
        else:
            return f"❌ No results found for '{topic}'. Try using 'scrape <url>' with a specific article URL."
    
    def _search_wikipedia(self, topic: str) -> str:
        """Search Wikipedia and add content"""
        try:
            # Wikipedia API search
            search_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": topic,
                "srlimit": 1
            }
            
            response = requests.get(search_url, params=params, timeout=10, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            search_results = data.get('query', {}).get('search', [])
            if not search_results:
                return None
            
            page_title = search_results[0]['title']
            
            # Get page content with more text
            content_params = {
                "action": "query",
                "format": "json",
                "titles": page_title,
                "prop": "extracts",
                "explaintext": True,
                "exsectionformat": "plain"
            }
            
            content_response = requests.get(search_url, params=content_params, timeout=10, headers=self.headers)
            content_response.raise_for_status()
            content_data = content_response.json()
            
            pages = content_data.get('query', {}).get('pages', {})
            for page_id, page_data in pages.items():
                if page_id != '-1' and 'extract' in page_data and page_data['extract']:
                    extract = page_data['extract'][:5000]  # Limit to 5k chars
                    metadata = {
                        "source": "wikipedia",
                        "topic": topic,
                        "title": page_title,
                        "url": f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                    }
                    self.rag_system.add_document(extract, metadata)
                    return f"✅ Added Wikipedia: '{page_title}'"
            
            return None
            
        except Exception as e:
            logging.error(f"Wikipedia search error: {str(e)}")
            print(f"Wikipedia error: {str(e)}")  # Debug print
            return None
    
    def _search_web(self, topic: str) -> str:
        """Search web and scrape first result"""
        try:
            # Try scraping a relevant health website directly
            # For health topics, use reliable sources
            health_keywords = ['diet', 'health', 'nutrition', 'food', 'exercise', 'fitness']
            
            if any(keyword in topic.lower() for keyword in health_keywords):
                # Try Mayo Clinic or similar reliable health sources
                search_term = topic.replace(' ', '+')
                potential_urls = [
                    f"https://www.mayoclinic.org/search/search-results?q={search_term}",
                    f"https://www.healthline.com/search?q1={search_term}",
                ]
                
                # For now, let's use a simpler approach - scrape Wikipedia directly
                wiki_url = f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
                scrape_result = self.scrape_url(wiki_url)
                
                if scrape_result['success'] and len(scrape_result['content']) > 100:
                    metadata = {
                        "source": "web_scrape",
                        "topic": topic,
                        "url": wiki_url,
                        "title": scrape_result['title']
                    }
                    self.rag_system.add_document(scrape_result['content'], metadata)
                    return f"✅ Added article: '{scrape_result['title']}'"
            
            return None
            
        except Exception as e:
            logging.error(f"Web search error: {str(e)}")
            print(f"Web search error: {str(e)}")  # Debug print
            return None
    
    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape multiple URLs and add to knowledge base"""
        results = []
        
        for url in urls:
            result = self.add_url_to_knowledge_base(url)
            results.append({"url": url, "result": result})
            time.sleep(1)  # Be polite, don't hammer servers
        
        return results