# pdf_helper.py

import io
import os
import tempfile
import warnings
import asyncio
from typing import Optional, Container, BinaryIO, cast

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=".*builtin type.*has no __module__ attribute",
)

from pdfminer.high_level import extract_text as extract_text_pdfminer
from pdfminer.pdfparser import PDFSyntaxError
from pdfminer.utils import open_filename, FileOrName
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
import fitz  # PyMuPDF

from .pdfpage import PDFPage
from .logging_helper import logger

def _extract_text_pymupdf(pdf_file: FileOrName) -> str:
    """Extract text from PDF using PyMuPDF (fitz) synchronously.

    Args:
        pdf_file (FileOrName): The PDF file path or file-like object.

    Returns:
        str: Extracted text from the PDF file.
    """
    # Use a temporary file to work around the issue with fitz opening BytesIO objects
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(pdf_file.read())  # Write the pdf_bytes to a temporary file
        temp_file.close()  # Ensure the file is closed

        # Open the temporary file with fitz
        with fitz.open(temp_file.name) as doc:
            text = ""
            for page in doc:
                text += page.get_text("text")  # Extract text
        # Delete the temporary file after processing
        os.remove(temp_file.name)

    return text

def _extract_text_pdfminer_patched(
    pdf_file: FileOrName,
    password: str = "",
    page_numbers: Optional[Container[int]] = None,
    maxpages: int = 0,
    caching: bool = True,
    codec: str = "utf-8",
    laparams: Optional[LAParams] = None,
) -> str:
    """Parse and return the text contained in a PDF file synchronously.

    Args:
        pdf_file (FileOrName): The PDF file path or file-like object.
        password (str): Password for encrypted PDFs.
        page_numbers (Optional[Container[int]]): Specific pages to extract.
        maxpages (int): Maximum number of pages to parse.
        caching (bool): Whether to cache resources.
        codec (str): Text decoding codec.
        laparams (Optional[LAParams]): Layout parameters.

    Returns:
        str: Extracted text.
    """
    laparams = laparams or LAParams()

    with open_filename(pdf_file, "rb") as fp, io.StringIO() as output_string:
        fp = cast(BinaryIO, fp)  # Ensure binary mode
        rsrcmgr = PDFResourceManager(caching=caching)
        device = TextConverter(rsrcmgr, output_string, codec=codec, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        for page in PDFPage.get_pages(
            fp,
            page_numbers,
            maxpages=maxpages,
            password=password,
            caching=caching,
        ):
            interpreter.process_page(page)

        return output_string.getvalue()

async def extract_text_from_pdf(pdf_bytes: bytes) -> Optional[str]:
    """
    Extract text from a PDF file asynchronously.

    Args:
        pdf_bytes (bytes): The raw bytes of the PDF file.

    Returns:
        Optional[str]: The extracted text or None if extraction fails.
    """
    def _attempt_extract(extract_func: callable) -> Optional[str]:
        with io.BytesIO(pdf_bytes) as pdf_file:
            # Call the extraction function with the correct arguments
            try:
                text = extract_func(pdf_file)
                if text and text.strip():
                    logger.debug("Extracted text from PDF successfully.")
                    return text
                logger.warning("No text extracted from PDF.")
                return None
            except Exception as e:
                logger.warning(f"Extraction function {extract_func.__name__} failed: {e}")
                return None

    try:
        # First attempt: Use PyMuPDF
        text = await asyncio.to_thread(_attempt_extract, _extract_text_pymupdf)
        if text:
            return text
    except PDFSyntaxError as e:
        logger.error(f"PDF syntax error: {e}")
    except Exception as e:
        logger.warning(f"First extraction method failed: {e}")

    logger.warning("Fallback to patched extract_text")
    try:
        # Second attempt: Use pdfminer
        fallback_text = await asyncio.to_thread(_attempt_extract, extract_text_pdfminer)
        if fallback_text:
            return fallback_text
    except Exception as e:
        logger.warning(f"Failed to extract text with patched method: {e}")

    # Third attempt: Use patched pdfminer
    logger.warning("Fallback to PyMuPDF patched text extraction")
    try:
        patched_text = await asyncio.to_thread(_attempt_extract, _extract_text_pdfminer_patched)
        return patched_text
    except Exception as e:
        logger.error(f"Failed to extract text from PDF using patched PyMuPDF: {e}")

    return None