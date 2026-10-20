import cv2
import numpy as np
from pathlib import Path
import time
import shutil
import tempfile
import os

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    from gtts import gTTS
except Exception:
    gTTS = None

try:
    from playsound import playsound
except Exception:
    playsound = None


BASE_DIR = Path(__file__).resolve().parent
KNOWN_FACES_DIR = BASE_DIR / "known_faces"
MODELS_DIR = BASE_DIR / "models"

CAMERA_INDEX = 0
SAMPLES_PER_PERSON = 30
UNKNOWN_THRESHOLD = 75

CASCADE_NAME = "haarcascade_frontalface_default.xml"


def clean_person_name(name):
    name = name.strip().replace(" ", "_")

    bad_chars = '<>:"/\\|?*'
    for ch in bad_chars:
        name = name.replace(ch, "")

    return name


def ensure_dirs():
    KNOWN_FACES_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)


class CameraPersonRecognition:
    def __init__(self):
        ensure_dirs()

        opencv_cascade = Path(cv2.data.haarcascades) / CASCADE_NAME
        local_cascade = MODELS_DIR / CASCADE_NAME

        if opencv_cascade.exists():
            cascade_path = str(opencv_cascade)
        elif local_cascade.exists():
            cascade_path = str(local_cascade)
        else:
            raise RuntimeError(
                "Face detector file not found.\n"
                "Run this command:\n"
                "curl.exe -L --fail -o models\\haarcascade_frontalface_default.xml "
                "https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades/haarcascade_frontalface_default.xml"
            )

        self.face_detector = cv2.CascadeClassifier(cascade_path)

        if self.face_detector.empty():
            raise RuntimeError(
                "Face detector file is wrong or damaged.\n"
                "Delete models/haarcascade_frontalface_default.xml and download it again."
            )

        if not hasattr(cv2, "face"):
            raise RuntimeError(
                "cv2.face not found.\n"
                "Run:\n"
                "python -m pip uninstall -y opencv-python opencv-contrib-python\n"
                "python -m pip install opencv-contrib-python numpy pyttsx3"
            )

        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.label_to_name = {}

        self.engine = None
        if pyttsx3 is not None:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", 150)
            except Exception:
                self.engine = None

        self.last_spoken = ""
        self.last_spoken_time = 0

    def arabic_name(self, name):
        clean_name = name.replace("_", " ").strip()

        names_map = {
            "haroun": "هارون",
            "haroon": "هارون",
            "harun": "هارون",
        }

        return names_map.get(clean_name.lower(), clean_name)

    def speak(self, text, lang="ar"):
        now = time.time()

        if text == self.last_spoken and now - self.last_spoken_time < 5:
            return

        self.last_spoken = text
        self.last_spoken_time = now

        if gTTS is not None:
            try:
                temp_dir = Path(tempfile.gettempdir())
                audio_file = temp_dir / f"smart_voice_{int(time.time() * 1000)}.mp3"

                tts = gTTS(text=text, lang=lang, slow=False)
                tts.save(str(audio_file))

                if playsound is not None:
                    playsound(str(audio_file))
                else:
                    os.startfile(str(audio_file))

                return

            except Exception as e:
                print(f"\nArabic voice error: {e}")

        if self.engine is not None:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"\npyttsx3 voice error: {e}")
        else:
            print("\nVoice engine not available.")

    def open_camera(self):
        for index in [CAMERA_INDEX, 0, 1, 2, 3, 4, 5]:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    return cap

            cap.release()

        return None

    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = self.face_detector.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(40, 40)
        )

        return gray, faces

    def get_biggest_face(self, faces):
        if len(faces) == 0:
            return None

        return max(faces, key=lambda f: f[2] * f[3])

    def register_person_by_camera(self):
        name = input("Enter person name: ").strip()
        name = clean_person_name(name)

        if not name:
            print("Name is required.")
            return

        person_dir = KNOWN_FACES_DIR / name
        person_dir.mkdir(parents=True, exist_ok=True)

        cap = self.open_camera()

        if cap is None:
            print("Camera not found.")
            print("Try CAMERA_INDEX = 1")
            return

        print("\nCamera opened.")
        print("Saving starts automatically when face is detected.")
        print("Press Q to cancel.\n")

        count = 0
        last_message_time = 0

        while True:
            ret, frame = cap.read()

            if not ret:
                print("Could not read from camera.")
                break

            gray, faces = self.detect_faces(frame)
            biggest_face = self.get_biggest_face(faces)

            if biggest_face is not None:
                x, y, w, h = biggest_face

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                face_roi = gray[y:y + h, x:x + w]
                face_roi = cv2.resize(face_roi, (200, 200))

                image_path = person_dir / f"{count + 1}.jpg"
                cv2.imwrite(str(image_path), face_roi)

                count += 1
                print(f"Saved: {count}/{SAMPLES_PER_PERSON}")

                cv2.putText(
                    frame,
                    f"Saved: {count}/{SAMPLES_PER_PERSON}",
                    (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )

                time.sleep(0.12)

            else:
                now = time.time()
                if now - last_message_time > 2:
                    print("No face detected. Move closer and improve light.")
                    last_message_time = now

                cv2.putText(
                    frame,
                    "No face detected - move closer",
                    (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            if count >= SAMPLES_PER_PERSON:
                print(f"Person registered successfully: {name}")
                self.speak(f"تم تسجيل {self.arabic_name(name)} بنجاح", "ar")
                break

            cv2.imshow("Register Person By Camera", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == ord("Q"):
                print("Registration canceled.")
                break

        cap.release()
        cv2.destroyAllWindows()

    def train_faces(self):
        ensure_dirs()

        faces_data = []
        labels = []
        self.label_to_name = {}

        label_id = 0

        for person_dir in KNOWN_FACES_DIR.iterdir():
            if not person_dir.is_dir():
                continue

            image_files = (
                list(person_dir.glob("*.jpg")) +
                list(person_dir.glob("*.jpeg")) +
                list(person_dir.glob("*.png"))
            )

            valid_count = 0

            for image_path in image_files:
                image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

                if image is None:
                    continue

                image = cv2.resize(image, (200, 200))
                faces_data.append(image)
                labels.append(label_id)
                valid_count += 1

            if valid_count > 0:
                self.label_to_name[label_id] = person_dir.name
                label_id += 1

        if len(faces_data) == 0:
            print("No registered persons found.")
            print("Register a person first.")
            return False

        self.recognizer.train(faces_data, np.array(labels, dtype=np.int32))

        print("\nTraining completed.")
        print("Registered persons:")
        for _, name in self.label_to_name.items():
            print(f"- {name}")

        return True

    def live_recognition_camera(self):
        if not self.train_faces():
            return

        print("\n Recognition Mode ")
        print("1. Monitor mode")
        print("2. Entry mode")
        print("3. Exit mode")

        mode_choice = input("Choose mode: ").strip()

        if mode_choice == "2":
            mode = "IN"
            print("Entry mode selected.")
        elif mode_choice == "3":
            mode = "OUT"
            print("Exit mode selected.")
        else:
            mode = "MONITOR"
            print("Monitor mode selected.")

        cap = self.open_camera()

        if cap is None:
            print("Camera not found.")
            print("Try CAMERA_INDEX = 1")
            return

        print("\nLive recognition started.")
        print("Camera is open now.")
        print("Press Q to close camera.\n")

        last_status_key = ""
        last_print_text = ""

        while True:
            ret, frame = cap.read()

            if not ret:
                print("\nCould not read from camera.")
                break

            gray, faces = self.detect_faces(frame)

            status_key = "NO_PERSON"
            screen_text = "No person in front of camera"
            voice_text = "لا يوجد شخص أمام الكاميرا"
            color = (0, 0, 255)

            if len(faces) == 0:
                cv2.putText(
                    frame,
                    screen_text,
                    (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    color,
                    2
                )

            else:
                biggest_face = self.get_biggest_face(faces)
                x, y, w, h = biggest_face

                face_roi = gray[y:y + h, x:x + w]
                face_roi = cv2.resize(face_roi, (200, 200))

                label, confidence = self.recognizer.predict(face_roi)

                if confidence < UNKNOWN_THRESHOLD:
                    name = self.label_to_name.get(label, "Unknown")
                    name_ar = self.arabic_name(name)

                    if mode == "IN":
                        status_key = f"IN_{name}"
                        screen_text = f"Entry: {name}"
                        voice_text = f"{name_ar} دخل النظام"

                    elif mode == "OUT":
                        status_key = f"OUT_{name}"
                        screen_text = f"Exit: {name}"
                        voice_text = f"{name_ar} خرج من النظام"

                    else:
                        status_key = f"KNOWN_{name}"
                        screen_text = f"Person found: {name}"
                        voice_text = f"{name_ar} موجود في النظام"

                    color = (0, 255, 0)

                else:
                    status_key = "UNKNOWN"
                    screen_text = "Person not found"
                    voice_text = "الشخص غير موجود في النظام"
                    color = (0, 0, 255)

                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

                cv2.putText(
                    frame,
                    screen_text,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
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

            if status_key != last_status_key:
                last_status_key = status_key

                line_text = f"Status: {screen_text}"
                clear_space = " " * max(0, len(last_print_text) - len(line_text))

                print(f"\r{line_text}{clear_space}", end="", flush=True)
                last_print_text = line_text

                self.speak(voice_text, "ar")

            cv2.imshow("Live Person Recognition", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == ord("Q"):
                break

        print()
        cap.release()
        cv2.destroyAllWindows()


def register_person_camera():
    system = CameraPersonRecognition()
    return system.register_person_by_camera()


def start_live_person_recognition():
    system = CameraPersonRecognition()
    return system.live_recognition_camera()


def list_persons():
    ensure_dirs()

    persons = sorted([p.name for p in KNOWN_FACES_DIR.iterdir() if p.is_dir()])

    if not persons:
        print("No registered persons found.")
        return []

    print("\nRegistered persons:")
    for i, person in enumerate(persons, start=1):
        print(f"{i}. {person}")

    return persons


def delete_person():
    persons = list_persons()

    if not persons:
        return

    value = input("Enter person number or exact name to delete: ").strip()

    selected_name = None

    if value.isdigit():
        index = int(value)
        if 1 <= index <= len(persons):
            selected_name = persons[index - 1]
    else:
        for person in persons:
            if person.lower() == value.lower():
                selected_name = person
                break

    if selected_name is None:
        print("Person not found.")
        return

    confirm = input(f"Delete '{selected_name}'? yes/no: ").strip().lower()

    if confirm not in ["yes", "y"]:
        print("Delete cancelled.")
        return

    shutil.rmtree(KNOWN_FACES_DIR / selected_name)
    print(f"Person deleted successfully: {selected_name}")


def train_model():
    system = CameraPersonRecognition()
    return system.train_faces()


def person_recognition_menu():
    while True:
        print("\n Person Recognition Menu ")
        print("1. Register new person by camera")
        print("2. Live camera recognition")
        print("3. List registered persons")
        print("4. Delete person")
        print("5. Train model")
        print("6. Back")

        choice = input("Choose option: ").strip()

        if choice == "1":
            register_person_camera()
        elif choice == "2":
            start_live_person_recognition()
        elif choice == "3":
            list_persons()
        elif choice == "4":
            delete_person()
        elif choice == "5":
            train_model()
        elif choice == "6":
            break
        else:
            print("Invalid option.")


def register_person():
    return register_person_camera()


def recognize_person():
    return start_live_person_recognition()


def recognize_face():
    return start_live_person_recognition()


def recognize_live():
    return start_live_person_recognition()


def start_face_recognition_camera():
    return start_live_person_recognition()


def live_person_recognition():
    return start_live_person_recognition()


def add_person():
    return register_person_camera()


def show_persons():
    return list_persons()


def list_persons_menu():
    return list_persons()


def delete_person_menu():
    return delete_person()


def remove_person():
    return delete_person()


def remove_person_menu():
    return delete_person()


def train_person_model():
    return train_model()


def train_model_menu():
    return train_model()


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)

    if "register" in name or "add" in name:
        return register_person_camera

    if "recognize" in name or "camera" in name or "live" in name:
        return start_live_person_recognition

    if "list" in name or "show" in name:
        return list_persons

    if "delete" in name or "remove" in name:
        return delete_person

    if "train" in name or "model" in name:
        return train_model

    raise AttributeError(name)


if __name__ == "__main__":
    person_recognition_menu()