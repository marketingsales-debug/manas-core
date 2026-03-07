import logging
import json
import subprocess
from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)

class BashTool:
    name = "bash"
    description = "Execute a shell command. Example: 'ls -la', 'pytest', 'python script.py'"
    trigger_words = ["bash", "shell", "cmd"]
    
    def __init__(self, cwd: str):
        self.cwd = cwd

    def run(self, args: str, context: dict = None) -> dict:
        cmd = args.strip()
        try:
             res = subprocess.run(cmd, shell=True, cwd=self.cwd, capture_output=True, text=True, timeout=30)
             out = (res.stdout + "\n" + res.stderr).strip()
             if res.returncode == 0:
                 return {"success": True, "output": out or "Command executed successfully.", "data": {"exit_code": 0}}
             else:
                 return {"success": False, "output": out[-2000:], "data": {"exit_code": res.returncode}}
        except Exception as e:
             return {"success": False, "output": str(e), "data": {}}

class CoderAgent(BaseAgent):
    """
    Open Hands / Devin style Autocoding Agent.
    Runs a loop: Thought -> Action (Tool) -> Observation.
    Has access to Python, Bash, FileReader, FileWriter.
    """
    def __init__(self, name: str = "Coder", llm_router=None, memory=None, working_dir: str = "."):
        super().__init__(name, llm_router, memory, working_dir)
        self.max_iterations = 10
        
        # Initialize internal tool dispatcher specifically for the Coder
        from ..executor.tools import ToolDispatcher, FileReaderTool, FileWriterTool, PythonREPLTool
        self.dispatcher = ToolDispatcher()
        self.dispatcher.register(FileReaderTool())
        self.dispatcher.register(FileWriterTool())
        self.dispatcher.register(PythonREPLTool())
        self.dispatcher.register(BashTool(self.working_dir))
        
    def run(self, task: str, **kwargs) -> AgentResult:
        if not self.llm_router:
            return AgentResult(False, "LLMRouter not available for coding loop.")
            
        self.status = "coding"
        self.log(f"Starting auto-coding task: {task}")
        self.log(f"Working Directory: {self.working_dir}")
        
        system_prompt = """You are the Manas Coder Agent, an autonomous software engineer.
You solve coding tasks by executing a series of commands.
You have the following tools available:
- file_reader: Read a file ('file_reader: path/to/file.py')
- file_writer: Write to a file ('file_writer: path/to/file.py|content')
- python_repl: Run python code ('python_repl: print(1+1)')
- bash: Run a bash command ('bash: ls -la' or 'bash: pytest')

ALWAYS respond in this EXACT JSON format:
{
  "thought": "What I need to do next and why",
  "tool": "tool_name_here",
  "args": "arguments_for_the_tool",
  "done": false
}

Set "done": true ONLY when you have fully completed the task and verified it works. When done is true, the tool and args fields can be empty or null.
"""

        conversation = [{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Task: {task}"}]
        
        final_output = ""
        
        for iteration in range(self.max_iterations):
            self.log(f"Iteration {iteration+1}/{self.max_iterations}...")
            
            # Format history for LLM prompt
            prompt = "\n".join(f"{msg['role'].upper()}: {msg['content']}" for msg in conversation)
            
            response_text = self.llm_router.generate(prompt=prompt, task_type="coding")
            
            try:
                # Extract JSON from response
                json_str = response_text[response_text.find("{"):response_text.rfind("}")+1]
                action_data = json.loads(json_str)
            except Exception as e:
                self.log(f"Failed to parse LLM JSON output: {e}\nRaw: {response_text[:200]}")
                conversation.append({"role": "user", "content": f"Error: Failed to parse JSON. Please strictly return ONLY valid JSON.\nRaw output was: {response_text}"})
                continue
                
            thought = action_data.get("thought", "")
            tool_name = action_data.get("tool", "")
            args = action_data.get("args", "")
            is_done = action_data.get("done", False)
            
            self.log(f"Thought: {thought}")
            
            # Save thought to conversation
            conversation.append({"role": "assistant", "content": json.dumps(action_data, indent=2)})
            
            if is_done:
                self.log("Task marked as COMPLETED by agent.")
                final_output = thought
                break
                
            if not tool_name or not args:
                self.log("Warning: Tool or args missing, asking for retry.")
                conversation.append({"role": "user", "content": "Error: You didn't specify a tool or args but done is false."})
                continue
                
            self.log(f"Action: {tool_name} => {args[:100]}...")
            
            # Map specific tool prefixes
            dispatch_text = f"{tool_name}: {args}"
            res = self.dispatcher.dispatch(dispatch_text)
            
            if not res:
                self.log(f"Tool {tool_name} failed to dispatch or was not found.")
                consequence = f"Tool Execution Failed: {tool_name} not recognized."
            elif not res.get("success"):
                err = res.get("output") or res.get("error", "Unknown error")
                self.log(f"Tool Error: {err[:200]}...")
                consequence = f"Tool Error:\n{err}"
            else:
                out = res.get("output", "Success")
                self.log(f"Tool Success. Output length: {len(str(out))}")
                consequence = f"Tool Execution Output:\n{str(out)[:2000]}"
                
            conversation.append({"role": "user", "content": consequence})
            
        else:
            self.log(f"Hit max iterations ({self.max_iterations}). Task aborted.")
            return AgentResult(False, "Exceeded maximum iterations without finishing.", logs="\n".join(self.logs))
            
        self.status = "idle"
        return AgentResult(True, final_output or "Completed autonomously.", logs="\n".join(self.logs))
