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
            'headings': [],
            'paragraphs': [],
            'images': [],
            'links': [],
            'lists': [],
            'tables': [],
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
    
    def extract_text_content(self, soup):
        """Extract all text content in sequence"""
        print("📝 Extracting text content...")
        
        # Get page title
        self.content['title'] = soup.title.string.strip() if soup.title else "No title"
        
        # Extract meta information
        for meta in soup.find_all('meta'):
            if meta.get('name'):
                self.content['meta_info'][meta['name']] = meta.get('content', '')
            elif meta.get('property'):
                self.content['meta_info'][meta['property']] = meta.get('content', '')
        
        # Extract headings in order
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            self.content['headings'].append({
                'level': heading.name,
                'text': heading.get_text(strip=True)
            })
        
        # Extract paragraphs
        for para in soup.find_all('p'):
            text = para.get_text(strip=True)
            if text:  # Only add non-empty paragraphs
                self.content['paragraphs'].append(text)
        
        # Extract lists
        for list_elem in soup.find_all(['ul', 'ol']):
            list_items = []
            for item in list_elem.find_all('li'):
                list_items.append(item.get_text(strip=True))
            if list_items:
                self.content['lists'].append({
                    'type': list_elem.name,
                    'items': list_items
                })
        
        # Extract tables
        for table in soup.find_all('table'):
            table_data = []
            headers = []
            
            # Get headers
            for th in table.find_all('th'):
                headers.append(th.get_text(strip=True))
            
            # Get rows
            for row in table.find_all('tr'):
                row_data = []
                for cell in row.find_all(['td', 'th']):
                    row_data.append(cell.get_text(strip=True))
                if row_data:
                    table_data.append(row_data)
            
            if table_data:
                self.content['tables'].append({
                    'headers': headers,
                    'data': table_data
                })
    
    def extract_images(self, soup):
        """Extract all images with sources"""
        print("🖼️  Extracting images...")
        
        for img in soup.find_all('img'):
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
        
        for link in soup.find_all('a', href=True):
            full_url = urljoin(self.url, link['href'])
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
            
            # Headings structure
            f.write("\n📑 HEADINGS:\n")
            f.write("-" * 40 + "\n")
            for heading in self.content['headings']:
                indent = "  " * (int(heading['level'][1]) - 1)
                f.write(f"{indent}[{heading['level'].upper()}] {heading['text']}\n")
            
            # Main content
            f.write("\n📝 MAIN CONTENT:\n")
            f.write("-" * 40 + "\n")
            for i, para in enumerate(self.content['paragraphs'], 1):
                f.write(f"\n[{i}] {para}\n")
            
            # Lists
            if self.content['lists']:
                f.write("\n📋 LISTS:\n")
                f.write("-" * 40 + "\n")
                for list_data in self.content['lists']:
                    f.write(f"\nList type: {list_data['type']}\n")
                    for i, item in enumerate(list_data['items'], 1):
                        f.write(f"  {i}. {item}\n")
            
            # Tables
            if self.content['tables']:
                f.write("\n📊 TABLES:\n")
                f.write("-" * 40 + "\n")
                for table in self.content['tables']:
                    if table['headers']:
                        f.write(" | ".join(table['headers']) + "\n")
                        f.write("-" * 50 + "\n")
                    for row in table['data']:
                        f.write(" | ".join(row) + "\n")
            
            # Images
            f.write("\n🖼️  IMAGES:\n")
            f.write("-" * 40 + "\n")
            for i, img in enumerate(self.content['images'], 1):
                f.write(f"\n{i}. URL: {img['url']}\n")
                f.write(f"   Alt Text: {img['alt_text']}\n")
                f.write(f"   Title: {img['title']}\n")
            
            # Links
            f.write("\n🔗 LINKS:\n")
            f.write("-" * 40 + "\n")
            for i, link in enumerate(self.content['links'], 1):
                f.write(f"\n{i}. {link['text']}\n")
                f.write(f"   URL: {link['url']}\n")
                if link['title']:
                    f.write(f"   Title: {link['title']}\n")
        
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
        self.extract_images(soup)
        self.extract_links(soup)
        
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
        print(f"📑 Headings: {len(self.content['headings'])}")
        print(f"📝 Paragraphs: {len(self.content['paragraphs'])}")
        print(f"🖼️  Images: {len(self.content['images'])}")
        print(f"🔗 Links: {len(self.content['links'])}")
        print(f"📋 Lists: {len(self.content['lists'])}")
        print(f"📊 Tables: {len(self.content['tables'])}")
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
