import requests
import time
import csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth
import os

BASE_URL = "https://habr.com"
URL = "https://habr.com/ru/articles/page{}/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

links = []

page = 1
while len(links) < 20:
    r = requests.get(URL.format(page), headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    titles = soup.find_all("a", class_="tm-title__link")

    for t in titles:
        link = urljoin(BASE_URL, t.get("href"))
        if "/articles/" in link:
            links.append(link)

        if len(links) >= 20:
            break

    page += 1
    time.sleep(1)


names = []
company = []
company_description = []
date = []
rating = []
text = []
urls = []
field = []

for link in links:
    try:
        r = requests.get(link, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")

        title = soup.find("h1")
        names.append(title.text.strip() if title else "")

        comp = soup.find("a", class_="tm-company-card__name")
        user = soup.find("a", class_="tm-user-info__username")

        if comp:
            company.append(comp.text.strip())
        elif user:
            company.append(user.text.strip())
        else:
            company.append("")

        desc = soup.find("div", class_="tm-company-card__description")
        if desc:
            company_description.append(desc.text.strip())
        else:
            company_description.append("-")

        d = soup.find("span", class_="tm-article-datetime-published")
        if d and d.time:
            date.append(d.time.get("datetime", "")[:10])
        else:
            date.append("")

        rate = soup.find("span", class_="tm-votes-lever__score-counter")
        rating.append(rate.text.strip() if rate else "0")

        body = soup.find("div", class_="article-formatted-body")
        if body:
            text.append(body.text.replace("\n", " ").strip())
        else:
            text.append("")

        f = ""
        if comp and comp.get("href"):
            try:
                comp_url = urljoin(BASE_URL, comp.get("href"))
                r2 = requests.get(comp_url, headers=headers)
                soup2 = BeautifulSoup(r2.text, "html.parser")

                cats = soup2.find_all("a", class_="tm-company-profile__categories-text")
                for c in cats:
                    f += c.text.strip() + ", "
            except:
                pass

        if f == "":
            hubs = soup.find_all("span", class_="tm-publication-hub__link-container")
            for h in hubs:
                f += h.text.strip() + " "

        field.append(f.strip(", "))
        urls.append(link)
        print("+", names[-1])
    except Exception as e:
        print("ошибка:", link)

    time.sleep(1)


pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))
os.makedirs("pdf", exist_ok=True)


def save_pdf(title, company_name, company_desc, date, rating, field, text, url, idx):
    filename = f"pdf/article_{idx}.pdf"

    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    x = 40
    y = height - 40
    max_width = width - 80
    line_height = 14

    def new_page():
        nonlocal y
        c.showPage()
        c.setFont("DejaVu", 10)
        y = height - 40

    def draw(text_line):
        nonlocal y

        words = text_line.split()
        line = ""

        for word in words:
            test = (line + " " + word).strip()

            if stringWidth(test, "DejaVu", 10) <= max_width:
                line = test
            else:
                if y < 40:
                    new_page()
                c.drawString(x, y, line)
                y -= line_height
                line = word

        if line:
            if y < 40:
                new_page()
            c.drawString(x, y, line)
            y -= line_height

    c.setFont("DejaVu", 10)

    draw(f"Title: {title}")
    draw(f"Company: {company_name}")
    draw(f"Company description: {company_desc}")
    draw(f"Date: {date}")
    draw(f"Rating: {rating}")
    draw(f"Field: {field}")
    draw(f"URL: {url}")
    draw("Text:")
    draw(text)

    c.save()


with open("habr.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["title", "company", "company_description", "date", "rating", "field", "text", "url"])

    i = 0
    for title, comp, desc, d, r, fld, txt, u in zip(names, company, company_description, date, rating, field, text, urls):
        i += 1
        writer.writerow([title, comp, desc, d, r, fld, txt, u])
        save_pdf(title, comp, desc, d, r, fld, txt, u, i)
