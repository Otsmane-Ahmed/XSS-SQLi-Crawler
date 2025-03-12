# XSS & SQLi Crawler

## Description
The **XSS & SQLi Crawler** is a security testing tool that scans all URLs of a target website for **Cross-Site Scripting (XSS)** and **SQL Injection (SQLi)** vulnerabilities. This tool systematically crawls a website and tests each discovered URL for potential security flaws.

## Features
- **Automated Website Crawling** – Extracts all internal links from the target domain.
- **SQL Injection Testing** – Detects SQL injection vulnerabilities using multiple payloads.
- **XSS Testing** – Scans for reflected cross-site scripting vulnerabilities.
- **TOR Integration** – Routes all traffic through the **TOR network** for anonymity.
- **Multi-Threading Support** – Enhances scanning speed by running multiple threads.
- **User-Agent Randomization** – Mimics different browsers to avoid detection.
- **Save & Load URLs** – Allows saving and reloading crawled URLs for future testing.

## Installation

### Prerequisites
Ensure you have **Python 3.x** installed. Additionally, the **TOR service** must be running before executing the script.

### Install Dependencies
Run the following command to install the required Python libraries:

```bash
pip install requests beautifulsoup4 socks stem argparse
```

### Start the TOR Service
Before running the script, ensure the TOR service is active:

```bash
sudo service tor start  
```

For Windows users, open the **TOR browser** and keep it running.

## Usage
### Starting a New Scan
To scan a website for vulnerabilities, use:

```bash
python xss_sqli_crawler.py
```

You will be prompted to choose between starting a new scan or loading previously saved URLs.

**Example:**
```
$ python xss_sqli_crawler.py
Choose an option:
1. Start a new scan
2. Load URLs from a text file
Enter your choice (1 or 2): 1
Enter the website URL to scan (e.g., http://example.com): http://example.com
[*] Starting new scan for http://example.com
[DEBUG] Found link: http://example.com/page1
[DEBUG] Found link: http://example.com/page2
[*] Found 2 links
[INFO] Saved 2 URLs to example_com_urls.txt
[+] SQLi vulnerability found in parameter 'id' at http://example.com/page1?id=1'
[+] XSS vulnerability found in path at http://example.com/page2/<script>alert(1)</script>
```

### Loading URLs from a File
If you have previously scanned a website and saved the URLs, you can reload them for testing:

```bash
python xss_sqli_crawler.py
```

**Example:**
```
$ python xss_sqli_crawler.py
Choose an option:
1. Start a new scan
2. Load URLs from a text file
Enter your choice (1 or 2): 2
Enter the path to the text file containing URLs: ./example_com_urls.txt
[INFO] Loaded 2 URLs from ./example_com_urls.txt
[*] Testing 2 loaded links
[+] SQLi vulnerability found in parameter 'id' at http://example.com/page1?id=1'
[+] XSS vulnerability found in path at http://example.com/page2/<script>alert(1)</script>
```

## Disclaimer
This tool is intended **for educational and security research purposes only**. Unauthorized scanning of systems you do not own is **illegal and unethical**. The author is not responsible for any misuse of this tool.

## License
This project is released under the **MIT License**.
