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
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['UPLOAD_EXTENSIONS'] = ['.txt', '.pdf']  # Updated for v0.2
app.config['REQUEST_TIMEOUT'] = 10  # seconds

# British/American English spelling dictionary
# Format: (British English, American English)
SPELLING_DICTIONARY = [
    ('aluminium', 'aluminum'),
    ('analyse', 'analyze'),
    ('analysed', 'analyzed'),
    ('analysing', 'analyzing'),
    ('anaemia', 'anemia'),
    ('anaemic', 'anemic'),
    ('anaesthesia', 'anesthesia'),
    ('anaesthetic', 'anesthetic'),
    ('apologise', 'apologize'),
    ('apologised', 'apologized'),
    ('apologising', 'apologizing'),
    ('appal', 'appall'),
    ('appalled', 'appalled'),
    ('artefact', 'artifact'),
    ('authorise', 'authorize'),
    ('authorised', 'authorized'),
    ('authorising', 'authorizing'),
    ('axe', 'ax'),
    ('behaviour', 'behavior'),
    ('behavioural', 'behavioral'),
    ('calibre', 'caliber'),
    ('cancelled', 'canceled'),
    ('cancelling', 'canceling'),
    ('candour', 'candor'),
    ('capitalise', 'capitalize'),
    ('capitalised', 'capitalized'),
    ('capitalising', 'capitalizing'),
    ('catalogue', 'catalog'),
    ('catalogued', 'cataloged'),
    ('categorise', 'categorize'),
    ('categorised', 'categorized'),
    ('centre', 'center'),
    ('centred', 'centered'),
    ('centring', 'centering'),
    ('cheque', 'check'),
    ('chequered', 'checkered'),
    ('civilisation', 'civilization'),
    ('civilise', 'civilize'),
    ('colonisation', 'colonization'),
    ('colonise', 'colonize'),
    ('colonised', 'colonized'),
    ('colonising', 'colonizing'),
    ('colour', 'color'),
    ('coloured', 'colored'),
    ('colouring', 'coloring'),
    ('computerise', 'computerize'),
    ('computerised', 'computerized'),
    ('connexion', 'connection'),
    ('counselling', 'counseling'),
    ('counsellor', 'counselor'),
    ('cosy', 'cozy'),
    ('criticise', 'criticize'),
    ('criticised', 'criticized'),
    ('criticising', 'criticizing'),
    ('defence', 'defense'),
    ('dialogue', 'dialog'),
    ('dialled', 'dialed'),
    ('dialling', 'dialing'),
    ('diarrhoea', 'diarrhea'),
    ('disc', 'disk'),
    ('dramatise', 'dramatize'),
    ('draught', 'draft'),
    ('drivelled', 'driveled'),
    ('encyclopaedia', 'encyclopedia'),
    ('economise', 'economize'),
    ('emphasise', 'emphasize'),
    ('emphasised', 'emphasized'),
    ('emphasising', 'emphasizing'),
    ('enquiry', 'inquiry'),
    ('enrol', 'enroll'),
    ('enrolment', 'enrollment'),
    ('enthral', 'enthrall'),
    ('equalise', 'equalize'),
    ('equalised', 'equalized'),
    ('equaliser', 'equalizer'),
    ('equalising', 'equalizing'),
    ('etiquette', 'etiquet'),
    ('favour', 'favor'),
    ('favourable', 'favorable'),
    ('favourite', 'favorite'),
    ('favoured', 'favored'),
    ('favouring', 'favoring'),
    ('fibre', 'fiber'),
    ('fictionalise', 'fictionalize'),
    ('fillet', 'filet'),
    ('finalise', 'finalize'),
    ('finalised', 'finalized'),
    ('finalising', 'finalizing'),
    ('flavour', 'flavor'),
    ('flavoured', 'flavored'),
    ('flavouring', 'flavoring'),
    ('focussed', 'focused'),
    ('focussing', 'focusing'),
    ('formalise', 'formalize'),
    ('formalised', 'formalized'),
    ('formalising', 'formalizing'),
    ('fossilise', 'fossilize'),
    ('fossilised', 'fossilized'),
    ('fossilising', 'fossilizing'),
    ('fulfil', 'fulfill'),
    ('fulfilled', 'fulfilled'),
    ('fulfilling', 'fulfilling'),
    ('galvanise', 'galvanize'),
    ('galvanised', 'galvanized'),
    ('galvanising', 'galvanizing'),
    ('generalise', 'generalize'),
    ('generalised', 'generalized'),
    ('globalisation', 'globalization'),
    ('globalise', 'globalize'),
    ('globalised', 'globalized'),
    ('globalising', 'globalizing'),
    ('glycerine', 'glycerin'),
    ('gramme', 'gram'),
    ('grey', 'gray'),
    ('harmonise', 'harmonize'),
    ('harmonised', 'harmonized'),
    ('harmonising', 'harmonizing'),
    ('homeopath', 'homeopath'),
    ('homeopathy', 'homeopathy'),
    ('honour', 'honor'),
    ('honourable', 'honorable'),
    ('humanise', 'humanize'),
    ('humanised', 'humanized'),
    ('humanising', 'humanizing'),
    ('humour', 'humor'),
    ('humoured', 'humored'),
    ('humouring', 'humoring'),
    ('humourous', 'humorous'),
    ('hypothesise', 'hypothesize'),
    ('idealise', 'idealize'),
    ('idealised', 'idealized'),
    ('idealising', 'idealizing'),
    ('immobilise', 'immobilize'),
    ('immobilised', 'immobilized'),
    ('immobilising', 'immobilizing'),
    ('improvise', 'improvize'),
    ('initialise', 'initialize'),
    ('initialised', 'initialized'),
    ('initialising', 'initializing'),
    ('italicise', 'italicize'),
    ('italicised', 'italicized'),
    ('italicising', 'italicizing'),
    ('jewellery', 'jewelry'),
    ('judgement', 'judgment'),
    ('kerb', 'curb'),
    ('labelled', 'labeled'),
    ('labelling', 'labeling'),
    ('labour', 'labor'),
    ('laboured', 'labored'),
    ('labouring', 'laboring'),
    ('leukaemia', 'leukemia'),
    ('levelled', 'leveled'),
    ('leveller', 'leveler'),
    ('levelling', 'leveling'),
    ('libelled', 'libeled'),
    ('libelling', 'libeling'),
    ('licence', 'license'),
    ('licensed', 'licensed'),
    ('litre', 'liter'),
    ('localise', 'localize'),
    ('localised', 'localized'),
    ('localising', 'localizing'),
    ('lustre', 'luster'),
    ('manoeuvre', 'maneuver'),
    ('marvellous', 'marvelous'),
    ('materialise', 'materialize'),
    ('materialised', 'materialized'),
    ('materialising', 'materializing'),
    ('maximise', 'maximize'),
    ('maximised', 'maximized'),
    ('maximising', 'maximizing'),
    ('meagre', 'meager'),
    ('memorise', 'memorize'),
    ('memorised', 'memorized'),
    ('memorising', 'memorizing'),
    ('metre', 'meter'),
    ('minimise', 'minimize'),
    ('minimised', 'minimized'),
    ('minimising', 'minimizing'),
    ('mobilise', 'mobilize'),
    ('mobilised', 'mobilized'),
    ('mobilising', 'mobilizing'),
    ('modelled', 'modeled'),
    ('modelling', 'modeling'),
    ('modernise', 'modernize'),
    ('modernised', 'modernized'),
    ('modernising', 'modernizing'),
    ('mould', 'mold'),
    ('moulded', 'molded'),
    ('moulding', 'molding'),
    ('naturalise', 'naturalize'),
    ('naturalised', 'naturalized'),
    ('naturalising', 'naturalizing'),
    ('neighbour', 'neighbor'),
    ('neighbourhood', 'neighborhood'),
    ('neighbouring', 'neighboring'),
    ('neutralise', 'neutralize'),
    ('neutralised', 'neutralized'),
    ('neutralising', 'neutralizing'),
    ('normalise', 'normalize'),
    ('normalised', 'normalized'),
    ('normalising', 'normalizing'),
    ('offence', 'offense'),
    ('optimise', 'optimize'),
    ('optimised', 'optimized'),
    ('optimising', 'optimizing'),
    ('organisation', 'organization'),
    ('organise', 'organize'),
    ('organised', 'organized'),
    ('organising', 'organizing'),
    ('paralyse', 'paralyze'),
    ('paralysed', 'paralyzed'),
    ('paralysing', 'paralyzing'),
    ('paediatric', 'pediatric'),
    ('paediatrician', 'pediatrician'),
    ('paediatrics', 'pediatrics'),
    ('personalise', 'personalize'),
    ('personalised', 'personalized'),
    ('personalising', 'personalizing'),
    ('philosophise', 'philosophize'),
    ('plough', 'plow'),
    ('ploughed', 'plowed'),
    ('ploughing', 'plowing'),
    ('polarise', 'polarize'),
    ('polarised', 'polarized'),
    ('polarising', 'polarizing'),
    ('popularise', 'popularize'),
    ('popularised', 'popularized'),
    ('popularising', 'popularizing'),
    ('practise', 'practice'),
    ('practised', 'practiced'),
    ('practising', 'practicing'),
    ('prioritise', 'prioritize'),
    ('prioritised', 'prioritized'),
    ('prioritising', 'prioritizing'),
    ('programme', 'program'),
    ('programmed', 'programed'),
    ('programmes', 'programs'),
    ('pulverised', 'pulverized'),
    ('pyjamas', 'pajamas'),
    ('quantise', 'quantize'),
    ('quantised', 'quantized'),
    ('quantising', 'quantizing'),
    ('racquet', 'racket'),
    ('radicalise', 'radicalize'),
    ('radicalised', 'radicalized'),
    ('radicalising', 'radicalizing'),
    ('realise', 'realize'),
    ('realised', 'realized'),
    ('realising', 'realizing'),
    ('recognise', 'recognize'),
    ('recognised', 'recognized'),
    ('recognising', 'recognizing'),
    ('reconnoitre', 'reconnoiter'),
    ('regularise', 'regularize'),
    ('regularised', 'regularized'),
    ('regularising', 'regularizing'),
    ('revelled', 'reveled'),
    ('revelling', 'reveling'),
    ('rigour', 'rigor'),
    ('rumour', 'rumor'),
    ('rumoured', 'rumored'),
    ('sanitise', 'sanitize'),
    ('sanitised', 'sanitized'),
    ('sanitising', 'sanitizing'),
    ('satirise', 'satirize'),
    ('satirised', 'satirized'),
    ('satirising', 'satirizing'),
    ('saviour', 'savior'),
    ('savour', 'savor'),
    ('savoured', 'savored'),
    ('savouring', 'savoring'),
    ('sceptic', 'skeptic'),
    ('sceptical', 'skeptical'),
    ('scepticism', 'skepticism'),
    ('scrutinise', 'scrutinize'),
    ('scrutinised', 'scrutinized'),
    ('scrutinising', 'scrutinizing'),
    ('sensationalise', 'sensationalize'),
    ('sensationalised', 'sensationalized'),
    ('sensationalising', 'sensationalizing'),
    ('sensitise', 'sensitize'),
    ('sensitised', 'sensitized'),
    ('sensitising', 'sensitizing'),
    ('shovelled', 'shoveled'),
    ('shovelling', 'shoveling'),
    ('signalled', 'signaled'),
    ('signalling', 'signaling'),
    ('snivelled', 'sniveled'),
    ('snivelling', 'sniveling'),
    ('socialise', 'socialize'),
    ('socialised', 'socialized'),
    ('socialising', 'socializing'),
    ('specialise', 'specialize'),
    ('specialised', 'specialized'),
    ('specialising', 'specializing'),
    ('speciality', 'specialty'),
    ('spectre', 'specter'),
    ('splendour', 'splendor'),
    ('standardise', 'standardize'),
    ('standardised', 'standardized'),
    ('standardising', 'standardizing'),
    ('sterilise', 'sterilize'),
    ('sterilised', 'sterilized'),
    ('sterilising', 'sterilizing'),
    ('stigmatise', 'stigmatize'),
    ('stigmatised', 'stigmatized'),
    ('stigmatising', 'stigmatizing'),
    ('subsidise', 'subsidize'),
    ('subsidised', 'subsidized'),
    ('subsidising', 'subsidizing'),
    ('succour', 'succor'),
    ('sulphur', 'sulfur'),
    ('sulphurous', 'sulfurous'),
    ('summarise', 'summarize'),
    ('summarised', 'summarized'),
    ('summarising', 'summarizing'),
    ('symbolise', 'symbolize'),
    ('symbolised', 'symbolized'),
    ('symbolising', 'symbolizing'),
    ('sympathise', 'sympathize'),
    ('sympathised', 'sympathized'),
    ('sympathising', 'sympathizing'),
    ('synchronise', 'synchronize'),
    ('synchronised', 'synchronized'),
    ('synchronising', 'synchronizing'),
    ('synthesise', 'synthesize'),
    ('synthesised', 'synthesized'),
    ('synthesising', 'synthesizing'),
    ('systematise', 'systematize'),
    ('systematised', 'systematized'),
    ('systematising', 'systematizing'),
    ('terrorise', 'terrorize'),
    ('terrorised', 'terrorized'),
    ('terrorising', 'terrorizing'),
    ('theatre', 'theater'),
    ('theatregoer', 'theatergoer'),
    ('theorise', 'theorize'),
    ('theorised', 'theorized'),
    ('theorising', 'theorizing'),
    ('tonne', 'ton'),
    ('tonnes', 'tons'),
    ('tranquillise', 'tranquilize'),
    ('tranquillised', 'tranquilized'),
    ('tranquillising', 'tranquilizing'),
    ('tranquilliser', 'tranquilizer'),
    ('tranquillity', 'tranquility'),
    ('traumatise', 'traumatize'),
    ('traumatised', 'traumatized'),
    ('traumatising', 'traumatizing'),
    ('travelled', 'traveled'),
    ('traveller', 'traveler'),
    ('travelling', 'traveling'),
    ('trialled', 'trialed'),
    ('trialling', 'trialing'),
    ('trivialise', 'trivialize'),
    ('trivialised', 'trivialized'),
    ('trivialising', 'trivializing'),
    ('tyre', 'tire'),
    ('unravelled', 'unraveled'),
    ('unravelling', 'unraveling'),
    ('utilise', 'utilize'),
    ('utilised', 'utilized'),
    ('utilising', 'utilizing'),
    ('valour', 'valor'),
    ('vapour', 'vapor'),
    ('verbalise', 'verbalize'),
    ('verbalised', 'verbalized'),
    ('verbalising', 'verbalizing'),
    ('victimise', 'victimize'),
    ('victimised', 'victimized'),
    ('victimising', 'victimizing'),
    ('visualise', 'visualize'),
    ('visualised', 'visualized'),
    ('visualising', 'visualizing'),
    ('vocalise', 'vocalize'),
    ('vocalised', 'vocalized'),
    ('vocalising', 'vocalizing'),
    ('vulcanised', 'vulcanized'),
    ('watercolour', 'watercolor'),
    ('westernise', 'westernize'),
    ('westernised', 'westernized'),
    ('westernising', 'westernizing'),
    ('whisky', 'whiskey'),
    ('wilful', 'willful'),
    ('wilfully', 'willfully'),
    ('winterise', 'winterize'),
    ('winterised', 'winterized'),
    ('winterising', 'winterizing'),
    ('yoghurt', 'yogurt'),
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
        original_text = ""
        
        # Determine which input method was used
        if request.form.get('text_input') and request.form.get('text_input').strip():
            # Text area input
            original_text = request.form.get('text_input')
            analysis_results = analyze_text(original_text)
            
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
                        original_text = uploaded_file.read().decode('utf-8')
                    elif file_ext == '.pdf':
                        # Process PDF file (v0.2 feature)
                        original_text = extract_text_from_pdf(uploaded_file)
                    
                    analysis_results = analyze_text(original_text)
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
                    original_text = ' '.join([element.get_text() for element in text_elements])
                    
                    if not original_text.strip():
                        error_message = "Could not extract meaningful text content from the provided URL."
                    else:
                        analysis_results = analyze_text(original_text)
                        
                except requests.exceptions.RequestException as e:
                    error_message = f"Error fetching URL: {str(e)}"
        else:
            error_message = "Please provide text, upload a file, or enter a URL for analysis."
            
        return render_template('index.html', analysis_results=analysis_results, error_message=error_message, original_text=original_text)
    
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