import argparse
import os
import sys
from watermark import embed_message, extract_message

def print_timing_info(timing):
    """
    Print timing information in the same format as the CUDA version.
    """
    print("Timing Information:")
    print(f"  Process execution time: {timing.process_time:.2f} ms")
    print(f"  Total execution time:   {timing.total_time:.2f} ms")

def main():
    """
    Main function to handle the command-line interface.
    """
    parser = argparse.ArgumentParser(description='Border-Hash Based Text Watermarking')
    parser.add_argument('--mode', required=True, choices=['embed', 'extract'], 
                        help='Operation mode: embed or extract')
    parser.add_argument('--input', required=True, help='Path to the input image')
    parser.add_argument('--output', help='Path to save the output image (required for embed mode)')
    parser.add_argument('--message', help='Text message to embed (required for embed mode)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.mode == 'embed':
        if not args.output:
            parser.error("--output is required for embed mode")
        if not args.message:
            parser.error("--message is required for embed mode")
    
    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist")
        sys.exit(1)
    
    try:
        if args.mode == 'embed':
            timing, bits_embedded = embed_message(args.input, args.output, args.message)
            print(f"Success: Message embedded into '{args.output}'")
            print(f"Message length: {len(args.message)} characters ({bits_embedded} bits)")
            print_timing_info(timing)
            
        elif args.mode == 'extract':
            message, timing = extract_message(args.input)
            print(f"Extracted message: {message}")
            print_timing_info(timing)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
