import asyncio
import os
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from urllib.parse import urlparse
import subprocess


async def scrape_website(sitemap_url: str, output_dir: str):
    """
    Scrapes a website starting from a sitemap URL and saves the content of each page.

    Args:
        sitemap_url: The URL of the sitemap.
        output_dir: The directory to save the scraped data.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    async with AsyncWebCrawler() as crawler:
        # First, crawl the sitemap to get all page URLs
        sitemap_result = await crawler.arun(
            url=sitemap_url,
            config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS
            )
        )

        if not sitemap_result.success:
            print(f"Failed to crawl sitemap: {sitemap_result.error_message}")
            return

        # Extract URLs from the sitemap content (this is a basic example, might need adjustment based on sitemap format)
        # This example assumes URLs are explicitly listed. A more robust solution would parse XML.
        
        # A simple way to find URLs in markdown (might need improvement)
        page_urls = []
        if sitemap_result.markdown:
            # Look for http/https links in the markdown content of the sitemap
            # This is a simplistic approach and might need refinement based on actual sitemap structure
            import re
            found_urls = re.findall(r'https?://[^\s<>"\'()]+', sitemap_result.markdown.raw_markdown)
            
            # Filter to include only URLs from the same domain as the sitemap
            sitemap_domain = urlparse(sitemap_url).netloc
            for url in found_urls:
                if urlparse(url).netloc == sitemap_domain and url != sitemap_url:
                    page_urls.append(url)
            
            # Remove duplicates
            page_urls = list(set(page_urls))


        if not page_urls:
            print("No page URLs found in the sitemap content. The sitemap might be in XML format or require specific parsing.")
            print("Attempting to use crawler's discovered links as a fallback if the sitemap itself is a page with links.")
            if sitemap_result.links and 'internal' in sitemap_result.links:
                 page_urls = [link['url'] for link in sitemap_result.links['internal']]
                 page_urls = list(set(page_urls)) # Remove duplicates
            if not page_urls:
                print("Still no URLs found. Please check the sitemap structure.")
                return


        print(f"Found {len(page_urls)} URLs to scrape from the sitemap.")

        # Define a single config for streaming
        run_config_streaming = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=50, # Only save pages with meaningful content
            stream=True # Enable streaming for async for
        )
        
        # Pass the single config object using the 'config' parameter
        results_stream = await crawler.arun_many(urls=page_urls, config=run_config_streaming)

        async for result in results_stream:
            if result.success and result.markdown and result.markdown.raw_markdown:
                # Sanitize URL to create a valid filename
                parsed_url = urlparse(result.url)
                # Use path and query to ensure uniqueness, replace slashes to avoid directory issues
                filename_base = str(parsed_url.path + (parsed_url.query or '')).replace('/', '_').replace('?', '_').replace('=', '_')
                if not filename_base or filename_base == '': # Handle root path
                    filename_base = "index"

                # Ensure filename ends with .md
                if not filename_base.endswith('.md'):
                     filename = f"{filename_base}.md"
                else:
                    filename = filename_base


                filepath = os.path.join(output_dir, filename)
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(result.markdown.raw_markdown)
                    print(f"Saved content from {result.url} to {filepath}")
                except Exception as e:
                    print(f"Error saving file {filepath} for url {result.url}: {e}")
            elif not result.success:
                print(f"Failed to crawl {result.url}: {result.error_message}")
            else:
                print(f"No markdown content extracted from {result.url} or content too short.")


if __name__ == "__main__":
    sitemap_url = "https://www.madewithnestle.ca/sitemap"
    output_directory = "scraper/data"
    
    # Web scraper setup
    try:
        subprocess.run(["crawl4ai-setup"], check=True, capture_output=True)
        print("Crawl4AI setup verified/completed.")
    except subprocess.CalledProcessError as e:
        print(f"Crawl4AI setup failed or was not found. Please run 'crawl4ai-setup' manually. Error: {e.stderr.decode()}")
        exit(1)
    except FileNotFoundError:
        print("Crawl4AI setup command not found. Ensure Crawl4AI is installed and in your PATH.")
        exit(1)

    asyncio.run(scrape_website(sitemap_url, output_directory))
