import cv2
import numpy as np
import hashlib
import random

def compute_border_hash(image):
    """
    Compute SHA-256 hash from the border pixels of the image.
    
    Args:
        image: The input image as a numpy array
        
    Returns:
        The SHA-256 hash of the border pixels
    """
    height, width = image.shape[:2]
    
    # Extract border pixels (top, bottom, left, right)
    top_row = image[0, :, :]
    bottom_row = image[height-1, :, :]
    left_col = image[1:height-1, 0, :]
    right_col = image[1:height-1, width-1, :]
    
    # Concatenate all border pixels
    border_pixels = np.concatenate((top_row.flatten(), bottom_row.flatten(), 
                                    left_col.flatten(), right_col.flatten()))
    
    # Compute SHA-256 hash
    hash_obj = hashlib.sha256(border_pixels.tobytes())
    return hash_obj.hexdigest()

def generate_pseudo_random_positions(hash_value, height, width, num_bits):
    """
    Generate pseudo-random positions for embedding/extracting bits.
    
    Args:
        hash_value: The hash value used as a seed
        height: Image height
        width: Image width
        num_bits: Number of positions needed
        
    Returns:
        List of (y, x) coordinates for embedding/extraction
    """
    # Convert hash to an integer and use as seed
    seed = int(hash_value, 16) % (2**32)
    random.seed(seed)
    
    # Create a list of all interior pixel coordinates
    interior_pixels = [(y, x) for y in range(1, height-1) for x in range(1, width-1)]
    
    # Check if we have enough pixels
    total_interior_pixels = len(interior_pixels)
    if total_interior_pixels < num_bits:
        raise ValueError(f"Image is too small for the message. Need at least {num_bits} interior pixels.")
    
    # Shuffle and return needed number of positions
    random.shuffle(interior_pixels)
    return interior_pixels[:num_bits]

def text_to_bits(text):
    """
    Convert text to a bit string using UTF-8 encoding.
    
    Args:
        text: The input text message
        
    Returns:
        A list of bits (0s and 1s)
    """
    # Convert text to bytes using UTF-8
    byte_array = text.encode('utf-8')
    
    # Convert each byte to bits
    bit_array = []
    for byte in byte_array:
        for i in range(8):
            bit_array.append((byte >> i) & 1)
    
    return bit_array

def bits_to_text(bits):
    """
    Convert a bit array back to text using UTF-8 decoding.
    
    Args:
        bits: List of bits (0s and 1s)
        
    Returns:
        The decoded text message
    """
    # Ensure the length is a multiple of 8
    if len(bits) % 8 != 0:
        bits = bits + [0] * (8 - (len(bits) % 8))
    
    # Convert bits to bytes
    byte_array = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte |= bits[i+j] << j
        byte_array.append(byte)
    
    # Decode bytes to text
    return byte_array.decode('utf-8', errors='replace')

def embed_message(input_path, output_path, message):
    """
    Embed a text message into an image using the border-hash method.
    
    Args:
        input_path: Path to the input image
        output_path: Path to save the watermarked image
        message: The text message to embed
    """
    # Load the image
    image = cv2.imread(input_path)
    if image is None:
        raise ValueError(f"Could not open image at {input_path}")
    
    height, width = image.shape[:2]
    
    # Compute hash from border pixels
    border_hash = compute_border_hash(image)
    
    # Convert message to bits
    message_bits = text_to_bits(message)
    message_length = len(message_bits)
    
    # Create 16-bit header for message length
    header_bits = []
    for i in range(16):
        header_bits.append((message_length >> i) & 1)
    
    # Combine header and message
    all_bits = header_bits + message_bits
    total_bits = len(all_bits)
    
    # Generate embedding positions
    positions = generate_pseudo_random_positions(border_hash, height, width, total_bits)
    
    # Embed bits into LSB of blue channel
    for i, (y, x) in enumerate(positions):
        if i < total_bits:
            # Clear the LSB of the blue channel
            image[y, x, 0] = image[y, x, 0] & 0xFE
            # Set the LSB according to the bit
            image[y, x, 0] = image[y, x, 0] | all_bits[i]
    
    # Save the watermarked image
    cv2.imwrite(output_path, image)
    return len(message_bits)

def extract_message(input_path):
    """
    Extract a hidden message from a watermarked image.
    
    Args:
        input_path: Path to the watermarked image
        
    Returns:
        The extracted text message
    """
    # Load the watermarked image
    image = cv2.imread(input_path)
    if image is None:
        raise ValueError(f"Could not open image at {input_path}")
    
    height, width = image.shape[:2]
    
    # Compute hash from border pixels
    border_hash = compute_border_hash(image)
    
    # Initially, we need at least 16 positions for the header
    positions = generate_pseudo_random_positions(border_hash, height, width, 16)
    
    # Extract header bits
    header_bits = []
    for y, x in positions[:16]:
        # Get LSB of blue channel
        bit = image[y, x, 0] & 1
        header_bits.append(bit)
    
    # Calculate message length from header
    message_length = 0
    for i, bit in enumerate(header_bits):
        message_length |= bit << i
    
    # Generate more positions if needed for the full message
    if len(positions) < 16 + message_length:
        positions = generate_pseudo_random_positions(border_hash, height, width, 16 + message_length)
    
    # Extract message bits
    message_bits = []
    for y, x in positions[16:16+message_length]:
        # Get LSB of blue channel
        bit = image[y, x, 0] & 1
        message_bits.append(bit)
    
    # Convert bits back to text
    extracted_message = bits_to_text(message_bits)
    
    return extracted_message
