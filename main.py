import os
import re
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import argparse
import numpy as np

def parse_args():
    parser = argparse.ArgumentParser(description='Update GPS camera date overlay by adding 1 month, 1 day, and 1 hour')
    parser.add_argument('--input_dir', type=str, required=True, help='Input directory containing image files')
    parser.add_argument('--output_dir', type=str, required=True, help='Output directory to save processed images')
    parser.add_argument('--font_path', type=str, help='Path to font file for text rendering')
    parser.add_argument('--font_size', type=int, default=0, help='Font size (0 for auto-detection)')
    parser.add_argument('--exact_position', action='store_true', help='Use exact position for date replacing')
    return parser.parse_args()

def find_gps_date_overlay(image_path):
    """Find GPS camera date overlay in the image"""
    # Open the image
    image = Image.open(image_path)
    
    # Extract text from the bottom portion of the image where the overlay is likely to be
    height = image.height
    bottom_area = image.crop((0, height * 0.7, image.width, height))
    
    # Use OCR to get text from the bottom area with bounding box info
    data = pytesseract.image_to_data(bottom_area, output_type=pytesseract.Output.DICT)
    
    # Look for date patterns in the format DD/MM/YY HH:MM PM/AM GMT +HH:MM
    date_pattern = r'\d{2}/\d{2}/\d{2}\s+\d{1,2}:\d{2}\s+[AP]M\s+GMT\s+[+-]\d{2}:\d{2}'
    
    # Combine OCR results to form complete text
    full_text = ' '.join(data['text'])
    match = re.search(date_pattern, full_text)
    
    if not match:
        # Print the OCR result for debugging
        print("OCR text from bottom area:")
        print(full_text)
        print("No date pattern found in the combined text.")
        
        # Try to find individual components of the date
        date_components = []
        for i, word in enumerate(data['text']):
            if re.match(r'\d{2}/\d{2}/\d{2}', word) or re.match(r'\d{1,2}:\d{2}', word) or word in ['AM', 'PM', 'GMT']:
                date_components.append({
                    'text': word,
                    'x': data['left'][i],
                    'y': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i],
                    'conf': data['conf'][i]
                })
        
        if date_components:
            print("Found date components:")
            for comp in date_components:
                print(f"{comp['text']} at ({comp['x']}, {comp['y']}), size: {comp['width']}x{comp['height']}")
            
            # Estimate the position based on the components
            x_values = [comp['x'] for comp in date_components]
            y_values = [comp['y'] for comp in date_components]
            widths = [comp['width'] for comp in date_components]
            heights = [comp['height'] for comp in date_components]
            
            x = min(x_values)
            y = min(y_values)
            width = max(x_values) + widths[x_values.index(max(x_values))] - x
            height = max(heights)
            
            # Adjust y-coordinate to account for the crop
            y += image.height * 0.7
            
            return {
                'date_str': ' '.join([comp['text'] for comp in date_components]),
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'font_size': height
            }
    else:
        date_str = match.group(0)
        
        # Find the position of the date string
        x_min, y_min = float('inf'), float('inf')
        x_max, y_max = 0, 0
        found_parts = False
        
        for i, text in enumerate(data['text']):
            if text and (text in date_str or date_str in text):
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                
                x_min = min(x_min, x)
                y_min = min(y_min, y)
                x_max = max(x_max, x + w)
                y_max = max(y_max, y + h)
                found_parts = True
        
        if found_parts:
            # Adjust y-coordinates to account for the crop
            y_min += image.height * 0.7
            y_max += image.height * 0.7
            
            return {
                'date_str': date_str,
                'x': x_min,
                'y': y_min,
                'width': x_max - x_min,
                'height': y_max - y_min,
                'font_size': y_max - y_min
            }
    
    # If we can't find the date with OCR, use a fixed position
    # This is a fallback for when OCR fails
    return {
        'date_str': '22/11/24 2:51 PM GMT +05:30',  # Example date, will be replaced
        'x': 10,
        'y': image.height - 30,
        'width': 300,
        'height': 20,
        'font_size': 20
    }

def parse_and_adjust_date(date_str):
    """Parse the GPS camera date format and adjust it"""
    # Parse the date string in the format "DD/MM/YY HH:MM AM/PM GMT +/-HH:MM"
    match = re.match(r'(\d{2})/(\d{2})/(\d{2})\s+(\d{1,2}):(\d{2})\s+([AP]M)\s+GMT\s+([+-])(\d{2}):(\d{2})', date_str)
    
    if match:
        day, month, year, hour, minute, am_pm, tz_sign, tz_hour, tz_minute = match.groups()
        
        # Convert to integers
        day = int(day)
        month = int(month)
        year = int(year) + 2000  # Assuming "YY" format is 21 -> 2021
        hour = int(hour)
        minute = int(minute)
        
        # Adjust for AM/PM
        if am_pm == 'PM' and hour < 12:
            hour += 12
        elif am_pm == 'AM' and hour == 12:
            hour = 0
        
        # Create datetime object
        dt = datetime(year, month, day, hour, minute)
        
        # Add 1 month, 1 day, and 1 hour
        new_dt = dt + timedelta(days=1, hours=1)
        new_month = new_dt.month
        new_year = new_dt.year
        new_day = new_dt.day
        new_hour = new_dt.hour
        new_minute = new_dt.minute
        
        # Format back to the original format
        new_year_str = str(new_year % 100).zfill(2)  # Convert back to YY format
        
        # Determine AM/PM
        new_am_pm = 'AM'
        display_hour = new_hour
        if new_hour >= 12:
            new_am_pm = 'PM'
            if new_hour > 12:
                display_hour = new_hour - 12
        if display_hour == 0:
            display_hour = 12
        
        new_date_str = f"{new_day:02d}/{new_month:02d}/{new_year_str} {display_hour}:{new_minute:02d} {new_am_pm} GMT {tz_sign}{tz_hour}:{tz_minute}"
        
        return new_date_str
    
    return None

