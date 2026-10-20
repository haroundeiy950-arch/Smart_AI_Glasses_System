
import time
from pathlib import Path

import cv2

try:
    from deepface import DeepFace
    DEEPFACE_IMPORT_ERROR = None
except Exception as error:
    DeepFace = None
    DEEPFACE_IMPORT_ERROR = error

try:
    import pyttsx3
except Exception:
    pyttsx3 = None


# =====================================
# Settings
# =====================================
BASE_DIR = Path(__file__).resolve().parent
KNOWN_FACES_DIR = BASE_DIR / "known_faces"

CAMERA_INDEX = 0
ANALYZE_EVERY_FRAMES = 15


# =====================================
# DeepFace check
# =====================================
def check_deepface_ready():
    if DeepFace is None:
        print("\nميزة تحليل الوجه غير جاهزة الآن.")
        print("شغّل المشروع باستخدام Python الموجود داخل venv311.")
        print("Installation commands:")
        print("python -m pip install deepface tf-keras")
        print(f"Real error: {DEEPFACE_IMPORT_ERROR}")
        return False

    return True


# =====================================
# Image path resolver
# =====================================
def resolve_face_image(value):
    """
    يقبل:
    - مسار صورة كامل.
    - مسار داخل المشروع.
    - اسم شخص مسجل مثل haroun.
    """

    value = value.strip().strip('"').strip("'")

    if not value:
        return None

    # المسار كما كتبه المستخدم
    direct_path = Path(value)

    if direct_path.is_file():
        return direct_path.resolve()

    # المسار بالنسبة إلى مجلد المشروع
    project_path = BASE_DIR / value

    if project_path.is_file():
        return project_path.resolve()

    if not KNOWN_FACES_DIR.exists():
        return None

    # البحث باسم المجلد بالضبط
    exact_person_dir = KNOWN_FACES_DIR / value

    if exact_person_dir.is_dir():
        image = get_first_image(exact_person_dir)

        if image is not None:
            return image.resolve()

    # البحث بدون حساسية للحروف
    for person_dir in KNOWN_FACES_DIR.iterdir():
        if not person_dir.is_dir():
            continue

        folder_name = person_dir.name.lower()
        requested_name = value.lower()

        # يدعم أسماء مثل:
        # haroun
        # 26c03c3f_haroun
        if (
            folder_name == requested_name
            or folder_name.endswith("_" + requested_name)
        ):
            image = get_first_image(person_dir)

            if image is not None:
                return image.resolve()

    return None


def get_first_image(folder):
    images = []

    for pattern in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
        images.extend(folder.glob(pattern))

    images = sorted(images)

    if not images:
        return None

    return images[0]


# =====================================
# Text emotion analysis
# =====================================
def analyze_text_emotion(text):
    text = text.strip().lower()

    if not text:
        print("Text is required.")
        return "unknown"

    emotion_words = {
        "happy": [
            "happy", "good", "great", "excellent", "love", "glad",
            "سعيد", "فرحان", "ممتاز", "رائع", "جميل", "احب", "أحب"
        ],
        "sad": [
            "sad", "unhappy", "cry", "bad", "hurt",
            "حزين", "زعلان", "بكاء", "سيء", "متألم"
        ],
        "angry": [
            "angry", "mad", "hate", "annoyed",
            "غاضب", "زعلان", "اكره", "أكره", "منزعج"
        ],
        "fear": [
            "fear", "afraid", "scared", "danger",
            "خائف", "خوف", "مرعوب", "خطر"
        ],
        "surprise": [
            "surprised", "wow", "unexpected",
            "مندهش", "مفاجأة", "واو"
        ]
    }

    scores = {
        emotion: 0
        for emotion in emotion_words
    }

    for emotion, words in emotion_words.items():
        for word in words:
            if word in text:
                scores[emotion] += 1

    dominant = max(scores, key=scores.get)

    if scores[dominant] == 0:
        dominant = "neutral"

    print("\n===== Text Emotion Result =====")
    print(f"Text: {text}")
    print(f"Detected emotion: {dominant}")
    print("===============================")

    return dominant


