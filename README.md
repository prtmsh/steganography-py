# Border-Hash Based Text Watermarking

This project implements an invisible text watermarking scheme based on a border-hash method. It allows embedding text messages into images and later extracting them.

## Project Structure

- `src/` - Contains the source code files
- `examples/` - Contains example images for testing

## How It Works

### Embedding Process

1. **Border Extraction & Hashing**: The outermost 1-pixel-wide border of the image is used to compute a SHA-256 hash.
   
2. **Pseudo-Random Pixel Selection**: The hash is used as a seed for a pseudo-random number generator to create a reproducible sequence of interior pixel positions.
   
3. **Message Encoding**: The user's text message is converted to bits using UTF-8 encoding, and a 16-bit header containing the message length is prepended.
   
4. **Watermark Embedding**: The bits are embedded into the least significant bit (LSB) of the blue channel of the selected interior pixels.

### Extraction Process

1. The same border hash is recomputed from the watermarked image.
   
2. The same pseudo-random sequence of pixel positions is generated.
   
3. The first 16 bits are extracted to determine the message length.
   
4. The remaining bits are extracted and converted back to text.

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/prtmsh/steganography-py.git
   cd steganography-py
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Embedding a Message

```
python src/main.py --mode embed --input examples/input.jpg --output examples/watermarked.png --message "Your secret message"
```

**Note**: We strongly recommend using PNG format for the output file to ensure watermark integrity. The program will automatically convert the output to PNG format if another format is specified.

### Extracting a Message

```
python src/main.py --mode extract --input examples/watermarked.png
```

## Requirements

- Python 3
- OpenCV
- NumPy
- Pillow

## Limitations

- The image must be large enough to accommodate the message.
- Maximum message size is 65,535 bytes (approx. 65KB).
- Modifications to the watermarked image (especially to the border) may prevent message recovery.
- The message is encoded in the LSB of the blue channel, which may be vulnerable to certain image manipulations.
- JPEG or other lossy compression formats will corrupt the watermark - always use PNG format.

## Troubleshooting

- If extraction fails, ensure you're using the exact same watermarked image that was generated (no resizing, recompression, etc.)
- The program will display debug information about message lengths during embedding and extraction
- If the extracted text is corrupted, it means the watermark has been damaged, possibly by image compression