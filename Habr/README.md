# Habr PDF Tools

Небольшой проект для сохранения свежих статей с Хабра в PDF и последующей выгрузки данных из PDF в CSV.

## Что внутри

- `main.py` - берет свежие статьи из RSS Хабра или список ссылок и сохраняет страницы в PDF через Selenium + Chrome.
- `pdf_to_csv.py` - читает PDF из `pdf_articles/` и сохраняет данные в `dataset.csv`.
- `print_pdf_lines.py` - выводит текст PDF построчно для проверки структуры документа.
- `habr_pdf_to_csv.ipynb` - ноутбук с вариантом конвертации PDF в CSV.
- `requirements.txt` - зависимости проекта.

## Установка

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Сохранить свежие статьи в PDF

```bash
.venv/bin/python main.py
```

По умолчанию скрипт берет 20 свежих статей и сохраняет их в папку `pdf_articles/`.

Можно указать количество:

```bash
.venv/bin/python main.py --latest-count 10
```

Можно передать конкретную ссылку:

```bash
.venv/bin/python main.py "https://habr.com/ru/articles/1032294/"
```

## Конвертировать PDF в CSV

```bash
.venv/bin/python pdf_to_csv.py
```

Результат сохраняется в `dataset.csv`.

## Посмотреть текст PDF построчно

```bash
.venv/bin/python print_pdf_lines.py "pdf_articles/example.pdf"
```

## Загрузка на GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git push -u origin main
```

В коммит не попадут `.venv/`, `pdf_articles/`, `dataset.csv` и кэш Python.
