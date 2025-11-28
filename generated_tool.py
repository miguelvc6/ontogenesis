from typing import List, Dict
import re
from bs4 import BeautifulSoup

def transform(input_data: str) -> List[Dict[str, str]]:
    """
    Transform a consultant profile HTML page into KGTriples using predicates:
    hasName, hasRole, hasEmail, hasPhone
    """
    if input_data is None:
        return []

    soup = BeautifulSoup(input_data, 'html.parser')
    if soup is None:
        return []

    def get_text(el) -> str:
        return el.get_text(strip=True) if el else ""

    def extract_name() -> str:
        name = None
        # 1) itemprop="name"
        el = soup.find(attrs={"itemprop": "name"})
        if el:
            name = get_text(el)
        # 2) meta author or og:title
        if not name:
            meta = soup.find('meta', attrs={'name': 'author'})
            if meta and meta.get('content'):
                name = meta['content'].strip()
        if not name:
            meta = soup.find('meta', attrs={'property': 'og:title'})
            if meta and meta.get('content'):
                name = meta['content'].strip()
        # 3) Heuristic: look for headings that look like a name
        if not name:
            for tag in ['h1', 'h2', 'h3', 'span', 'div', 'p']:
                for el in soup.find_all(tag, limit=100):
                    txt = get_text(el)
                    if not txt:
                        continue
                    parts = txt.split()
                    if len(parts) >= 2 and all(p[0].isupper() for p in parts[:2]):
                        # Exclude common non-name terms
                        low = txt.lower()
                        if any(w in low for w in ['profile', 'consultant', 'about', 'contact']):
                            continue
                        name = txt
                        break
                if name:
                    break
        # 4) Fallback: any text that resembles a name (two capitalized words)
        if not name:
            for line in soup.stripped_strings:
                parts = line.split()
                if len(parts) >= 2 and all(p[0].isupper() for p in parts[:2]):
                    name = line.strip()
                    break
        return name

    def extract_role() -> str:
        role = None
        # itemprop="jobTitle"
        el = soup.find(attrs={"itemprop": "jobTitle"})
        if el:
            role = get_text(el)
        # name-based role
        if not role:
            el = soup.find(attrs={"name": "role"})
            if el:
                role = get_text(el)
        # class containing 'role'
        if not role:
            for el in soup.find_all(class_=lambda c: c and 'role' in c.lower()):
                role = get_text(el)
                if role:
                    break
        # heuristic headings mentioning role/position/title
        if not role:
            for tag in ['h2', 'h3', 'strong', 'p', 'span']:
                for el in soup.find_all(tag):
                    txt = get_text(el)
                    if not txt:
                        continue
                    low = txt.lower()
                    if any(w in low for w in ['role', 'position', 'title', 'designation']):
                        role = txt
                        break
                if role:
                    break
        return role

    def extract_email() -> str:
        # mailto links
        a = soup.find('a', href=lambda href: href and href.startswith('mailto:'))
        if a and a.get('href'):
            return a['href'][7:]
        # text search
        text = soup.get_text(" ", strip=True)
        m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if m:
            return m.group(0)
        return None

    def extract_phone() -> str:
        # tel links
        a = soup.find('a', href=lambda href: href and href.startswith('tel:'))
        if a and a.get('href'):
            return a['href'][4:]
        # text search
        text = soup.get_text(" ", strip=True)
        m = re.findall(r'(\+?\d[\d\s\-\(\)]{7,}\d)', text)
        if m:
            return m[0]
        return None

    name = extract_name()
    subject = name if name else "ConsultantProfile"

    triples: List[Dict[str, str]] = []

    def add_triple(predicate: str, obj: str):
        if obj is None or obj == "":
            return
        triples.append({"subject": subject, "predicate": predicate, "object": obj})

    if name:
        add_triple("hasName", name)

    role = extract_role()
    if role:
        add_triple("hasRole", role)

    email = extract_email()
    if email:
        add_triple("hasEmail", email)

    phone = extract_phone()
    if phone:
        add_triple("hasPhone", phone)

    return triples