# =====================================
# Image emotion analysis
# =====================================
def analyze_image_emotion(image_value):
    if not check_deepface_ready():
        return None

    image_path = resolve_face_image(image_value)

    if image_path is None:
        print(f"\nImage or registered person not found: {image_value}")
        print("Use one of these examples:")
        print("haroun")
        print("known_faces/haroun/1.jpg")
        return None

    print(f"\nAnalyzing image: {image_path}")
    print("The first analysis may load the emotion model.")

    try:
        results = DeepFace.analyze(
            img_path=str(image_path),
            actions=["emotion"],
            detector_backend="skip",
            enforce_detection=False
        )

        if isinstance(results, list):
            result = results[0]
        else:
            result = results

        dominant_emotion = result.get(
            "dominant_emotion",
            "unknown"
        )

        emotion_scores = result.get("emotion", {})

        print("\n===== Image Emotion Result =====")
        print(f"Image: {image_path.name}")
        print(f"Dominant emotion: {dominant_emotion}")

        if emotion_scores:
            print("\nEmotion scores:")

            sorted_scores = sorted(
                emotion_scores.items(),
                key=lambda item: item[1],
                reverse=True
            )

            for emotion, score in sorted_scores:
                print(f"- {emotion}: {float(score):.2f}%")

        print("================================")

        return result

    except Exception as error:
        print("\nEmotion analysis failed.")
        print(f"Error: {error}")
        return None



# Compare two faces

def verify_two_faces(first_value, second_value):
    if not check_deepface_ready():
        return None

    first_path = resolve_face_image(first_value)
    second_path = resolve_face_image(second_value)

    if first_path is None:
        print(f"First image or person not found: {first_value}")
        return None

    if second_path is None:
        print(f"Second image or person not found: {second_value}")
        return None

    print(f"\nFirst image: {first_path}")
    print(f"Second image: {second_path}")
    print("Comparing faces...")

    try:
        result = DeepFace.verify(
            img1_path=str(first_path),
            img2_path=str(second_path),
            model_name="SFace",
            detector_backend="skip",
            enforce_detection=False
        )

        verified = bool(result.get("verified", False))
        distance = result.get("distance")
        threshold = result.get("threshold")

        print("\n===== Face Comparison Result =====")

        if verified:
            print("Result: Same person.")
        else:
            print("Result: Different persons.")

        if distance is not None:
            print(f"Distance: {float(distance):.4f}")

        if threshold is not None:
            print(f"Threshold: {float(threshold):.4f}")

        print("==================================")

        return result

    except Exception as error:
        print("\nFace comparison failed.")
        print(f"Error: {error}")
        return None



# Live camera emotion

def start_face_emotion_camera():
    if not check_deepface_ready():
        return

    cap = open_camera()

    if cap is None:
        print("Camera not found.")
        print("Try changing CAMERA_INDEX from 0 to 1.")
        return

    engine = create_speech_engine()

    print("\nLive face emotion camera started.")
    print("Press Q to close the camera.")

    frame_count = 0
    last_emotion = "Analyzing..."

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("Could not read from camera.")
                break

            frame_count += 1

            # لا نحلل كل إطار حتى لا تصبح الكاميرا بطيئة
            if frame_count % ANALYZE_EVERY_FRAMES == 0:
                try:
                    results = DeepFace.analyze(
                        img_path=frame,
                        actions=["emotion"],
                        detector_backend="opencv",
                        enforce_detection=False,
                        silent=True
                    )

                    if isinstance(results, list):
                        result = results[0]
                    else:
                        result = results

                    new_emotion = result.get(
                        "dominant_emotion",
                        "unknown"
                    )

                    if new_emotion != last_emotion:
                        last_emotion = new_emotion
                        print(f"Detected emotion: {last_emotion}")
                        speak_text(engine, f"Emotion {last_emotion}")

                except Exception:
                    last_emotion = "No face detected"

            cv2.putText(
                frame,
                f"Emotion: {last_emotion}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                "Press Q to close",
                (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.imshow("Live Face Emotion", frame)

            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), ord("Q")):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


def open_camera():
    indexes = [CAMERA_INDEX, 0, 1, 2, 3, 4, 5]
    tried = set()

    for index in indexes:
        if index in tried:
            continue

        tried.add(index)

        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

        if cap.isOpened():
            ret, _ = cap.read()

            if ret:
                return cap

        cap.release()

    return None


