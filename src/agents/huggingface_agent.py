"""
HuggingFaceAgent - Manas's gateway to the open AI ecosystem.
"""

import logging
import os
from huggingface_hub import HfApi, hf_hub_download
from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)

class HuggingFaceAgent(BaseAgent):
    """
    The HuggingFaceAgent allows Manas to:
    1. Search for models on the Hub.
    2. Download models/datasets for local use.
    3. Interface with HF Inference Endpoints.
    """

    def __init__(self, name: str, llm_router, memory, data_dir: str):
        super().__init__(name, llm_router, memory, data_dir)
        self.api = HfApi(token=os.environ.get("HF_TOKEN"))
        self.model_cache_dir = os.path.join(data_dir, "models")
        os.makedirs(self.model_cache_dir, exist_ok=True)

    def run(self, task: str, **kwargs) -> AgentResult:
        """
        Main execution loop.
        Supported tasks: "search_models", "download_model", "get_info".
        """
        self.log(f"Starting Hugging Face task: {task}")
        
        if task == "search_models":
            query = kwargs.get("query", "")
            return self._search_models(query)
        elif task == "download_model":
            repo_id = kwargs.get("repo_id", "")
            filename = kwargs.get("filename", None)
            return self._download_model(repo_id, filename)
        elif task == "get_info":
            repo_id = kwargs.get("repo_id", "")
            return self._get_model_info(repo_id)
        else:
            return AgentResult(False, f"Unknown task: {task}")

    def _search_models(self, query: str) -> AgentResult:
        """Search for models on the Hub."""
        try:
            models = self.api.list_models(
                search=query,
                limit=5,
                sort="downloads"
            )
            
            results = []
            for m in models:
                results.append({
                    "id": m.modelId,
                    "downloads": m.downloads,
                    "likes": m.likes,
                    "tags": m.tags[:5] if m.tags else []
                })
            
            self.log(f"Found {len(results)} models matching '{query}'")
            return AgentResult(True, results)
        except Exception as e:
            return AgentResult(False, str(e))

    def _download_model(self, repo_id: str, filename: str = None) -> AgentResult:
        """Download a model file or repo."""
        try:
            # If no filename, we download the whole repo (might be large, so we log warning)
            if not filename:
                self.log(f"No filename specified. Attempting to download repo: {repo_id}")
                # For safety, we'll only allow downloading the config for now in auto-mode
                filename = "config.json"

            file_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                cache_dir=self.model_cache_dir
            )
            
            self.log(f"Successfully downloaded {filename} from {repo_id} to {file_path}")
            return AgentResult(True, {"path": file_path, "repo": repo_id})
        except Exception as e:
            return AgentResult(False, str(e))

    def _get_model_info(self, repo_id: str) -> AgentResult:
        """Get detailed metadata for a specific model."""
        try:
            info = self.api.model_info(repo_id)
            details = {
                "id": info.modelId,
                "author": info.author,
                "lastModified": info.lastModified,
                "pipeline_tag": info.pipeline_tag,
                "downloads": info.downloads
            }
            return AgentResult(True, details)
        except Exception as e:
            return AgentResult(False, str(e))
