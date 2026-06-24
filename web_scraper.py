import requests
from bs4 import BeautifulSoup
import os
import json
from urllib.parse import urljoin, urlparse
from datetime import datetime
import re

class WebScraperBot:
    def __init__(self, url):
        self.url = url
        self.domain = urlparse(url).netloc
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.content = {
            'url': url,
            'scraped_at': datetime.now().isoformat(),
            'title': '',
            'sections': [],
            'meta_info': {}
        }
    
    def fetch_page(self):
        """Fetch the webpage content"""
        try:
            response = self.session.get(self.url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except requests.RequestException as e:
            print(f"❌ Error fetching page: {e}")
            return None
    
    def get_content_root(self, soup):
        """Return the main content container if available, otherwise the full page."""
        selectors = [
            {'name': 'main'},
            {'name': 'div', 'attrs': {'id': 'content'}},
            {'name': 'div', 'attrs': {'id': 'main'}},
            {'name': 'article'},
            {'name': 'section', 'attrs': {'class': re.compile(r'\b(main|content|article)\b', re.I)}},
            {'name': 'div', 'attrs': {'class': re.compile(r'\b(main|content|article)\b', re.I)}}
        ]
        for selector in selectors:
            root = soup.find(**selector)
            if root and root.get_text(strip=True):
                return root
        return soup
    
    def extract_text_content(self, soup):
        """Extract all text content in sequence"""
        print("📝 Extracting text content...")
        
        content_root = self.get_content_root(soup)
        
        # Get page title
        self.content['title'] = soup.title.string.strip() if soup.title else "No title"
        
        # Extract meta information
        for meta in soup.find_all('meta'):
            if meta.get('name'):
                self.content['meta_info'][meta['name']] = meta.get('content', '')
            elif meta.get('property'):
                self.content['meta_info'][meta['property']] = meta.get('content', '')
        
        # Build sections from page elements in document order
        section = {
            'heading': {'level': 'h0', 'text': 'Introduction'},
            'content': []
        }
        self.content['sections'].append(section)
        
        for element in content_root.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'table', 'img', 'a'], recursive=True):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                section = {
                    'heading': {
                        'level': element.name,
                        'text': element.get_text(strip=True)
                    },
                    'content': []
                }
                self.content['sections'].append(section)
                continue
            
            if element.name == 'p':
                text = element.get_text(strip=True)
                if text:
                    section['content'].append({'type': 'paragraph', 'text': text})
                continue
            
            if element.name in ['ul', 'ol']:
                items = [li.get_text(strip=True) for li in element.find_all('li') if li.get_text(strip=True)]
                if items:
                    section['content'].append({'type': 'list', 'list_type': element.name, 'items': items})
                continue
            
            if element.name == 'table':
                headers = [th.get_text(strip=True) for th in element.find_all('th')]
                rows = []
                for row in element.find_all('tr'):
                    cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                    if cells:
                        rows.append(cells)
                if rows:
                    section['content'].append({'type': 'table', 'headers': headers, 'rows': rows})
                continue
            
            if element.name == 'img':
                img_src = element.get('src') or element.get('data-src')
                if img_src:
                    section['content'].append({
                        'type': 'image',
                        'url': urljoin(self.url, img_src),
                        'alt_text': element.get('alt', ''),
                        'title': element.get('title', '')
                    })
                continue
            
            if element.name == 'a':
                href = element.get('href')
                if href:
                    href = href.strip()
                    if href and not href.startswith(('javascript:', '#', 'mailto:')):
                        section['content'].append({
                            'type': 'link',
                            'url': urljoin(self.url, href),
                            'text': element.get_text(strip=True),
                            'title': element.get('title', '')
                        })
                continue
    
    def extract_images(self, soup):
        """Extract all images with sources"""
        print("🖼️  Extracting images...")
        content_root = self.get_content_root(soup)
        
        for img in content_root.find_all('img'):
            img_src = img.get('src') or img.get('data-src')
            if img_src:
                full_url = urljoin(self.url, img_src)
                self.content['images'].append({
                    'url': full_url,
                    'alt_text': img.get('alt', ''),
                    'title': img.get('title', '')
                })
    
    def extract_links(self, soup):
        """Extract all links with their text"""
        print("🔗 Extracting links...")
        content_root = self.get_content_root(soup)
        
        for link in content_root.find_all('a', href=True):
            href = link['href'].strip()
            if not href or href.startswith(('javascript:', '#', 'mailto:')):
                continue
            full_url = urljoin(self.url, href)
            self.content['links'].append({
                'url': full_url,
                'text': link.get_text(strip=True),
                'title': link.get('title', '')
            })
    
    def save_to_file(self, filename='scraped_content.json'):
        """Save all extracted content to a JSON file"""
        print(f"💾 Saving content to {filename}...")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.content, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Content saved successfully to {filename}")
    
    def save_to_text(self, filename='scraped_content.txt'):
        """Save content in a readable text format"""
        print(f"📄 Saving readable text to {filename}...")
        
        with open(filename, 'w', encoding='utf-8') as f:
            # Write header
            f.write("=" * 80 + "\n")
            f.write(f"WEB SCRAPER BOT - CONTENT EXTRACTION\n")
            f.write(f"URL: {self.url}\n")
            f.write(f"Scraped at: {self.content['scraped_at']}\n")
            f.write("=" * 80 + "\n\n")
            
            # Title
            f.write(f"📌 PAGE TITLE: {self.content['title']}\n\n")
            
            # Meta Information
            f.write("📋 META INFORMATION:\n")
            f.write("-" * 40 + "\n")
            for key, value in self.content['meta_info'].items():
                f.write(f"{key}: {value}\n")
            
            # Sections with content under headings
            f.write("\n📑 SECTIONS:\n")
            f.write("-" * 80 + "\n")
            for section in self.content['sections']:
                heading = section['heading']
                if heading['level'] == 'h0':
                    f.write("\nINTRODUCTION:\n")
                else:
                    indent = "  " * (int(heading['level'][1]) - 1)
                    f.write(f"\n{indent}[{heading['level'].upper()}] {heading['text']}:\n")
                f.write("-" * 60 + "\n")

                if not section['content']:
                    f.write("(No content found under this heading)\n")
                for item in section['content']:
                    if item['type'] == 'paragraph':
                        f.write(f"\n{item['text']}\n")
                    elif item['type'] == 'list':
                        f.write(f"\nList ({item['list_type']}):\n")
                        for idx, list_item in enumerate(item['items'], 1):
                            f.write(f"  {idx}. {list_item}\n")
                    elif item['type'] == 'table':
                        if item['headers']:
                            f.write("\n" + " | ".join(item['headers']) + "\n")
                            f.write("-" * 50 + "\n")
                        for row in item['rows']:
                            f.write(" | ".join(row) + "\n")
                    elif item['type'] == 'image':
                        f.write(f"\nImage URL: {item['url']}\n")
                        f.write(f"Alt Text: {item['alt_text']}\n")
                        if item['title']:
                            f.write(f"Title: {item['title']}\n")
                    elif item['type'] == 'link':
                        f.write(f"\nLink: {item['text']}\n")
                        f.write(f"URL: {item['url']}\n")
                        if item['title']:
                            f.write(f"Title: {item['title']}\n")
                f.write("\n" + "=" * 80 + "\n")
        
        print(f"✅ Text file saved successfully to {filename}")
    
    def scrape(self):
        """Main scraping function"""
        print(f"🚀 Starting to scrape: {self.url}")
        print("-" * 50)
        
        soup = self.fetch_page()
        if not soup:
            print("❌ Failed to fetch page. Exiting.")
            return False
        
        # Extract all content
        self.extract_text_content(soup)
        
        # Create output directory
        output_dir = "scraped_data"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate filename based on domain and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain_name = self.domain.replace('.', '_')
        base_filename = f"{output_dir}/{domain_name}_{timestamp}"
        
        # Save in both formats
        self.save_to_file(f"{base_filename}.json")
        self.save_to_text(f"{base_filename}.txt")
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 EXTRACTION SUMMARY")
        print("=" * 50)
        print(f"📌 Title: {self.content['title']}")
        print(f"📑 Sections: {len(self.content['sections'])}")
        print(f"📝 Paragraphs: {sum(1 for s in self.content['sections'] for item in s['content'] if item['type'] == 'paragraph')}")
        print(f"🖼️  Images: {sum(1 for s in self.content['sections'] for item in s['content'] if item['type'] == 'image')}")
        print(f"🔗 Links: {sum(1 for s in self.content['sections'] for item in s['content'] if item['type'] == 'link')}")
        print(f"📋 Lists: {sum(1 for s in self.content['sections'] for item in s['content'] if item['type'] == 'list')}")
        print(f"📊 Tables: {sum(1 for s in self.content['sections'] for item in s['content'] if item['type'] == 'table')}")
        print(f"\n💾 Files saved in '{output_dir}' directory")
        return True

def main():
    """Main function to run the scraper"""
    print("\n🌐 WEB SCRAPER BOT")
    print("=" * 50)
    
    # Get URL from user
    url = input("Enter the URL to scrape: ").strip()
    
    if not url:
        print("❌ No URL provided. Exiting.")
        return
    
    # Add http:// if not present
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        print(f"🔧 Added https:// prefix: {url}")
    
    # Create and run scraper
    scraper = WebScraperBot(url)
    scraper.scrape()
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
