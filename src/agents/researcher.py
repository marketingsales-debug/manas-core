import logging
from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)

class ResearcherAgent(BaseAgent):
    """
    Agent responsible for searching the web, reading pages, and summarizing information.
    Uses WebExplorer (DuckDuckGo Lite) for search and extraction.
    """
    def __init__(self, name: str = "Researcher", llm_router=None, memory=None):
        super().__init__(name, llm_router, memory)
        self.web_explorer = None
        try:
            from ..executor.web import WebExplorer
            self.web_explorer = WebExplorer()
        except ImportError:
            self.log("Failed to load WebExplorer")

    def run(self, task: str, **kwargs) -> AgentResult:
        self.status = "researching"
        self.log(f"Starting research: {task}")
        
        if not self.web_explorer:
            return AgentResult(False, "WebExplorer not available.")
            
        if not self.llm_router:
            return AgentResult(False, "LLMRouter not available for summarization.")
            
        # 1. Determine search query
        query_prompt = f"Based on this research task: '{task}', what is the single best Google search query? Return ONLY the query string, nothing else."
        query = self.llm_router.generate(prompt=query_prompt, task_type="simple").strip('"\'')
        self.log(f"Generated search query: {query}")
        
        # 2. Search
        results = self.web_explorer.search(query, max_results=3)
        if not results:
            return AgentResult(False, "No search results found.")
            
        # 3. Read pages
        read_contents = []
        for res in results:
            url = res.get("url")
            if url:
                self.log(f"Reading {url}...")
                page_data = self.web_explorer.read_page(url, max_chars=3000)
                if page_data.get("content"):
                    read_contents.append(f"Source: {url}\n{page_data['content']}")
                    
        if not read_contents:
            return AgentResult(False, "Failed to extract content from any search results.")
            
        # 4. Summarize
        self.log("Summarizing findings...")
        context = "\n\n---\n\n".join(read_contents)
        summary_prompt = f"Research Task: {task}\n\nSearch Findings:\n{context}\n\nProvide a comprehensive summary addressing the research task based ONLY on the provided findings."
        
        summary = self.llm_router.generate(prompt=summary_prompt, task_type="reasoning")
        
        # 5. Store in memory if available
        if self.memory and hasattr(self.memory, 'store'):
            try:
                self.memory.store(
                    content=f"Research on '{query}': {summary}",
                    memory_type="semantic",
                    tier="long_term"
                )
                self.log("Stored findings in long-term memory.")
            except Exception as e:
                self.log(f"Memory store warning: {e}")
            
        self.status = "idle"
        return AgentResult(True, summary, logs="\n".join(self.logs))
