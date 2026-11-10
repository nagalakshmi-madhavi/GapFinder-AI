from io import BytesIO
from pypdf import PdfReader


def extract_pdf_text(file_bytes: bytes):
    reader = PdfReader(BytesIO(file_bytes))

    chunks = []

    # Read each PDF page
    for page_number, page in enumerate(reader.pages, start=1):

        text = page.extract_text() or ""

        if not text.strip():
            continue

        # Split page text into smaller chunks
        chunk_size = 1000
        overlap = 150

        start = 0

        while start < len(text):

            end = start + chunk_size

            chunk_text = text[start:end]

            chunks.append({
                "page": page_number,
                "text": chunk_text
            })

            start += chunk_size - overlap

    return chunks