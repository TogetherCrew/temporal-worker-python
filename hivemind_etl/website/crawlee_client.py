import asyncio
from typing import Any

from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
from defusedxml import ElementTree as ET


class CrawleeClient:
    def __init__(
        self,
        max_requests: int = 20,
        headless: bool = True,
        browser_type: str = "chromium",
    ) -> None:
        self.crawler = PlaywrightCrawler(
            max_requests_per_crawl=max_requests,
            headless=headless,
            browser_type=browser_type,
        )

        # do not persist crawled data to local storage
        self.crawler._configuration.persist_storage = False
        self.crawler._configuration.write_metadata = False

        @self.crawler.router.default_handler
        async def request_handler(context: PlaywrightCrawlingContext) -> None:
            context.log.info(f"Processing {context.request.url} ...")

            inner_text = await context.page.inner_text(selector="body")

            if "sitemap.xml" in context.request.url:
                links = self._extract_links_from_sitemap(inner_text)
                await context.add_requests(requests=list(set(links)))
            else:
                await context.enqueue_links()

            data = {
                "url": context.request.url,
                "title": await context.page.title(),
                "inner_text": inner_text,
            }

            await context.push_data(data)

    def _extract_links_from_sitemap(self, sitemap_content: str) -> list[str]:
        """

        Extract URLs from a sitemap XML content.

        Parameters
        ----------
        sitemap_content : str
            The XML content of the sitemap

        Raises
        ------
        ET.ParseError
        If the XML content is malformed

        Returns
        -------
        links : list[str]
            list of valid URLs extracted from the sitemap
        """
        links = []
        try:
            root = ET.fromstring(sitemap_content)
            namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            for element in root.findall("ns:url/ns:loc", namespace):
                url = element.text.strip() if element.text else None
                if url and url.startswith(("http://", "https://")):
                    links.append(url)
        except ET.ParseError as e:
            raise ValueError(f"Invalid sitemap XML: {str(e)}")

        return links

    async def crawl(self, links: list[str]) -> list[dict[str, Any]]:
        """
        Crawl websites and extract data from all inner links under the domain routes.

        Parameters
        ----------
        links : list[str]
            List of valid URLs to crawl

        Returns
        -------
        crawled_data : list[dict[str, Any]]
            List of dictionaries containing crawled data with keys:
            - url: str
            - title: str
            - inner_text: str

        Raises
        ------
        ValueError
            If any of the input URLs is invalid (not starting with http or https)
        TimeoutError
            If the crawl operation times out
        """
        # Validate input URLs
        valid_links = []
        for url in links:
            if url and isinstance(url, str) and url.startswith(("http://", "https://")):
                valid_links.append(url)
            else:
                raise ValueError(f"Invalid URL: {url}")

        try:
            await self.crawler.add_requests(requests=valid_links)
            await asyncio.wait_for(self.crawler.run(), timeout=3600)  # 1 hour timeout
            crawled_data = await self.crawler.get_data()
            return crawled_data.items
        except asyncio.TimeoutError:
            raise TimeoutError("Crawl operation timed out")
