import requests
import subprocess
import webbrowser
import os
import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AgentSystem:
    """Advanced agent system for automation tasks"""
    
    def __init__(self):
        self.tools = {
            'web_search': self.web_search,
            'open_browser': self.open_browser,
            'execute_command': self.execute_command,
            'read_file': self.read_file,
            'list_files': self.list_files
        }
        self.allowed_commands = {"dir", "echo", "pwd", "whoami"}
    
    def execute_agent_task(self, task_description: str) -> str:
        """Execute complex agent tasks"""
        try:
            # Parse task description to determine which tool to use
            task_lower = task_description.lower()
            
            if any(keyword in task_lower for keyword in ['search', 'google', 'find']):
                return self.web_search(task_description)
            elif any(keyword in task_lower for keyword in ['open', 'browser', 'website']):
                return self.open_browser(task_description)
            elif any(keyword in task_lower for keyword in ['run', 'execute', 'command']):
                return self.execute_command(task_description)
            elif any(keyword in task_lower for keyword in ['read', 'file']):
                return self.read_file(task_description)
            elif any(keyword in task_lower for keyword in ['list', 'directory']):
                return self.list_files(task_description)
            else:
                return (
                    "Agent planner is available, but this task needs a supported action. "
                    "Try listing files, reading a file, opening a browser, or running a safe command."
                )
                
        except Exception as e:
            logger.error(f"Error executing agent task: {e}")
            return f"Error executing task: {str(e)}"
    
    def web_search(self, query: str) -> str:
        """Perform web search (placeholder - would integrate with search API)"""
        results = self.web_search_results(query)
        if not results:
            return (
                f"Search intent detected for: {query}. "
                "No live results were available, so the web tool returned an offline fallback."
            )
        lines = [f"{index + 1}. {item['title']} - {item['url']}" for index, item in enumerate(results)]
        return "\n".join(lines)

    def web_search_results(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            response = requests.get(
                "https://duckduckgo.com/html/",
                params={"q": query},
                timeout=6,
                headers={"User-Agent": "VIRA-AI/2.0"},
            )
            response.raise_for_status()
            html = response.text
            matches = re.findall(
                r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                html,
                flags=re.IGNORECASE | re.DOTALL,
            )
            results = []
            for url, title in matches[:limit]:
                clean_title = re.sub(r"<.*?>", "", title).strip()
                results.append(
                    {
                        "type": "web",
                        "title": clean_title,
                        "url": url,
                        "snippet": clean_title,
                    }
                )
            return results
        except Exception as e:
            logger.warning(f"Web search unavailable: {e}")
            return []
    
    def open_browser(self, url: str) -> str:
        """Open URL in browser"""
        try:
            # Extract URL from task description
            if 'http' in url:
                webbrowser.open(url)
                return f"Opened browser with URL: {url}"
            else:
                # Assume it's a search query
                search_url = f"https://www.google.com/search?q={url.replace(' ', '+')}"
                webbrowser.open(search_url)
                return f"Opened browser with search: {search_url}"
        except Exception as e:
            return f"Error opening browser: {str(e)}"
    
    def execute_command(self, command: str) -> str:
        """Execute system command"""
        try:
            # Extract command from task description
            if 'command' in command:
                cmd = command.split('command', 1)[1].strip()
            else:
                cmd = command

            command_name = cmd.split()[0].lower() if cmd.split() else ""
            if command_name not in self.allowed_commands:
                return (
                    f"Blocked command '{command_name or cmd}'. "
                    f"Allowed commands: {', '.join(sorted(self.allowed_commands))}."
                )
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return f"Command executed successfully:\n{result.stdout}"
            else:
                return f"Command failed with error:\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Command execution timed out"
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def read_file(self, file_path: str) -> str:
        """Read file content"""
        try:
            # Extract file path from task description
            if 'file' in file_path:
                path = file_path.split('file', 1)[1].strip()
            else:
                path = file_path
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return f"File content ({path}):\n{content[:500]}..." if len(content) > 500 else f"File content ({path}):\n{content}"
            
        except FileNotFoundError:
            return f"File not found: {file_path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def list_files(self, directory: str) -> str:
        """List files in directory"""
        try:
            # Extract directory path from task description
            if 'directory' in directory:
                path = directory.split('directory', 1)[1].strip()
            elif 'folder' in directory:
                path = directory.split('folder', 1)[1].strip()
            else:
                path = directory
            
            if not os.path.exists(path):
                return f"Directory does not exist: {path}"
            
            files = os.listdir(path)
            file_list = "\n".join(files)
            
            return f"Files in {path}:\n{file_list}"
            
        except Exception as e:
            return f"Error listing files: {str(e)}"

# Global agent instance
agent_system = AgentSystem()
