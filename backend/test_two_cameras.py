import cv2
import sys
import time

def test_two_cameras():
    print("Testing BOTH CAMERAS (CAM001 and CAM002) simultaneously...")
    
    cap1 = cv2.VideoCapture(0, cv2.CAP_DSHOW) if hasattr(cv2, 'CAP_DSHOW') else cv2.VideoCapture(0)
    cap2 = cv2.VideoCapture(1, cv2.CAP_DSHOW) if hasattr(cv2, 'CAP_DSHOW') else cv2.VideoCapture(1)

    print("CAM001 (Device 0) opened:", cap1.isOpened())
    print("CAM002 (Device 1) opened:", cap2.isOpened())

    c1_count = 0
    c2_count = 0

    for i in range(30):
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()

        if ret1 and frame1 is not None:
            c1_count += 1
            if c1_count == 1:
                cv2.imwrite("backend/debug_frames/test_two_cam001.jpg", frame1)
        
        if ret2 and frame2 is not None:
            c2_count += 1
            if c2_count == 1:
                cv2.imwrite("backend/debug_frames/test_two_cam002.jpg", frame2)
        
        time.sleep(0.03)

    print(f"CAM001 raw frames read: {c1_count}/30")
    print(f"CAM002 raw frames read: {c2_count}/30")

    cap1.release()
    cap2.release()

if __name__ == "__main__":
    test_two_cameras()
