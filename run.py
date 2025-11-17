"""
FUO Scraper - Run Script
Chạy script này để khởi động web application
"""
import os
import sys

# Add src/backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'src', 'backend')
sys.path.insert(0, backend_path)

if __name__ == "__main__":
    print("=" * 60)
    print("🕷️  FUO Scraper Web Application")
    print("=" * 60)
    print("Server đang chạy tại: http://localhost:8211")
    print("Nhấn Ctrl+C để dừng server")
    print("=" * 60)
    
    # Tạo các thư mục cần thiết
    os.makedirs("archive/images", exist_ok=True)
    os.makedirs("archive/documents", exist_ok=True)
    
    # Import and run
    import uvicorn
    
    # Chạy server với app path
    uvicorn.run(
        "api.app:app",
        host="127.0.0.1",
        port=8211,
        reload=True,
        reload_dirs=[backend_path]
    )
