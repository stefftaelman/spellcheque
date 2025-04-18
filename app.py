from flask import Flask, render_template, request, redirect, url_for
import requests
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import urlparse

app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['UPLOAD_EXTENSIONS'] = ['.txt']
app.config['REQUEST_TIMEOUT'] = 10  # seconds

# British/American English spelling dictionary
# Format: (British English, American English)
SPELLING_DICTIONARY = [
    ('colour', 'color'),
    ('behaviour', 'behavior'),
    ('centre', 'center'),
    ('analyse', 'analyze'),
    ('optimise', 'optimize'),
    ('licence', 'license'),
    ('defence', 'defense'),
    ('modelling', 'modeling'),
    ('travelled', 'traveled'),
    ('programme', 'program'),
    ('organisation', 'organization'),
    ('realise', 'realize'),
    ('favourite', 'favorite'),
    ('dialogue', 'dialog'),
    ('metre', 'meter'),
    ('flavour', 'flavor'),
    ('theatre', 'theater'),
    ('labour', 'labor'),
    ('neighbour', 'neighbor'),
    ('cosy', 'cozy'),
    ('apologise', 'apologize'),
    ('speciality', 'specialty'),
    ('cheque', 'check'),
    ('catalogue', 'catalog'),
    ('grey', 'gray'),
    ('jewellery', 'jewelry'),
    ('pyjamas', 'pajamas'),
    ('tyre', 'tire'),
    ('aluminium', 'aluminum'),
    ('fulfil', 'fulfill'),
]

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
                error_message = "Invalid file type. Please upload a .txt file."
            else:
                try:
                    text_content = uploaded_file.read().decode('utf-8')
                    analysis_results = analyze_text(text_content)
                except Exception as e:
                    error_message = f"Error reading file: {str(e)}"
                    
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