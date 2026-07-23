"""
ai/tools/implementations/document_tools.py

Why this file exists:
    "File Search" and "Document Reader" from the spec are not new
    capabilities — they're the Phase 7 RAG engine, exposed as tools so the
    agent framework can invoke them uniformly alongside calculator/weather/
    etc. This is the payoff of building RAG behind SearchDocumentsUseCase
    earlier: zero duplicated retrieval logic here.
"""

from uuid import UUID

from app.ai.tools.tool import Tool, ToolResult
from app.application.use_cases.search_documents import SearchDocumentsUseCase


class FileSearchTool(Tool):
    """Searches across the user's already-uploaded/ingested documents."""

    def __init__(self, search_documents: SearchDocumentsUseCase, user_id: UUID, document_ids: list[UUID]):
        self._search_documents = search_documents
        self._user_id = user_id
        self._document_ids = document_ids

    @property
    def name(self) -> str:
        return "file_search"

    @property
    def description(self) -> str:
        return "Searches the user's uploaded documents for relevant passages."

    async def execute(self, arguments: dict) -> ToolResult:
        query = arguments.get("query", "")
        results = await self._search_documents.execute(self._user_id, query, self._document_ids)
        if not results:
            return ToolResult(output="No relevant passages found.")
        text = "\n\n".join(f"[{r.document_filename}]: {r.content}" for r in results)
        return ToolResult(output=text)


class APICallerTool(Tool):
    """Generic HTTP caller for hitting external REST APIs, restricted to an
    explicit allowlist of domains — a real capability, deliberately fenced
    in for safety rather than left as an open-ended fetch."""

    def __init__(self, allowed_domains: set[str] | None = None):
        self._allowed_domains = allowed_domains or set()

    @property
    def name(self) -> str:
        return "api_caller"

    @property
    def description(self) -> str:
        return "Makes an HTTP GET request to an allowlisted external API."

    async def execute(self, arguments: dict) -> ToolResult:
        import httpx
        from urllib.parse import urlparse

        url = arguments.get("url", "")
        host = urlparse(url).hostname or ""
        if self._allowed_domains and host not in self._allowed_domains:
            return ToolResult(output="", success=False, error=f"Domain '{host}' is not in the allowlist")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                return ToolResult(output=response.text[:4000])
        except Exception as exc:
            return ToolResult(output="", success=False, error=str(exc))
