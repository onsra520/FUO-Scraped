"""FastAPI server for FUO Scraper application."""
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, JSONResponse
from fastapi.requests import Request
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional, Dict
import asyncio
from concurrent.futures import ThreadPoolExecutor

from scraper.fuo_scraper import FUOScraper
from database import db

# Load environment variables
load_dotenv()

app = FastAPI(title="FUO Scraper", version="1.0.0")

# Mount static files and templates
app.mount(
    "/static",
    StaticFiles(directory="src/frontend/static"),
    name="static"
)
templates = Jinja2Templates(directory="src/frontend/templates")

# Store scraping tasks
scraping_tasks: Dict[str, Dict] = {}

executor = ThreadPoolExecutor(max_workers=1)


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print("\n🔄 Syncing archive to database...")
    db.sync_from_archive()
    print("✅ Database sync complete\n")


class ScrapeRequest(BaseModel):
    url: str
    headless: bool = False
    item_delay: int = 2
    page_load_timeout: int = 10
    element_timeout: int = 10


class SearchRequest(BaseModel):
    query: str


@app.get("/")
async def home(request: Request):
    """Render homepage."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/view/{course_code}/{thread_name}")
async def view_thread(request: Request, course_code: str, thread_name: str):
    """Render thread viewer page."""
    return templates.TemplateResponse(
        "viewer.html",
        {
            "request": request,
            "course_code": course_code,
            "thread_name": thread_name
        }
    )


@app.get("/api/courses")
async def get_courses():
    """Get all scraped courses from database."""
    try:
        all_threads = db.get_all_threads()
        
        # Group by course code
        courses = {}
        for thread in all_threads:
            course_code = thread['course_code']
            if course_code not in courses:
                courses[course_code] = []
            
            courses[course_code].append({
                'name': thread['thread_name'],
                'image_count': thread['image_count'],
                'has_pdf': bool(thread['pdf_path'] and os.path.exists(thread['pdf_path'])),
                'course_code': course_code
            })
        
        return JSONResponse(content={"success": True, "courses": courses})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/thread/{course_code}/{thread_name}/images")
async def get_images(course_code: str, thread_name: str):
    """Get list of images for a specific thread from database."""
    try:
        thread = db.get_thread(course_code, thread_name)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        images_folder = thread['images_folder']
        if not os.path.exists(images_folder):
            raise HTTPException(status_code=404, detail="Images folder not found")
        
        # Get image files
        image_files = sorted(
            [f for f in os.listdir(images_folder) if f.endswith(('.jpg', '.jpeg', '.png'))],
            key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else 0
        )
        
        # Return relative paths for API
        relative_images = [
            f"/api/image/{course_code}/{thread_name}/{img}"
            for img in image_files
        ]
        
        return JSONResponse(content={
            "success": True,
            "images": relative_images,
            "count": len(relative_images)
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/image/{course_code}/{thread_name}/{filename}")
async def get_image(course_code: str, thread_name: str, filename: str):
    """Serve a specific image file."""
    image_path = os.path.join(
        "archive", "images", course_code, thread_name, filename
    )
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(image_path)


@app.get("/api/thread/{course_code}/{thread_name}/pdf")
@app.head("/api/thread/{course_code}/{thread_name}/pdf")
async def get_pdf(course_code: str, thread_name: str):
    """Serve PDF file for a thread from database."""
    thread = db.get_thread(course_code, thread_name)
    
    if not thread or not thread['pdf_path']:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    pdf_path = thread['pdf_path']
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{thread_name}.pdf"
    )


@app.post("/api/scrape")
async def start_scrape(
    scrape_request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """Start a new scraping task."""
    url = scrape_request.url
    
    # Validate URL
    if not url.startswith("https://fuoverflow.com/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL. Must be a FUOverflow thread URL."
        )
    
    # Create task ID
    task_id = url.split("/threads/")[1].split("/")[0] if "/threads/" in url else str(hash(url))
    
    # Check if already scraping
    if task_id in scraping_tasks and scraping_tasks[task_id]["status"] == "running":
        return JSONResponse(content={
            "success": False,
            "error": "This thread is already being scraped.",
            "task_id": task_id
        })
    
    # Initialize task
    scraping_tasks[task_id] = {
        "status": "running",
        "progress": 0,
        "total": 0,
        "url": url
    }
    
    # Start background task with settings
    background_tasks.add_task(
        run_scraper,
        task_id,
        url,
        scrape_request.headless,
        scrape_request.item_delay,
        scrape_request.page_load_timeout,
        scrape_request.element_timeout
    )
    
    return JSONResponse(content={
        "success": True,
        "task_id": task_id,
        "message": "Scraping started"
    })


@app.get("/api/scrape/status/{task_id}")
async def get_scrape_status(task_id: str):
    """Get status of a scraping task."""
    if task_id not in scraping_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return JSONResponse(content={
        "success": True,
        "task": scraping_tasks[task_id]
    })


@app.get("/api/search/suggestions")
async def search_suggestions(q: str):
    """Get search suggestions from database."""
    try:
        threads = db.search_threads(q)
        suggestions = set()
        
        for thread in threads[:10]:
            suggestions.add(thread['course_code'])
            suggestions.add(thread['thread_name'])
        
        return JSONResponse(content={
            "success": True,
            "suggestions": sorted(list(suggestions))[:5]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
async def search(search_request: SearchRequest):
    """Search for threads in database."""
    try:
        threads = db.search_threads(search_request.query)
        
        # Group by course code
        grouped = {}
        for thread in threads:
            course_code = thread['course_code']
            if course_code not in grouped:
                grouped[course_code] = []
            
            grouped[course_code].append({
                'name': thread['thread_name'],
                'image_count': thread['image_count'],
                'has_pdf': bool(thread['pdf_path'] and os.path.exists(thread['pdf_path'])),
                'course_code': course_code
            })
        
        return JSONResponse(content={
            "success": True,
            "results": grouped
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_scraper(
    task_id: str,
    url: str,
    headless: bool = False,
    item_delay: int = 2,
    page_load_timeout: int = 10,
    element_timeout: int = 10
):
    """Run scraper in background."""
    try:
        username = os.getenv("FUO_USERNAME")
        password = os.getenv("FUO_PASSWORD")
        
        if not username or not password:
            scraping_tasks[task_id]["status"] = "error"
            scraping_tasks[task_id]["error"] = "Missing credentials"
            return
        
        scraper = FUOScraper(
            username,
            password,
            headless=headless,
            item_delay=item_delay,
            page_load_timeout=page_load_timeout,
            element_timeout=element_timeout
        )
        
        def progress_callback(current, total):
            scraping_tasks[task_id]["progress"] = current
            scraping_tasks[task_id]["total"] = total
        
        result = scraper.scrape_images(url, progress_callback)
        
        if result["success"]:
            scraping_tasks[task_id]["status"] = "completed"
            scraping_tasks[task_id]["result"] = result
        else:
            scraping_tasks[task_id]["status"] = "error"
            scraping_tasks[task_id]["error"] = result.get("error", "Unknown error")
            
    except Exception as e:
        scraping_tasks[task_id]["status"] = "error"
        scraping_tasks[task_id]["error"] = str(e)


@app.get("/favicon.ico")
async def favicon():
    """Return favicon or 204 No Content to avoid 404 errors."""
    # Return empty response with 204 status (no favicon configured)
    return JSONResponse(content={}, status_code=204)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8211)
