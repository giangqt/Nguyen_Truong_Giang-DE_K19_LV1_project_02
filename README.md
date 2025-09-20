# 🛒 Tiki Product Data Collector

## 🚀 Introduction
  - This project is to collect product information from Tiki.vn using product IDs.
  - The pipeline fetches product details via Tiki’s API, processes the description content, and saves the results into structured JSON files.

---

## 🗂 Project Structure
Project2/
│
├── __pycache__/
├── dataset/
├── src/
├── main.py
└── requirements.txt
🛠 Requirements
  - Python 3.10+
  - Required libraries:
    ```bash
    pip install -r requirements.txt
    ```

`requirements.txt`:
```txt
pandas
requests
aiohttp
aiofiles
tqdm
```

---

## 📡 API Details
  - List product IDs: Provided in dataset/product_ids.csv
  - Product detail API:
    ```bash
    https://api.tiki.vn/product-detail/api/v1/products/<product_id>
    ```
  - The pipeline sends requests to the above API for each product ID.

---

## 📈 Features
  - Automatically splits output into multiple JSON files (≈1000 products/file)
  - Handles asynchronous downloading for speed
  - Standardizes product description field. Includes product:
    ```bash
    id, name, url_key, price, description, and images
    ```
---

## 📬 Contact
Email: ng.truonggiang2417@gmail.com

---
