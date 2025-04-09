from flask import Flask, render_template, request
from serpapi import GoogleSearch
import requests

app = Flask(__name__)

# Live conversion rate from USD to INR
def get_live_usd_to_inr():
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        data = response.json()
        return data["rates"].get("INR", 83.15)
    except Exception:
        return 83.15

# SerpAPI Key
SERP_API_KEY = "e22917284ef385bf533ed0745cb1d396bfb06115470d1fd4d2634e15051c2757"

# Allowed platforms
ALLOWED_SOURCES = ["amazon", "flipkart", "ebay", "croma", "reliance digital", "reliancedigital", "zepto"]

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []

    if request.method == 'POST':
        product_name = request.form['query']
        inr_rate = get_live_usd_to_inr()

        # Search from both India and US
        search_params = [
            {"gl": "in", "hl": "en"},
            {"gl": " us", "hl": "en"}
        ]

        for loc in search_params:
            params = {
                "engine": "google_shopping",
                "q": product_name,
                "api_key": SERP_API_KEY,
                "gl": loc["gl"],
                "hl": loc["hl"]
            }

            search = GoogleSearch(params)
            results_dict = search.get_dict()
            shopping_results = results_dict.get("shopping_results", [])

            for item in shopping_results:
                price = item.get("extracted_price", 0)
                source = item.get("source", "").lower()

                # Skip invalid or low prices
                if price is None or price < 1:
                    continue

                if not any(site in source for site in ALLOWED_SOURCES):
                    continue

                # Convert USD to INR only for US results
                if loc["gl"] == "us":
                    price = round(price * inr_rate, 2)
                else:
                    price = round(price, 2)

                # Fix eBay redirection
                link = item.get("link", "#")
                if "ebay" in source and "rover.ebay" in link:
                    search_term = product_name.replace(" ", "+")
                    link = f"https://www.ebay.com/sch/i.html?_nkw={search_term}"

                results.append({
                    "title": item.get("title", "No Title"),
                    "price": price,
                    "link": link,
                    "image": item.get("thumbnail", ""),
                    "source": item.get("source", "Unknown")
                })

        # Sort by price ascending
        results.sort(key=lambda x: x['price'])

    return render_template('index.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
