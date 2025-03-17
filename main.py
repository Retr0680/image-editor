from PIL import Image, ImageDraw, ImageFont
import pytesseract
from datetime import datetime, timedelta
import re
import os

# Set the Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Function to update the date and time
def update_datetime(text):
    # Regex to find date and time in the text
    datetime_pattern = r'\b(\d{2}/\d{2}/\d{4} \d{2}:\d{2}[AP]M GMT\+\d{2}:\d{2})\b'
    match = re.search(datetime_pattern, text)
    if match:
        original_datetime = match.group(1)
        # Parse the original date and time
        dt = datetime.strptime(original_datetime, '%d/%m/%Y %I:%M%p GMT%z')
        # Add 1 month, 1 day, and 1 hour
        updated_dt = dt + timedelta(days=1, hours=1)
        updated_dt = updated_dt.replace(month=dt.month + 1)
        # Format the updated date and time
        updated_datetime = updated_dt.strftime('%d/%m/%Y %I:%M%p GMT%z')
        # Replace the original date and time in the text
        text = text.replace(original_datetime, updated_datetime)
    return text

# Function to process each image
def process_image(image_path, output_path):
    print(f"Processing {image_path}")
    # Open the image
    image = Image.open(image_path)
    
    # Use OCR to extract text and its bounding boxes
    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    
    # Loop through the OCR results to find the date and time
    for i in range(len(ocr_data['text'])):
        text = ocr_data['text'][i]
        if text.strip():  # Skip empty text
            # Update the date and time in the text
            updated_text = update_datetime(text)
            if updated_text != text:  # If the text was updated
                # Get the bounding box coordinates
                x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                # Draw a white rectangle to cover the original text
                draw = ImageDraw.Draw(image)
                draw.rectangle([x, y, x + w, y + h], fill="white")
                # Draw the updated text in the same position
                font = ImageFont.load_default()  # Use default font or specify a custom font
                draw.text((x, y), updated_text, font=font, fill="black")
    
    # Save the updated image
    image.save(output_path)
    print(f"Processed and saved: {output_path}")

# Directory containing the images
input_dir = r'C:\Users\Retr0\Documents\Retr0\image editor\input'
output_dir = r'C:\Users\Retr0\Documents\Retr0\image editor\output'

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Process all images in the directory
for filename in os.listdir(input_dir):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        process_image(input_path, output_path)
        print(f'Processed {filename}')
    else:
        print(f'Skipping unsupported file: {filename}')

print('All images processed.')