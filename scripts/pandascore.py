import requests

TOKEN = "rpEUd7r7WOqmirBOTqIxeFnz3MgbqhwLjnGWwZb3paM2iNPm0cA"
resp = requests.get(
    "https://api.pandascore.co/lol/matches/running",
    headers={"Authorization": f"Bearer {TOKEN}"},
    params={"page[size]": 50, "sort": "-begin_at"},  # or filter[...] / search[...]
)
print(resp.headers.get("X-Rate-Limit-Remaining"))
print(resp.json())
