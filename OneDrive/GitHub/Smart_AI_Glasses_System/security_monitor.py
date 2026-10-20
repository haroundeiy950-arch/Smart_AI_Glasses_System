import cv2
import csv
import time
from pathlib import Path
from datetime import datetime

from person_recognition import CameraPersonRecognition, UNKNOWN_THRESHOLD

try:
    from ai_assistant import AITextAssistant
except Exception:
    AITextAssistant = None


BASE_DIR = Path(__file__).resolve().parent
SECURITY_DIR = BASE_DIR / "security_logs"
UNKNOWN_DIR = SECURITY_DIR / "unknown_persons"
KNOWN_DIR = SECURITY_DIR / "known_persons"
IN_DIR = SECURITY_DIR / "entry_logs"
OUT_DIR = SECURITY_DIR / "exit_logs"
EVENTS_FILE = SECURITY_DIR / "security_events.csv"


def ensure_security_dirs():
    SECURITY_DIR.mkdir(parents=True, exist_ok=True)
    UNKNOWN_DIR.mkdir(parents=True, exist_ok=True)
    KNOWN_DIR.mkdir(parents=True, exist_ok=True)
    IN_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not EVENTS_FILE.exists():
        with open(EVENTS_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "time",
                "mode",
                "status",
                "person_name",
                "confidence",
                "image_path",
                "ai_note"
            ])


