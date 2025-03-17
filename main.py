from PIL import Image, ImageDraw, ImageFont
import pytesseract
from datetime import datetime, timedelta
import re
import os

# Function to update the date and time
def update_datetime(text):
    datetime_pattern = r'\b(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\b'
    match = re.search(datetime_pattern, text)
    if match:
        original_datetime = match.group(1)
        dt = datetime.strptime(original_datetime, '%Y-%m-%d %H:%M:%S')
        updated_dt = dt + timedelta(days=1, hours=1)  # Add 1 day and 1 hour
        updated_dt = updated_dt.replace(month=dt.month + 1)  # Add 1 month
        updated_datetime = updated_dt.strftime('%Y-%m-%d %H:%M:%S')
        text = text.replace(original_datetime, updated_datetime)
    return text

# Function to process each image
def process_image(image_path, output_path):
    print(f"Processing {image_path}")
    image = Image.open(image_path)
    
    # Use OCR to extract text
    text = pytesseract.image_to_string(image)
    print(f"Extracted text: {text}")
    
    # Update the date and time in the text
    updated_text = update_datetime(text)
    print(f"Updated text: {updated_text}")
    
    # Draw the updated text on the image
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((10, 10), updated_text, font=font, fill="black")
    
    # Save the updated image
    image.save(output_path)
    print(f"Saved to {output_path}")

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