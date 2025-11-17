"""Init file for scraper package."""
from .fuo_scraper import FUOScraper
from .utils import (
    get_all_courses,
    get_thread_images,
    get_pdf_path,
    search_threads,
    get_search_suggestions
)

__all__ = [
    'FUOScraper',
    'get_all_courses',
    'get_thread_images',
    'get_pdf_path',
    'search_threads',
    'get_search_suggestions'
]
