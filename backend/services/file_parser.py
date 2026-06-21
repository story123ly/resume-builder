"""文件解析服务：支持 PDF / Word / 纯文本"""


async def parse_pdf(file_path: str) -> str:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        return f"[PDF解析错误: {e}]"


async def parse_docx(file_path: str) -> str:
    try:
        from docx import Document
        doc = Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return text.strip()
    except Exception as e:
        return f"[Word解析错误: {e}]"


async def parse_file(file_path: str) -> str:
    ext = file_path.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return await parse_pdf(file_path)
    elif ext in ("docx", "doc"):
        return await parse_docx(file_path)
    elif ext in ("txt", "md"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    else:
        return f"[不支持的文件格式: .{ext}]"
