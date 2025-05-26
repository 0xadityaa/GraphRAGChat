import asyncio
import os
import json
import aiohttp
import aiofiles
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, FilterChain, DomainFilter
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from urllib.parse import urlparse, urljoin
import subprocess
from pathlib import Path
import time
from datetime import datetime


async def download_media_file(session: aiohttp.ClientSession, url: str, output_dir: str, media_type: str) -> str:
    """
    Downloads a media file (image, video, audio) to the specified directory.
    
    Args:
        session: aiohttp session for downloading
        url: URL of the media file
        output_dir: Directory to save the file
        media_type: Type of media (images, videos, audio)
    
    Returns:
        Local file path if successful, None if failed
    """
    try:
        # Create media type subdirectory
        media_dir = os.path.join(output_dir, media_type)
        os.makedirs(media_dir, exist_ok=True)
        
        # Extract filename from URL
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename or '.' not in filename:
            # Generate filename based on URL hash and timestamp
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            timestamp = int(time.time())
            # Try to guess extension from URL
            if 'jpg' in url or 'jpeg' in url:
                ext = '.jpg'
            elif 'png' in url:
                ext = '.png'
            elif 'gif' in url:
                ext = '.gif'
            elif 'webp' in url:
                ext = '.webp'
            elif 'mp4' in url:
                ext = '.mp4'
            elif 'webm' in url:
                ext = '.webm'
            elif 'mp3' in url:
                ext = '.mp3'
            else:
                ext = '.bin'
            filename = f"media_{url_hash}_{timestamp}{ext}"
        
        filepath = os.path.join(media_dir, filename)
        
        # Download the file
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                async with aiofiles.open(filepath, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                print(f"    📁 Downloaded {media_type}: {filename}")
                return filepath
            else:
                print(f"    ❌ Failed to download {url}: HTTP {response.status}")
                return None
                
    except Exception as e:
        print(f"    ❌ Error downloading {url}: {e}")
        return None


async def scrape_website_comprehensive(start_url: str, output_dir: str, max_pages: int = None, max_depth: int = None):
    """
    Comprehensive website scraping with unlimited crawling and full media extraction.

    Args:
        start_url: The starting URL to begin crawling from.
        output_dir: The directory to save all scraped data.
        max_pages: Maximum number of pages to crawl (None for unlimited).
        max_depth: Maximum depth to crawl (None for unlimited).
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create subdirectories for different types of content
    content_dir = os.path.join(output_dir, "content")
    media_dir = os.path.join(output_dir, "media")
    data_dir = os.path.join(output_dir, "data")
    downloads_dir = os.path.join(output_dir, "downloads")
    
    for directory in [content_dir, media_dir, data_dir, downloads_dir]:
        os.makedirs(directory, exist_ok=True)

    # Extract domain from start URL for filtering
    parsed_url = urlparse(start_url)
    domain = parsed_url.netloc
    
    # Create a filter chain to stay within the same domain
    filter_chain = FilterChain([
        DomainFilter(
            allowed_domains=[domain],
            blocked_domains=[]  # Can add specific subdomains to block if needed
        )
    ])

    # Configure BFS deep crawl strategy for comprehensive crawling
    deep_crawl_strategy = BFSDeepCrawlStrategy(
        max_depth=max_depth or 50,        # Very deep crawling (or unlimited)
        include_external=False,           # Stay within the same domain
        max_pages=max_pages or 10000,    # Very high page limit (or unlimited)
        filter_chain=filter_chain        # Apply domain filtering
    )

    # Configure browser for basic operation
    browser_config = BrowserConfig(
        headless=True,  # Run in headless mode for better performance
        verbose=True
    )

    # Define comprehensive crawler configuration
    crawler_config = CrawlerRunConfig(
        deep_crawl_strategy=deep_crawl_strategy,
        scraping_strategy=LXMLWebScrapingStrategy(),
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=10,          # Lower threshold to capture more content
        stream=True,                      # Enable streaming for real-time processing
        verbose=True,                     # Show crawling progress
        
        # Media and content extraction settings
        exclude_external_images=False,    # Include external images
        wait_for_images=True,            # Ensure images are fully loaded
        
        # Table extraction settings
        table_score_threshold=3,         # Lower threshold to capture more tables
        
        # Simplified JavaScript execution
        js_code="""
            // Simple scroll to load content
            window.scrollTo(0, document.body.scrollHeight);
            setTimeout(() => window.scrollTo(0, 0), 1000);
        """,
    )

    # Statistics tracking
    stats = {
        'pages_crawled': 0,
        'images_found': 0,
        'tables_found': 0,
        'links_found': 0,
        'media_downloaded': 0,
        'start_time': datetime.now(),
        'errors': []
    }

    # Create aiohttp session for downloading media
    async with aiohttp.ClientSession() as session:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            print(f"🚀 Starting comprehensive crawl of: {start_url}")
            print(f"📂 Target domain: {domain}")
            print(f"📊 Max pages: {'Unlimited' if not max_pages else max_pages}")
            print(f"📊 Max depth: {'Unlimited' if not max_depth else max_depth}")
            print("=" * 80)

            # Use streaming mode to process results as they arrive
            try:
                async for result in await crawler.arun(url=start_url, config=crawler_config):
                    stats['pages_crawled'] += 1
                    page_num = stats['pages_crawled']
                    
                    try:
                        if result.success and result.markdown and result.markdown.raw_markdown:
                            # Create safe filename
                            parsed_result_url = urlparse(result.url)
                            path_parts = parsed_result_url.path.strip('/').split('/')
                            filename_base = '_'.join(part for part in path_parts if part) or 'index'
                            
                            # Sanitize filename
                            filename_base = ''.join(c for c in filename_base if c.isalnum() or c in '._-')[:100]
                            if not filename_base:
                                filename_base = f"page_{page_num}"

                            # Save page content
                            content_file = os.path.join(content_dir, f"{filename_base}.md")
                            
                            # Get metadata
                            depth = result.metadata.get('depth', 0) if result.metadata else 0
                            parent_url = result.metadata.get('parent_url', 'N/A') if result.metadata else 'N/A'
                            
                            # Create comprehensive content with metadata
                            content = f"""# {result.url}

**Page:** {page_num}
**Crawl Depth:** {depth}
**Parent URL:** {parent_url}
**Crawl Date:** {datetime.now().isoformat()}
**Status:** Success

---

## Page Content

{result.markdown.raw_markdown}

---

## Metadata
- Word Count: {len(result.markdown.raw_markdown.split()) if result.markdown.raw_markdown else 0}
- Title: {getattr(result, 'title', 'N/A')}
- Description: {getattr(result, 'description', 'N/A')}

"""
                            
                            # Save content
                            try:
                                with open(content_file, 'w', encoding='utf-8') as f:
                                    f.write(content)
                            except Exception as e:
                                stats['errors'].append(f"Error saving content for {result.url}: {e}")
                                print(f"[{page_num:4d}] ❌ Error saving content: {e}")

                            # Process media only if available
                            if hasattr(result, 'media') and result.media:
                                try:
                                    # Handle images
                                    images = result.media.get("images", [])
                                    if images:
                                        stats['images_found'] += len(images)
                                        print(f"[{page_num:4d}] 🖼️  Found {len(images)} images")
                                        
                                        # Save image metadata
                                        image_data = []
                                        for img in images:
                                            img_data = {
                                                'src': img.get('src', ''),
                                                'alt': img.get('alt', ''),
                                                'description': img.get('desc', ''),
                                                'score': img.get('score', 0),
                                                'type': img.get('type', 'image'),
                                                'width': img.get('width'),
                                                'height': img.get('height'),
                                                'page_url': result.url
                                            }
                                            image_data.append(img_data)
                                            
                                            # Download high-scoring images
                                            if img.get('score', 0) > 2 and img.get('src'):
                                                try:
                                                    img_url = urljoin(result.url, img['src'])
                                                    downloaded_path = await download_media_file(session, img_url, media_dir, 'images')
                                                    if downloaded_path:
                                                        stats['media_downloaded'] += 1
                                                        img_data['local_path'] = downloaded_path
                                                except Exception as e:
                                                    print(f"    ❌ Error downloading image {img.get('src', '')}: {e}")
                                        
                                        # Save images metadata
                                        if image_data:
                                            try:
                                                images_file = os.path.join(data_dir, f"{filename_base}_images.json")
                                                with open(images_file, 'w', encoding='utf-8') as f:
                                                    json.dump(image_data, f, indent=2, ensure_ascii=False)
                                            except Exception as e:
                                                print(f"    ❌ Error saving images metadata: {e}")

                                    # Handle tables
                                    tables = result.media.get("tables", [])
                                    if tables:
                                        stats['tables_found'] += len(tables)
                                        print(f"[{page_num:4d}] 📊 Found {len(tables)} tables")
                                        
                                        # Save table data
                                        try:
                                            tables_file = os.path.join(data_dir, f"{filename_base}_tables.json")
                                            with open(tables_file, 'w', encoding='utf-8') as f:
                                                json.dump(tables, f, indent=2, ensure_ascii=False)
                                        except Exception as e:
                                            print(f"    ❌ Error saving tables: {e}")
                                            
                                except Exception as e:
                                    print(f"[{page_num:4d}] ❌ Error processing media: {e}")

                            # Process links
                            if hasattr(result, 'links') and result.links:
                                try:
                                    internal_links = result.links.get("internal", [])
                                    external_links = result.links.get("external", [])
                                    total_links = len(internal_links) + len(external_links)
                                    stats['links_found'] += total_links
                                    
                                    if total_links > 0:
                                        print(f"[{page_num:4d}] 🔗 Found {len(internal_links)} internal + {len(external_links)} external links")
                                        
                                        # Save links data
                                        links_data = {
                                            'page_url': result.url,
                                            'internal_links': internal_links,
                                            'external_links': external_links,
                                            'crawl_date': datetime.now().isoformat()
                                        }
                                        links_file = os.path.join(data_dir, f"{filename_base}_links.json")
                                        with open(links_file, 'w', encoding='utf-8') as f:
                                            json.dump(links_data, f, indent=2, ensure_ascii=False)
                                except Exception as e:
                                    print(f"[{page_num:4d}] ❌ Error processing links: {e}")

                            print(f"[{page_num:4d}] ✅ Depth {depth}: {result.url}")

                        elif not result.success:
                            print(f"[{stats['pages_crawled']:4d}] ❌ Failed: {result.url} - {result.error_message}")
                            stats['errors'].append(f"Failed to crawl {result.url}: {result.error_message}")
                        else:
                            print(f"[{stats['pages_crawled']:4d}] ⚠️  No content: {result.url}")

                    except Exception as e:
                        stats['errors'].append(f"Error processing result {result.url}: {e}")
                        print(f"[{stats['pages_crawled']:4d}] ❌ Error processing result: {e}")

            except Exception as e:
                stats['errors'].append(f"Error during crawl: {e}")
                print(f"❌ Error during crawl: {e}")

            # Generate final report
            end_time = datetime.now()
            duration = end_time - stats['start_time']
            
            # Save comprehensive statistics
            final_stats = {
                'crawl_summary': {
                    'start_url': start_url,
                    'domain': domain,
                    'start_time': stats['start_time'].isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': duration.total_seconds(),
                    'duration_human': str(duration)
                },
                'statistics': {
                    'pages_crawled': stats['pages_crawled'],
                    'images_found': stats['images_found'],
                    'tables_found': stats['tables_found'],
                    'links_found': stats['links_found'],
                    'media_downloaded': stats['media_downloaded'],
                    'errors_count': len(stats['errors'])
                },
                'errors': stats['errors']
            }
            
            stats_file = os.path.join(output_dir, 'crawl_statistics.json')
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(final_stats, f, indent=2, ensure_ascii=False)

            print("\n" + "=" * 80)
            print("🏁 COMPREHENSIVE CRAWL COMPLETED!")
            print("=" * 80)
            print(f"📊 Pages crawled: {stats['pages_crawled']}")
            print(f"🖼️  Images found: {stats['images_found']}")
            print(f"📊 Tables extracted: {stats['tables_found']}")
            print(f"🔗 Links discovered: {stats['links_found']}")
            print(f"💾 Media downloaded: {stats['media_downloaded']}")
            print(f"⏱️  Duration: {duration}")
            print(f"❌ Errors: {len(stats['errors'])}")
            print(f"📂 All data saved to: {output_dir}")
            print("=" * 80)


if __name__ == "__main__":
    # Configuration for comprehensive crawling
    start_url = "https://www.madewithnestle.ca/"
    output_directory = "scraper/comprehensive_data"
    max_pages_limit = None  # Unlimited pages - will crawl everything
    max_depth_limit = None  # Unlimited depth - will go as deep as possible
    
    # Web scraper setup
    try:
        subprocess.run(["crawl4ai-setup"], check=True, capture_output=True)
        print("✅ Crawl4AI setup verified/completed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Crawl4AI setup failed or was not found. Please run 'crawl4ai-setup' manually. Error: {e.stderr.decode()}")
        exit(1)
    except FileNotFoundError:
        print("❌ Crawl4AI setup command not found. Ensure Crawl4AI is installed and in your PATH.")
        exit(1)

    # Run the comprehensive crawl
    print("🚀 Starting comprehensive crawl of Nestlé website...")
    print("⚠️  WARNING: This will crawl ALL available pages and download ALL media!")
    print("📂 This may take a long time and use significant disk space.")
    
    asyncio.run(scrape_website_comprehensive(start_url, output_directory, max_pages_limit, max_depth_limit))
