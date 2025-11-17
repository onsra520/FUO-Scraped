import os
import time
import re
import requests
from PIL import Image
from pypdf import PdfWriter, PdfReader
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict, List, Tuple


class FUOScraper:
    """Scrape images from FUOverflow and organize them by course code."""
    
    def __init__(
        self,
        username: str,
        password: str,
        headless: bool = False,
        item_delay: int = 2,
        page_load_timeout: int = 10,
        element_timeout: int = 10
    ):
        self.username = username
        self.password = password
        self.driver = None
        self.headless = headless
        self.item_delay = item_delay
        self.page_load_timeout = page_load_timeout
        self.element_timeout = element_timeout
        
    def parse_thread_name(self, url: str) -> Tuple[str, str]:
        """
        Extract course code and full name from thread URL.
        Example: https://fuoverflow.com/threads/jpd113-su25-b5-mc.4934/
        Returns: ('JPD113', 'JPD113_SU25_B5_MC')
        """
        # Extract thread name from URL
        match = re.search(r'/threads/([^/]+)/', url)
        if not match:
            raise ValueError("Invalid thread URL format")
        
        thread_name = match.group(1)
        # Remove the trailing number if exists (e.g., .4934)
        thread_name = re.sub(r'\.\d+$', '', thread_name)
        
        # Convert to uppercase and replace hyphens with underscores
        full_name = thread_name.upper().replace('-', '_')
        
        # Extract course code (first 6 characters)
        course_code = full_name[:6]
        
        return course_code, full_name
    
    def create_folder_structure(self, course_code: str, full_name: str) -> Tuple[str, str, str]:
        """
        Create folder structure: archive/images/{course_code}/{full_name}
        Returns: (parent_folder_path, images_folder_path, pdf_folder_path)
        """
        parent_folder = os.path.join("archive", "images", course_code)
        images_folder = os.path.join(parent_folder, full_name)
        pdf_folder = os.path.join("archive", "documents", course_code)
        
        os.makedirs(images_folder, exist_ok=True)
        os.makedirs(pdf_folder, exist_ok=True)
        
        return parent_folder, images_folder, pdf_folder
    
    def init_driver(self):
        """Initialize Selenium WebDriver."""
        if self.driver is None:
            options = webdriver.EdgeOptions()
            if self.headless:
                options.add_argument('--headless')
                options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            self.driver = webdriver.Edge(options=options)
            if not self.headless:
                self.driver.set_window_size(1920, 1080)
    
    def login(self, url: str):
        """Login to FUOverflow."""
        self.driver.get(url)
        time.sleep(self.page_load_timeout)
        
        try:
            login_button = WebDriverWait(self.driver, self.element_timeout).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    "a.p-navgroup-link.p-navgroup-link--textual.p-navgroup-link--logIn"
                ))
            )
            login_button.click()
            time.sleep(self.page_load_timeout)
            
            input_username = self.driver.find_element(By.NAME, "login")
            input_password = self.driver.find_element(By.NAME, "password")
            
            input_username.send_keys(self.username)
            input_password.send_keys(self.password)
            
            submit_button = self.driver.find_element(
                By.CSS_SELECTOR,
                "button.button--primary.button.button--icon.button--icon--login"
            )
            submit_button.click()
            time.sleep(3)
            
            return True
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def get_image_urls(self) -> List[str]:
        """Extract all image URLs from the current page."""
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, "lxml")
        all_images = soup.find_all("a", class_="file-preview js-lbImage")
        
        img_urls = []
        for img in all_images:
            if img.has_attr("href"):
                img_url = img["href"]
                if not img_url.startswith("http"):
                    img_url = "https://fuoverflow.com" + img_url
                img_urls.append(img_url)
        
        return img_urls
    
    def scrape_images(self, url: str, progress_callback=None) -> Dict:
        """
        Scrape images from FUOverflow thread and save them.
        Returns dict with status, folder paths, and image count.
        """
        try:
            # Parse thread information
            course_code, full_name = self.parse_thread_name(url)
            
            # Create folder structure
            parent_folder, images_folder, pdf_folder = self.create_folder_structure(
                course_code, full_name
            )
            
            # Initialize driver and login
            self.init_driver()
            if not self.login(url):
                return {
                    "success": False,
                    "error": "Login failed",
                    "course_code": course_code,
                    "full_name": full_name
                }
            
            # Get image URLs
            img_urls = self.get_image_urls()
            
            if not img_urls:
                return {
                    "success": False,
                    "error": "No images found",
                    "course_code": course_code,
                    "full_name": full_name
                }
            
            # Download images
            for idx, img_url in enumerate(img_urls, 1):
                try:
                    if progress_callback:
                        progress_callback(idx, len(img_urls))
                    
                    # Open image in new tab
                    self.driver.execute_script(f"window.open('{img_url}', '_blank');")
                    time.sleep(self.item_delay)
                    
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    
                    # Save screenshot
                    img_name = f"{idx}.jpg"
                    img_path = os.path.join(images_folder, img_name)
                    self.driver.save_screenshot(img_path)
                    
                    # Close tab and switch back
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error downloading image {idx}: {e}")
                    continue
            
            # Create PDF
            pdf_path = self.create_pdf(images_folder, pdf_folder, full_name)
            
            # Save to database
            from database import db
            db.add_thread(
                course_code=course_code,
                thread_name=full_name,
                pdf_path=pdf_path,
                images_folder=images_folder,
                image_count=len(img_urls),
                thread_url=url
            )
            
            return {
                "success": True,
                "course_code": course_code,
                "full_name": full_name,
                "images_folder": images_folder,
                "pdf_path": pdf_path,
                "image_count": len(img_urls)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def create_pdf(self, images_folder: str, pdf_folder: str, name: str) -> str:
        """Create PDF from images in the folder."""
        writer = PdfWriter()
        
        # Get all image files
        image_files = sorted(
            [f for f in os.listdir(images_folder) if f.endswith('.jpg')],
            key=lambda x: int(x.split('.')[0])
        )
        
        for image_name in image_files:
            try:
                image_path = os.path.join(images_folder, image_name)
                img = Image.open(image_path)
                
                # Convert to PDF
                img_pdf_path = f"{image_path}.pdf"
                img.save(img_pdf_path, "PDF", resolution=100.0)
                
                # Add to writer
                img_pdf = PdfReader(img_pdf_path)
                writer.add_page(img_pdf.pages[0])
                
                # Clean up temporary PDF
                os.remove(img_pdf_path)
            except Exception as e:
                print(f"Error processing {image_name}: {e}")
                continue
        
        # Save final PDF
        pdf_filename = f"{name}.pdf"
        pdf_path = os.path.join(pdf_folder, pdf_filename)
        
        with open(pdf_path, "wb") as output_file:
            writer.write(output_file)
        
        return pdf_path
