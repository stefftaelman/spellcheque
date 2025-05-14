"""
PDF handler module for extracting text from PDF files and storing them for viewing.
"""
import os
import io
import uuid
import datetime
import PyPDF2
from pdfminer.high_level import extract_text as pdfminer_extract_text


# Dictionary to track temporarily stored PDFs
PDF_FILES = {}
# Default expiry time for stored PDFs (1 hour)
PDF_EXPIRY_SECONDS = 3600


def process_pdf_file(pdf_file, temp_folder=None):
    """
    Extract text from a PDF file and store it temporarily for viewing.
    
    Args:
        pdf_file: The uploaded PDF file object
        temp_folder (str): Folder to store temporary PDF files
        
    Returns:
        tuple: (extracted_text, pdf_id) where extracted_text is the text content
               and pdf_id is the unique identifier for the stored PDF
               
    Raises:
        ValueError: If text extraction fails
    """
    try:
        # Save a copy of the PDF for viewing
        file_stream = io.BytesIO(pdf_file.read())
        # Reset the file pointer
        file_stream.seek(0)
        
        # Generate a unique ID for this PDF
        pdf_id = str(uuid.uuid4())
        
        # Save the PDF to a temporary file
        if temp_folder is None:
            import tempfile
            temp_folder = tempfile.gettempdir()
            
        pdf_path = os.path.join(temp_folder, f"{pdf_id}.pdf")
        with open(pdf_path, 'wb') as f:
            f.write(file_stream.read())
            
        # Store the PDF path in our tracking dictionary with expiry time
        PDF_FILES[pdf_id] = {
            'path': pdf_path,
            'timestamp': datetime.datetime.now()
        }
        
        # Reset file pointer for text extraction
        file_stream.seek(0)
        
        # First try with PyPDF2
        pdf_content = ""
        reader = PyPDF2.PdfReader(file_stream)
        if len(reader.pages) == 0:
            raise ValueError("PDF file contains no pages")
            
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_text = page.extract_text() or ""
            pdf_content += page_text + " "
            
        # If PyPDF2 extracted meaningful content, return it along with the PDF ID
        if pdf_content.strip():
            return pdf_content, pdf_id
            
        # If PyPDF2 failed to extract meaningful content, try with pdfminer
        # Reset file pointer to beginning for pdfminer
        file_stream.seek(0)
        pdf_content = pdfminer_extract_text(file_stream)
        
        if not pdf_content.strip():
            raise ValueError("Could not extract text from the PDF. It may be scanned without OCR or corrupted.")
            
        return pdf_content, pdf_id
        
    except Exception as e:
        # Clean up any temporary file that might have been created
        if 'pdf_id' in locals() and pdf_id in PDF_FILES:
            try:
                os.remove(PDF_FILES[pdf_id]['path'])
                del PDF_FILES[pdf_id]
            except:
                pass
        # Re-raise with a more user-friendly message
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def get_pdf_path(pdf_id):
    """
    Get the path to a stored PDF file.
    
    Args:
        pdf_id (str): The unique identifier for the PDF
        
    Returns:
        str: Path to the PDF file
        
    Raises:
        ValueError: If the PDF ID is invalid or the file doesn't exist
    """
    if pdf_id not in PDF_FILES:
        raise ValueError("PDF not found or expired")
    
    pdf_path = PDF_FILES[pdf_id]['path']
    
    if not os.path.exists(pdf_path):
        del PDF_FILES[pdf_id]
        raise ValueError("PDF file no longer available")
    
    return pdf_path


def cleanup_expired_pdfs():
    """Clean up PDF files that have expired."""
    current_time = datetime.datetime.now()
    for key in list(PDF_FILES.keys()):
        if (current_time - PDF_FILES[key]['timestamp']).total_seconds() > PDF_EXPIRY_SECONDS:
            try:
                os.remove(PDF_FILES[key]['path'])
            except:
                pass
            del PDF_FILES[key]