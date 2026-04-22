import requests

SEARCH_URL = "https://www.pathofexile.com/api/trade/search/Mirage"
FETCH_URL = "https://www.pathofexile.com/api/trade/fetch/{}?query={}"

# your query payload would go here (simplified example)
payload = {
    "query": {},
    "sort": {"price": "asc"}
}

# Step 1: search
res = requests.post(SEARCH_URL, json=payload).json()

query_id = res["id"]
item_ids = res["result"][:1]  # first item

# Step 2: fetch item
fetch_res = requests.get(
    FETCH_URL.format(",".join(item_ids), query_id)
).json()

item = fetch_res["result"][0]

print("Whisper message:")
print(item["listing"]["whisper"])