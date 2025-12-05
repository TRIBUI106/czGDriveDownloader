import os
import re
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import threading

class GDriveDownloader:
    def __init__(self, config_file="config.json"):
        self.config = self.load_config(config_file)
        self.download_dir = self.config.get("download_directory", "./downloads")
        self.max_workers = self.config.get("max_threads", 5)
        self.session = requests.Session()
        self.lock = threading.Lock()
        
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create default config
            default_config = {
                "download_directory": "./downloads",
                "max_threads": 5,
                "chunk_size": 8192
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            return default_config
    
    def extract_file_id(self, url):
        """Extract file ID from Google Drive URL"""
        patterns = [
            r'/file/d/([a-zA-Z0-9_-]+)',
            r'id=([a-zA-Z0-9_-]+)',
            r'/folders/([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_file_metadata(self, file_id):
        """Get file metadata from Google Drive"""
        url = f"https://drive.google.com/uc?id={file_id}&export=download"
        response = self.session.get(url, stream=True, allow_redirects=True)
        
        # Try to get filename from headers
        filename = None
        if 'Content-Disposition' in response.headers:
            content_disp = response.headers['Content-Disposition']
            filename_match = re.search(r'filename="?([^"]+)"?', content_disp)
            if filename_match:
                filename = filename_match.group(1)
        
        if not filename:
            filename = f"file_{file_id}"
        
        return {
            'filename': filename,
            'url': url,
            'file_id': file_id
        }
    
    def download_file(self, file_id, folder_name=None):
        """Download a single file from Google Drive"""
        try:
            metadata = self.get_file_metadata(file_id)
            filename = metadata['filename']
            
            # Create download directory
            if folder_name:
                save_dir = os.path.join(self.download_dir, folder_name)
            else:
                save_dir = self.download_dir
            
            os.makedirs(save_dir, exist_ok=True)
            filepath = os.path.join(save_dir, filename)
            
            # Download with confirmation token if needed
            url = metadata['url']
            response = self.session.get(url, stream=True, allow_redirects=True)
            
            # Check for download confirmation
            if 'download_warning' in response.text or response.status_code != 200:
                # Try with confirmation token
                for key, value in response.cookies.items():
                    if key.startswith('download_warning'):
                        url = f"{metadata['url']}&confirm={value}"
                        response = self.session.get(url, stream=True)
                        break
            
            # Save file
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=self.config.get("chunk_size", 8192)):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Print progress
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            with self.lock:
                                print(f"  [{filename}] {progress:.1f}% - {downloaded}/{total_size} bytes", end='\r')
            
            with self.lock:
                print(f"\n✓ Downloaded: {filename} -> {filepath}")
            return True
            
        except Exception as e:
            with self.lock:
                print(f"✗ Error downloading {file_id}: {str(e)}")
            return False
    
    def download_multiple(self, drive_links):
        """Download multiple files using multi-threading"""
        print(f"Starting downloads with {self.max_workers} threads...")
        print(f"Download directory: {self.download_dir}\n")
        
        tasks = []
        for link in drive_links:
            file_id = self.extract_file_id(link)
            if file_id:
                # Extract folder name from link if it's a named link
                folder_name = f"drive_{file_id[:8]}"
                tasks.append((file_id, folder_name))
            else:
                print(f"✗ Invalid link: {link}")
        
        successful = 0
        failed = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.download_file, file_id, folder_name): (file_id, folder_name)
                for file_id, folder_name in tasks
            }
            
            for future in as_completed(futures):
                if future.result():
                    successful += 1
                else:
                    failed += 1
        
        print(f"\n{'='*50}")
        print(f"Download completed!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"{'='*50}")


def main():
    """Main function"""
    print("=" * 50)
    print("Google Drive Multi-threaded Downloader")
    print("=" * 50)
    
    # Initialize downloader
    downloader = GDriveDownloader()
    
    # Example usage - Add your Google Drive links here
    drive_links = [
        # Add your links here, for example:
        # "https://drive.google.com/file/d/1ABC123xyz/view",
        # "https://drive.google.com/file/d/2DEF456uvw/view",
    ]
    
    # Or input links manually
    print("\nEnter Google Drive links (one per line, empty line to finish):")
    while True:
        link = input("Link: ").strip()
        if not link:
            break
        drive_links.append(link)
    
    if drive_links:
        downloader.download_multiple(drive_links)
    else:
        print("No links provided!")


if __name__ == "__main__":
    main()