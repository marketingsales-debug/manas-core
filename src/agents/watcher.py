import logging
import re
import time
from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class WatcherAgent(BaseAgent):
    """
    Watcher Agent: Navigates to a URL, observes it for a while, captures text/screenshots,
    and returns an analysis of what transpired on the page.
    """
    def __init__(self, name: str = "Watcher", llm_router=None, memory=None):
        super().__init__(name, llm_router, memory)
        self.sensory = None
        try:
            from .sensory_processing import SensoryProcessing
            self.sensory = SensoryProcessing(self.llm_router)
        except ImportError:
            self.log("Failed to load SensoryProcessing module.")

    def run(self, task: str, **kwargs) -> AgentResult:
        if not self.sensory:
            return AgentResult(False, "Sensory module not available.")
            
        # Try to extract a URL from the task instruction
        urls = re.findall(r'(https?://[^\s]+)', task)
        url = urls[0] if urls else None
        
        if not url:
            return AgentResult(False, "No valid URL found in the task instruction to watch. Please provide a full http:// or https:// URL.")

        self.status = f"watching {url}"
        self.log(f"Starting to watch URL: {url}")
        
        if not self.sensory.init_browser(headless=True):
             return AgentResult(False, "Could not initialize browser.")
             
        res = self.sensory.browse_to(url)
        if "failed" in res.lower():
             self.sensory.close_browser()
             return AgentResult(False, res)
             
        self.log(f"Arrived at {url}. Observing for 5 seconds...")
        time.sleep(5)
        
        # Gather context
        text = self.sensory.get_page_text()
        screenshot_bytes = self.sensory.capture_screenshot()
        
        analysis = "No visual capabilities available."
        prompt = f"Analyze this UI for task: {task}\nVisible text: {text[:1000]}"
        
        if screenshot_bytes and self.llm_router:
            self.log("Capturing screenshot and sending to Vision LLM...")
            analysis = self.llm_router.generate(
                prompt=prompt, 
                task_type="vision", 
                image_bytes=screenshot_bytes
            )
        elif self.llm_router:
             self.log("No vision available, falling back to text analysis...")
             analysis = self.llm_router.generate(prompt=prompt, task_type="reasoning")

        self.sensory.close_browser()
        
        output = f"Watched {url}.\nAnalysis:\n{analysis}"
        
        if self.memory and hasattr(self.memory, 'store'):
            try:
                self.memory.store(
                    content=f"Observation from watching {url}: {analysis}",
                    memory_type="episodic",
                    tier="short_term" 
                )
                self.log("Stored observation in short-term memory.")
            except Exception as e:
                self.log(f"Memory store warning: {e}")
                
        self.status = "idle"
        return AgentResult(True, output, logs="\n".join(self.logs))
