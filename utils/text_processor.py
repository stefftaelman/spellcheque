"""
Text processor module for handling raw text input.
"""

def process_text_input(text_input):
    """
    Process raw text input directly submitted by the user.
    
    Args:
        text_input (str): The raw text provided by the user
        
    Returns:
        tuple: (text_content, None) where text_content is the processed text
              The second value is None since there's no associated file ID
    """
    # For direct text input, we just return the text as is
    # No special processing needed
    return text_input, None