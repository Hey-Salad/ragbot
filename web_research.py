import logging
import time
from typing import Any, Dict, List
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

from config import Config
from rag_system import RAGSystem
from security_utils import validate_public_http_url

logger = logging.getLogger(__name__)


class WebResearcher:
    def __init__(self):
        self.config = Config()
        self.rag_system = RAGSystem()
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "HeySalad-RAGBot/1.0 (+https://github.com/Hey-Salad/ragbot)"
        }

    def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape content from a public URL."""
        allowed, reason = validate_public_http_url(url)
        if not allowed:
            return {"success": False, "url": url, "error": reason}

        try:
            response = self.session.get(
                url,
                headers=self.headers,
                timeout=self.config.REQUEST_TIMEOUT_SECONDS,
                stream=True,
            )
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "").lower()
            if not any(token in content_type for token in ("text/html", "text/plain", "application/xhtml+xml")):
                return {
                    "success": False,
                    "url": url,
                    "error": f"Unsupported content type: {content_type or 'unknown'}",
                }

            content = self._read_limited_response(response)
            soup = BeautifulSoup(content, "html.parser")

            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            text = soup.get_text(separator=" ")
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = " ".join(chunk for chunk in chunks if chunk)
            title = soup.title.string.strip() if soup.title and soup.title.string else urlparse(url).netloc

            return {
                "success": True,
                "url": url,
                "title": title,
                "content": clean_text[:10000],
                "length": len(clean_text),
            }
        except Exception as exc:
            logger.warning("Error scraping %s: %s", url, exc)
            return {"success": False, "url": url, "error": "Unable to scrape URL"}

    def add_url_to_knowledge_base(self, url: str) -> str:
        result = self.scrape_url(url)
        if not result["success"]:
            return f"Failed to scrape {url}: {result['error']}"

        metadata = {
            "source": "web",
            "url": url,
            "title": result["title"],
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        add_result = self.rag_system.add_document(result["content"], metadata)
        return f"Added content from {result['title']}\n{add_result}\nSource: {url}"

    def research_topic(self, topic: str, num_sources: int = 3) -> str:
        results = []

        try:
            response = self.session.get(
                "https://api.duckduckgo.com/",
                params={"q": topic, "format": "json"},
                timeout=self.config.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("Abstract"):
                self.rag_system.add_document(
                    data["Abstract"],
                    {"source": "duckduckgo", "topic": topic, "type": "abstract"},
                )
                results.append("Added DuckDuckGo abstract")

            if data.get("RelatedTopics"):
                for item in data["RelatedTopics"][:num_sources]:
                    if isinstance(item, dict) and item.get("Text"):
                        self.rag_system.add_document(
                            item["Text"],
                            {"source": "duckduckgo", "topic": topic, "type": "related"},
                        )
                        results.append("Added related DuckDuckGo info")
        except Exception as exc:
            logger.warning("DuckDuckGo research failed for %s: %s", topic, exc)

        wiki_result = self._search_wikipedia(topic)
        if wiki_result:
            results.append(wiki_result)

        if not results:
            web_result = self._search_web(topic)
            if web_result:
                results.append(web_result)

        if results:
            return f"Researched '{topic}':\n\n" + "\n".join(results)
        return f"No results found for '{topic}'. Try using 'scrape <url>' with a specific public article URL."

    def _search_wikipedia(self, topic: str) -> str:
        try:
            response = self.session.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "list": "search",
                    "srsearch": topic,
                    "srlimit": 1,
                },
                timeout=self.config.REQUEST_TIMEOUT_SECONDS,
                headers=self.headers,
            )
            response.raise_for_status()
            search_results = response.json().get("query", {}).get("search", [])
            if not search_results:
                return ""

            page_title = search_results[0]["title"]
            content_response = self.session.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "titles": page_title,
                    "prop": "extracts",
                    "explaintext": True,
                    "exsectionformat": "plain",
                },
                timeout=self.config.REQUEST_TIMEOUT_SECONDS,
                headers=self.headers,
            )
            content_response.raise_for_status()
            pages = content_response.json().get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id != "-1" and page_data.get("extract"):
                    extract = page_data["extract"][:5000]
                    self.rag_system.add_document(
                        extract,
                        {
                            "source": "wikipedia",
                            "topic": topic,
                            "title": page_title,
                            "url": f"https://en.wikipedia.org/wiki/{quote_plus(page_title.replace(' ', '_'))}",
                        },
                    )
                    return f"Added Wikipedia article '{page_title}'"
        except Exception as exc:
            logger.warning("Wikipedia research failed for %s: %s", topic, exc)
        return ""

    def _search_web(self, topic: str) -> str:
        try:
            wiki_url = f"https://en.wikipedia.org/wiki/{quote_plus(topic.replace(' ', '_'))}"
            scrape_result = self.scrape_url(wiki_url)
            if scrape_result["success"] and len(scrape_result["content"]) > 100:
                self.rag_system.add_document(
                    scrape_result["content"],
                    {
                        "source": "web_scrape",
                        "topic": topic,
                        "url": wiki_url,
                        "title": scrape_result["title"],
                    },
                )
                return f"Added article '{scrape_result['title']}'"
        except Exception as exc:
            logger.warning("Fallback web search failed for %s: %s", topic, exc)
        return ""

    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        results = []
        for url in urls:
            results.append({"url": url, "result": self.add_url_to_knowledge_base(url)})
            time.sleep(1)
        return results

    def _read_limited_response(self, response: requests.Response) -> bytes:
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > self.config.MAX_SCRAPE_BYTES:
            raise ValueError("Remote document exceeds configured scrape size limit")

        body = bytearray()
        for chunk in response.iter_content(chunk_size=8192):
            body.extend(chunk)
            if len(body) > self.config.MAX_SCRAPE_BYTES:
                raise ValueError("Remote document exceeds configured scrape size limit")
        return bytes(body)
