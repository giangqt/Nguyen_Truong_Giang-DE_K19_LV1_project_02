from collections import defaultdict
from datetime import datetime


class CrawlStats:
    """Tracks crawling statistics and provides summary reporting"""
    
    def __init__(self):
        self.total_products = 0
        self.completed = 0
        self.failed = 0
        self.error_codes = defaultdict(int)
        self.products_with_missing_fields = 0
        self.failed_products = []  # Store failed product details
        self.start_time = None
        self.end_time = None
        
    def add_success(self):
        self.completed += 1
        
    def add_failure(self, status_code=None, product_id=None, error_message=None):
        self.failed += 1
        if status_code:
            self.error_codes[status_code] += 1
        
        # Store failed product details
        if product_id:
            self.failed_products.append({
                "product_id": product_id,
                "error_code": status_code or "UNKNOWN",
                "error_message": error_message or "",
                "timestamp": datetime.now().isoformat()
            })
            
    def add_missing_fields(self):
        self.products_with_missing_fields += 1
        
    def print_summary(self):
        print("\n" + "="*10 + " CrawL Summary " + "="*10)
        print(f"Total products: {self.total_products}")
        print(f"✅ Completed: {self.completed}")
        print(f"❌ Failed: {self.failed}")
        print("\nError summary (HTTP codes):")
        for code, count in self.error_codes.items():
            print(f"{code}: {count}")
        print(f"\nProducts with missing fields: {self.products_with_missing_fields}")
        
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            print(f"\nExecution time: {duration:.2f} seconds")
            if self.completed > 0:
                print(f"Average time per product: {duration/self.completed:.3f} seconds")