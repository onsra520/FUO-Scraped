import os, time, requests
from PIL import Image
from pypdf import PdfReader, PdfWriter
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def PDFWriter(Image_Folder):
    Name = Image_Folder
    os.makedirs("Exercise Folder", exist_ok=True)
    PDF_Writer = PdfWriter()

    Image_Files = []
    for Num in range(1, len(os.listdir(Image_Folder)) + 1):
        Image_Files.append(f"{Num}.jpg".lower())

    for Image_Name in Image_Files:
        Image_Path = os.path.join(Image_Folder, Image_Name)
        Img = Image.open(Image_Path)
        Img_PDF_Path = Image_Path + ".pdf"
        Img.save(Img_PDF_Path, "PDF")
        Img_PDF = PdfReader(Img_PDF_Path)
        PDF_Writer.add_page(Img_PDF.pages[0])
        os.remove(Img_PDF_Path)

    PDF_Name = f"{Name}.pdf"
    Output_PDF_Path = os.path.join("Exercise Folder", PDF_Name)
    with open(Output_PDF_Path, "wb") as Output_PDF:
        PDF_Writer.write(Output_PDF)

    print(f"Đã tạo thành công file: {PDF_Name}")


class ScrapeRunning:
    def __init__(self, Folder_Name, URLs):
        self.Account = {"User Name": "trtien520", "Password": "Trtien0408**"}
        self.Folder_Name = Folder_Name
        self.URLs = URLs
        self.Question = 1
        self.Folder_Path = self.Create_Folder()
        self.Driver = webdriver.Edge()
        self.Scrape_Image()
        PDFWriter(Folder_Name)

    def Create_Folder(self):
        if not os.path.exists(self.Folder_Name):
            os.makedirs(self.Folder_Name, exist_ok=True)
        return os.path.abspath(self.Folder_Name)

    def Login_Account(self):
        self.Driver.get(self.URLs)
        time.sleep(3)
        Login_Button = WebDriverWait(self.Driver, 1).until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "a.p-navgroup-link.p-navgroup-link--textual.p-navgroup-link--logIn",
                )
            )
        )
        Login_Button.click()
        time.sleep(5)

        Input_Username = self.Driver.find_element(By.NAME, "login")
        Input_Password = self.Driver.find_element(By.NAME, "password")

        Input_Username.send_keys(self.Account["User Name"])
        Input_Password.send_keys(self.Account["Password"])

        Submit_Button = self.Driver.find_element(
            By.CSS_SELECTOR,
            "button.button--primary.button.button--icon.button--icon--login",
        )
        Submit_Button.click()
        time.sleep(2)

    def Get_Img_URLs(self):
        print("Đang lấy tất cả các URL ảnh...")
        Page = self.Driver.page_source
        Source = BeautifulSoup(Page, "lxml")
        All_Image = Source.find_all("a", class_="file-preview js-lbImage")

        Img_URLs = []
        for img in All_Image:
            if img.has_attr("href"):
                img_url = img["href"]
                Img_URLs.append(img_url)

        print(f"Đã lấy {len(Img_URLs)} URL ảnh.")
        return Img_URLs

    def Save_Image(self, Image_URL, Img_Name):
        try:
            Folder_Path = self.Folder_Path
            if not os.path.exists(Folder_Path):
                os.makedirs(Folder_Path, exist_ok=True)

            Img_Path = os.path.join(Folder_Path, Img_Name)
            print(f"Đang tải ảnh từ {Image_URL}")
            Img_Data = requests.get(Image_URL).content

            with open(Img_Path, "wb") as img_file:
                img_file.write(Img_Data)
            print(f"Đã lưu ảnh: {Img_Name}")
        except Exception as e:
            print(f"Lỗi khi lưu ảnh {Img_Name}: {e}")

    def Scrape_Image(self):
        self.Driver.set_window_size(1920, 1080)
        time.sleep(10)
        self.Login_Account()
        time.sleep(3)

        Img_URLs = self.Get_Img_URLs()

        for img_url in Img_URLs:
            full_img_url = "https://fuoverflow.com" + img_url
            print(f"Mở ảnh tại: {full_img_url}")

            self.Driver.execute_script(f"window.open('{full_img_url}', '_blank');")
            time.sleep(2)

            self.Driver.switch_to.window(self.Driver.window_handles[-1])

            try:
                Img_Name = f"{self.Question}.jpg"

                Screenshot_Path = os.path.join(self.Folder_Path, Img_Name)
                self.Driver.save_screenshot(Screenshot_Path)

                print(f"Đã chụp màn hình và lưu vào {Screenshot_Path}")

                self.Question += 1

            except Exception as e:
                print(f"Lỗi khi lấy ảnh từ tab mới: {e}")

            time.sleep(1)
            self.Driver.close()
            self.Driver.switch_to.window(self.Driver.window_handles[0])

        self.Driver.quit()