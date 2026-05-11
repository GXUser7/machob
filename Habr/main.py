import argparse
import base64
import hashlib
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


DEFAULT_OUTPUT_DIR = Path("pdf_articles")
DEFAULT_RSS_URL = "https://habr.com/ru/rss/articles/"
DEFAULT_CHROME_PROFILE_DIR = Path.home() / ".config" / "google-chrome"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Open Habr article pages in Chrome via Selenium and save them to PDF "
            "without parsing the article content."
        )
    )
    parser.add_argument(
        "urls",
        nargs="*",
        help="One or more Habr article URLs.",
    )
    parser.add_argument(
        "--urls-file",
        type=Path,
        help="Text file with one URL per line.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where PDFs will be saved. Default: pdf_articles",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=90000,
        help="Page load timeout in milliseconds. Default: 90000",
    )
    parser.add_argument(
        "--delay-after-load",
        type=float,
        default=2.5,
        help="Extra wait time after the page is loaded, in seconds. Default: 2.5",
    )
    parser.add_argument(
        "--format",
        default="A4",
        help="PDF paper format supported by Chrome. Default: A4",
    )
    parser.add_argument(
        "--landscape",
        action="store_true",
        help="Save PDF in landscape orientation.",
    )
    parser.add_argument(
        "--latest-count",
        type=int,
        default=20,
        help=(
            "How many latest Habr articles to fetch automatically when no URLs "
            "are provided. Default: 20"
        ),
    )
    parser.add_argument(
        "--rss-url",
        default=DEFAULT_RSS_URL,
        help=f"RSS feed with latest Habr articles. Default: {DEFAULT_RSS_URL}",
    )
    parser.add_argument(
        "--chrome-executable",
        type=Path,
        help=(
            "Path to your Chrome/Chromium executable. "
            "Use this together with --chrome-user-data-dir to reuse your browser profile."
        ),
    )
    parser.add_argument(
        "--chrome-user-data-dir",
        type=Path,
        help=(
            "Path to the Chrome user data directory with your extensions "
            f"(for example: {DEFAULT_CHROME_PROFILE_DIR})."
        ),
    )
    parser.add_argument(
        "--chrome-profile",
        default="Default",
        help=(
            "Chrome profile directory name inside user data dir, for example "
            "'Default' or 'Profile 1'. Default: Default"
        ),
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Run browser in visible mode.",
    )
    return parser.parse_args()


def read_urls(cli_urls: list[str], urls_file: Path | None) -> list[str]:
    urls: list[str] = []
    urls.extend(url.strip() for url in cli_urls if url.strip())

    if urls_file:
        file_urls = [
            line.strip()
            for line in urls_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        urls.extend(file_urls)

    unique_urls: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    return unique_urls


def fetch_latest_article_urls(rss_url: str, limit: int) -> list[str]:
    if limit <= 0:
        return []

    response = requests.get(
        rss_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            )
        },
        timeout=30,
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)
    items = root.findall("./channel/item")

    urls: list[str] = []
    seen: set[str] = set()

    for item in items:
        link = item.findtext("link", default="").strip()
        if not link:
            continue

        normalized_link = normalize_article_url(link)
        if "/articles/" not in normalized_link:
            continue
        if normalized_link in seen:
            continue

        seen.add(normalized_link)
        urls.append(normalized_link)

        if len(urls) >= limit:
            break

    return urls


def build_output_name(url: str, index: int) -> str:
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]
    article_slug = path_parts[-1] if path_parts else "article"

    cleaned_slug = re.sub(r"[^0-9A-Za-z_-]+", "_", article_slug).strip("_")
    if not cleaned_slug:
        cleaned_slug = "article"

    short_hash = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"{index:02d}_{cleaned_slug}_{short_hash}.pdf"


def normalize_article_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed._replace(query="", fragment="").geturl()


