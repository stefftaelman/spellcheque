from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import tempfile

# Import utility modules
from utils.text_processor import process_text_input
from utils.url_processor import process_url_input
from utils.file_processor import process_file_upload
from utils.pdf_handler import get_pdf_path, cleanup_expired_pdfs
from utils.analyzer import analyze_text

app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['UPLOAD_EXTENSIONS'] = ['.txt', '.pdf']
app.config['REQUEST_TIMEOUT'] = 10  # seconds
app.config['TEMP_FOLDER'] = tempfile.gettempdir()  # For storing PDFs temporarily

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Initialize variables for analysis results
        analysis_results = None
        error_message = None
        original_text = ""
        pdf_id = None  # Store PDF ID for PDF viewer
        
        # Determine which input method was used
        try:
            if request.form.get('text_input') and request.form.get('text_input').strip():
                # Text area input
                original_text, _ = process_text_input(request.form.get('text_input'))
                analysis_results = analyze_text(original_text)
                
            elif request.files.get('file_upload') and request.files.get('file_upload').filename:
                # File upload
                uploaded_file = request.files['file_upload']
                original_text, pdf_id = process_file_upload(
                    uploaded_file, 
                    app.config['UPLOAD_EXTENSIONS'],
                    app.config['MAX_CONTENT_LENGTH']
                )
                analysis_results = analyze_text(original_text)
                    
            elif request.form.get('url_input') and request.form.get('url_input').strip():
                # URL input
                url = request.form.get('url_input')
                original_text, _ = process_url_input(url, app.config['REQUEST_TIMEOUT'])
                analysis_results = analyze_text(original_text)
                    
            else:
                error_message = "Please provide text, upload a file, or enter a URL for analysis."
                
        except ValueError as e:
            error_message = str(e)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            
        return render_template('index.html', 
                              analysis_results=analysis_results, 
                              error_message=error_message, 
                              original_text=original_text,
                              pdf_id=pdf_id)
    
    # For GET requests, just render the form
    return render_template('index.html')

@app.route('/pdf/<pdf_id>')
def serve_pdf(pdf_id):
    """Serve a temporarily stored PDF file."""
    try:
        # Get the PDF path
        pdf_path = get_pdf_path(pdf_id)
        
        # Clean up old PDFs
        cleanup_expired_pdfs()
        
        # Serve the PDF file
        return send_file(pdf_path, mimetype='application/pdf')
    except ValueError as e:
        return str(e), 404

if __name__ == '__main__':
    app.run(debug=True)