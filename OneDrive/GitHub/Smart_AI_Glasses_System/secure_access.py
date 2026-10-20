import csv
import time
from datetime import datetime
from pathlib import Path

import cv2

from person_recognition import (
    CameraPersonRecognition,
    UNKNOWN_THRESHOLD,
)


BASE_DIR = Path(__file__).resolve().parent
ACCESS_DIR = BASE_DIR / "access_security"
DENIED_DIR = ACCESS_DIR / "denied_images"
SUCCESS_DIR = ACCESS_DIR / "successful_images"
ACCESS_LOG_FILE = ACCESS_DIR / "access_attempts.csv"


def ensure_access_dirs():
    ACCESS_DIR.mkdir(parents=True, exist_ok=True)
    DENIED_DIR.mkdir(parents=True, exist_ok=True)
    SUCCESS_DIR.mkdir(parents=True, exist_ok=True)

    if not ACCESS_LOG_FILE.exists():
        with open(
            ACCESS_LOG_FILE,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "date_time",
                    "result",
                    "person",
                    "reason",
                    "image_path",
                ]
            )


def safe_person_name(name: str) -> str:
    value = str(name or "Unknown").strip().replace(" ", "_")

    for character in '<>:"/\\|?*':
        value = value.replace(character, "")

    return value or "Unknown"


def save_access_image(
    frame,
    result: str,
    person: str = "Unknown",
) -> str:
    ensure_access_dirs()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_name = safe_person_name(person)

    if result.upper() == "ALLOWED":
        folder = SUCCESS_DIR
    else:
        folder = DENIED_DIR

    image_path = folder / (
        f"{timestamp}_{result.upper()}_{safe_name}.jpg"
    )

    saved = cv2.imwrite(str(image_path), frame)

    if not saved:
        return ""

    return str(image_path)


def log_access_attempt(
    result: str,
    person: str,
    reason: str,
    image_path: str = "",
) -> None:
    ensure_access_dirs()

    with open(
        ACCESS_LOG_FILE,
        "a",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                result,
                person,
                reason,
                image_path,
            ]
        )


def capture_denied_image(
    reason: str = "Access denied",
    timeout_seconds: int = 8,
) -> str:
    ensure_access_dirs()

    face_system = CameraPersonRecognition()
    cap = face_system.open_camera()

    if cap is None:
        print("Camera not found. Denied image was not captured.")
        return ""

    print("\nCamera opened to record the denied attempt.")
    print("Please look at the camera.")

    start_time = time.time()
    last_frame = None
    saved_path = ""

    try:
        while time.time() - start_time < timeout_seconds:
            ret, frame = cap.read()

            if not ret:
                continue

            last_frame = frame.copy()
            gray, faces = face_system.detect_faces(frame)

            cv2.putText(
                frame,
                "ACCESS DENIED",
                (25, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3,
            )

            if len(faces) > 0:
                biggest_face = face_system.get_biggest_face(faces)

                if biggest_face is not None:
                    x, y, w, h = biggest_face

                    cv2.rectangle(
                        frame,
                        (x, y),
                        (x + w, y + h),
                        (0, 0, 255),
                        3,
                    )

                    saved_path = save_access_image(
                        last_frame,
                        result="DENIED",
                        person="Unknown",
                    )
                    break

            cv2.imshow("Denied Access Camera", frame)

            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), ord("Q")):
                break

        if not saved_path and last_frame is not None:
            saved_path = save_access_image(
                last_frame,
                result="DENIED",
                person="Unknown",
            )

    finally:
        cap.release()
        cv2.destroyAllWindows()

    return saved_path


def verify_owner_face(
    required_name: str,
    timeout_seconds: int = 20,
    required_matches: int = 5,
):
    ensure_access_dirs()

    face_system = CameraPersonRecognition()

    if not face_system.train_faces():
        return False, "Unknown", ""

    cap = face_system.open_camera()

    if cap is None:
        print("Camera not found.")
        return False, "Unknown", ""

    required_clean = safe_person_name(required_name).lower()

    start_time = time.time()
    consecutive_matches = 0
    detected_name = "Unknown"
    last_original_frame = None

    print("\nFace verification camera opened.")
    print(f"Required owner: {required_name}")
    print("Look directly at the camera.")
    print("Press Q to cancel.")

    try:
        while time.time() - start_time < timeout_seconds:
            ret, frame = cap.read()

            if not ret:
                continue

            original_frame = frame.copy()
            last_original_frame = original_frame

            gray, faces = face_system.detect_faces(frame)

            screen_text = "No face detected"
            color = (0, 0, 255)

            if len(faces) > 0:
                biggest_face = face_system.get_biggest_face(faces)

                if biggest_face is not None:
                    x, y, w, h = biggest_face

                    face_roi = gray[y:y + h, x:x + w]
                    face_roi = cv2.resize(face_roi, (200, 200))

                    label, confidence = (
                        face_system.recognizer.predict(face_roi)
                    )

                    if confidence < UNKNOWN_THRESHOLD:
                        detected_name = face_system.label_to_name.get(
                            label,
                            "Unknown",
                        )

                        detected_clean = safe_person_name(
                            detected_name
                        ).lower()

                        if detected_clean == required_clean:
                            consecutive_matches += 1
                            screen_text = (
                                f"Owner verified: {detected_name} "
                                f"{consecutive_matches}/{required_matches}"
                            )
                            color = (0, 255, 0)

                        else:
                            consecutive_matches = 0
                            screen_text = (
                                f"Access denied: {detected_name}"
                            )
                            color = (0, 0, 255)

                    else:
                        detected_name = "Unknown"
                        consecutive_matches = 0
                        screen_text = "Unknown person"
                        color = (0, 0, 255)

                    cv2.rectangle(
                        frame,
                        (x, y),
                        (x + w, y + h),
                        color,
                        3,
                    )

                    cv2.putText(
                        frame,
                        f"Score: {confidence:.2f}",
                        (x, y + h + 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        color,
                        2,
                    )

            cv2.putText(
                frame,
                screen_text,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2,
            )

            cv2.imshow("Owner Face Verification", frame)

            if consecutive_matches >= required_matches:
                image_path = save_access_image(
                    original_frame,
                    result="ALLOWED",
                    person=detected_name,
                )

                return True, detected_name, image_path

            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), ord("Q")):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    image_path = ""

    if last_original_frame is not None:
        image_path = save_access_image(
            last_original_frame,
            result="DENIED",
            person=detected_name,
        )

    return False, detected_name, image_path


if __name__ == "__main__":
    result = verify_owner_face("haroun")
    print(result)