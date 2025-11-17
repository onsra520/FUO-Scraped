-- FUO Scraper Database Schema

CREATE TABLE IF NOT EXISTS scraped_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL,
    thread_name TEXT NOT NULL,
    thread_url TEXT,
    pdf_path TEXT,
    images_folder TEXT NOT NULL,
    image_count INTEGER DEFAULT 0,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_code, thread_name)
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_course_code ON scraped_threads(course_code);
CREATE INDEX IF NOT EXISTS idx_thread_name ON scraped_threads(thread_name);
CREATE INDEX IF NOT EXISTS idx_scraped_at ON scraped_threads(scraped_at DESC);
