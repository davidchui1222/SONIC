import cv2
import os
import sys
sys.path.append('/home/davidchui1222/.local/lib/python3.11/site-packages')
import shutil
import numpy as np
from tensorflow.keras.applications.inception_v3 import InceptionV3, preprocess_input, decode_predictions

# Load the InceptionV3 model pre-trained on ImageNet data
model = InceptionV3(weights='imagenet')

# Path to the folder containing videos
videos_folder = '/home/davidchui1222/scripts/fixed_videos'
output_folder = '/var/www/html/squirrel-vid'
output_folder2 = '/var/www/html/vid'

# Iterate over each file in the folder
for filename in os.listdir(videos_folder):
    if filename.endswith(".mp4"):
        # Load the video file
        video_path = os.path.join(videos_folder, filename)
        cap = cv2.VideoCapture(video_path)

        # Check if the video opened successfully
        if not cap.isOpened():
            print(f"Error opening video file: {filename}")
            os.remove(video_path)
            print(f"Corrupted '{filename}' has been removed")
            continue

        fox_squirrel_detected = False
        while True:
            # Read the frame
            ret, frame = cap.read()

            # Break the loop if we have reached the end of the video
            if not ret:
                break

            # Convert the frame to RGB format
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Resize the frame to the input size expected by the model
            img_array = cv2.resize(rgb_frame, (299, 299))
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)

            # Predict the class of the frame
            predictions = model.predict(img_array)

            # Decode and print the top-3 predicted classes
            decoded_predictions = decode_predictions(predictions, top=5)[0]
            print("\nPredictions for frame in {}: ".format(filename))

            for i, (imagenet_id, label, score) in enumerate(decoded_predictions):
                if label == 'fox_squirrel':
                    print("{}. {}: {:.2f}%".format(i + 1, label, score * 100))

                    # Move the video to the output folder
                    new_video_path = os.path.join(output_folder, filename)
                    shutil.move(video_path, new_video_path)

                    # Set the flag to indicate detection
                    fox_squirrel_detected = True

                    # Break out of the loop to process the next video
                    break

        # Release the video capture object
        cap.release()

        # If 'fox_squirrel' is detected, move to the next video
        if fox_squirrel_detected:
            continue

        # If 'fox_squirrel' is not detected, move to the second output folder
        new_video_path = os.path.join(output_folder2, filename)
        shutil.move(video_path, new_video_path)

# Destroy all OpenCV windows
cv2.destroyAllWindows()