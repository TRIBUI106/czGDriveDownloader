# 🚀 Google Drive Multi-threaded Downloader

Tool download file từ Google Drive với tốc độ cao sử dụng multi-threading, hỗ trợ download nhiều file cùng lúc với tên file và định dạng chính xác.

## ✨ Tính năng

- ⚡ **Multi-threading**: Download nhiều file đồng thời để tăng tốc độ
- 📦 **Batch Download**: Thêm nhiều link Google Drive và download cùng lúc
- 📝 **Tên file chính xác**: Tự động lấy tên file gốc từ Google Drive
- 🎯 **Định dạng đúng**: Tự động nhận diện và thêm extension (.pdf, .jpg, .zip, v.v.)
- ⚙️ **Cấu hình linh hoạt**: Dễ dàng tùy chỉnh qua file config.json
- 📊 **Progress Tracking**: Hiển thị tiến trình download realtime
- 🔄 **Xử lý file lớn**: Hỗ trợ download file lớn với confirmation token
- 🛡️ **Error Handling**: Xử lý lỗi và retry tự động

## 📋 Yêu cầu

- Python 3.7+
- pip (Python package manager)

## 🔧 Cài đặt

### 1. Clone hoặc tải project

```bash
git clone <repository-url>
cd gdrive-downloader
```

### 2. Cài đặt thư viện cần thiết

```bash
pip install requests beautifulsoup4
```

Hoặc sử dụng requirements.txt:

```bash
pip install -r requirements.txt
```

## 🚀 Sử dụng

### Cách 1: Chạy trực tiếp

```bash
python gdrive_downloader.py
```

Sau đó nhập các link Google Drive khi được yêu cầu:

```
Link 1: https://drive.google.com/file/d/1ABC123xyz/view
Link 2: https://drive.google.com/file/d/2DEF456uvw/view
Link 3: [Enter để bắt đầu download]
```

### Cách 2: Thêm link trực tiếp vào code

Mở file `gdrive_downloader.py` và thêm link vào danh sách:

```python
drive_links = [
    "https://drive.google.com/file/d/1ABC123xyz/view",
    "https://drive.google.com/file/d/2DEF456uvw/view",
    "https://drive.google.com/file/d/3GHI789rst/view",
]
```

## ⚙️ Cấu hình

File `config.json` sẽ được tự động tạo khi chạy lần đầu:

```json
{
    "download_directory": "./downloads",
    "max_threads": 5,
    "chunk_size": 32768
}
```

### Các tham số:

- **download_directory**: Thư mục lưu file (mặc định: `./downloads`)
- **max_threads**: Số thread download đồng thời (khuyến nghị: 3-10)
- **chunk_size**: Kích thước mỗi chunk download (bytes, mặc định: 32KB)

### Tùy chỉnh:

```json
{
    "download_directory": "D:/MyDownloads",
    "max_threads": 8,
    "chunk_size": 65536
}
```

## 📁 Cấu trúc thư mục

```
gdrive-downloader/
├── gdrive_downloader.py    # Script chính
├── config.json             # File cấu hình (tự động tạo)
├── README.md              # Hướng dẫn này
├── requirements.txt       # Danh sách thư viện
└── downloads/            # Thư mục chứa file download
    ├── document.pdf
    ├── image.jpg
    └── video.mp4
```

## 🎯 Các loại link hỗ trợ

Tool hỗ trợ nhiều định dạng URL của Google Drive:

```
https://drive.google.com/file/d/FILE_ID/view
https://drive.google.com/file/d/FILE_ID/view?usp=sharing
https://drive.google.com/open?id=FILE_ID
https://drive.google.com/uc?id=FILE_ID
```

## 📊 Ví dụ output

```
============================================================
🚀 Google Drive Multi-threaded Downloader
============================================================
✓ Created config file: config.json

📎 Enter Google Drive links (one per line)
   Press Enter twice (empty line) to start downloading

Link 1: https://drive.google.com/file/d/1ABC123xyz/view
Link 2: 

============================================================
Starting downloads with 5 threads...
Download directory: /path/to/downloads
============================================================

[1/1] Queued: 1ABC123xyz

============================================================

  [Document.pdf] 45.2% - 2048000/4529152 bytes
✓ Downloaded: Document.pdf
  Saved to: /path/to/downloads/Document.pdf

============================================================
📊 Download Summary
============================================================
✓ Successful: 1
✗ Failed: 0
📁 Location: /path/to/downloads
============================================================
```

## 🔍 Xử lý sự cố

### File download bị thiếu extension:
✅ **Đã fix**: Tool giờ tự động nhận diện và thêm extension dựa trên:
- Content-Type header từ Google Drive
- Tên file gốc từ metadata
- Mapping các loại file phổ biến

### Tên file không đúng:
✅ **Đã fix**: Tool lấy tên chính xác từ Google Drive metadata

### Download chậm:
- Tăng `max_threads` trong config.json (khuyến nghị: 5-10)
- Tăng `chunk_size` cho file lớn (64KB - 128KB)

### Lỗi kết nối:
- Kiểm tra kết nối internet
- Google Drive có thể giới hạn tốc độ download
- Thử giảm `max_threads`

## 💡 Tips

1. **Tối ưu tốc độ**: Với file nhỏ, dùng 8-10 threads. File lớn dùng 3-5 threads
2. **Tránh rate limit**: Không nên download quá nhiều file cùng lúc
3. **File lớn**: Google Drive có thể yêu cầu xác nhận, tool tự động xử lý
4. **Đường dẫn tuyệt đối**: Có thể dùng đường dẫn đầy đủ trong config (VD: `D:/Downloads`)

## 🐛 Báo lỗi

Nếu gặp vấn đề, vui lòng cung cấp:
- Link Google Drive đang thử download
- Thông báo lỗi đầy đủ
- File config.json đang dùng

## 📝 License

MIT License - Tự do sử dụng và chỉnh sửa

## 🙏 Credits

Developed with ❤️ for fast and efficient Google Drive downloads