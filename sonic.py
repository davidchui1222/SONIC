from gpiozero import MotionSensor
import numpy as np
import os
import cv2
import time
import threading
import subprocess
import threading

# OpenCV settings
camera_width = 640
camera_height = 480
camera_fps = 30

# Stream settings
online = False
stream_start = False
ffmpeg_process = None
rtmp_server = 'rtmp://35.197.194.26:1935/live/playlist'
ffmpeg_command = [
    'ffmpeg',
    '-re',
    '-f', 'rawvideo',
    '-pix_fmt', 'bgr24',
    '-s', f'{camera_width}x{camera_height}',
    '-r', str(camera_fps),
    '-i', '-',
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-preset', 'ultrafast',
    '-tune', 'zerolatency',
    '-g', '30',
    '-f', 'flv',
    rtmp_server
]

last_ssh_time = 0
ssh_interval = 60

# Function for streaming
def stream():
	global ffmpeg_process
	ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)

pir = MotionSensor(17)

# Function to generate timestamp in the format "YYYY-MM-DD_HH-MM-SS"
def get_timestamp():
    return time.strftime("%Y-%m-%d_%H-%M-%S")

# Set video source (0 for default camera, V4L2 for Linux backend framework)
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)  
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height) 

# Settings for image capture
image_output_directory = "/home/pi/Pictures/images"
last_image_time = 0
image_interval = 5  # 5 seconds interval

# Settings for video record
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
vid_output_directory = "/home/pi/Videos/videos"
video_filename = f"un_{get_timestamp()}.mp4" #Initialise first video file name
video_path = os.path.join(vid_output_directory, video_filename)
video = cv2.VideoWriter(video_path, fourcc, 15.0, (camera_width, camera_height))

# Function to be called when pir goes from INACTIVE to ACTIVE
def to_active():
    global video_filename
    global video_path
    global video
    global video_counter
    global vid_output_directory
    
    # Initiate video recording file
    video_filename = f"un_{get_timestamp()}.mp4"
    video_path = os.path.join(vid_output_directory, video_filename)
    video = cv2.VideoWriter(video_path, fourcc, 15.0, (camera_width, camera_height))

    print(f"New Video recording in progress... ({video_filename})")
pir.when_motion = to_active

# Function to be called when pir goes from ACTIVE to INACTIVE
def to_inactive():
    global video_counter
    global video_filename
    
    # Save video recording file
    print(f"Video Saved: {video_filename}")    
    
pir.when_no_motion = to_inactive

# Function for image capture
def img(frame):
    global image_filename
    global image_path
    global last_image_time

    # Check if the time interval has passed
    current_time = time.time()
    if current_time - last_image_time >= image_interval:
        # Take picture
        image_filename = f"{get_timestamp()}.jpg"
        image_path = os.path.join(image_output_directory, image_filename)
        cv2.imwrite(image_path, frame)
        print(f"Image Captured: {image_filename}")
        last_image_time = current_time

# Function for online status check (Pi -> Server)
def online_status():
	global online
	try:
		# Run the ping command with a timeout of 5 seconds and capture the output
		subprocess.check_output(['ping', '-c', '4', '-W', '5', '35.246.23.111'], stderr=subprocess.STDOUT, universal_newlines=True)
		print("Server is reacheable.")
		online = True
		
	except subprocess.CalledProcessError as e:
		# If the ping command returns a non-zero exit code, consider the internet as unreachable
		print("Server is not reachable. Error:", e.output)
		online = False

# Start the thread for checking online status
ping_thread = threading.Thread(target=online_status, daemon=True)
ping_thread.start()

# Function for checking active connections
clients = 0

def active_connections():
    global last_ssh_time
    global clients
    global online

    current_time = time.time()
    if current_time - last_ssh_time >= ssh_interval and online:
        try:
            ssh_command = ['ssh', 'pi@35.197.194.26', 'netstat -nt | grep :443 | wc -l | xargs']
            result = subprocess.run(ssh_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            last_ssh_time = current_time
            clients = int(result.stdout.strip())
            print(clients)
        except subprocess.CalledProcessError as e:
            print(f"SSH command failed with error: {e}")
            clients = 0
            # Handle the error (e.g., log it, set clients to a default value, etc.)

# Main loop for recording video frames
while True:
	if cap.isOpened():
		active_connections()
		ret, frame = cap.read()
		frame = cv2.rotate(frame, cv2.ROTATE_180)
		if ret:

			# Send frame to FFmpeg process
			if online and clients > 0:
				if not stream_start:
					stream()
					stream_start = True
				else:
					ffmpeg_process.stdin.write(frame.tobytes())
			
			if not online and stream_start:
				ffmpeg_process.terminate()
				stream_start = False
			
	if pir.motion_detected:
		# Record video while motion
		video.write(frame)

		# Capture images while motion with a 5-second delay
		img(frame)

# Release resources
cap.release()
