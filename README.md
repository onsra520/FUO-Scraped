# FUO Scraper - Web Application

Ứng dụng web scraper để tải và tổ chức hình ảnh từ FUOverflow.

## Tính năng

- 🕷️ Scrape hình ảnh từ FUOverflow threads
- 📁 Tự động tổ chức theo mã môn học (6 ký tự đầu)
- 📄 Tự động tạo PDF từ hình ảnh
- 🗄️ SQLite database để quản lý dữ liệu
- 🖼️ Xem hình ảnh one-by-one hoặc scroll PDF
- 🔍 Tìm kiếm với suggestions tự động
- ⚙️ Settings cho scraper (Headless mode, v.v.)
- 🎨 Dark theme UI hiện đại
- ⚡ FastAPI backend với port 8211

## Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình môi trường

Tạo file `.env` trong thư mục gốc:

```
FUO_USERNAME=your_username
FUO_PASSWORD=your_password
```

### 3. Tạo thư mục cần thiết

```bash
mkdir -p archive/images archive/documents
```

## Sử dụng

### Chạy server

Cách đơn giản nhất - chạy từ thư mục root:

```bash
python run.py
```

Hoặc với uvicorn trực tiếp:

```bash
cd src/backend/api
python app.py
```

Hoặc:

```bash
uvicorn src.backend.api.app:app --host 0.0.0.0 --port 8211 --reload
```

Server sẽ chạy tại: `http://localhost:8211`

## Cấu trúc dự án

```
FUO-Scraped/
├── archive/
│   ├── images/          # Hình ảnh được tổ chức theo mã môn
│   │   ├── JPD113/
│   │   │   ├── JPD113_SU25_B5_MC/
│   │   │   └── JPD113_SU25_B6_MC/
│   │   └── ...
│   └── documents/       # PDF files
│       ├── JPD113/
│       └── ...
├── src/
│   ├── backend/
│   │   ├── api/
│   │   │   └── app.py           # FastAPI server
│   │   ├── database/
│   │   │   ├── schema.sql       # Database schema
│   │   │   └── database.py      # Database manager
│   │   └── scraper/
│   │       ├── fuo_scraper.py   # Scraper class
│   │       └── utils.py         # Helper functions
│   └── frontend/
│       ├── static/
│       │   ├── css/
│       │   │   └── style.css    # Dark theme CSS
│       │   └── js/
│       │       ├── main.js      # Homepage logic
│       │       └── viewer.js    # Viewer logic
│       └── templates/
│           ├── index.html       # Homepage
│           └── viewer.html      # Image/PDF viewer
├── run.py               # Script chạy server (main entry point)
├── .env                 # Environment variables (create this)
├── .env.example         # Example environment file
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## API Endpoints

### GET /
Homepage với scraper input và danh sách folders

### GET /view/{course_code}/{thread_name}
Xem hình ảnh và PDF của một thread

### GET /api/courses
Lấy danh sách tất cả các môn đã scrape

### POST /api/scrape
Bắt đầu scrape một thread mới
```json
{
    "url": "https://fuoverflow.com/threads/..."
}
```

### GET /api/scrape/status/{task_id}
Kiểm tra tiến trình scraping

### GET /api/search/suggestions?q={query}
Lấy gợi ý tìm kiếm

### POST /api/search
Tìm kiếm threads
```json
{
    "query": "JPD113"
}
```

### GET /api/thread/{course_code}/{thread_name}/images
Lấy danh sách hình ảnh của thread

### GET /api/thread/{course_code}/{thread_name}/pdf
Tải PDF của thread

## Cách hoạt động

1. **Scraping**: Nhập link thread từ FUOverflow
2. **Settings**: Tùy chọn headless mode để scrape nhanh hơn
3. **Login**: Tự động đăng nhập bằng credentials từ .env
4. **Download**: Tải tất cả hình ảnh từ thread
5. **Organize**: Lưu vào `archive/images/{COURSE_CODE}/{THREAD_NAME}/`
6. **PDF Creation**: Tạo PDF và lưu vào `archive/documents/{COURSE_CODE}/`
7. **Database**: Lưu thông tin vào SQLite database
8. **Display**: Hiển thị trong homepage và có thể xem từng ảnh hoặc PDF

## Yêu cầu hệ thống

- Python 3.8+
- Edge WebDriver (cho Selenium)
- Kết nối internet
- Tài khoản FUOverflow hợp lệ

## Lưu ý

- Port mặc định: **8211**
- Scraper sử dụng Edge browser
- Hình ảnh được lưu dưới dạng .jpg
- PDF được tạo tự động sau khi scrape xong
- Folder được tổ chức theo 6 ký tự đầu của tên thread

## Troubleshooting

### Lỗi login
- Kiểm tra username/password trong file .env
- Đảm bảo tài khoản FUOverflow còn hoạt động

### Lỗi Edge WebDriver
- Cài đặt Edge browser
- Cập nhật Edge lên phiên bản mới nhất
- Selenium tự động tải WebDriver phù hợp

### Lỗi port đã sử dụng
- Thay đổi port trong `run.py` hoặc `app.py`: `uvicorn.run(app, host="0.0.0.0", port=XXXX)`

## License

MIT License
