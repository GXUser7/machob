import glob
import re
from datetime import date, timedelta
from pathlib import Path

import fitz
import pandas as pd


PDF_GLOB = "pdf_articles/*.pdf"
OUTPUT_CSV = "dataset.csv"


def extract_text_from_pdf(pdf_path: str) -> list[str]:
    doc = fitz.open(pdf_path)
    try:
        pages = []
        for current_page in range(len(doc)):
            page = doc.load_page(current_page)
            pages.append(page.get_text("text"))
        return pages
    finally:
        doc.close()


def clean_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        line = line.replace("\xa0", " ")
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    return lines


def normalize_article_text(pages: list[str]) -> str:
    all_lines = []
    for page_text in pages:
        all_lines.extend(clean_lines(page_text))
    return " ".join(all_lines)


def convert_habr_date(raw_date: str) -> str:
    raw_date = raw_date.strip().lower()
    today = date.today()

    if "назад" not in raw_date:
        return raw_date

    number_match = re.search(r"\d+", raw_date)
    number = int(number_match.group(0)) if number_match else 0

    if any(word in raw_date for word in ("секунд", "минут", "мин", "час")):
        return today.isoformat()

    if any(word in raw_date for word in ("день", "дня", "дней")):
        return (today - timedelta(days=number)).isoformat()

    if any(word in raw_date for word in ("недел", "неделю")):
        return (today - timedelta(weeks=number)).isoformat()

    if any(word in raw_date for word in ("месяц", "месяца", "месяцев")):
        return (today - timedelta(days=number * 30)).isoformat()

    if any(word in raw_date for word in ("год", "года", "лет")):
        return (today - timedelta(days=number * 365)).isoformat()

    return today.isoformat()


def parse_first_page_tail(first_page_text: str) -> dict[str, str]:
    lines = clean_lines(first_page_text)

    complexity_words = {"Простой", "Средний", "Сложный"}
    category_words = {
        "Обзор",
        "Кейс",
        "Туториал",
        "Мнение",
        "Дайджест",
        "Перевод",
        "Ретроспектива",
        "Новость",
        "Интервью",
    }
    service_lines = {
        "РЕ КЛА МА",
        "РЕКЛАМА",
        "При поддержке",
        "Подборка курсов от Хабра",
        "Объяснить с",
    }

    published_ago_re = re.compile(
        r"^\d+\s+(?:секунд(?:у|ы)?|минут(?:у|ы)?|мин|час(?:а|ов)?|день|дня|дней|"
        r"недел(?:ю|и|ь)|месяц(?:а|ев)?|год|года|лет)\s+назад$",
        re.IGNORECASE,
    )
    read_time_re = re.compile(r"^\d+\s*мин$")
    views_re = re.compile(r"^\d+(?:[.,]\d+)?\s*[KkКкMmМм]?$")

    result = {
        "UserName": "",
        "TopicTitle": "",
        "Tags": "",
        "Date": "",
        "Categories": "",
    }

    date_index = None
    for index, line in enumerate(lines):
        if published_ago_re.match(line):
            date_index = index
            result["Date"] = convert_habr_date(line)
            if index > 0:
                result["UserName"] = lines[index - 1]
            break

    if date_index is None:
        return result

    meta_index = None
    for index in range(date_index + 1, len(lines)):
        line = lines[index]
        if line in complexity_words or read_time_re.match(line):
            meta_index = index
            break

    if meta_index is None:
        return result

    title_lines = [
        line
        for line in lines[date_index + 1 : meta_index]
        if line not in service_lines
    ]
    result["TopicTitle"] = " ".join(title_lines)

    index = meta_index
    if index < len(lines) and lines[index] in complexity_words:
        index += 1

    if index < len(lines) and read_time_re.match(lines[index]):
        index += 1

    if index < len(lines) and views_re.match(lines[index]):
        index += 1

    tags = []
    categories = []
    while index < len(lines):
        line = lines[index]
        if line in service_lines:
            index += 1
            continue
        if line in category_words:
            categories.append(line)
        else:
            tags.append(line)
        index += 1

    result["Tags"] = ", ".join(tags)
    result["Categories"] = ", ".join(categories)
    return result


def main() -> None:
    all_pdf = sorted(glob.glob(PDF_GLOB))

    records = []
    broken_files = []

    for pdf_path in all_pdf:
        try:
            pages = extract_text_from_pdf(pdf_path)
            first_page_text = pages[0] if pages else ""
            parsed = parse_first_page_tail(first_page_text)

            records.append(
                {
                    "FileName": Path(pdf_path).name,
                    "UserName": parsed["UserName"],
                    "TopicTitle": parsed["TopicTitle"],
                    "Tags": parsed["Tags"],
                    "Date": parsed["Date"],
                    "Categories": parsed["Categories"],
                    "TextArticle": normalize_article_text(pages),
                }
            )
            print(Path(pdf_path).name)
        except Exception as error:
            broken_files.append((pdf_path, error))

    df = pd.DataFrame(
        records,
        columns=[
            "FileName",
            "UserName",
            "TopicTitle",
            "Tags",
            "Date",
            "Categories",
            "TextArticle",
        ],
    )
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"Saved {len(df)} rows to {OUTPUT_CSV}")
    if broken_files:
        print("Could not process:")
        for pdf_path, error in broken_files:
            print(f"{pdf_path}: {error}")


if __name__ == "__main__":
    main()