def create_driver(
    timeout_ms: int,
    chrome_executable: Path | None,
    chrome_user_data_dir: Path | None,
    chrome_profile: str,
    show_browser: bool,
) -> webdriver.Chrome:
    options = Options()
    options.add_argument("--window-size=1440,2200")
    options.add_argument("--lang=ru-RU")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    if not show_browser:
        options.add_argument("--headless=new")

    if chrome_executable:
        options.binary_location = str(chrome_executable)

    if chrome_user_data_dir:
        options.add_argument(f"--user-data-dir={chrome_user_data_dir}")
        options.add_argument(f"--profile-directory={chrome_profile}")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(max(1, timeout_ms // 1000))
    return driver


def wait_for_page_ready(driver: webdriver.Chrome, delay_after_load: float) -> None:
    WebDriverWait(driver, 20).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    auto_scroll(driver)
    time.sleep(delay_after_load)


def auto_scroll(driver: webdriver.Chrome) -> None:
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollBy(0, Math.max(600, window.innerHeight * 0.8));")
        time.sleep(0.15)
        new_position = driver.execute_script(
            "return window.pageYOffset + window.innerHeight"
        )
        current_height = driver.execute_script("return document.body.scrollHeight")

        if new_position >= current_height:
            break

        if current_height != last_height:
            last_height = current_height

    driver.execute_script("window.scrollTo(0, 0);")


def save_url_to_pdf(
    driver: webdriver.Chrome,
    url: str,
    output_path: Path,
    timeout_ms: int,
    pdf_format: str,
    landscape: bool,
    delay_after_load: float,
) -> None:
    try:
        driver.get(url)
        wait_for_page_ready(driver, delay_after_load)
    except TimeoutException:
        # If the page keeps loading additional resources forever, we still try
        # to export the already rendered state.
        pass

    pdf_data = driver.execute_cdp_cmd(
        "Page.printToPDF",
        {
            "landscape": landscape,
            "printBackground": True,
            "preferCSSPageSize": True,
            "displayHeaderFooter": False,
            "paperWidth": paper_size_to_inches(pdf_format)[0],
            "paperHeight": paper_size_to_inches(pdf_format)[1],
            "marginTop": 0.47,
            "marginBottom": 0.47,
            "marginLeft": 0.39,
            "marginRight": 0.39,
        },
    )
    output_path.write_bytes(base64.b64decode(pdf_data["data"]))


def paper_size_to_inches(pdf_format: str) -> tuple[float, float]:
    formats = {
        "A4": (8.27, 11.69),
        "A3": (11.69, 16.54),
        "A5": (5.83, 8.27),
        "Letter": (8.5, 11.0),
        "Legal": (8.5, 14.0),
        "Tabloid": (11.0, 17.0),
    }
    return formats.get(pdf_format, formats["A4"])


def export_pdfs(
    urls: Iterable[str],
    output_dir: Path,
    timeout_ms: int,
    pdf_format: str,
    landscape: bool,
    delay_after_load: float,
    chrome_executable: Path | None,
    chrome_user_data_dir: Path | None,
    chrome_profile: str,
    show_browser: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    driver = create_driver(
        timeout_ms=timeout_ms,
        chrome_executable=chrome_executable,
        chrome_user_data_dir=chrome_user_data_dir,
        chrome_profile=chrome_profile,
        show_browser=show_browser,
    )

    try:
        for index, url in enumerate(urls, start=1):
            output_name = build_output_name(url, index)
            output_path = output_dir / output_name
            print(f"[{index}] Saving {url}")
            save_url_to_pdf(
                driver=driver,
                url=url,
                output_path=output_path,
                timeout_ms=timeout_ms,
                pdf_format=pdf_format,
                landscape=landscape,
                delay_after_load=delay_after_load,
            )
            print(f"[{index}] Saved to {output_path}")
    finally:
        driver.quit()


def main() -> None:
    args = parse_args()
    urls = read_urls(args.urls, args.urls_file)

    if not urls:
        print(
            f"No URLs provided. Fetching {args.latest_count} latest Habr articles "
            f"from RSS: {args.rss_url}"
        )
        urls = fetch_latest_article_urls(
            rss_url=args.rss_url,
            limit=args.latest_count,
        )

    if not urls:
        raise SystemExit("Could not find article URLs to save.")

    if bool(args.chrome_executable) != bool(args.chrome_user_data_dir):
        raise SystemExit(
            "To reuse your Chrome profile, pass both --chrome-executable and "
            "--chrome-user-data-dir."
        )

    try:
        export_pdfs(
            urls=urls,
            output_dir=args.output_dir,
            timeout_ms=args.timeout_ms,
            pdf_format=args.format,
            landscape=args.landscape,
            delay_after_load=args.delay_after_load,
            chrome_executable=args.chrome_executable,
            chrome_user_data_dir=args.chrome_user_data_dir,
            chrome_profile=args.chrome_profile,
            show_browser=args.show_browser,
        )
    except WebDriverException as error:
        raise SystemExit(f"Selenium/Chrome error: {error}") from error


if __name__ == "__main__":
    main()
