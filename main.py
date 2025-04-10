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
    parser.add_argument('--exact_position', action='store_true', help='Use exact position for date replacing')
    return parser.parse_args()

def find_gps_date_overlay(image_path):
    image = Image.open(image_path)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    date_pattern = r'\d{2}/\d{2}/\d{2}\s+\d{1,2}:\d{2}\s+[AP]M\s+GMT\s+[+-]\d{2}:\d{2}'
    full_text = ' '.join(data['text'])
    match = re.search(date_pattern, full_text)
    if match:
        return extract_date_info(match.group(0), data)
    return find_date_components(data)

def extract_date_info(date_str, data):
    x_min, y_min, x_max, y_max = float('inf'), float('inf'), 0, 0
    for i, text in enumerate(data['text']):
        if text and (text in date_str or date_str in text):
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            x_min, y_min = min(x_min, x), min(y_min, y)
            x_max, y_max = max(x_max, x + w), max(y_max, y + h)
    return {'date_str': date_str, 'x': x_min, 'y': y_min, 'width': x_max - x_min, 'height': y_max - y_min, 'font_size': y_max - y_min}

def find_date_components(data):
    date_components = []
    for i, word in enumerate(data['text']):
        if re.match(r'\d{2}/\d{2}/\d{2}', word) or re.match(r'\d{1,2}:\d{2}', word) or word in ['AM', 'PM', 'GMT']:
            date_components.append({'text': word, 'x': data['left'][i], 'y': data['top'][i], 'width': data['width'][i], 'height': data['height'][i], 'conf': data['conf'][i]})
    if date_components:
        x_values = [comp['x'] for comp in date_components]
        y_values = [comp['y'] for comp in date_components]
        widths = [comp['width'] for comp in date_components]
        heights = [comp['height'] for comp in date_components]
        x, y = min(x_values), min(y_values)
        width = max(x_values) + widths[x_values.index(max(x_values))] - x
        height = max(heights)
        return {'date_str': ' '.join([comp['text'] for comp in date_components]), 'x': x, 'y': y, 'width': width, 'height': height, 'font_size': height}
    return {'date_str': '22/11/24 2:51 PM GMT +05:30', 'x': 10, 'y': 30, 'width': 300, 'height': 20, 'font_size': 20}

def parse_and_adjust_date(date_str):
    match = re.match(r'(\d{2})/(\d{2})/(\d{2})\s+(\d{1,2}):(\d{2})\s+([AP]M)\s+GMT\s+([+-])(\d{2}):(\d{2})', date_str)
    if match:
        day, month, year, hour, minute, am_pm, tz_sign, tz_hour, tz_minute = match.groups()
        year, hour, minute = int(year) + 2000, int(hour), int(minute)
        if am_pm == 'PM' and hour < 12: hour += 12
        elif am_pm == 'AM' and hour == 12: hour = 0
        dt = datetime(year, int(month), int(day), hour, minute) + timedelta(days=1, hours=1)
        new_hour, new_am_pm = (dt.hour % 12 or 12), 'AM' if dt.hour < 12 else 'PM'
        return f"{dt.day:02d}/{dt.month:02d}/{dt.year % 100:02d} {new_hour}:{dt.minute:02d} {new_am_pm} GMT {tz_sign}{tz_hour}:{tz_minute}"
    return None

def sample_background_color(image, x, y, width, height):
    img_array = np.array(image)
    x, y, width, height = int(x), int(y), int(width), int(height)
    samples = []
    if y > 5 and y < img_array.shape[0]:
        samples.extend(img_array[y-5:y, x:x+width].reshape(-1, img_array.shape[2]))
    if y + height + 5 < img_array.shape[0]:
        samples.extend(img_array[y+height:y+height+5, x:x+width].reshape(-1, img_array.shape[2]))
    sample_tuples = [tuple(sample) for sample in samples]
    if sample_tuples:
        color_counts = {color: sample_tuples.count(color) for color in set(sample_tuples)}
        return max(color_counts.items(), key=lambda x: x[1])[0]
    return (0, 0, 0)

def adjust_font_size(draw, font_path, text, box_width, box_height):
    font_size = box_height
    font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.truetype("arial.ttf", font_size)
    while True:
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        if text_width <= box_width and text_height <= box_height:
            break
        font_size -= 1
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.truetype("arial.ttf", font_size)
    return font, text_width, text_height

def update_image_overlay(image_path, output_path, overlay_info, new_date_str, font_path=None, exact_position=False):
    image = Image.open(image_path).convert("RGBA")
    draw = ImageDraw.Draw(image)
    
    if exact_position:
        x, y, width, height = overlay_info['x'], overlay_info['y'], overlay_info['width'], overlay_info['height']
    else:
        x, y, width, height = overlay_info['x'], overlay_info['y'], overlay_info['width'], overlay_info['height']
    
    # Sample the background color around the text area
    bg_color = sample_background_color(image, x, y, width, height)
    
    # Ensure bg_color is a tuple of three elements (RGB)
    if len(bg_color) == 4:
        bg_color = bg_color[:3]
    
    # Draw a rectangle to cover the original text
    draw.rectangle([x, y, x + width, y + height], fill=bg_color)
    
    # Adjust font size to fit the new text within the original text's bounding box
    font, text_width, text_height = adjust_font_size(draw, font_path, new_date_str, width, height)
    
    # Center the new date text within the bounding box
    text_x = x + (width - text_width) / 2
    text_y = y + (height - text_height) / 2
    draw.text((text_x, text_y), new_date_str, font=font, fill=(255, 255, 255))
    
    # Convert back to RGB mode before saving as JPEG
    image = image.convert("RGB")
    image.save(output_path)
    
    print(f"Updated image: {image_path}")
    print(f"New date overlay: {new_date_str}")
    print(f"Overlay position: ({x}, {y}), size: ({width}, {height})")
    print(f"Font size: {font.size}")
    print(f"Saved to: {output_path}")

def process_images(input_dir, output_dir, font_path=None, exact_position=False):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            overlay_info = find_gps_date_overlay(input_path)
            if overlay_info:
                new_date_str = parse_and_adjust_date(overlay_info['date_str']) or "22/11/24 2:51 PM GMT +05:30"
                update_image_overlay(input_path, output_path, overlay_info, new_date_str, font_path, exact_position)
                print(f"Processed image: {filename}")

def main():
    args = parse_args()
    process_images(args.input_dir, args.output_dir, args.font_path, args.exact_position)

if __name__ == "__main__":
    main()