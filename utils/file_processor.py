"""
File processor module for handling file uploads (.txt and .pdf).
"""
import os
from utils.pdf_handler import process_pdf_file


def process_file_upload(uploaded_file, allowed_extensions, max_size_bytes=10*1024*1024):
    """
    Process an uploaded file (.txt or .pdf).
    
    Args:
        uploaded_file: The uploaded file object from Flask request
        allowed_extensions (list): List of allowed file extensions
        max_size_bytes (int): Maximum allowed file size in bytes
        
    Returns:
        tuple: (text_content, pdf_id) where text_content is the extracted text
               and pdf_id is the ID of the PDF file (if applicable, else None)
               
    Raises:
        ValueError: If the file is invalid, too large, or text extraction fails
    """
    # Check file extension
    filename = uploaded_file.filename
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise ValueError(f"Invalid file type. Please upload a {' or '.join(allowed_extensions)} file.")
    
    # Check file size (Flask should handle this via MAX_CONTENT_LENGTH, but we double-check)
    uploaded_file.seek(0, os.SEEK_END)
    file_size = uploaded_file.tell()
    uploaded_file.seek(0)  # Reset file pointer to beginning
    
    if file_size > max_size_bytes:
        raise ValueError(f"File is too large. Maximum size is {max_size_bytes/1024/1024:.1f} MB.")
    
    try:
        if file_ext == '.txt':
            # Process text file
            text_content = uploaded_file.read().decode('utf-8')
            return text_content, None
        elif file_ext == '.pdf':
            # Process PDF file using the PDF handler module
            return process_pdf_file(uploaded_file)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    except UnicodeDecodeError:
        raise ValueError("Unable to decode the text file. Please ensure it's encoded in UTF-8.")
    except Exception as e:
        raise ValueError(f"Error processing file: {str(e)}")