from bs4 import BeautifulSoup
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
driver = webdriver.Chrome(options=chrome_options)

names = []
country = []
category = []
year = []
rating = []
links = []
description = []

for page in range(1, 6):
    while True:
        url = f"https://www.kinopoisk.ru/lists/movies/top250/?page={page}"
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "styles_root__dtojy")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        all_films = soup.find_all("div", class_="styles_root__dtojy")
        print(f"cтраница {page} найдено {len(all_films)}")
        if len(all_films) == 50:
            break
        else:
            print("cтраница загрузилась криво")

    for i in all_films:
        names.append(i.find("div", class_="desktop-list-main-info_mainTitle__qkaXI").text)
        info = i.find("div", class_="desktop-list-main-info_additionalInfo__Qdq1X").text
        country.append(info.split(' • ')[0])
        category.append(info.split(' • ')[1].split('\xa0\xa0')[0])
        rating.append(i.find("span", class_="styles_kinopoiskValuePositive__drZK2 styles_kinopoiskValue__wuWe_ styles_top250Type__CJzTF").text)
        buff = i.find("span", class_="desktop-list-main-info_secondaryText__gwhDJ").text.split(',')
        links.append(i.find("a", class_="styles_poster__u9xhS styles_root__vaZRT")["href"])
        if len(buff) == 3:
            year.append(buff[1].strip())
        else:
            year.append(buff[0])

for i in links:
    while True:
        url = f"https://www.kinopoisk.ru{i}"
        print(url)
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "styles_paragraph__V0fA2")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        prop = soup.find("p", class_="styles_paragraph__V0fA2").text
        print(prop)

        if prop == None:
            print(f"Текст не найден")
        else:
            description.append(prop)
            break

driver.quit()


with open("films.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["name", "country", "category", "year", "rating", "description"])
    for i, j, l, y, r, d in zip(names, country, category, year, rating, description):
        writer.writerow([i, j, l, y, r, d])