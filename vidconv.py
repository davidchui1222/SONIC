import os

# Specify the full path to ffmpeg
ffmpeg_path = '/usr/bin/ffmpeg'

# Specify the input and output folders
input_folder = '/home/davidchui1222/scripts/videos'
output_folder = '/home/davidchui1222/scripts/fixed_videos'

# Iterate over files in the input folder
for filename in os.listdir(input_folder):
    if filename.startswith('un') and filename.endswith('.mp4'):
        input_file = os.path.join(input_folder, filename)
        output_file = os.path.join(output_folder, filename[3:])  # Remove the 'un_' prefix

        # Run ffmpeg command
        command = f'sudo {ffmpeg_path} -i {input_file} -vcodec libx264 -f mp4 {output_file}'
        
        # Print debug information
        print(f'Running command: {command}')

        # Uncomment the line below to execute the ffmpeg command
        os.system(command)

        os.remove(input_file)
        print(f'Deleted original file: {input_file}')