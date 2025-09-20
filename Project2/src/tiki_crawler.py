import asyncio
import aiohttp
import pandas as pd
import re
import os
import time
from tqdm.asyncio import tqdm_asyncio

from src.crawl_stats import CrawlStats
from src.deduplication import DeduplicationUtils
from src.file_handler import FileHandler


class TikiCrawler:
    """Main crawler class for Tiki products"""
    
    def __init__(self, input_file="product_ids.csv", output_folder="products_json", 
                 batch_size=1000, concurrent_requests=50, max_retries=5):
        self.input_file = input_file
        self.output_folder = output_folder
        self.batch_size = batch_size
        self.concurrent_requests = concurrent_requests
        self.max_retries = max_retries
        self.stats = CrawlStats()
        self.product_ids = []
        self.file_handler = FileHandler(output_folder)
        
    def load_product_ids(self):
        """Load product IDs from CSV file"""
        df = pd.read_csv(self.input_file)
        self.product_ids = df['id'].astype(str).tolist()
        self.stats.total_products = len(self.product_ids)
        print(f"Loaded {len(self.product_ids)} product IDs")
        
    def deduplicate_input_ids(self):
        """Remove duplicate product IDs from input list"""
        original_count = len(self.product_ids)
        self.product_ids = DeduplicationUtils.deduplicate_list(self.product_ids)
        duplicate_count = original_count - len(self.product_ids)
        
        if duplicate_count > 0:
            print(f"🔄 Removed {duplicate_count} duplicate product IDs")
            print(f"📊 Unique products to crawl: {len(self.product_ids)}")
        
        self.stats.total_products = len(self.product_ids)

    def filter_uncrawled_products(self):
        """Remove already crawled products from the queue"""
        already_crawled = DeduplicationUtils.get_already_crawled_ids(self.output_folder)
        
        if already_crawled:
            original_count = len(self.product_ids)
            self.product_ids = [pid for pid in self.product_ids if pid not in already_crawled]
            skipped_count = original_count - len(self.product_ids)
            
            if skipped_count > 0:
                print(f"⏭️  Skipping {skipped_count} already crawled products")
                print(f"🎯 Remaining products to crawl: {len(self.product_ids)}")
        
    def clean_description(self, text):
        """Clean HTML tags and normalize whitespace in description"""
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def has_missing_fields(self, product_data):
        """Check if product has missing required fields"""
        required_fields = ['id', 'name', 'url_key', 'price', 'description', 'images']
        for field in required_fields:
            if field == 'images':
                if not isinstance(product_data.get(field), list) or len(product_data[field]) == 0:
                    return True
            elif not product_data.get(field):
                return True
        return False

    async def fetch_product(self, session, product_id):
        """Fetch single product with retry logic"""
        url = f"https://api.tiki.vn/product-detail/api/v1/products/{product_id}"
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                async with session.get(url, timeout=20) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        product_data = {
                            "id": data.get("id"),
                            "name": data.get("name"),
                            "url_key": data.get("url_key"),
                            "price": data.get("price"),
                            "description": self.clean_description(data.get("description")),
                            "images": [img.get("base_url") for img in data.get("images", [])]
                        }
                        
                        if self.has_missing_fields(product_data):
                            self.stats.add_missing_fields()
                        
                        self.stats.add_success()
                        return product_data
                    else:
                        last_error = f"HTTP {resp.status}"
                        if attempt == 0 and resp.status != 404:
                            print(f"Failed {product_id}: HTTP {resp.status}")
                        
            except asyncio.TimeoutError:
                last_error = "Request timeout"
                if attempt == 0:
                    print(f"Timeout {product_id}")
            except Exception as e:
                last_error = str(e)[:100]  # Limit error message length
                if attempt == 0:
                    print(f"Error {product_id}: {str(e)[:50]}")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
        
        # All attempts failed, record the failure
        error_code = "TIMEOUT" if "timeout" in str(last_error).lower() else "ERROR"
        if "HTTP" in str(last_error):
            error_code = last_error.split()[1] if len(last_error.split()) > 1 else "HTTP_ERROR"
        
        self.stats.add_failure(error_code, product_id, last_error)
        return None

    async def fetch_batch(self, product_ids, batch_num, total_batches):
        """Fetch a batch of products with progress tracking"""
        connector = aiohttp.TCPConnector(limit=self.concurrent_requests)
        async with aiohttp.ClientSession(connector=connector) as session:
            results = []
            print(f"\nProcessing batch {batch_num}/{total_batches} ({len(product_ids)} products)")
            
            for i in range(0, len(product_ids), self.concurrent_requests):
                chunk_ids = product_ids[i:i+self.concurrent_requests]
                tasks = [self.fetch_product(session, pid) for pid in chunk_ids]
                
                chunk_results = await tqdm_asyncio.gather(
                    *tasks, desc=f"Batch {batch_num} - Chunk {i//self.concurrent_requests + 1}"
                )
                
                results.extend([r for r in chunk_results if r is not None])
                print(f"Batch {batch_num} progress: {min(i + self.concurrent_requests, len(product_ids))}/{len(product_ids)}")
            
            return results

    async def crawl(self):
        """Main crawling method with deduplication"""
        self.stats.start_time = time.time()
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Add deduplication steps
        self.deduplicate_input_ids()
        self.file_handler.load_existing_results(self.stats, self.has_missing_fields)
        self.filter_uncrawled_products()
        
        # If no products left to crawl
        if not self.product_ids:
            print("✅ All products already crawled!")
            self.stats.end_time = time.time()
            self.stats.print_summary()
            return
        
        total_batches = (len(self.product_ids) + self.batch_size - 1) // self.batch_size
        print(f"Starting crawl of {len(self.product_ids)} products in {total_batches} batches")
        print(f"Batch size: {self.batch_size}, Concurrent requests: {self.concurrent_requests}")
        print("-" * 50)
        
        for start in range(0, len(self.product_ids), self.batch_size):
            end = min(start + self.batch_size, len(self.product_ids))
            batch_ids = self.product_ids[start:end]
            batch_index = start // self.batch_size
            batch_num = batch_index + 1
            filename = f"{self.output_folder}/products_{batch_num}.json"
            
            # Skip existing batches
            if os.path.exists(filename):
                print(f"Batch {batch_num}/{total_batches} already exists, skipping...")
                continue

            print(f"\n{'='*20} BATCH {batch_num}/{total_batches} {'='*20}")
            print(f"Products {start+1} to {end}")
            
            batch_start = time.time()
            products = await self.fetch_batch(batch_ids, batch_num, total_batches)
            batch_duration = time.time() - batch_start
            
            await self.file_handler.save_batch(products, batch_index)
            
            # Batch summary
            print(f"✅ Batch {batch_num} completed: {len(products)}/{len(batch_ids)} products saved")
            print(f"⏱️  Batch time: {batch_duration:.2f}s, Rate: {len(products)/batch_duration:.2f} products/sec")
            print(f"📊 Overall progress: {self.stats.completed}/{len(self.product_ids)} ({self.stats.completed/len(self.product_ids)*100:.1f}%)")
            
            if self.stats.failed > 0:
                print(f"❌ Failures so far: {self.stats.failed}")
            
            await asyncio.sleep(2)  # Respectful delay
        
        self.stats.end_time = time.time()
        await self.file_handler.save_failed_products_by_error(self.stats.failed_products)
        self.stats.print_summary()
        
        # New deduplication checks
        print("\n" + "="*20 + " POST-CRAWL ANALYSIS " + "="*20)
        DeduplicationUtils.check_duplicate_products_in_output(self.output_folder)