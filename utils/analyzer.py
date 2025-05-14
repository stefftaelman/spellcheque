"""
Text analyzer module for British/American English spelling detection.
"""
import re
import os
import csv


def load_spelling_dictionary(file_path):
    """
    Load the British/American English spelling dictionary from a CSV file.
    
    Args:
        file_path (str): Path to the CSV file containing the word pairs
        
    Returns:
        list: A list of tuples with (British English, American English) pairs
    """
    dictionary = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            for row in reader:
                if len(row) >= 2:
                    dictionary.append((row[0], row[1]))
    except Exception as e:
        # Fall back to the empty dictionary if loading fails
        print(f"Error loading spelling dictionary: {str(e)}")
        
    return dictionary


# Load the spelling dictionary from the CSV file
# Get the absolute path to the data directory based on the current module's location
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(CURRENT_DIR), 'data')
DICT_PATH = os.path.join(DATA_DIR, 'spelling_dictionary.csv')

# Load the dictionary
SPELLING_DICTIONARY = load_spelling_dictionary(DICT_PATH)


def preprocess_text(text):
    """Preprocess text for analysis."""
    # Convert to lowercase for case-insensitive matching
    text = text.lower()
    # Tokenize the text - split by whitespace and remove punctuation
    tokens = re.findall(r'\b\w+\b', text)
    return tokens


def analyze_text(text):
    """
    Analyze the provided text for British/American English spelling variations.
    
    Args:
        text (str): The text content to analyze
        
    Returns:
        dict: Analysis results including counts, percentages, and word summaries
    """
    # Text preprocessing
    tokens = preprocess_text(text)
    
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