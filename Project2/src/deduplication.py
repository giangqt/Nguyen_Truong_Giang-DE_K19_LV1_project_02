import os
import json


class DeduplicationUtils:
    """Utilities for handling duplicate detection and removal"""
    
    @staticmethod
    def deduplicate_list(items):
        """Remove duplicates from list while preserving order"""
        return list(dict.fromkeys(items))
    
    @staticmethod
    def get_already_crawled_ids(output_folder):
        """Get set of product IDs that were already successfully crawled"""
        crawled_ids = set()
        
        if not os.path.exists(output_folder):
            return crawled_ids
        
        for filename in os.listdir(output_folder):
            if filename.startswith("products_") and filename.endswith(".json"):
                try:
                    filepath = os.path.join(output_folder, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for product in data:
                            if product.get('id'):
                                crawled_ids.add(str(product['id']))
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
        
        return crawled_ids
    
    @staticmethod
    def check_duplicate_products_in_output(output_folder):
        """Check for duplicate products across all batch files"""
        product_ids_seen = {}
        
        if not os.path.exists(output_folder):
            return
        
        for filename in os.listdir(output_folder):
            if filename.startswith("products_") and filename.endswith(".json"):
                try:
                    filepath = os.path.join(output_folder, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for product in data:
                            product_id = str(product.get('id', 'unknown'))
                            if product_id in product_ids_seen:
                                product_ids_seen[product_id].append(filename)
                            else:
                                product_ids_seen[product_id] = [filename]
                except Exception as e:
                    print(f"Error checking duplicates in {filename}: {e}")
        
        duplicates = {pid: files for pid, files in product_ids_seen.items() 
                     if len(files) > 1}
        
        if duplicates:
            print(f"\n⚠️  Found {len(duplicates)} duplicate products:")
            for product_id, files in list(duplicates.items())[:5]:
                print(f"   Product {product_id}: {files}")
            if len(duplicates) > 5:
                print(f"   ... and {len(duplicates) - 5} more")
        else:
            print("✅ No duplicate products found in output files")