# 📸 Image Editor

This script processes images to update the GPS camera date overlay by adding 1 month, 1 day, and 1 hour to the existing date.
[![wakatime](https://wakatime.com/badge/user/6fce47e6-f384-4fb2-9ab4-d7ce4a048eb8/project/75cfb9b3-5b90-428c-8677-8bf0bdf0e300.svg)](https://wakatime.com/badge/user/6fce47e6-f384-4fb2-9ab4-d7ce4a048eb8/project/75cfb9b3-5b90-428c-8677-8bf0bdf0e300)

## 🚀 Features

- Automatically detects and updates GPS camera date overlays in images.
- Customizable font and size for the date overlay.
- Supports exact positioning for date replacement.
- Samples background color to blend the new date overlay seamlessly.

## 🛠️ Requirements

- Python 3.x
- Pillow
- pytesseract
- numpy

You can install the required packages using pip:
```sh
pip install pillow pytesseract numpy
```

## 📋 Usage

```sh
python main.py --input_dir <input_directory> --output_dir <output_directory> [--font_path <font_file>] [--font_size <font_size>] [--exact_position]
```

### Arguments

- `--input_dir`: Input directory containing image files (required)
- `--output_dir`: Output directory to save processed images (required)
- `--font_path`: Path to font file for text rendering (optional)
- `--font_size`: Font size (0 for auto-detection) (optional)
- `--exact_position`: Use exact position for date replacing (optional)

### Example

```sh
python main.py --input_dir ./images --output_dir ./output --font_path ./fonts/arial.ttf --font_size 20 --exact_position
```

This command processes all images in the `./images` directory, updates the GPS camera date overlay, and saves the processed images to the `./output` directory using the specified font and size.

## 📖 Description

The script performs the following steps:

1. Parses command-line arguments.
2. Processes each image in the input directory:
   - Finds the GPS camera date overlay in the image.
   - Parses and adjusts the date.
   - Samples the background color around the text area.
   - Updates the image overlay with the new date.
3. Saves the processed images to the output directory.

## 📷 Example Images

*Before and After*

![Before](./examples/before.jpg) ![After](./examples/after.jpg)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [Pillow](https://python-pillow.org/)
- [pytesseract](https://github.com/madmaze/pytesseract)
- [NumPy](https://numpy.org/)

