from PIL import Image, ImageDraw, ImageFont
import pytesseract
from datetime import datetime, timedelta
import re
import os

# Constants
TESSERACT_EXECUTABLE_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
DATE_TIME_PATTERN = r'\b(\d{2}/\d{2}/\d{2} \d{2}:\d{2} [AP]M GMT\+\d{2}:\d{2})\b'
DATE_TIME_FORMAT = '%d/%m/%y %I:%M %p GMT%z'

def update_date_time(text: str) -> str:
    """
    Updates the date and time in the given text by adding 1 month, 1 day, and 1 hour.

    Args:
        text (str): The text containing the date and time.

    Returns:
        str: The updated text with the new date and time.
    """
    match = re.search(DATE_TIME_PATTERN, text)
    if match:
        original_date_time = match.group(1)
        print(f"Original date and time: {original_date_time}")
        date_time = datetime.strptime(original_date_time, DATE_TIME_FORMAT)
        print(f"Date and time object: {date_time}")
        updated_date_time = date_time + timedelta(days=1, hours=1)
        updated_date_time = updated_date_time.replace(month=date_time.month + 1)
        print(f"Updated date and time: {updated_date_time}")
        updated_text = text.replace(original_date_time, updated_date_time.strftime(DATE_TIME_FORMAT))
        print(f"Updated text: {updated_text}")
        return updated_text
    return text

def process_image(image_path: str, output_path: str) -> None:
    """
    Processes the given image by updating the date and time using OCR and image processing techniques.

    Args:
        image_path (str): The path to the input image.
        output_path (str): The path to the output image.
    """
    print(f"Processing {image_path}")
    image = Image.open(image_path)
    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    for i in range(len(ocr_data['text'])):
        text = ocr_data['text'][i]
        if text.strip():
            print(f"Extracted text: {text}")
            updated_text = update_date_time(text)
            if updated_text != text:
                x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                draw = ImageDraw.Draw(image)
                draw.rectangle([x, y, x + w, y + h], fill="white")
                font = ImageFont.load_default()
                draw.text((x, y), updated_text, font=font, fill="black")

    image.save(output_path)
    print(f"Processed and saved: {output_path}")

def process_directory(input_dir: str, output_dir: str) -> None:
    """
    Processes all images in the given directory by updating the date and time using OCR and image processing techniques.

    Args:
        input_dir (str): The path to the input directory.
        output_dir (str): The path to the output directory.
    """
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            process_image(input_path, output_path)
        else:
            print(f"Skipping unsupported file: {filename}")

def main() -> None:
    """
    Main function to process images in a directory.
    """
    input_dir = input("Enter the path to the input directory: ")
    output_dir = input("Enter the path to the output directory: ")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    process_directory(input_dir, output_dir)
    print('All images processed.')

if __name__ == "__main__":
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXECUTABLE_PATH
    main()