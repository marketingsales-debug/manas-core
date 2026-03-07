"""
Web Explorer - Learn from the internet.

Like a human browsing the web:
- Search for information
- Read web pages
- Extract and learn from content
- Curiosity-driven exploration
"""

import requests
import time

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


class WebExplorer:
    """
    Explores the internet to learn.

    Uses DuckDuckGo (no API key needed) for search.
    Extracts text from web pages for learning.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Manas/0.1 (Cognitive AI Learning Agent)"
        })
        self.search_history: list[dict] = []
        self.pages_read: list[dict] = []

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Search the web using DuckDuckGo Lite.

        Returns list of {title, url, snippet}.
        """
        try:
            resp = self.session.get(
                "https://lite.duckduckgo.com/lite/",
                params={"q": query},
                timeout=10,
            )
            results = []

            if HAS_BS4:
                soup = BeautifulSoup(resp.text, "html.parser")
                links = soup.find_all("a", class_="result-link")
                snippets = soup.find_all("td", class_="result-snippet")

                for i, link in enumerate(links[:max_results]):
                    result = {
                        "title": link.get_text(strip=True),
                        "url": link.get("href", ""),
                        "snippet": snippets[i].get_text(strip=True) if i < len(snippets) else "",
                    }
                    results.append(result)
            else:
                results = [{"title": "Install beautifulsoup4 for web search", "url": "", "snippet": "pip install beautifulsoup4"}]

            self.search_history.append({
                "query": query,
                "results_count": len(results),
                "timestamp": time.time(),
            })

            return results

        except Exception as e:
            return [{"title": "Search failed", "url": "", "snippet": str(e)}]

    def read_page(self, url: str, max_chars: int = 5000) -> dict:
        """
        Read and extract text from a web page.

        Like a human reading: extracts the meaningful content,
        ignores navigation/ads.
        """
        try:
            resp = self.session.get(url, timeout=10)

            if HAS_BS4:
                soup = BeautifulSoup(resp.text, "html.parser")

                # Remove script/style elements
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()

                text = soup.get_text(separator="\n", strip=True)
                # Clean up whitespace
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                content = "\n".join(lines)[:max_chars]
                title = soup.title.string if soup.title else ""
            else:
                content = resp.text[:max_chars]
                title = ""

            result = {
                "url": url,
                "title": title,
                "content": content,
                "length": len(content),
                "timestamp": time.time(),
            }

            self.pages_read.append(result)
            return result

        except Exception as e:
            return {
                "url": url,
                "title": "Error",
                "content": str(e),
                "length": 0,
                "timestamp": time.time(),
            }

    def learn_about(self, topic: str) -> dict:
        """
        Curiosity-driven learning: search for a topic and read about it.

        Returns extracted knowledge.
        """
        results = self.search(topic, max_results=3)

        knowledge = {
            "topic": topic,
            "sources": [],
            "summary_points": [],
        }

        for result in results:
            if result.get("url"):
                page = self.read_page(result["url"], max_chars=3000)
                knowledge["sources"].append({
                    "title": result.get("title", ""),
                    "url": result["url"],
                    "content_preview": page.get("content", "")[:500],
                })
                # Extract key sentences (simple extraction)
                content = page.get("content", "")
                sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 30]
                knowledge["summary_points"].extend(sentences[:3])

        return knowledge