def create_speech_engine():
    if pyttsx3 is None:
        return None

    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        return engine
    except Exception:
        return None


def speak_text(engine, text):
    if engine is None:
        return

    try:
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass



# Emotion menu class

class EmotionAnalyzer:
    def analyze_menu(self):
        text = input("Enter text to analyze: ").strip()
        return analyze_text_emotion(text)

    def emotion_menu(self):
        while True:
            print("\nEmotion Analysis Menu ")
            print("1. Analyze text emotion")
            print("2. Analyze image face emotion")
            print("3. Compare two faces")
            print("4. Live camera face emotion")
            print("5. Back")

            choice = input("Choose option: ").strip()

            if choice == "1":
                self.analyze_menu()

            elif choice == "2":
                image_value = input(
                    "Enter image path or registered person name: "
                ).strip()

                analyze_image_emotion(image_value)

            elif choice == "3":
                first_value = input(
                    "Enter first image path or person name: "
                ).strip()

                second_value = input(
                    "Enter second image path or person name: "
                ).strip()

                verify_two_faces(
                    first_value,
                    second_value
                )

            elif choice == "4":
                start_face_emotion_camera()

            elif choice == "5":
                break

            else:
                print("Invalid option.")


# =====================================
# Compatibility names
# =====================================
def emotion_menu():
    analyzer = EmotionAnalyzer()
    analyzer.emotion_menu()


def analyze_face_emotion(image_value):
    return analyze_image_emotion(image_value)


def compare_faces(first_value, second_value):
    return verify_two_faces(first_value, second_value)


def live_face_emotion():
    return start_face_emotion_camera()


if __name__ == "__main__":
    emotion_menu()
def start_face_emotion_camera():
    if cv2 is None:
        print("OpenCV not installed.")
        print("Run: python -m pip install opencv-python")
        return

    if not check_deepface_ready():
        return

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Camera not found.")
        return

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    print("\n===== Live Face Emotion Camera =====")
    print("Stand in front of camera.")
    print("Press Q or ESC to exit.")

    last_analysis_time = 0
    current_emotion = "neutral"
    current_confidence = 0

    while True:
        ret, frame = cap.read()

        if not ret or frame is None:
            print("Cannot read camera.")
            break

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(80, 80)
        )

        cv2.putText(
            frame,
            "Live Face Emotion | Press Q to exit",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 0),
            2
        )

        if len(faces) == 0:
            cv2.putText(
                frame,
                "No face detected",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

        for (x, y, w, h) in faces:
            face_img = frame[y:y + h, x:x + w]
            now = time.time()

            if now - last_analysis_time >= 1.5:
                try:
                    result = DeepFace.analyze(
                        img_path=face_img,
                        actions=["emotion"],
                        enforce_detection=False,
                        silent=True
                    )

                    if isinstance(result, list):
                        result = result[0]

                    current_emotion = result.get("dominant_emotion", "neutral")
                    emotion_data = result.get("emotion", {})
                    current_confidence = emotion_data.get(current_emotion, 0)

                    arabic_emotion, message = emotion_details(current_emotion)

                    print("--------------------------")
                    print("Face Emotion:", arabic_emotion)
                    print("Confidence:", round(current_confidence, 2))
                    print("Details:", message)

                except Exception as error:
                    print("Emotion analysis error:", error)

                last_analysis_time = now

            arabic_emotion, message = emotion_details(current_emotion)

            if current_emotion == "neutral":
                color = (0, 255, 0)

            elif current_emotion in ["happy", "surprise"]:
                color = (0, 255, 255)

            elif current_emotion in ["sad", "fear"]:
                color = (255, 0, 0)

            else:
                color = (0, 0, 255)

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                color,
                2
            )

            cv2.putText(
                frame,
                f"Emotion: {current_emotion}",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                color,
                2
            )

            cv2.putText(
                frame,
                f"Confidence: {current_confidence:.1f}%",
                (x, y + h + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2
            )

        cv2.imshow("Smart AI Glasses - Face Emotion", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q") or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()