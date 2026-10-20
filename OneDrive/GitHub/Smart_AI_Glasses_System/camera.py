from typing import Optional

try:
    import cv2
except ImportError:
    cv2 = None

from settings import CAMERA_INDEX


class CameraSystem:
    def __init__(self, camera_index: int = CAMERA_INDEX):
        self.camera_index = camera_index
        self.cap = None

    def open_camera(self):
        if cv2 is None:
            print("Error: OpenCV not installed. Run: python -m pip install opencv-contrib-python")
            return None

        possible_indexes = [self.camera_index, 0, 1, 2, 3, 4, 5]
        tried = set()

        for index in possible_indexes:
            if index in tried:
                continue
            tried.add(index)

            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

            if not cap.isOpened():
                cap.release()
                cap = cv2.VideoCapture(index)

            if not cap.isOpened():
                cap.release()
                continue

            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"Camera opened successfully. Index: {index}")
                self.cap = cap
                return cap

            cap.release()

        print("Error: Camera not found.")
        print("Close Camera App / Zoom / Teams and try again.")
        return None

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None


def open_camera(camera_index: int = CAMERA_INDEX):
    return CameraSystem(camera_index).open_camera()
