import os
import pytesseract
from PIL import Image, ImageDraw, ImageFont
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import cv2
import re
import numpy as np

# Configure Tesseract path (adjust if needed)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Example Windows path

def find_date_time_location(image_path, date_time_str):
    """
    Finds the bounding box coordinates of the date/time string in the image.

    Args:
        image_path: Path to the image.
        date_time_str: The date/time string to locate.

    Returns:
        A tuple (x, y, w, h) representing the bounding box, or None if not found.
    """
    img_cv = cv2.imread(image_path)
    img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    d = pytesseract.image_to_data(img_gray, output_type=pytesseract.Output.DICT)
    n_boxes = len(d['text'])
    for i in range(n_boxes):
        if int(d['conf'][i]) > 60: # confidence of 60%
            if date_time_str == d['text'][i]:
                (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
                return x, y, w, h
                
            # if the dates are split up, check for part of the dates in each text box.
            elif date_time_str in d['text'][i]:
              
                temp_x = 99999999999
                temp_y = 99999999999
                temp_w = 0
                temp_h = 0

                # iterate through all text boxes again to see if the date is split up.
                for j in range(n_boxes):
                  if date_time_str in d['text'][j]:
                    if d['left'][j] < temp_x:
                      temp_x = d['left'][j]
                    if d['top'][j] < temp_y:
                      temp_y = d['top'][j]
                    if (d['left'][j] + d['width'][j]) > temp_w:
                      temp_w = d['left'][j] + d['width'][j]
                    if d['height'][j] > temp_h:
                      temp_h = d['height'][j]
                      
                # if the date was found split up.
                if temp_x != 99999999999:
                  return temp_x, temp_y, temp_w - temp_x, temp_h
    return None

def get_most_common_font_color(image_path, bounding_box):
    """
    Detects the most common font color within a bounding box.

    Args:
        image_path: Path to the image.
        bounding_box: (x, y, w, h) of the bounding box.

    Returns:
        A tuple (R, G, B) representing the most common color, or (0,0,0) if error
    """
    if bounding_box is None:
      return (0,0,0)
    
    x, y, w, h = bounding_box
    try:
      img = cv2.imread(image_path)
      roi = img[y:y + h, x:x + w]

      # Reshape for easier color counting
      pixels = roi.reshape(-1, 3)

      # Count color occurrences
      unique, counts = np.unique(pixels, axis=0, return_counts=True)

      # Most common color
      most_common_color = tuple(unique[np.argmax(counts)].tolist())

      return most_common_color
    except Exception as e:
        print(f"Error getting font color in {image_path}: {e}")
        return (0,0,0)


def process_image(image_path):
    """
    Processes a single image: extracts text, updates date/time, and redraws.

    Args:
        image_path: Path to the image.
    """
    try:
        img = Image.open(image_path)
        img_cv = cv2.imread(image_path)
        img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(img_gray)

        # Find the date/time string (more robust regex)
        date_time_str = None
        for line in text.split('\n'):
            match = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", line) # Example format YYYY-MM-DD HH:MM:SS
            if match:
                try:
                    parse(match.group(0))
                    date_time_str = match.group(0)
                    break
                except ValueError:
                    pass
        if date_time_str:
            original_datetime = parse(date_time_str)
            adjusted_datetime = original_datetime + relativedelta(months=1, days=1, hours=1)
            adjusted_datetime_str = adjusted_datetime.strftime("%Y-%m-%d %H:%M:%S")  # Format to match original.

            # Find the bounding box of the original date/time
            bounding_box = find_date_time_location(image_path, date_time_str)

            # Get the most common color in that area
            font_color = get_most_common_font_color(image_path, bounding_box)

            # Determine font size using bounding box height
            if bounding_box:
              font_size = bounding_box[3]
            else:
              font_size = 20 #default

            # Load the font
            try:
              font = ImageFont.truetype("arial.ttf", font_size) #attempt to use arial first.
            except IOError:
              font = ImageFont.load_default() #default to system font.

            # Draw over the old text
            draw = ImageDraw.Draw(img)
            if bounding_box:
                x, y, w, h = bounding_box
                # Draw a rectangle over the original text
                draw.rectangle([x, y, x + w, y + h], fill=(0, 0, 0)) # black fill to cover the original.

                # Draw the updated text on the image
                draw.text((x, y), adjusted_datetime_str, font=font, fill=font_color)
            else:
                print(f"Could not determine text location. drawing text on 10,10: {image_path}")
                draw.text((10, 10), adjusted_datetime_str, font=font, fill=font_color) # draw at 10,10 if location could not be determined.

            img.save(image_path)  # Overwrite the original image
            print(f"Processed: {image_path}")
        else:
            print(f"Date/time not found in: {image_path}")

    except Exception as e:
        print(f"Error processing {image_path}: {e}")


def batch_process_images(image_directory):
    """
    Processes all images in a directory.

    Args:
        image_directory: Path to the directory containing images.
    """
    for filename in os.listdir(image_directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(image_directory, filename)
            process_image(image_path)


# Example usage
image_directory = "path/to/your/images"  # Replace with your image directory.
batch_process_images(image_directory)
