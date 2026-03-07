import logging
import json
import time
from typing import List, Dict
from pathlib import Path
import subprocess

logger = logging.getLogger(__name__)


class ScouterAgent:
    """
    Discovery Agent — Browses the web to find new tools and capabilities.
    Uses Playwright when available, falls back to requests+BeautifulSoup.
    """
    def __init__(self, name: str, llm_router, sensory, metadata_dir: str, knowledge_graph=None):
        self.name = name
        self.llm_router = llm_router
        self.sensory = sensory
        self.knowledge_graph = knowledge_graph
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.discovery_dir = self.metadata_dir.parent / "discovery"
        self.discovery_dir.mkdir(parents=True, exist_ok=True)
        self.capability_catalog_path = self.metadata_dir / "capability_catalog.json"
        self._load_catalog()

    def _load_catalog(self):
        if self.capability_catalog_path.exists():
            with open(self.capability_catalog_path, "r") as f:
                self.catalog = json.load(f)
        else:
            self.catalog = {"discovery_date": time.time(), "tools": []}

    def _save_catalog(self):
        with open(self.capability_catalog_path, "w") as f:
            json.dump(self.catalog, f, indent=2)

    def _fetch_page(self, url: str) -> str:
        """
        Fetches a web page. Tries Playwright first (full JS rendering),
        falls back to requests+BeautifulSoup (static HTML).
        """
        # Method 1: Try Playwright (full browser)
        try:
            self.sensory.init_browser(headless=True)
            self.sensory.browse_to(url)
            page_text = self.sensory.get_page_text()
            self.sensory.close_browser()
            if page_text and len(page_text) > 100:
                logger.info(f"{self.name}: Fetched via Playwright: {url}")
                return page_text
        except Exception as e:
            logger.debug(f"{self.name}: Playwright failed ({e}), trying requests...")

        # Method 2: Fallback to requests + BeautifulSoup
        try:
            import requests
            try:
                from bs4 import BeautifulSoup
                has_bs4 = True
            except ImportError:
                has_bs4 = False

            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "Manas/1.0 (AI Discovery Agent)"
            })
            resp.raise_for_status()

            if has_bs4:
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
                logger.info(f"{self.name}: Fetched via requests+BS4: {url}")
                return text[:15000]
            else:
                # Raw HTML fallback
                return resp.text[:15000]
        except Exception as e:
            logger.warning(f"{self.name}: All fetch methods failed for {url}: {e}")
            return ""

    def scout(self, url: str = "https://altern.ai/?utm_source=awesomeaitools") -> str:
        """Browse a URL and discover tools."""
        logger.info(f"{self.name}: Scouting {url}...")

        page_text = self._fetch_page(url)
        if not page_text:
            return f"❌ Could not fetch {url}. Check your internet connection."

        # Analyze page content via LLM to extract tool info
        prompt = (
            f"Analyze the following text from {url} and identify any AI tools, frameworks, or libraries "
            f"that would be useful for an autonomous AI agent. Return a JSON list of objects with "
            f"'name', 'description', 'url', and 'category'.\n\n"
            f"TEXT:\n{page_text[:10000]}"
        )

        extraction_res = self.llm_router.generate(prompt=prompt, task_type="reasoning")

        # Parse LLM JSON output
        json_str = extraction_res.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        try:
            new_tools = json.loads(json_str)
            count = 0
            for tool in new_tools:
                if isinstance(tool, dict) and tool.get('name'):
                    name = tool['name']
                    if name not in [t['name'] for t in self.catalog['tools']]:
                        self.catalog['tools'].append(tool)
                        count += 1
                        
                        # Phase 14: KnowledgeGraph Ingestion
                        if self.knowledge_graph:
                            entity_id = name.lower().replace(" ", "_").replace("/", "_")
                            self.knowledge_graph.add_entity(entity_id, name, "tool", properties=tool)
                            category_id = tool.get("category", "tool_category").lower().replace(" ", "_")
                            self.knowledge_graph.add_entity(category_id, tool.get("category", "Category"), "category")
                            self.knowledge_graph.add_relation(entity_id, category_id, "belongs_to")

            self._save_catalog()
            return f"✅ Scouting complete. Discovered {count} new tools. Total in catalog: {len(self.catalog['tools'])}."
        except Exception as e:
            return f"⚠️ Discovered tools but couldn't parse: {e}. Raw: {extraction_res[:300]}"

    def search_github(self, query: str, limit: int = 5) -> List[Dict]:
        """Search GitHub for repositories. Tries gh CLI first, falls back to public API."""
        logger.info(f"{self.name}: Searching GitHub for '{query}'...")
        
        # 1. Try gh CLI
        try:
            cmd = ["gh", "repo", "search", query, "--limit", str(limit), "--json", "fullName,description,url,stargazerCount"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                repos = json.loads(res.stdout)
                results = []
                for repo in repos:
                    results.append({
                        "name": repo["fullName"],
                        "description": repo["description"],
                        "url": repo["url"],
                        "stars": repo["stargazerCount"],
                        "category": "github_repo"
                    })
                return results
        except Exception as e:
            logger.debug(f"{self.name}: gh search failed ({e}), trying public API fallback...")

        # 2. Fallback to requests (Public Search API)
        try:
            import requests
            api_url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={limit}"
            resp = requests.get(api_url, timeout=15, headers={
                "User-Agent": "Manas/1.0 (AI Discovery Agent)",
                "Accept": "application/vnd.github.v3+json"
            })
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for repo in data.get("items", []):
                    results.append({
                        "name": repo["full_name"],
                        "description": repo["description"],
                        "url": repo["html_url"],
                        "stars": repo["stargazers_count"],
                        "category": "github_repo"
                    })
                return results
            else:
                logger.warning(f"{self.name}: GitHub API fallback failed: {resp.status_code} {resp.text}")
                return []
        except Exception as e:
            logger.error(f"{self.name}: All GitHub search methods failed: {e}")
            return []

    def search_github_bounties(self, logic: str = "bounty+language:python", limit: int = 5) -> List[Dict]:
        """
        Phase 37: Web3 Bounty Hunting
        Actively scans GitHub issues/repos for paid bounties to monetize.
        """
        logger.info(f"{self.name}: Hunting GitHub Bounties for: '{logic}'...")
        try:
            import requests
            # We search specifically for issues with bounty labels or repos with bounty descriptions
            api_url = f"https://api.github.com/search/issues?q={logic}+state:open&sort=created&order=desc&per_page={limit}"
            resp = requests.get(api_url, timeout=15, headers={
                "User-Agent": "Manas/1.0 (AI Bounty Hunter)",
                "Accept": "application/vnd.github.v3+json"
            })
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for issue in data.get("items", []):
                    results.append({
                        "title": issue["title"],
                        "url": issue["html_url"],
                        "body": issue.get("body", "")[:200] + "...",
                        "bounty_source": "github_issue"
                    })
                return results
            else:
                logger.warning(f"{self.name}: GitHub Bounty API failed: {resp.status_code} {resp.text}")
                return []
        except Exception as e:
            logger.error(f"{self.name}: Failed to hunt bounties: {e}")
            return []

    def clone_repo(self, repo_url: str) -> str:
        """Clone a GitHub repository into the discovery directory."""
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        dest_path = self.discovery_dir / repo_name
        
        if dest_path.exists():
            return f"✅ Repository {repo_name} already exists at {dest_path}."

        logger.info(f"{self.name}: Cloning {repo_url} to {dest_path}...")
        try:
            # Try gh repo clone first
            cmd = ["gh", "repo", "clone", repo_url, str(dest_path)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                self.catalog['tools'].append({
                    "name": repo_name,
                    "url": repo_url,
                    "path": str(dest_path),
                    "category": "cloned_repo",
                    "discovery_date": time.time()
                })
                self._save_catalog()
                return f"✅ Successfully cloned {repo_name} to {dest_path}."
            else:
                # Fallback to standard git clone
                logger.info(f"{self.name}: gh clone failed, falling back to git clone...")
                cmd = ["git", "clone", repo_url, str(dest_path)]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    self.catalog['tools'].append({
                        "name": repo_name,
                        "url": repo_url,
                        "path": str(dest_path),
                        "category": "cloned_repo",
                        "discovery_date": time.time()
                    })
                    self._save_catalog()
                    return f"✅ Successfully cloned {repo_name} (git fallback) to {dest_path}."
                else:
                    return f"❌ Failed to clone {repo_name}: {res.stderr}"
        except Exception as e:
            return f"❌ Error cloning {repo_name}: {e}"

    def scout_github_trending(self) -> str:
        """Scout GitHub trending repos — uses gh if available, otherwise falls back to scraping."""
        try:
            # Try gh first
            results = self.search_github("stars:>1000", limit=10) # Simple heuristic for "trending"
            if results:
                count = 0
                for repo in results:
                    if repo['name'] not in [t['name'] for t in self.catalog['tools']]:
                        self.catalog['tools'].append(repo)
                        count += 1
                self._save_catalog()
                return f"✅ Scouting GitHub trending (via gh) complete. Discovered {count} new tools."
        except:
            pass
        return self.scout("https://github.com/trending?since=daily")

    def scout_github_topic(self, topic: str) -> str:
        """Scout a specific GitHub topic via search."""
        results = self.search_github(f"topic:{topic}", limit=10)
        if results:
            count = 0
            for repo in results:
                if repo['name'] not in [t['name'] for t in self.catalog['tools']]:
                    self.catalog['tools'].append(repo)
                    count += 1
            self._save_catalog()
            return f"✅ Scouting GitHub topic '{topic}' complete. Discovered {count} new tools."
        return self.scout(f"https://github.com/topics/{topic}")

    def get_catalog_summary(self) -> str:
        """Returns a human-readable summary of discovered tools."""
        if not self.catalog['tools']:
            return "Capability catalog is empty. Run a scout mission first."

        summary = "📋 Discovered Capabilities:\n"
        for tool in self.catalog['tools'][:15]:
            name = tool.get('name', '?')
            desc = tool.get('description', '')[:60]
            summary += f"  • **{name}**: {desc}\n"

        if len(self.catalog['tools']) > 15:
            summary += f"\n  ...and {len(self.catalog['tools']) - 15} more."

        return summary
