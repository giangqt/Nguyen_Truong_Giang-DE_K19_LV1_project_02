import os
import json
import aiofiles
from collections import defaultdict


class FileHandler:
    """Handles all file operations for the crawler"""
    
    def __init__(self, output_folder):
        self.output_folder = output_folder
    
    async def save_batch(self, products, batch_index):
        """Save batch to JSON file"""
        filename = f"{self.output_folder}/products_{batch_index+1}.json"
        async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(products, ensure_ascii=False, indent=2))
    
    async def save_failed_products_by_error(self, failed_products):
        """Save failed products grouped by error code"""
        if not failed_products:
            return
            
        # Group failed products by error code
        failed_by_error = defaultdict(list)
        for failed_product in failed_products:
            error_code = failed_product.get("error_code", "UNKNOWN")
            failed_by_error[error_code].append(failed_product)
        
        # Save each error type to separate files
        for error_code, products in failed_by_error.items():
            filename = f"{self.output_folder}/failed_{error_code.lower()}.json"
            
            # Load existing failed products for this error code
            existing_failed = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        existing_failed = json.load(f)
                except Exception as e:
                    print(f"Error loading existing {filename}: {e}")
            
            # Combine and deduplicate
            existing_ids = {item.get("product_id") for item in existing_failed}
            new_failed = [p for p in products if p.get("product_id") not in existing_ids]
            all_failed = existing_failed + new_failed
            
            # Save to file
            async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(all_failed, ensure_ascii=False, indent=2))
            
            print(f"💾 Saved {len(new_failed)} new {error_code} failures to {filename}")
            print(f"📊 Total {error_code} failures: {len(all_failed)}")
        
        # Also save a consolidated failed products list
        all_failed_path = f"{self.output_folder}/all_failed_products.json"
        async with aiofiles.open(all_failed_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(failed_products, ensure_ascii=False, indent=2))
        
        print(f"💾 Saved all failed products to {all_failed_path}")
        
        # Print detailed error breakdown
        print(f"\n📊 DETAILED ERROR BREAKDOWN:")
        total_failed = sum(len(products) for products in failed_by_error.values())
        for error_code, products in sorted(failed_by_error.items()):
            percentage = (len(products) / total_failed * 100) if total_failed > 0 else 0
            print(f"   {error_code}: {len(products)} failures ({percentage:.1f}%)")
        print(f"   TOTAL FAILED: {total_failed}")
    
    def load_existing_results(self, stats, has_missing_fields_func):
        """Load statistics from existing files for resume functionality"""
        if not os.path.exists(self.output_folder):
            return
            
        # Load existing successful results
        for filename in os.listdir(self.output_folder):
            if filename.startswith("products_") and filename.endswith(".json"):
                try:
                    filepath = os.path.join(self.output_folder, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for product in data:
                            stats.add_success()
                            if has_missing_fields_func(product):
                                stats.add_missing_fields()
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        # Load existing failed results from error-specific files
        for filename in os.listdir(self.output_folder):
            if filename.startswith("failed_") and filename.endswith(".json"):
                try:
                    filepath = os.path.join(self.output_folder, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        failed_data = json.load(f)
                        for failed_item in failed_data:
                            error_code = failed_item.get("error_code", "UNKNOWN")
                            stats.failed += 1
                            stats.error_codes[error_code] += 1
                            stats.failed_products.append(failed_item)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")