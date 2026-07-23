"""
ai/tools/implementations/python_sandbox.py

Why this file exists:
    Executes short Python snippets for the user in a genuinely restricted
    environment: a separate subprocess (crashes/hangs cannot take down the
    API server), a hard wall-clock timeout, and CPU/memory limits via the
    Unix `resource` module when available. On Windows, the timeout still
    applies, but OS memory limits require a container or job-object wrapper.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

try:
    import resource
except ModuleNotFoundError:
    resource = None

from app.ai.tools.tool import Tool, ToolResult

_TIMEOUT_SECONDS = 5
_MAX_MEMORY_BYTES = 128 * 1024 * 1024  # 128MB
_MAX_OUTPUT_CHARS = 4000


def _limit_resources():
    """Runs in the child process before exec when Unix resource limits exist."""
    if resource is None:
        return
    resource.setrlimit(resource.RLIMIT_CPU, (_TIMEOUT_SECONDS, _TIMEOUT_SECONDS))
    resource.setrlimit(resource.RLIMIT_AS, (_MAX_MEMORY_BYTES, _MAX_MEMORY_BYTES))


class PythonSandboxTool(Tool):
    @property
    def name(self) -> str:
        return "python_sandbox"

    @property
    def description(self) -> str:
        return "Executes a short Python snippet in an isolated subprocess and returns stdout."

    async def execute(self, arguments: dict) -> ToolResult:
        code = arguments.get("code", "")
        if not code.strip():
            return ToolResult(output="", success=False, error="Missing 'code' argument")

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "snippet.py"
            script_path.write_text(code, encoding="utf-8")

            subprocess_kwargs = {"cwd": tmpdir}
            if resource is not None:
                subprocess_kwargs["preexec_fn"] = _limit_resources

            try:
                process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-I",
                    str(script_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    **subprocess_kwargs,
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=_TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(output="", success=False, error=f"Execution exceeded {_TIMEOUT_SECONDS}s timeout")
            except Exception as exc:
                return ToolResult(output="", success=False, error=f"Execution failed: {exc}")

            if process.returncode != 0:
                error_text = stderr.decode(errors="replace")[:_MAX_OUTPUT_CHARS]
                return ToolResult(output="", success=False, error=error_text or "Non-zero exit code")

            output = stdout.decode(errors="replace")[:_MAX_OUTPUT_CHARS]
            return ToolResult(output=output)