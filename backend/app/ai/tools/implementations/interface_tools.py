"""
ai/tools/implementations/interface_tools.py

Why this file exists:
    The spec calls several tools out explicitly as "(interface)" — Web
    Search, Weather, Browser automation, Email, Calendar — meaning: define
    the contract and wiring now, but the actual external API key/vendor
    choice is a deployment-time decision, not something to hardcode. Each
    class below is fully wired into the Tool framework and registry; only
    the concrete HTTP call to a real provider (SerpAPI, OpenWeather,
    Playwright, Gmail API, Google Calendar API) is left as a clearly
    marked extension point, since which vendor to use is your call.
"""

from app.ai.tools.tool import Tool, ToolResult


class WebSearchTool(Tool):
    """Interface tool: wire to a real search API (Brave Search API,
    SerpAPI, Bing Search) when you choose one."""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Searches the web for current information on a query."

    async def execute(self, arguments: dict) -> ToolResult:
        query = arguments.get("query", "")
        if not query:
            return ToolResult(output="", success=False, error="Missing 'query' argument")
        return ToolResult(
            output="",
            success=False,
            error="web_search is not configured — wire a search provider API key to enable this tool",
        )


class WeatherTool(Tool):
    """Interface tool: wire to a real weather API (OpenWeatherMap,
    National Weather Service) when you choose one."""

    @property
    def name(self) -> str:
        return "weather"

    @property
    def description(self) -> str:
        return "Gets current weather conditions for a location."

    async def execute(self, arguments: dict) -> ToolResult:
        location = arguments.get("location", "")
        if not location:
            return ToolResult(output="", success=False, error="Missing 'location' argument")
        return ToolResult(
            output="", success=False, error="weather is not configured — wire a weather provider API key to enable this tool"
        )


class BrowserAutomationTool(Tool):
    """Interface tool: wire to Playwright/Puppeteer or a hosted browser
    automation service when needed."""

    @property
    def name(self) -> str:
        return "browser_automation"

    @property
    def description(self) -> str:
        return "Navigates and interacts with web pages programmatically."

    async def execute(self, arguments: dict) -> ToolResult:
        return ToolResult(output="", success=False, error="browser_automation is not configured")


class EmailTool(Tool):
    """Interface tool: wire to the Gmail API or SMTP once OAuth scopes /
    credentials for sending mail on the user's behalf are set up."""

    @property
    def name(self) -> str:
        return "email"

    @property
    def description(self) -> str:
        return "Sends or reads email on the user's behalf."

    async def execute(self, arguments: dict) -> ToolResult:
        return ToolResult(output="", success=False, error="email is not configured")


class CalendarTool(Tool):
    """Interface tool: wire to Google Calendar API once OAuth scopes are
    set up (can reuse the Google OAuth client from Phase 4)."""

    @property
    def name(self) -> str:
        return "calendar"

    @property
    def description(self) -> str:
        return "Reads or creates calendar events on the user's behalf."

    async def execute(self, arguments: dict) -> ToolResult:
        return ToolResult(output="", success=False, error="calendar is not configured")
