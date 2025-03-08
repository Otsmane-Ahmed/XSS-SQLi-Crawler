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
To scan a website for vulnerabilities, use:

```bash
python xss_sqli_crawler.py <target_url>
```

The script will crawl the target site, extract all internal URLs, and test them for **XSS** and **SQL Injection** vulnerabilities.

## Example Output
```
[*] Found 42 links.
[+] SQLi vulnerability found in parameter 'id' at http://example.com/index.php?id=1'
[+] XSS vulnerability found in parameter 'query' at http://example.com/search.php?query=<script>alert(1)</script>
```

## Disclaimer
This tool is intended **for educational and security research purposes only**. Unauthorized scanning of systems you do not own is **illegal and unethical**. The author is not responsible for any misuse of this tool.

## License
This project is released under the **MIT License**.
