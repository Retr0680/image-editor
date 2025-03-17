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
        actual_font_size = overlay_info['font_size']

# Sample the background color
bg_color = sample_background_color(image, x, y, width, height)

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

# Paste the text area onto the original image
new_image.paste(text_area, (x, y))

# Save the modified image
new_image.save(output_path)