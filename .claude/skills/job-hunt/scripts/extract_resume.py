"""Print a resume's text and every hyperlink in it, so setup can rebuild it faithfully.

Usage: python extract_resume.py <resume.pdf|resume.docx>
"""
import sys
from pathlib import Path


def from_pdf(path):
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    text = "\n".join(p.extract_text() or "" for p in reader.pages)
    links = []
    for page in reader.pages:
        for annot in page.get("/Annots") or []:
            action = annot.get_object().get("/A")
            if action and "/URI" in action:
                links.append(str(action["/URI"]))
    return text, links, len(reader.pages)


def from_docx(path):
    from docx import Document
    doc = Document(str(path))
    lines = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            lines.append(" | ".join(c.text for c in row.cells))
    links = [r.target_ref for r in doc.part.rels.values() if "hyperlink" in r.reltype]
    return "\n".join(lines), links, None


def main():
    path = Path(sys.argv[1])
    ext = path.suffix.lower()
    if ext == ".pdf":
        text, links, pages = from_pdf(path)
    elif ext == ".docx":
        text, links, pages = from_docx(path)
    else:
        sys.exit("Only .pdf and .docx resumes are supported. Export the resume to one of those first.")
    print(f"=== {path.name} ({pages or '?'} page(s)) ===")
    print(text.strip())
    print("\n=== Hyperlinks (in order of appearance) ===")
    for link in dict.fromkeys(links):  # de-dup, keep order
        print(link)


if __name__ == "__main__":
    main()
