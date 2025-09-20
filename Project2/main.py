import asyncio
from src.tiki_crawler import TikiCrawler


async def main():
    """Entry point - Simple and clean main function"""
    
    # Initialize crawler 
    crawler = TikiCrawler(
        input_file="dataset\\product_ids.csv",
        output_folder="products_json",
        batch_size=1000,
        concurrent_requests=50,
        max_retries=5
    )
    
    # Load product IDs and start crawling
    crawler.load_product_ids()
    await crawler.crawl()


if __name__ == "__main__":
    asyncio.run(main())