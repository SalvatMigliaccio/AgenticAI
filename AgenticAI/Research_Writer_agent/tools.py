import httpx 
from langchain.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchRun

#tool 1 - DuckDuckGoSearchRun
# LangChain ships a ready-made wrapper around DuckDuckGo — no API key needed.
# Returns a plain string with the top search results concatenated.
duckduckgo_tool = DuckDuckGoSearchRun(
    name="web_search",
    description="Search the web for information using DuckDuckGo. Useful for when you need to answer questions about current events or general knowledge. Use this tool to find information on the web. Input: a search query string.",
)

#tool 2 Web Scraper
# Fetches the raw text of a web page given its URL. the researcher uses this after web_search to read full articles and extract relevant information.
class ScraperWebsiteTool(BaseTool):
    name: str = "scrape_website"
    description: str = (
        "fetches the full text content of a web page given its URL. Useful for when you need to read full articles and extract relevant information."
        "input: a valid URL string starting with http:// or https://"
    )
    
    def _run(self, url: str) -> str:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
            r = httpx.get(url.strip(), headers=headers, timeout=15, follow_redirects=True)
            r.raise_for_status()  # Raise an error for bad responses
                        # Basic cleanup — strip HTML tags with a simple approach.
            # For production use beautifulsoup4 instead.
            text = r.text
            import re
            text = re.sub(r"<[^>]+>", " ", text)       # remove HTML tags
            text = re.sub(r"\s+", " ", text).strip()    # collapse whitespace
            return text[:10000]  # cap at 10000 chars to stay within context window
        except Exception as e:
            return f"Could not scrape '{url}': {e}"

scrape_tool = ScraperWebsiteTool()
