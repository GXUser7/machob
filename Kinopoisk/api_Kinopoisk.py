import requests
import csv
import time

API_KEY = "M110TH7-9A64ZBK-PXQFWXC-0S3AW6M"

url = "https://api.poiskkino.dev/v1.4/movie"

headers = {
    "X-API-KEY": API_KEY
}

all_movies = []
page = 1

while len(all_movies) < 250:
    params = {
        "page": page,
        "limit": 10,
        "sortField": "rating.kp",
        "sortType": -1,
        "notNullFields": ["rating.kp", "votes.kp"],
        "rating.kp": "7-10",
        "votes.kp": "50000-10000000",
    }

    response = requests.get(url, headers=headers, params=params)
    
    print(f"\n--- Страница {page} ---")
    print(f"Статус: {response.status_code}")
    print(f"URL: {response.url[:120]}...")
    
    data = response.json()
    print(f"Ключи в ответе: {list(data.keys())}")
    
    if "message" in data:
        print(f"ОШИБКА API: {data['message']}")
        break
    if "docs" not in data:
        print(f"Нет ключа 'docs' в ответе")
        print(f"Ответ: {data}")
        break
    
    movies = data["docs"]
    
    if not movies:
        print("Фильмы закончились (пустой docs)")
        break
    
    all_movies.extend(movies)
    print(f"Получено: {len(movies)} | Всего собрано: {len(all_movies)}")

    if len(movies) < 10:
        print("Последняя страница (меньше 10 элементов)")
        break

    page += 1
    time.sleep(0.3)

print(f"\n=== ИТОГО: {len(all_movies)} фильмов ===")

names = []
country = []
category = []
year = []
rating = []
votes = []
description = []

for m in all_movies:
    names.append(m.get("name", "") or m.get("alternativeName", "") or "")
    
    if m.get("countries"):
        country.append(m["countries"][0]["name"])
    else:
        country.append("")
    
    if m.get("genres"):
        category.append(m["genres"][0]["name"])
    else:
        category.append("")
    
    year.append(m.get("year", ""))
    rating.append(m.get("rating", {}).get("kp", ""))
    votes.append(m.get("votes", {}).get("kp", ""))
    
    desc = m.get("description", "") or m.get("shortDescription", "") or ""
    description.append(desc.replace('\n', ' ').replace('\r', ' '))

with open("top250.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["name", "country", "category", "year", "rating", "votes", "description"])
    for row in zip(names, country, category, year, rating, votes, description):
        writer.writerow(row)

print(f"Сохранено в top250.csv")