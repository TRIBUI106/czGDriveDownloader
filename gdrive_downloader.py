import os
import re
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import threading
from bs4 import BeautifulSoup

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
                "chunk_size": 32768
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            print(f"✓ Created config file: {config_file}")
            return default_config
    
    def extract_file_id(self, url):
        """Extract file ID from Google Drive URL"""
        patterns = [
            r'/file/d/([a-zA-Z0-9_-]+)',
            r'id=([a-zA-Z0-9_-]+)',
            r'/folders/([a-zA-Z0-9_-]+)',
            r'drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def is_folder(self, file_id):
        """Check if the ID is a folder"""
        url = f"https://drive.google.com/drive/folders/{file_id}"
        response = self.session.get(url, allow_redirects=True)
        return 'folders' in response.url
    
    def get_folder_name(self, file_id):
        """Get folder name from Google Drive"""
        try:
            url = f"https://drive.google.com/drive/folders/{file_id}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                # Try to extract folder name from title
                title_match = re.search(r'<title>([^<]+)</title>', response.text)
                if title_match:
                    folder_name = title_match.group(1).replace(' - Google Drive', '').strip()
                    # Clean folder name
                    folder_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name)
                    return folder_name if folder_name else f"folder_{file_id[:8]}"
            
            return f"folder_{file_id[:8]}"
        except:
            return f"folder_{file_id[:8]}"
    
    def get_file_metadata(self, file_id):
        """Get file metadata from Google Drive"""
        try:
            # First, try to get file info page
            info_url = f"https://drive.google.com/file/d/{file_id}/view"
            response = self.session.get(info_url)
            
            filename = None
            
            # Try to extract filename from page title
            if response.status_code == 200:
                title_match = re.search(r'<title>([^<]+)</title>', response.text)
                if title_match:
                    filename = title_match.group(1).replace(' - Google Drive', '').strip()
                    # Clean filename
                    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            # Get download URL
            download_url = f"https://drive.google.com/uc?id={file_id}&export=download"
            
            # Try direct download to get proper filename and extension
            response = self.session.get(download_url, stream=True, allow_redirects=True)
            
            # Get filename from Content-Disposition header
            if 'Content-Disposition' in response.headers:
                content_disp = response.headers['Content-Disposition']
                filename_match = re.search(r'filename\*?=["\']?(?:UTF-8\'\')?([^"\';]+)', content_disp)
                if filename_match:
                    header_filename = filename_match.group(1)
                    # Decode URL-encoded filename
                    from urllib.parse import unquote
                    header_filename = unquote(header_filename)
                    if header_filename and '.' in header_filename:
                        filename = header_filename
            
            # Get content type to determine extension
            content_type = response.headers.get('Content-Type', '')
            
            # If still no filename or no extension, try to add one
            if not filename or '.' not in filename:
                extension = self.get_extension_from_content_type(content_type)
                if filename and extension:
                    filename = f"{filename}{extension}"
                elif not filename:
                    filename = f"file_{file_id}{extension}"
            
            return {
                'filename': filename,
                'url': download_url,
                'file_id': file_id,
                'response': response
            }
        except Exception as e:
            print(f"Error getting metadata: {e}")
            return {
                'filename': f"file_{file_id}",
                'url': f"https://drive.google.com/uc?id={file_id}&export=download",
                'file_id': file_id,
                'response': None
            }
    
    def get_extension_from_content_type(self, content_type):
        """Get file extension from content type"""
        extensions = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'application/pdf': '.pdf',
            'application/zip': '.zip',
            'application/x-rar-compressed': '.rar',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
            'text/plain': '.txt',
            'text/html': '.html',
            'video/mp4': '.mp4',
            'audio/mpeg': '.mp3',
        }
        
        for mime_type, ext in extensions.items():
            if mime_type in content_type:
                return ext
        
        return ''
    
    def download_file(self, file_id, folder_name=None):
        """Download a single file from Google Drive"""
        try:
            # Check if it's a folder
            if self.is_folder(file_id):
                with self.lock:
                    print(f"⚠ Skipping folder: {file_id} (folder download not implemented yet)")
                return False
            
            metadata = self.get_file_metadata(file_id)
            filename = metadata['filename']
            
            # Create download directory
            if folder_name:
                save_dir = os.path.join(self.download_dir, folder_name)
            else:
                save_dir = self.download_dir
            
            os.makedirs(save_dir, exist_ok=True)
            filepath = os.path.join(save_dir, filename)
            
            # Use existing response if available
            response = metadata.get('response')
            if not response:
                url = metadata['url']
                response = self.session.get(url, stream=True, allow_redirects=True)
            
            # Check for download confirmation (large files)
            cookies = response.cookies
            if 'download_warning' in response.text or response.status_code != 200:
                for key, value in cookies.items():
                    if key.startswith('download_warning'):
                        url = f"{metadata['url']}&confirm={value}"
                        response = self.session.get(url, stream=True)
                        break
            
            # Save file
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=self.config.get("chunk_size", 32768)):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Print progress
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            with self.lock:
                                print(f"  [{filename}] {progress:.1f}% - {downloaded}/{total_size} bytes", end='\r')
            
            with self.lock:
                print(f"\n✓ Downloaded: {filename}")
                print(f"  Saved to: {filepath}\n")
            return True
            
        except Exception as e:
            with self.lock:
                print(f"✗ Error downloading {file_id}: {str(e)}")
            return False
    
    def download_multiple(self, drive_links):
        """Download multiple files using multi-threading"""
        print(f"\n{'='*60}")
        print(f"Starting downloads with {self.max_workers} threads...")
        print(f"Download directory: {os.path.abspath(self.download_dir)}")
        print(f"{'='*60}\n")
        
        tasks = []
        for i, link in enumerate(drive_links, 1):
            file_id = self.extract_file_id(link)
            if file_id:
                # Get appropriate folder name
                if self.is_folder(file_id):
                    folder_name = self.get_folder_name(file_id)
                else:
                    # For files, create a meaningful folder name or use None for root
                    folder_name = None  # Download directly to root
                
                tasks.append((file_id, folder_name))
                print(f"[{i}/{len(drive_links)}] Queued: {file_id}")
            else:
                print(f"✗ Invalid link: {link}")
        
        print(f"\n{'='*60}\n")
        
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
        
        print(f"\n{'='*60}")
        print(f"📊 Download Summary")
        print(f"{'='*60}")
        print(f"✓ Successful: {successful}")
        print(f"✗ Failed: {failed}")
        print(f"📁 Location: {os.path.abspath(self.download_dir)}")
        print(f"{'='*60}\n")


def main():
    """Main function"""
    print("\n" + "="*60)
    print("🚀 Google Drive Multi-threaded Downloader")
    print("="*60)
    
    # Initialize downloader
    downloader = GDriveDownloader()
    
    # Example usage - Add your Google Drive links here
    drive_links = [
        # Add your links here, for example:
        # "https://drive.google.com/file/d/1ABC123xyz/view",
        # "https://drive.google.com/file/d/2DEF456uvw/view",
    ]
    
    # Or input links manually
    print("\n📎 Enter Google Drive links (one per line)")
    print("   Press Enter twice (empty line) to start downloading\n")
    
    line_count = 1
    while True:
        link = input(f"Link {line_count}: ").strip()
        if not link:
            break
        drive_links.append(link)
        line_count += 1
    
    if drive_links:
        downloader.download_multiple(drive_links)
    else:
        print("\n⚠ No links provided!")
        print("Please run the script again and enter at least one Google Drive link.\n")


if __name__ == "__main__":
    main()