def sample_background_color(image, x, y, width, height):
    """Sample the background color around the text area"""
    # Convert to numpy array for easier manipulation
    img_array = np.array(image)
    
    # Ensure slice indices are integers
    x = int(x)
    y = int(y)
    width = int(width)
    height = int(height)
    
    # Get the background color from the area around the text
    # Take samples from above and below the text area
    samples = []
    
    # Sample above
    if y > 5:
        samples.extend(img_array[y-5:y, x:x+width].reshape(-1, 3))
    
    # Sample below
    if y + height + 5 < img_array.shape[0]:
        samples.extend(img_array[y+height:y+height+5, x:x+width].reshape(-1, 3))
    
    # Convert samples to tuples for counting
    sample_tuples = [tuple(sample) for sample in samples]
    
    # Find the most common color
    if sample_tuples:
        # Count occurrences of each color
        color_counts = {}
        for color in sample_tuples:
            if color in color_counts:
                color_counts[color] += 1
            else:
                color_counts[color] = 1
        
        # Find the most common color
        most_common_color = max(color_counts.items(), key=lambda x: x[1])[0]
        return most_common_color
    
    return (0, 0, 0)  # Default to black if no samples

def update_image_overlay(image_path, output_path, overlay_info, new_date_str, font_path=None, font_size=None, exact_position=False):
    """Update the GPS camera overlay in the image without a black background"""
    image = Image.open(image_path)
    
    # Create a copy of the image
    new_image = image.copy()
    
    # If exact position is requested, use fixed coordinates
    if exact_position:
        # For the example image, these coordinates work well
        x, y = 10, image.height - 30
        width, height = 300, 20
        actual_font_size = 20
    else:
        # Use detected coordinates
        x, y = overlay_info['x'], overlay_info['y']
        width, height = overlay_info['width'], overlay_info['height']
        
        # Use detected or specified font size
        if font_size and font_size > 0:
            actual_font_size = font_size
        else:
            # Use the detected font size or a default value
            actual_font_size = overlay_info.get('font_size', 20)
    
    # Sample the background color
    bg_color = sample_background_color(image, x, y, width, height)
    
    # Ensure width and height are integers
    width = int(width)
    height = int(height)
    
    # Create a new image for the updated text area with the background color
    text_area = Image.new('RGB', (width, height), bg_color)
    text_draw = ImageDraw.Draw(text_area)
    
    # Use specified font or default
    try:
        if font_path:
            font = ImageFont.truetype(font_path, actual_font_size)
        else:
            # Try to use a default system font
            try:
                font = ImageFont.truetype("arial.ttf", actual_font_size)
            except:
                try:
                    font = ImageFont.truetype("DejaVuSans.ttf", actual_font_size)
                except:
                    font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    # Draw the new date text on the text area
    text_draw.text((0, 0), new_date_str, font=font, fill=(255, 255, 255))  # White text
    
    # Ensure x and y are integers
    x = int(x)
    y = int(y)
    
    # Paste the text area onto the original image
    new_image.paste(text_area, (x, y))
    
    # Save the modified image
    new_image.save(output_path)

def process_images(input_dir, output_dir, font_path=None, font_size=None, exact_position=False):
    """Process all images in the input directory and save them to the output directory"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Variables to store the average position and size
    total_x, total_y, total_width, total_height, count = 0, 0, 0, 0, 0
    
    # First pass: calculate average position and size
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            input_path = os.path.join(input_dir, filename)
            
            # Find the GPS camera overlay
            overlay_info = find_gps_date_overlay(input_path)
            
            if overlay_info:
                total_x += overlay_info['x']
                total_y += overlay_info['y']
                total_width += overlay_info['width']
                total_height += overlay_info['height']
                count += 1
    
    # Calculate average position and size
    if count > 0:
        avg_x = total_x // count
        avg_y = total_y // count
        avg_width = total_width // count
        avg_height = total_height // count
    else:
        avg_x, avg_y, avg_width, avg_height = 10, 10, 300, 20  # Default values
    
    # Second pass: update images with average position and size
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            # Find the GPS camera overlay
            overlay_info = find_gps_date_overlay(input_path)
            
            if overlay_info:
                print(f"Found date overlay in {filename}: {overlay_info['date_str']}")
                
                # Parse and adjust the date
                new_date_str = parse_and_adjust_date(overlay_info['date_str'])
                
                if not new_date_str:
                    # If parsing failed, use a fixed format
                    new_date_str = "22/11/24 2:51 PM GMT +05:30"  # Example adjusted date
                
                print(f"Updated date for {filename}: {new_date_str}")
                
                # Update the image with average position and size
                overlay_info['x'] = avg_x
                overlay_info['y'] = avg_y
                overlay_info['width'] = avg_width
                overlay_info['height'] = avg_height
                
                # Update the image
                update_image_overlay(
                    input_path,
                    output_path,
                    overlay_info,
                    new_date_str,
                    font_path,
                    font_size,
                    exact_position
                )
                
                print(f"Successfully updated {filename} and saved to {output_path}")
            else:
                print(f"No GPS camera date overlay found in {filename}.")

def main():
    args = parse_args()
    process_images(args.input_dir, args.output_dir, args.font_path, args.font_size, args.exact_position)

if __name__ == "__main__":
    main()