import os
import shutil
import sys
sys.path.append('/home/davidchui1222/.local/lib/python3.11/site-packages')
from datetime import datetime
import numpy as np
from tensorflow.keras.applications.inception_v3 import InceptionV3, preprocess_input, decode_predictions
from PIL import Image

# Load the InceptionV3 model pre-trained on ImageNet data
model = InceptionV3(weights='imagenet')

# Path to the folder containing images
folder_path = '/home/davidchui1222/scripts/images'
output_folder = '/var/www/html/squirrel-img'
output_folder2 = '/var/www/html/img'

# Ensure output directories exist
os.makedirs(output_folder, exist_ok=True)
os.makedirs(output_folder2, exist_ok=True)

# Iterate over each file in the folder
for filename in os.listdir(folder_path):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        try:
            img_path = os.path.join(folder_path, filename)

            # Use PIL to open the image
            with Image.open(img_path) as img:
                img = img.convert("RGB")  # Ensure the image is in RGB mode
                img = img.resize((299, 299))  # Resize the image if needed
                img_array = np.array(img)

            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)

            # Predict the class of the image
            predictions = model.predict(img_array)

            # Decode and print all predicted classes
            decoded_predictions = decode_predictions(predictions, top=10)[0]
            print("\nPredictions for {}: ".format(filename))
            for i, (imagenet_id, label, score) in enumerate(decoded_predictions):
                print("{}. {}: {:.2f}%".format(i + 1, label, score * 100))

            # Move to the appropriate directory based on detection
            fox_squirrel_detected = any(label == 'fox_squirrel' for (_, label, _) in decoded_predictions)
            if fox_squirrel_detected:
                shutil.copy(img_path, os.path.join(output_folder, filename))
            else:
                shutil.copy(img_path, os.path.join(output_folder2, filename))

            # Remove the file after processing
            os.remove(img_path)

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            # Remove the corrupte