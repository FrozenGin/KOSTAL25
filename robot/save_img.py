# from picamera2 import Picamera2
# Example: Save an image from the camera
from picamera2 import Picamera2
import os

RESOLUTION = (640, 480)  # 4:3 resolution (max 2592x1944)
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": RESOLUTION}))
picam2.start()

def save_image(filename: str = "image.jpg") -> None:
	"""Capture a frame and save it as an image file."""
	frame = picam2.capture_array()
	if frame is None:
		print("Failed to capture image from camera.")
		return
	try:
		import cv2
	except ImportError:
		raise ImportError("OpenCV (cv2) is required to save images. Install with 'pip install opencv-python'.")
	success = cv2.imwrite(filename, frame)
	if success:
		print(f"Image saved as {filename}")
	else:
		print("Failed to save image.")

def main():
	print("Press Enter to capture and save an image...")
	while True:
		input()  # Wait for button press (Enter key)
		filename = input("Enter filename (default: image.jpg): ").strip() or "image.jpg"
		save_image(filename)

if __name__ == "__main__":
	main()
