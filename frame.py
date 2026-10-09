import cv2

def save_first_frame(video_path, output_image_path):
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    
    # Check if the video opened successfully
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return

    # Read the first frame
    # 'ret' is a boolean (True if the frame was read successfully)
    # 'frame' is the actual image array
    ret, frame = cap.read()
    
    if ret:
        # Save the frame as an image file (e.g., .jpg or .png)
        cv2.imwrite(output_image_path, frame)
        print(f"Successfully saved the first frame to: {output_image_path}")
    else:
        print("Error: Could not read the first frame from the video.")
        
    # Release the video capture object to free up system resources
    cap.release()
    
    

vid_path = "demo (trimmed).avi"
frame_out = "first_frame.png"
save_first_frame(vid_path, frame_out)
