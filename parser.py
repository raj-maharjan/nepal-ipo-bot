import re
from difflib import SequenceMatcher
from typing import Tuple, Optional, Dict, Any

def fuzzy_match(name: str, candidates: list[str], threshold: float = 0.6) -> Optional[str]:
    """
    Find the best fuzzy match for a name in the list of candidates.
    """
    best_match = None
    best_score = 0
    
    for candidate in candidates:
        # Direct substring match (case insensitive)
        if name.lower() in candidate.lower() or candidate.lower() in name.lower():
            return candidate
        
        # Fuzzy matching using sequence matcher
        score = SequenceMatcher(None, name.lower(), candidate.lower()).ratio()
        if score > threshold and score > best_score:
            best_score = score
            best_match = candidate
    
    return best_match

def extract_person_company_and_kitta(msg: str, known_people: list[str]) -> Dict[str, Any]:
    """
    Extract person name, company, and kitta from various message formats.
    Supports patterns like:
    - "appy ipo for kaka for company abc"
    - "apply ipo for john in xyz"
    - "ipo kaka abc"
    - "apply for sarah company def"
    - "apply ipo for nene for company urja 10 kitta"
    """
    msg = msg.lower().strip()
    
    # Common patterns to look for
    patterns = [
        # Pattern: "appy/apply ipo for {name} for company {company}"
        r'(?:appy|apply)\s+(?:ipo\s+)?for\s+([a-zA-Z\s]+?)\s+(?:for\s+)?company\s+([a-zA-Z0-9\s]+)',
        
        # Pattern: "apply ipo for {name} in {company}"
        r'(?:appy|apply)\s+(?:ipo\s+)?for\s+([a-zA-Z\s]+?)\s+in\s+([a-zA-Z0-9\s]+)',
        
        # Pattern: "ipo {name} {company}"
        r'ipo\s+([a-zA-Z\s]+?)\s+([a-zA-Z0-9\s]+)',
        
        # Pattern: "apply for {name} company {company}"
        r'apply\s+for\s+([a-zA-Z\s]+?)\s+company\s+([a-zA-Z0-9\s]+)',
        
        # Pattern: "{name} {company}" (simple two-word pattern)
        r'^([a-zA-Z]+)\s+([a-zA-Z0-9]+)$',
        
        # Pattern: "for {name} {company}"
        r'for\s+([a-zA-Z\s]+?)\s+([a-zA-Z0-9\s]+)',
    ]
    
    person = None
    company = None
    kitta = None
    
    # Extract kitta from message (number before "kitta" keyword)
    kitta_pattern = r'(\d+)\s+kitta'
    kitta_match = re.search(kitta_pattern, msg, re.IGNORECASE)
    if kitta_match:
        kitta = kitta_match.group(1)
        # Remove kitta part from message for further processing
        msg = re.sub(kitta_pattern, '', msg, flags=re.IGNORECASE).strip()
    
    # Try each pattern
    for pattern in patterns:
        match = re.search(pattern, msg, re.IGNORECASE)
        if match:
            potential_person = match.group(1).strip()
            potential_company = match.group(2).strip()
            
            # Try to find the person in known_people using fuzzy matching
            matched_person = fuzzy_match(potential_person, known_people)
            if matched_person:
                person = matched_person
                company = potential_company
                break
    
    # If no pattern matched, try to extract using word-based approach
    if not person:
        words = msg.split()
        
        # Look for person names in the message
        for i, word in enumerate(words):
            # Skip common words that are not names
            if word in ['for', 'in', 'company', 'apply', 'appy', 'ipo', 'the', 'a', 'an']:
                continue
                
            # Try to match this word or phrase with known people
            matched_person = fuzzy_match(word, known_people)
            if matched_person:
                person = matched_person
                
                # Look for company name (next word or remaining words)
                if i + 1 < len(words):
                    company = ' '.join(words[i+1:])
                    # Remove common words from company
                    company_words = company.split()
                    company_words = [w for w in company_words if w not in ['for', 'in', 'company', 'apply', 'appy', 'ipo', 'the', 'a', 'an']]
                    company = ' '.join(company_words)
                break
    
    # Clean up company name
    if company:
        # Remove common prefixes/suffixes
        company = re.sub(r'^(for|in|company)\s+', '', company, flags=re.IGNORECASE)
        company = re.sub(r'\s+(for|in|company)$', '', company, flags=re.IGNORECASE)
        company = company.strip()
        
        # If company is empty after cleaning, set to None
        if not company:
            company = None
    
    return {
        "person": person,
        "company": company,
        "kitta": kitta
    }

# Test function to validate the parser
def test_parser():
    """
    Test the parser with various message formats.
    """
    known_people = ["kaka", "john", "sarah", "mike", "alice", "nene"]
    
    test_messages = [
        "appy ipo for kaka for company abc",
        "apply ipo for john in xyz",
        "ipo kaka abc",
        "apply for sarah company def",
        "for mike abc",
        "kaka abc",
        "apply ipo for alice in xyz corp",
        "appy for kaka company abc ltd",
        "apply ipo for nene for company urja 10 kitta",
        "apply ipo for kaka for company himstar 5 kitta",
        "apply ipo for john in xyz 15 kitta",
    ]
    
    print("Testing parser with various message formats:")
    print("=" * 50)
    
    for msg in test_messages:
        result = extract_person_company_and_kitta(msg, known_people)
        print(f"Message: '{msg}'")
        print(f"  Person: {result['person']}")
        print(f"  Company: {result['company']}")
        print(f"  Kitta: {result['kitta']}")
        print("-" * 30)

if __name__ == "__main__":
    test_parser()
