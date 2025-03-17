from PIL import Image, ImageDraw, ImageFont
import pytesseract
from datetime import datetime, timedelta
import re
import os

# Set the Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Function to update the date and time
def update_datetime(text):
    """
    Updates the date and time in the given text by adding 1 month, 1 day, and 1 hour.
    
    Args:
        text (str): The text containing the date and time.
    
    Returns:
        str: The updated text with the new date and time.
    """
    datetime_pattern = r'\b(\d{2}/\d{2}/\d{4} \d{2}:\d{2}[AP]M GMT\+\d{2}:\d{2})\b'
    match = re.search(datetime_pattern, text)
    if match:
        original_datetime = match.group(1)
        dt = datetime.strptime(original_datetime, '%d/%m/%Y %I:%M%p GMT%z')
        updated_dt = dt + timedelta(days=1, hours=1)
        updated_dt = updated_dt.replace(month=dt.month + 1)
        updated_datetime = updated_dt.strftime('%d/%m/%Y %I:%M%p GMT%z')
        text = text.replace(original_datetime, updated_datetime)
    return text

# Function to process each image
def process_image(image_path, output_path):
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
            updated_text = update_datetime(text)
            if updated_text != text:
                x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                draw = ImageDraw.Draw(image)
                draw.rectangle([x, y, x + w, y + h], fill="white")
                font = ImageFont.load_default()
                draw.text((x, y), updated_text, font=font, fill="black")
    
    image.save(output_path)
    print(f"Processed and saved: {output_path}")

# Function to process a directory of images
def process_directory(input_dir, output_dir):
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
            print(f'Skipping unsupported file: {filename}')

# Main function
def main():
    input_dir = input("Enter the path to the input directory: ")
    output_dir = input("Enter the path to the output directory: ")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    process_directory(input_dir, output_dir)
    print('All images processed.')

if __name__ == "__main__":
    main()