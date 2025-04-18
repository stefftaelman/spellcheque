from flask import Flask, render_template, request, redirect, url_for
import requests
from bs4 import BeautifulSoup
import re
import os
import io
from urllib.parse import urlparse
import PyPDF2
from pdfminer.high_level import extract_text as pdfminer_extract_text

app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['UPLOAD_EXTENSIONS'] = ['.txt', '.pdf']  # Updated for v0.2
app.config['REQUEST_TIMEOUT'] = 10  # seconds

# British/American English spelling dictionary
# Format: (British English, American English)
SPELLING_DICTIONARY = [
    ('aluminium', 'aluminum'),
    ('analyse', 'analyze'),
    ('apologise', 'apologize'),
    ('behaviour', 'behavior'),
    ('catalogue', 'catalog'),
    ('cheque', 'check'),
    ('centre', 'center'),
    ('colour', 'color'),
    ('cosy', 'cozy'),
    ('defence', 'defense'),
    ('dialogue', 'dialog'),
    ('favourite', 'favorite'),
    ('flavour', 'flavor'),
    ('fulfil', 'fulfill'),
    ('grey', 'gray'),
    ('jewellery', 'jewelry'),
    ('labour', 'labor'),
    ('licence', 'license'),
    ('metre', 'meter'),
    ('modelling', 'modeling'),
    ('neighbour', 'neighbor'),
    ('travelling', 'traveling'),
    ('travelled', 'traveled'),
    ('plough', 'plow'),
    ('programme', 'program'),
    ('pyjamas', 'pajamas'),
    ('optimise', 'optimize'),
    ('organisation', 'organization'),
    ('realise', 'realize'),
    ('savour', 'savor'),
    ('sceptical', 'skeptical'),
    ('speciality', 'specialty'),
    ('sulphur', 'sulfur'),
    ('theatre', 'theater'),
    ('tyre', 'tire'),
    ('whisky', 'whiskey'),
]

def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file using both PyPDF2 and pdfminer.six for maximum compatibility."""
    try:
        # First try with PyPDF2
        pdf_content = ""
        file_stream = io.BytesIO(pdf_file.read())
        # Reset file pointer to beginning for PyPDF2
        file_stream.seek(0)
        
        reader = PyPDF2.PdfReader(file_stream)
        if len(reader.pages) == 0:
            raise ValueError("PDF file contains no pages")
            
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            pdf_content += page.extract_text() + " "
            
        # If PyPDF2 extracted meaningful content, return it
        if pdf_content.strip():
            return pdf_content
            
        # If PyPDF2 failed to extract meaningful content, try with pdfminer
        # Reset file pointer to beginning for pdfminer
        file_stream.seek(0)
        pdf_content = pdfminer_extract_text(file_stream)
        
        if not pdf_content.strip():
            raise ValueError("Could not extract text from the PDF. It may be scanned without OCR or corrupted.")
            
        return pdf_content
        
    except Exception as e:
        # Re-raise with a more user-friendly message
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Initialize variables for analysis results
        analysis_results = None
        error_message = None
        
        # Determine which input method was used
        if request.form.get('text_input') and request.form.get('text_input').strip():
            # Text area input
            text_content = request.form.get('text_input')
            analysis_results = analyze_text(text_content)
            
        elif request.files.get('file_upload') and request.files.get('file_upload').filename:
            # File upload
            uploaded_file = request.files['file_upload']
            file_ext = os.path.splitext(uploaded_file.filename)[1].lower()
            
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                error_message = f"Invalid file type. Please upload a {' or '.join(app.config['UPLOAD_EXTENSIONS'])} file."
            else:
                try:
                    if file_ext == '.txt':
                        # Process text file
                        text_content = uploaded_file.read().decode('utf-8')
                    elif file_ext == '.pdf':
                        # Process PDF file (v0.2 feature)
                        text_content = extract_text_from_pdf(uploaded_file)
                    
                    analysis_results = analyze_text(text_content)
                except ValueError as e:
                    error_message = str(e)
                except Exception as e:
                    error_message = f"Error processing file: {str(e)}"
                    
        elif request.form.get('url_input') and request.form.get('url_input').strip():
            # URL input
            url = request.form.get('url_input')
            
            # Basic URL validation
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                error_message = "Invalid URL format. Please enter a complete URL (e.g., https://example.com)."
            else:
                try:
                    # Fetch content from URL
                    response = requests.get(url, timeout=app.config['REQUEST_TIMEOUT'])
                    response.raise_for_status()  # Raise exception for 4xx/5xx status codes
                    
                    # Parse HTML and extract text content
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove script and style elements
                    for script_or_style in soup(['script', 'style']):
                        script_or_style.decompose()
                        
                    # Extract text from main content elements
                    text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td'])
                    text_content = ' '.join([element.get_text() for element in text_elements])
                    
                    if not text_content.strip():
                        error_message = "Could not extract meaningful text content from the provided URL."
                    else:
                        analysis_results = analyze_text(text_content)
                        
                except requests.exceptions.RequestException as e:
                    error_message = f"Error fetching URL: {str(e)}"
        else:
            error_message = "Please provide text, upload a file, or enter a URL for analysis."
            
        return render_template('index.html', analysis_results=analysis_results, error_message=error_message)
    
    # For GET requests, just render the form
    return render_template('index.html')

def analyze_text(text):
    """Analyze the provided text for British/American English spelling variations."""
    
    # Text preprocessing
    text = text.lower()
    # Tokenize the text - split by whitespace and remove punctuation
    tokens = re.findall(r'\b\w+\b', text)
    
    # Initialize counters and result data structure
    british_count = 0
    american_count = 0
    found_words_details = []
    
    # Process each token through the spelling dictionary
    for token in tokens:
        for br_spelling, am_spelling in SPELLING_DICTIONARY:
            if token == br_spelling:
                british_count += 1
                found_words_details.append({
                    'bre': br_spelling,
                    'ame': am_spelling,
                    'found': 'bre'
                })
                break  # No need to check further for this token
            elif token == am_spelling:
                american_count += 1
                found_words_details.append({
                    'bre': br_spelling,
                    'ame': am_spelling,
                    'found': 'ame'
                })
                break  # No need to check further for this token
    
    # Calculate total and percentages
    total_found = british_count + american_count
    
    if total_found > 0:
        british_percentage = (british_count / total_found) * 100
        american_percentage = (american_count / total_found) * 100
    else:
        british_percentage = 0
        american_percentage = 0
    
    # Aggregate found words for display
    word_summary = {}
    for word in found_words_details:
        key = (word['bre'], word['ame'])
        if key not in word_summary:
            word_summary[key] = {'bre_count': 0, 'ame_count': 0}
        
        if word['found'] == 'bre':
            word_summary[key]['bre_count'] += 1
        else:
            word_summary[key]['ame_count'] += 1
    
    # Format for template display
    found_words_summary = [
        {
            'bre_spelling': key[0],
            'ame_spelling': key[1],
            'bre_count': value['bre_count'],
            'ame_count': value['ame_count']
        }
        for key, value in word_summary.items()
    ]
    
    # Sort by total occurrences (descending)
    found_words_summary.sort(
        key=lambda x: (x['bre_count'] + x['ame_count']),
        reverse=True
    )
    
    return {
        'british_count': british_count,
        'american_count': american_count,
        'total_found': total_found,
        'british_percentage': british_percentage,
        'american_percentage': american_percentage,
        'found_words_summary': found_words_summary
    }

if __name__ == '__main__':
    app.run(debug=True)