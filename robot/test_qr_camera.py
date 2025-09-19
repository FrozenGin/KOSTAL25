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
    print("=" * 50)
    
    try:
        # Method 1: Let QRCamera create its own PiCar instance
        print("Method 1: QRCamera creates its own PiCar instance")
        print("-" * 50)
        with QRCamera() as qr_scanner:
            result = qr_scanner.start_scan()
            print(f"Scan result: {result}")
        
        print("\n" + "=" * 50)
        
        # Method 2: Pass existing PiCar instance
        print("Method 2: Using shared PiCar instance")
        print("-" * 50)
        from picar import Picar
        
        picar = Picar()
        try:
            with QRCamera(picar_instance=picar) as qr_scanner:
                result = qr_scanner.start_scan()
                print(f"Scan result: {result}")
        finally:
            picar.exit()  # Clean up the picar instance manually
        
        print("\nTest completed successfully!")
        print("=" * 50)
        print("Usage examples:")
        print("1. Auto-managed PiCar:")
        print("   with QRCamera() as scanner:")
        print("       result = scanner.start_scan()")
        print()
        print("2. Shared PiCar instance:")
        print("   picar = Picar()")
        print("   with QRCamera(picar_instance=picar) as scanner:")
        print("       result = scanner.start_scan()")
        print("   picar.exit()")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        logging.error(f"Test failed: {e}")

if __name__ == "__main__":
    main()