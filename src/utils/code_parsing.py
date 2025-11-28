import re

def extract_code_block(text: str, language: str = "python") -> str:
    """
    Extracts the content of a markdown code block for a specific language.
    If no code block is found, returns the original text (fallback).
    """
    pattern = rf"```{language}\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Fallback: try finding any code block
    pattern_any = r"```\s*(.*?)\s*```"
    match_any = re.search(pattern_any, text, re.DOTALL)
    if match_any:
        return match_any.group(1).strip()
        
    return text.strip()
