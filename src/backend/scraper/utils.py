"""Utility functions for file and folder management."""
import os
from typing import List, Dict


def get_all_courses() -> Dict[str, List[Dict]]:
    """
    Get all scraped courses organized by course code.
    Returns: {
        'JPD113': [
            {'name': 'JPD113_SU25_B5_MC', 'image_count': 10, 'has_pdf': True},
            ...
        ],
        ...
    }
    """
    courses = {}
    images_base = os.path.join("archive", "images")
    documents_base = os.path.join("archive", "documents")
    
    if not os.path.exists(images_base):
        return courses
    
    # Iterate through course code folders
    for course_code in os.listdir(images_base):
        course_path = os.path.join(images_base, course_code)
        if not os.path.isdir(course_path):
            continue
        
        courses[course_code] = []
        
        # Iterate through individual thread folders
        for thread_name in os.listdir(course_path):
            thread_path = os.path.join(course_path, thread_name)
            if not os.path.isdir(thread_path):
                continue
            
            # Count images
            image_files = [
                f for f in os.listdir(thread_path)
                if f.endswith(('.jpg', '.jpeg', '.png'))
            ]
            image_count = len(image_files)
            
            # Check if PDF exists
            pdf_path = os.path.join(
                documents_base, course_code, f"{thread_name}.pdf"
            )
            has_pdf = os.path.exists(pdf_path)
            
            courses[course_code].append({
                'name': thread_name,
                'image_count': image_count,
                'has_pdf': has_pdf,
                'course_code': course_code
            })
    
    return courses


def get_thread_images(course_code: str, thread_name: str) -> List[str]:
    """Get list of image paths for a specific thread."""
    images_path = os.path.join(
        "archive", "images", course_code, thread_name
    )
    
    if not os.path.exists(images_path):
        return []
    
    image_files = sorted(
        [f for f in os.listdir(images_path) if f.endswith(('.jpg', '.jpeg', '.png'))],
        key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else 0
    )
    
    return [os.path.join(images_path, f) for f in image_files]


def get_pdf_path(course_code: str, thread_name: str) -> str:
    """Get PDF path for a specific thread."""
    pdf_path = os.path.join(
        "archive", "documents", course_code, f"{thread_name}.pdf"
    )
    return pdf_path if os.path.exists(pdf_path) else None


def search_threads(query: str) -> List[Dict]:
    """Search for threads by name (case-insensitive)."""
    query = query.lower()
    results = []
    
    courses = get_all_courses()
    for course_code, threads in courses.items():
        for thread in threads:
            if query in thread['name'].lower():
                results.append(thread)
    
    return results


def get_search_suggestions(query: str, limit: int = 5) -> List[str]:
    """Get search suggestions based on partial query."""
    if not query:
        return []
    
    query = query.lower()
    suggestions = set()
    
    courses = get_all_courses()
    for course_code, threads in courses.items():
        # Add course code as suggestion
        if query in course_code.lower():
            suggestions.add(course_code)
        
        # Add thread names as suggestions
        for thread in threads:
            if query in thread['name'].lower():
                suggestions.add(thread['name'])
    
    return sorted(list(suggestions))[:limit]
