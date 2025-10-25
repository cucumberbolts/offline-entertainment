import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}

def get_article_text(url):
    """
    Fetches an article from a given URL and extracts its main text.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Prefer semantic <article> tag
        article = soup.find("article")
        if article:
            paras = article.find_all("p")
            if paras:
                return "\n\n".join(p.get_text(strip=True) for p in paras)

        # Fallbacks: BBC uses a few different wrapper classes/data attributes
        selectors = [
            'div[data-component="text-block"] p',
            'div.ssrcss-uf6wea-RichTextComponentWrapper p',  # common RichText wrapper
            'main p',
        ]
        for sel in selectors:
            paras = soup.select(sel)
            if paras:
                return "\n\n".join(p.get_text(strip=True) for p in paras)

        # Last resort: all <p> on page (may include nav/ads)
        paras = soup.find_all("p")
        return "\n\n".join(p.get_text(strip=True) for p in paras) if paras else ""

    except requests.RequestException:
        return ""

def _is_article_html(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    # semantic <article> or BBC text-block nodes
    if soup.find("article"):
        return True
    if soup.select('div[data-component="text-block"]'):
        return True
    # JSON-LD may declare an Article or include articleBody
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "{}")
        except Exception:
            continue
        if isinstance(data, dict):
            if data.get("@type") == "Article" or data.get("articleBody"):
                return True
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and (item.get("@type") == "Article" or item.get("articleBody")):
                    return True
    return False

def fetch_articles(search_term: str) -> str:
    """
    Scrapes BBC Travel for articles, filters by search_term, and returns results as a string.
    """
    try:
        homepage = "https://www.bbc.com/travel"
        r = requests.get(homepage, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
    except requests.RequestException as e:
        return f"Error: Could not connect to BBC Travel. {e}"
if __name__ == "__main__":
    homepage = "https://www.bbc.com/travel"
    r = requests.get(homepage, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # collect candidate links from the Travel homepage
    anchors = soup.select('a[href^="/travel/"], a[href^="/news/stories/"]')
    pagelinks = []
    seen = set()
    for a in anchors:
        href = a.get("href")
        if not href:
            continue
        full = urljoin(homepage, href.split("#", 1)[0])
        if full in seen:
            continue
        seen.add(full)
        pagelinks.append(full)
        if len(pagelinks) >= 30: # Limit to 30 links to keep it fast
            break

    results = []
    search_term_lower = search_term.lower()

    for link in pagelinks:
        try:
            # fetch the candidate page
            r2 = requests.get(link, headers=HEADERS, timeout=12)
            r2.raise_for_status()
        except requests.RequestException:
            continue # Skip this link if it fails

        if not _is_article_html(r2.text):
            continue # Skip if it's not an article

        text = get_article_text(link)
        if not text or len(text) < 300:
            continue # Skip if text is too short
        
        str_link = str(link)
        
        # Filter: check for negative keywords
        if "cultural-experiences" in str_link or "worlds-table" in str_link or "/destinations/" in str_link:
            continue
            
        # Filter: check for positive search term
        # If search_term is blank, match all (as per original script)
        is_match = False
        if not search_term_lower:
            is_match = True
        elif search_term_lower in text.lower():
            is_match = True

        if is_match:
            result_string = f"URL: {link}\nLength: {len(text)}\n\n{text[:1000]}...\n\n"
            result_string += ("=" * 80 + "\n\n")
            results.append(result_string)

    if not results:
        return f"No articles found matching '{search_term}'."

    return "".join(results)


if __name__ == "__main__":
    # This block now just tests the function
    term = input("Enter search terms (comma-separated) or leave blank to get all articles: ")
    print("--- Scraping... ---")
    articles_text = fetch_articles(term)
    print(articles_text)
        if len(pagelinks) >= 30:
            break

    search_terms = []
    add = input("Enter search terms (comma-separated) or leave blank to get all articles: ")
    search_terms.append(add)
    for link in pagelinks:
        try:
            # fetch the candidate page and decide if it's an article (not a listing)
            r2 = requests.get(link, headers=HEADERS, timeout=12)
            r2.raise_for_status()
        except requests.RequestException:
            continue

        if not _is_article_html(r2.text):
            # likely a category/listing page — skip
            continue

        text = get_article_text(link)
        if not text or len(text) < 300:
            # still too short to be a full article
            continue
        str_link = str(link)
        # optional: filter by search terms
        for term in search_terms:
            if term.lower() in text.lower() and "cultural-experiences" not in str_link and "worlds-table" not in str_link and "/destinations/" not in str_link:
                print("URL:", link)
                print("Length:", len(text))
                print(text[:1000])
                print("\n" + "=" * 80 + "\n")
                break
