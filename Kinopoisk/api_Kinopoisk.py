import requests
import csv

API_KEY = "M110TH7-9A64ZBK-PXQFWXC-0S3AW6M"

url = "https://api.poiskkino.dev/v1.4/movie"

params = {
    "lists": "top250",
    "limit": 250,
    "sortField": "top250",
    "sortType": 1
}

headers = {
    "X-API-KEY": API_KEY
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

names = []
country = []
category = []
year = []
rating = []
description = []

movies = data["docs"]

for m in movies:
    names.append(m.get("name", ""))
    if m.get("countries"):
        country.append(m["countries"][0]["name"])
    if m.get("genres"):
        category.append(m["genres"][0]["name"])
    year.append(m.get("year", ""))
    rating.append(m.get("rating", {}).get("kp", ""))
    description.append(m.get("description", "").replace('\n', ' '))

with open("top250.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["name", "country", "category", "year", "rating", "description"])
    for i, j, l, y, r, d in zip(names, country, category, year, rating, description):
        writer.writerow([i, j, l, y, r, d])