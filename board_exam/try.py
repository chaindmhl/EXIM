from PIL import Image
import io

image_path = '/home/icebox/Electronic_exam/media/question_images/circle.png'

# Open the file as binary and read its content
with open(image_path, 'rb') as f:
    image_data = f.read()

# Create a binary stream from the image data
image_stream = io.BytesIO(image_data)

# Attempt to open the image using PIL/Pillow
try:
    # Pass the binary stream directly to Image.open()
    image = Image.open(image_stream)
    # Image can be opened successfully
    print("Image opened successfully!")
except Exception as e:
    # Failed to open the image
    print("Error:", e)
