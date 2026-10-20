import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from openai import OpenAI
except Exception as e:
    OpenAI = None
    OPENAI_IMPORT_ERROR = e


class AITextAssistant:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

        if OpenAI is None:
            self.client = None
            self.error = OPENAI_IMPORT_ERROR

        elif not self.api_key:
            self.client = None
            self.error = "OPENAI_API_KEY not found in .env file"

        else:
            self.client = OpenAI(api_key=self.api_key)
            self.error = None

    def local_answer(self, question):
        q = question.lower()

        if "camera" in q:
            return (
                "To use the camera: choose option 1 to register a new person, "
                "choose option 3 to train the face model, then choose option 4 "
                "to start live face recognition."
            )

        if "translate" in q or "translation" in q:
            return (
                "Translation is available from option 6. "
                "If it does not work, install the library using: "
                "python -m pip install deep-translator"
            )

        if "voice" in q or "speech" in q or "sound" in q or "tts" in q:
            return (
                "Text to speech is available from option 7. "
                "Some languages such as Kinyarwanda may not have a ready voice "
                "in gTTS or Edge TTS."
            )

        if "face" in q or "person" in q or "recognition" in q:
            return (
                "For person recognition: choose option 1 to register the person, "
                "choose option 3 to train the model, then choose option 4 "
                "to open the camera and recognize the person live."
            )

        if "deepface" in q or "emotion" in q:
            return (
                "Emotion analysis is available from option 8. "
                "It requires DeepFace. Install it using: "
                "python -m pip install deepface"
            )

        if "opencv" in q or "cv2" in q:
            return (
                "If you have an OpenCV or cv2.face problem, run: "
                "python -m pip uninstall -y opencv-python opencv-contrib-python "
                "then run: python -m pip install opencv-contrib-python numpy"
            )

        return (
            "I am a local assistant. To use real AI, make sure that "
            "OPENAI_API_KEY exists inside the .env file."
        )

    def ask_ai(self, question):
        if self.client is None:
            return self.local_answer(question)

        try:
            response = self.client.responses.create(
                model="gpt-5-mini",
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are an AI assistant inside a Python project called "
                            "Smart AI Glasses System. Answer in simple English. "
                            "Help with face recognition, camera, translation, speech, "
                            "meeting notes, project features, and Python errors."
                        ),
                    },
                    {
                        "role": "user",
                        "content": question,
                    },
                ],
            )

            return response.output_text

        except Exception as e:
            return (
                f"AI error: {e}\n\n"
                f"Local answer:\n{self.local_answer(question)}"
            )

    def assistant_menu(self):
        print("\n===== AI Text Assistant =====")
        print("Ask any question about the project.")
        print("Type back to return to the main menu.\n")

        while True:
            question = input("Ask AI: ").strip()

            if question.lower() in ["back", "exit", "return", "quit"]:
                break

            if not question:
                print("Please write your question first.")
                continue

            print("\nAI Answer:")
            print(self.ask_ai(question))
            print()


def ai_text_assistant_menu():
    system = AITextAssistant()
    return system.assistant_menu()


def start_ai_assistant():
    return ai_text_assistant_menu()


if __name__ == "__main__":
    ai_text_assistant_menu()