import pdfplumber


def extract_pages(path: str):
  pages = []
  with pdfplumber.open(path) as pdf:
    for i, page in enumerate(pdf.pages, start=1):
      text = page.extract_text() or ""
      pages.append({"page": i, "text": text})
  return pages