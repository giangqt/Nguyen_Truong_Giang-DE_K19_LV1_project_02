🛒 Tiki Product Data Collector

🚀 Introduction
  - This project is to collect product information from Tiki.vn using product IDs.
  - The pipeline fetches product details via Tiki’s API, processes the description content, and saves the results into structured JSON files.
🗂 Project Structure
Project2/
│
├── dataset/
│   └── product_ids.csv           
│
├── src/                          
│
├── __pycache__/                 
│
├── main.py                       
└── README.md                     

🛠 Requirements

Python 3.10+

Required libraries:

pip install -r requirements.txt


Example requirements.txt:

requests
pandas
aiohttp
aiofiles
tqdm
beautifulsoup4

⚙️ Running ETL

Run the pipeline to extract, transform, and save product data:

cd Project2
python main.py


Steps:

[EXTRACT] Read product IDs from dataset/product_ids.csv

[TRANSFORM] Clean/standardize product description

[LOAD] Save to JSON files (1000 products per file)

📡 API Details

List product IDs: Provided in dataset/product_ids.csv

Product detail API:

https://api.tiki.vn/product-detail/api/v1/products/<product_id>


The pipeline sends requests to the above API for each product ID.

📈 Features

Automatically splits output into multiple JSON files (≈1000 products/file)

Handles asynchronous downloading for speed

Standardizes product description field

Includes product id, name, url_key, price, description, and images

📬 Contact

Email: your_email@example.com
