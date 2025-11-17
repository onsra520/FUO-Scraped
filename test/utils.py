import os
from PIL import Image
from pypdf import PdfReader, PdfWriter


def folder_check() -> None:
    """Check and create 'Exercise Folder' if it doesn't exist."""
    sub_folder = ["images", "documents"]
    for folder in sub_folder:
        if not os.path.exists(os.path.join("archive", folder)):
            os.makedirs(os.path.join("archive", folder))
            print(f"{folder} is created")
        else:
            print(f"{folder} already exists")


def pdf_writer(image_folder: str) -> None:
    """Create a PDF file from images in the specified folder.

    Args:
        image_folder (str): The folder containing images to be converted to PDF.
    """

    writer = PdfWriter()
    image_file = []
    image_file.extend(
        f"{Num}.jpg".lower()
        for Num in range(1, len(os.listdir(image_folder)) + 1)
    )

    for image_name in image_file:
        image_path = os.path.join(image_folder, image_name)
        img = Image.open(image_path)
        img_pdf_path = f"{image_path}.pdf"
        img.save(img_pdf_path, "PDF")
        img_pdf = PdfReader(img_pdf_path)
        writer.add_page(img_pdf.pages[0])
        os.remove(img_pdf_path)

    file_name = f"{image_folder}.pdf"
    output_path = os.path.join("archive", "documents", file_name)
    with open(output_path, "wb") as output_file:
        writer.write(output_file)

    print(f"{file_name} created successfully.")

if __name__ == "__main__":
    folder_check()