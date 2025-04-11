# watermark.py - Updated with benchmarking
import cv2
import numpy as np
import hashlib
import random
import time

class TimingInfo:
    """
    Class to hold timing information for benchmarking.
    Mirrors the TimingInfo struct in the CUDA version.
    """
    def __init__(self):
        self.process_time = 0.0  # Time for the core processing (equivalent to gpuTime)
        self.total_time = 0.0    # Total execution time

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

def embed_message(input_path, output_path, message):
    """
    Embed a text message into an image using the border-hash method.
    
    Args:
        input_path: Path to the input image
        output_path: Path to save the watermarked image
        message: The text message to embed
        
    Returns:
        TimingInfo object containing process and total execution times
    """
    # Create TimingInfo object
    timing = TimingInfo()
    
    # Start measuring total time
    total_start = time.time()
    
    # Load the image
    image = cv2.imread(input_path)
    if image is None:
        raise ValueError(f"Could not open image at {input_path}")
    
    height, width = image.shape[:2]
    
    # Compute hash from border pixels
    border_hash = compute_border_hash(image)
    
    # Convert message to bytes
    message_bytes = message.encode('utf-8')
    message_length = len(message_bytes)
    
    # Ensure message length isn't too large for 16-bit encoding
    if message_length > 65535:
        raise ValueError("Message too large - maximum size is 65535 bytes")
    
    # We'll encode the length as a fixed 2-byte (16-bit) unsigned integer
    length_bytes = message_length.to_bytes(2, byteorder='big')
    
    # Combine header and message
    data_to_hide = length_bytes + message_bytes
    total_bits = len(data_to_hide) * 8
    
    # Start measuring process time (equivalent to GPU time in CUDA version)
    process_start = time.time()
    
    # Generate embedding positions
    positions = generate_pseudo_random_positions(border_hash, height, width, total_bits)
    
    # Embed bits into LSB of blue channel
    bit_index = 0
    for byte in data_to_hide:
        for bit_pos in range(8):  # Process each bit in the byte
            y, x = positions[bit_index]
            # Clear the LSB of the blue channel
            image[y, x, 0] = image[y, x, 0] & 0xFE
            # Set the LSB according to the current bit (MSB first)
            bit = (byte >> (7 - bit_pos)) & 1
            image[y, x, 0] = image[y, x, 0] | bit
            bit_index += 1
    
    # End process time measurement
    process_end = time.time()
    timing.process_time = (process_end - process_start) * 1000  # Convert to milliseconds
    
    # Save the watermarked image using PNG format to avoid compression artifacts
    # Make sure the filename ends with .png regardless of input
    if not output_path.lower().endswith('.png'):
        output_path = output_path.rsplit('.', 1)[0] + '.png'
    cv2.imwrite(output_path, image, [cv2.IMWRITE_PNG_COMPRESSION, 0])
    
    # End total time measurement
    total_end = time.time()
    timing.total_time = (total_end - total_start) * 1000  # Convert to milliseconds
    
    print(f"DEBUG: Embedded message length: {message_length} bytes")
    
    # Return the timing information and the number of bits embedded
    return timing, total_bits

def extract_message(input_path):
    """
    Extract a hidden message from a watermarked image.
    
    Args:
        input_path: Path to the watermarked image
        
    Returns:
        A tuple containing (extracted_message, TimingInfo)
    """
    # Create TimingInfo object
    timing = TimingInfo()
    
    # Start measuring total time
    total_start = time.time()
    
    # Load the watermarked image
    image = cv2.imread(input_path)
    if image is None:
        raise ValueError(f"Could not open image at {input_path}")
    
    height, width = image.shape[:2]
    
    # Compute hash from border pixels
    border_hash = compute_border_hash(image)
    
    # Start measuring process time
    process_start = time.time()
    
    # First, extract just the 2-byte length header
    header_bits = 16  # 2 bytes = 16 bits
    positions = generate_pseudo_random_positions(border_hash, height, width, header_bits)
    
    # Read the 16 bits for the length
    length_bits = []
    for i in range(16):
        y, x = positions[i]
        bit = image[y, x, 0] & 1  # Get LSB
        length_bits.append(bit)

    # Convert bits to bytes (2 bytes)
    length_bytes = bytearray(2)
    for i in range(2):
        for j in range(8):
            # MSB first
            length_bytes[i] = (length_bytes[i] << 1) | length_bits[i*8 + j]
    
    # Extract the message length from the header bytes
    message_length = int.from_bytes(length_bytes, byteorder='big')
    
    print(f"DEBUG: Detected message length: {message_length} bytes")
    
    # Safety check to prevent excessive memory usage
    if message_length > 65535 or message_length <= 0:
        process_end = time.time()
        timing.process_time = (process_end - process_start) * 1000
        total_end = time.time()
        timing.total_time = (total_end - total_start) * 1000
        return f"Error: Invalid message length detected: {message_length}", timing
    
    # Generate positions for the full message (header + message)
    total_bits = 16 + (message_length * 8)
    positions = generate_pseudo_random_positions(border_hash, height, width, total_bits)
    
    # Extract message bits
    message_bits = []
    for i in range(16, total_bits):
        y, x = positions[i]
        bit = image[y, x, 0] & 1
        message_bits.append(bit)
    
    # Convert bits to bytes
    message_bytes = bytearray(message_length)
    for i in range(message_length):
        byte = 0
        for j in range(8):
            # Process 8 bits at a time, MSB first
            if i*8 + j < len(message_bits):
                byte = (byte << 1) | message_bits[i*8 + j]
        message_bytes[i] = byte
    
    # End process time measurement
    process_end = time.time()
    timing.process_time = (process_end - process_start) * 1000  # Convert to milliseconds
    
    # Convert bytes to string
    try:
        message = message_bytes.decode('utf-8')
        result = message
    except UnicodeDecodeError:
        # If decoding fails, return a hex representation of the bytes for debugging
        hex_data = ''.join(f'{b:02x}' for b in message_bytes)
        result = f"Error: Could not decode message as UTF-8. First 32 bytes in hex: {hex_data[:64]}..."
    
    # End total time measurement
    total_end = time.time()
    timing.total_time = (total_end - total_start) * 1000  # Convert to milliseconds
    
    return result, timing