"""Database module for FUO Scraper using SQLite."""

import sqlite3
import os
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Database:
    """SQLite database manager for scraped threads."""

    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        if db_path is None:
            db_path = os.getenv("DB_PATH", "archive/fuo_scraper.db")
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Create database and tables if they don't exist."""
        # Ensure archive directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Read schema file
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = f.read()

        # Execute schema
        conn = self.get_connection()
        try:
            conn.executescript(schema)
            conn.commit()
        finally:
            conn.close()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add_thread(
        self,
        course_code: str,
        thread_name: str,
        pdf_path: str,
        images_folder: str,
        image_count: int,
        thread_url: Optional[str] = None,
    ) -> int:
        """Add or update a scraped thread."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO scraped_threads 
                (course_code, thread_name, thread_url, pdf_path, images_folder, image_count)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(course_code, thread_name) 
                DO UPDATE SET
                    pdf_path = excluded.pdf_path,
                    images_folder = excluded.images_folder,
                    image_count = excluded.image_count,
                    scraped_at = CURRENT_TIMESTAMP
                """,
                (
                    course_code,
                    thread_name,
                    thread_url,
                    pdf_path,
                    images_folder,
                    image_count,
                ),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_all_threads(self) -> List[Dict]:
        """Get all scraped threads."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT * FROM scraped_threads 
                ORDER BY scraped_at DESC
                """
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_threads_by_course(self, course_code: str) -> List[Dict]:
        """Get all threads for a specific course."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT * FROM scraped_threads 
                WHERE course_code = ?
                ORDER BY scraped_at DESC
                """,
                (course_code,),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_thread(self, course_code: str, thread_name: str) -> Optional[Dict]:
        """Get a specific thread."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT * FROM scraped_threads 
                WHERE course_code = ? AND thread_name = ?
                """,
                (course_code, thread_name),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def search_threads(self, query: str) -> List[Dict]:
        """Search threads by course code or thread name."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT * FROM scraped_threads 
                WHERE course_code LIKE ? OR thread_name LIKE ?
                ORDER BY scraped_at DESC
                """,
                (f"%{query}%", f"%{query}%"),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_all_course_codes(self) -> List[str]:
        """Get all unique course codes."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT DISTINCT course_code 
                FROM scraped_threads 
                ORDER BY course_code
                """
            )
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        finally:
            conn.close()

    def delete_thread(self, course_code: str, thread_name: str) -> bool:
        """Delete a thread from database."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                """
                DELETE FROM scraped_threads 
                WHERE course_code = ? AND thread_name = ?
                """,
                (course_code, thread_name),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def sync_from_archive(self):
        """Sync existing archive data to database."""
        images_dir = "archive/images"
        documents_dir = "archive/documents"
        
        if not os.path.exists(images_dir):
            return
        
        synced_count = 0
        
        # Scan all course codes in archive/images
        for course_code in os.listdir(images_dir):
            course_path = os.path.join(images_dir, course_code)
            if not os.path.isdir(course_path):
                continue
            
            # Scan all thread folders in this course
            for thread_name in os.listdir(course_path):
                thread_path = os.path.join(course_path, thread_name)
                if not os.path.isdir(thread_path):
                    continue
                
                # Check if already in database
                existing = self.get_thread(course_code, thread_name)
                if existing:
                    continue
                
                # Count images
                image_files = [
                    f for f in os.listdir(thread_path)
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))
                ]
                image_count = len(image_files)
                
                # Check for PDF
                pdf_path = os.path.join(documents_dir, course_code, f"{thread_name}.pdf")
                if not os.path.exists(pdf_path):
                    pdf_path = ""
                
                # Add to database
                try:
                    self.add_thread(
                        course_code=course_code,
                        thread_name=thread_name,
                        pdf_path=pdf_path,
                        images_folder=thread_path,
                        image_count=image_count,
                        thread_url=None
                    )
                    synced_count += 1
                    print(f"✓ Synced: {course_code}/{thread_name} ({image_count} images)")
                except Exception as e:
                    print(f"✗ Failed to sync {course_code}/{thread_name}: {e}")
        
        if synced_count > 0:
            print(f"\n✅ Synced {synced_count} thread(s) from archive to database")
        else:
            print("ℹ️  No new threads to sync")


# Global database instance
db = Database()
