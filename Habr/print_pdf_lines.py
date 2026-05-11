import sys

import fitz


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python print_pdf_lines.py <pdf_file>")

    pdf_path = sys.argv[1]

    doc = fitz.open(pdf_path)
    try:
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            page_text = page.get_text("text")
            for line in page_text.splitlines():
                print(line)
    finally:
        doc.close()


if __name__ == "__main__":
    main()
