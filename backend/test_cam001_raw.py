import cv2
import sys

def test_cam001():
    print("Testing CAM001 RAW...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if hasattr(cv2, 'CAP_DSHOW') else cv2.VideoCapture(0)
    print("CAM001 opened:", cap.isOpened())

    if not cap.isOpened():
        print("Failed to open CAM001 (Device 0)")
        return

    frames_read = 0
    for _ in range(30):
        ret, frame = cap.read()
        if ret and frame is not None:
            frames_read += 1
            h, w = frame.shape[:2]
            if frames_read == 1:
                print(f"CAM001 RAW first frame received! Shape: {w}x{h}")
                cv2.imwrite("backend/debug_frames/test_cam001_raw.jpg", frame)
    
    print(f"CAM001 RAW completed: {frames_read}/30 frames successfully read.")
    cap.release()

if __name__ == "__main__":
    test_cam001()