class SecurityCameraMonitor:
    def __init__(self):
        ensure_security_dirs()

        self.face_system = CameraPersonRecognition()
        self.last_event_times = {}
        self.event_delay_seconds = 8

        self.ai = None
        if AITextAssistant is not None:
            try:
                self.ai = AITextAssistant()
            except Exception:
                self.ai = None

    def make_ai_note(self, mode, status, name, confidence):
        if status == "KNOWN":
            return f"Known person detected. Name: {name}. Mode: {mode}. Access logged."

        if status == "UNKNOWN":
            return (
                "Security alert: unknown person detected. "
                "Real image saved for review."
            )

        return "Event logged."

    def should_log_event(self, key):
        now = time.time()
        last_time = self.last_event_times.get(key, 0)

        if now - last_time >= self.event_delay_seconds:
            self.last_event_times[key] = now
            return True

        return False

    def save_face_image(self, frame, x, y, w, h, status, name, mode):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = name.replace(" ", "_").replace("/", "_").replace("\\", "_")

        if status == "UNKNOWN":
            folder = UNKNOWN_DIR
        elif mode == "IN":
            folder = IN_DIR
        elif mode == "OUT":
            folder = OUT_DIR
        else:
            folder = KNOWN_DIR

        image_name = f"{timestamp}_{mode}_{status}_{safe_name}.jpg"
        image_path = folder / image_name

        face_crop = frame[y:y + h, x:x + w]

        if face_crop is None or face_crop.size == 0:
            cv2.imwrite(str(image_path), frame)
        else:
            cv2.imwrite(str(image_path), face_crop)

        return str(image_path)

    def write_event(self, mode, status, name, confidence, image_path, ai_note):
        with open(EVENTS_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                mode,
                status,
                name,
                round(float(confidence), 2),
                image_path,
                ai_note
            ])

    def run_camera_monitor(self, mode="MONITOR"):
        if not self.face_system.train_faces():
            return

        cap = self.face_system.open_camera()

        if cap is None:
            print("Camera not found.")
            print("Try CAMERA_INDEX = 1")
            return

        print("\nSecurity camera monitor started.")
        print(f"Mode: {mode}")
        print("Press Q to close camera.\n")

        while True:
            ret, frame = cap.read()

            if not ret:
                print("Could not read from camera.")
                break

            gray, faces = self.face_system.detect_faces(frame)

            if len(faces) == 0:
                cv2.putText(
                    frame,
                    "No person detected",
                    (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            for (x, y, w, h) in faces:
                face_roi_gray = gray[y:y + h, x:x + w]
                face_roi_gray = cv2.resize(face_roi_gray, (200, 200))

                label, confidence = self.face_system.recognizer.predict(face_roi_gray)

                face_color = frame[y:y + h, x:x + w]

                if confidence < UNKNOWN_THRESHOLD:
                    name = self.face_system.label_to_name.get(label, "Unknown")
                    status = "KNOWN"
                    color = (0, 255, 0)

                    if mode == "OUT":
                        text = f"Exit: {name}"
                        voice = f"Exit logged. {name}"
                    elif mode == "IN":
                        text = f"Entry: {name}"
                        voice = f"Entry logged. {name}"
                    else:
                        text = f"Known person: {name}"
                        voice = f"Known person. {name}"

                else:
                    name = "Unknown"
                    status = "UNKNOWN"
                    color = (0, 0, 255)
                    text = "Unknown person"
                    voice = "Warning. Unknown person detected."

                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

                cv2.putText(
                    frame,
                    text,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

                cv2.putText(
                    frame,
                    f"Score: {round(confidence, 2)}",
                    (x, y + h + 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2
                )

                event_key = f"{mode}_{status}_{name}"

                if self.should_log_event(event_key):
                    image_path = self.save_face_image(
                        frame, x, y, w, h, status, name, mode
                    )

                    ai_note = self.make_ai_note(mode, status, name, confidence)

                    self.write_event(
                        mode=mode,
                        status=status,
                        name=name,
                        confidence=confidence,
                        image_path=image_path,
                        ai_note=ai_note
                    )

                    print("\n  Security Event ")
                    print(f"Status: {status}")
                    print(f"Name: {name}")
                    print(f"Image saved: {image_path}")
                    print(f"AI Note: {ai_note}")
                    print("\n")

                    self.face_system.speak(voice)

                    if face_color is not None and face_color.size > 0:
                        show_face = cv2.resize(face_color, (250, 250))

                        if status == "KNOWN":
                            window_title = f"KNOWN PERSON - {name}"
                        else:
                            window_title = "UNKNOWN PERSON - REAL IMAGE"

                        cv2.imshow(window_title, show_face)

            cv2.imshow("Security Camera Monitor", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == ord("Q"):
                break

        cap.release()
        cv2.destroyAllWindows()

    def review_last_events_with_ai(self):
        if not EVENTS_FILE.exists():
            print("No security events found.")
            return

        with open(EVENTS_FILE, "r", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))

        if not rows:
            print("No security events found.")
            return

        last_events = rows[-20:]

        text = "Review these security camera events and give a short summary:\n\n"

        for event in last_events:
            text += (
                f"Time: {event['time']}, "
                f"Mode: {event['mode']}, "
                f"Status: {event['status']}, "
                f"Name: {event['person_name']}, "
                f"Confidence: {event['confidence']}, "
                f"Image: {event['image_path']}\n"
            )

        if self.ai is None:
            print("AI Assistant not available.")
            print(text)
            return

        print("\nAI Security Review:")
        print(self.ai.ask_ai(text))


def security_monitor_menu():
    monitor = SecurityCameraMonitor()

    while True:
        print("\n===== Security Camera Monitor =====")
        print("1. Start meeting security monitor")
        print("2. Start entry mode")
        print("3. Start exit mode")
        print("4. AI review last security events")
        print("5. Back")

        choice = input("Choose option: ").strip()

        if choice == "1":
            monitor.run_camera_monitor(mode="MONITOR")

        elif choice == "2":
            monitor.run_camera_monitor(mode="IN")

        elif choice == "3":
            monitor.run_camera_monitor(mode="OUT")

        elif choice == "4":
            monitor.review_last_events_with_ai()

        elif choice == "5":
            break

        else:
            print("Invalid option.")


def start_security_monitor():
    return security_monitor_menu()


if __name__ == "__main__":
    security_monitor_menu()