from typing import List, Dict, Optional
import re
from bs4 import BeautifulSoup

def looks_like_name(text: str) -> bool:
    if not text:
        return False
    t = text.strip()
    if not t:
        return False
    # Split into tokens and evaluate only a few first tokens for name-like pattern
    tokens = t.split()
    if len(tokens) < 2:
        return False

    stop_words = {
        'consultant','profile','director','manager','lead','senior','junior',
        'chief','head','staff','team','associate','officer','engineer',
        'analyst','specialist'
    }

    # Reject if contains stop words
    for w in tokens:
        if w.lower() in stop_words:
            return False

    # Check that at least first 2 tokens look like name parts
    count_valid = 0
    for w in tokens[:3]:
        if re.match(r'^[A-Z][a-zA-Z\.\-]*$', w):
            count_valid += 1
    if count_valid < 2:
        return False

    return True

def extract_name(soup: BeautifulSoup) -> Optional[str]:
    # 1) Look for elements with class containing 'name'
    for tag in soup.find_all(True):
        classes = tag.get('class') or []
        if any(isinstance(c, str) and 'name' in c.lower() for c in classes):
            text = tag.get_text(strip=True)
            if text and looks_like_name(text):
                return text

    # 2) Look for elements with id containing 'name'
    for tag in soup.find_all(True):
        tid = tag.get('id') or ''
        if 'name' in tid.lower():
            text = tag.get_text(strip=True)
            if text and looks_like_name(text):
                return text

    # 3) Fallback: headings that look like a name
    for tag in soup.find_all(['h1','h2','h3']):
        text = tag.get_text(strip=True)
        if text and looks_like_name(text):
            return text

    # 4) Any tag that looks like a name (last resort)
    for tag in soup.find_all(True):
        text = tag.get_text(strip=True)
        if text and looks_like_name(text):
            return text

    return None

def extract_role(soup: BeautifulSoup) -> Optional[str]:
    # 1) Look for class labels
    for tag in soup.find_all(True):
        classes = tag.get('class') or []
        label_present = any('role' in c.lower() or 'title' in c.lower() or
                            'designation' in c.lower() or 'position' in c.lower()
                            for c in classes if isinstance(c, str))
        if label_present:
            text = tag.get_text(strip=True)
            if text:
                if ':' in text:
                    val = text.split(':', 1)[1].strip()
                else:
                    val = text
                if val:
                    # Avoid cases where the value is just the label
                    if val.lower() not in {'role','title','designation','position'}:
                        return val
            # continue searching others
    # 2) Look for lines like "Role: Senior Consultant" etc.
    for tag in soup.find_all(True):
        text = tag.get_text(strip=True)
        if not text:
            continue
        m = re.match(r'(?i)role\s*[:\-]?\s*(.*)', text)
        if m:
            val = m.group(1).strip()
            if val:
                return val
        m = re.match(r'(?i)title\s*[:\-]?\s*(.*)', text)
        if m:
            val = m.group(1).strip()
            if val:
                return val
        m = re.match(r'(?i)designation\s*[:\-]?\s*(.*)', text)
        if m:
            val = m.group(1).strip()
            if val:
                return val
        m = re.match(r'(?i)position\s*[:\-]?\s*(.*)', text)
        if m:
            val = m.group(1).strip()
            if val:
                return val
    return None

def extract_email(soup: BeautifulSoup) -> Optional[str]:
    emails = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.lower().startswith('mailto:'):
            emails.append(href.split(':', 1)[1].strip())
    if emails:
        return emails[0]
    # Fallback: search in text
    text = soup.get_text(" ", strip=True)
    m = re.findall(r'[\w\.-]+@[\w\.-]+\.[A-Za-z]{2,}', text)
    if m:
        return m[0]
    return None

def extract_phone(soup: BeautifulSoup) -> Optional[str]:
    phones = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.lower().startswith('tel:'):
            phones.append(href.split(':', 1)[1].strip())
    if phones:
        return phones[0]
    text = soup.get_text(" ", strip=True)
    # Common international and local formats
    candidates = re.findall(r'(\+?\d[\d\s\-\(\)]{6,}\d)', text)
    for cand in candidates:
        digits = re.sub(r'\D', '', cand)
        if len(digits) >= 7:
            return cand.strip()
    return None

def extract_website(soup: BeautifulSoup) -> Optional[str]:
    websites = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        lhref = href.lower()
        if lhref.startswith(('http://', 'https://')) and not lhref.startswith(('mailto:', 'tel:')):
            websites.append(href)
    if websites:
        return websites[0]
    return None

def extract_company(soup: BeautifulSoup) -> Optional[str]:
    # Heuristic: look for labels like Organization/Company/Employer/Affiliation
    for tag in soup.find_all(True):
        text = tag.get_text(strip=True)
        if not text:
            continue
        lower = text.lower()
        if lower.startswith(('organization', 'organization:', 'org', 'company', 'employer', 'affiliation')):
            if ':' in text:
                val = text.split(':', 1)[1].strip()
            else:
                val = text
            if val and val.lower() not in {'organization', 'company'}:
                return val
    # More relaxed search: any line containing these keywords
    for tag in soup.find_all(True):
        text = tag.get_text(strip=True)
        if not text:
            continue
        for kw in ('organization', 'company', 'employer', 'affiliation'):
            if kw in text.lower():
                m = re.match(r'(?i).*(?:organization|company|employer|affiliation)\s*[:\-]?\s*(.*)', text)
                if m:
                    val = m.group(1).strip()
                    if val:
                        return val
    return None

def transform(input_data: str) -> List[Dict[str, str]]:
    if input_data is None:
        return []

    soup = BeautifulSoup(input_data, 'html.parser')

    name = extract_name(soup)
    subject = f"ConsultantProfile:{name}" if name else "ConsultantProfile:Unknown"

    triples: List[Dict[str, str]] = []

    if name:
        triples.append({'subject': subject, 'predicate': 'hasName', 'object': name})

    role = extract_role(soup)
    if role:
        triples.append({'subject': subject, 'predicate': 'hasRole', 'object': role})

    email = extract_email(soup)
    if email:
        triples.append({'subject': subject, 'predicate': 'hasEmail', 'object': email})

    phone = extract_phone(soup)
    if phone:
        triples.append({'subject': subject, 'predicate': 'hasPhone', 'object': phone})

    website = extract_website(soup)
    if website:
        triples.append({'subject': subject, 'predicate': 'hasWebsite', 'object': website})

    company = extract_company(soup)
    if company:
        triples.append({'subject': subject, 'predicate': 'affiliatedWith', 'object': company})

    return triples