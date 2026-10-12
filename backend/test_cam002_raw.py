import cv2
import sys

def test_cam002():
    print("Testing CAM002 RAW...")
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW) if hasattr(cv2, 'CAP_DSHOW') else cv2.VideoCapture(1)
    print("CAM002 opened:", cap.isOpened())

    if not cap.isOpened():
        print("Failed to open CAM002 (Device 1)")
        return

    frames_read = 0
    for _ in range(30):
        ret, frame = cap.read()
        if ret and frame is not None:
            frames_read += 1
            h, w = frame.shape[:2]
            if frames_read == 1:
                print(f"CAM002 RAW first frame received! Shape: {w}x{h}")
                cv2.imwrite("backend/debug_frames/test_cam002_raw.jpg", frame)
    
    print(f"CAM002 RAW completed: {frames_read}/30 frames successfully read.")
    cap.release()

if __name__ == "__main__":
    test_cam002()
