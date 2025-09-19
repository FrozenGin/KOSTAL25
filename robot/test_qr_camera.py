#!/usr/bin/env python3
"""
Simple test script for the QRCamera class.
Demonstrates how to use the QR camera scanner.
"""

import logging
import time
from qr_camera import QRCamera

def main():
    # Set up logging to see what's happening
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("Starting QR Camera Test")
    print("=" * 30)
    
    try:
        # Using context manager (recommended - automatic cleanup)
        print("Testing QR Camera with context manager...")
        with QRCamera() as qr_scanner:
            result = qr_scanner.start_scan()
            print(f"Scan result: {result}")
        
        print("\nTest completed successfully!")
        print("=" * 30)
        print("To use in your code:")
        print("from qr_camera import QRCamera")
        print("with QRCamera() as scanner:")
        print("    result = scanner.start_scan()")
        print("    print(result)")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        logging.error(f"Test failed: {e}")

if __name__ == "__main__":
    main()