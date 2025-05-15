from .docx_parser import DocxParser
from .pdf_parser import PDFParser

def new_parser(file_path):
    import os
    from pathlib import Path
    if not os.path.exists(file_path):
        raise Exception(f'doc: {file_path} is not exists.')
    file_path = Path(file_path)
    suffix = file_path.suffix
    if suffix == '.docx':
        return DocxParser(file_path)
    elif suffix == '.pdf':
        return PDFParser(file_path)
    else:
        raise Exception(f'un-support file type: {suffix}')
