from database import DatabaseManager
from emotion import EmotionAnalyzer
from translator import TranslatorSystem
from speech_system import SpeechSystem
from meeting_assistant import MeetingAssistant
from ai_assistant import ai_text_assistant_menu
from security_monitor import security_monitor_menu
from control_manager import control_manager_menu, auto_backup_on_start

from person_recognition import (
    register_person,
    list_persons,
    train_model,
    recognize_live,
    delete_person_menu
)

from settings import APP_NAME, create_project_folders, print_project_info


class SmartGlassesUI:
    def __init__(self):
        create_project_folders()

        # يعمل نسخة احتياطية تلقائيًا عند تشغيل المشروع
        try:
            auto_backup_on_start()
        except Exception as e:
            print(f"Auto backup warning: {e}")

        self.db = DatabaseManager()
        self.translator = TranslatorSystem()
        self.speech = SpeechSystem()
        self.emotion = EmotionAnalyzer()
        self.meeting = MeetingAssistant()

    def show_menu(self) -> None:
        print("\n" + "=" * 45)
        print(APP_NAME)
        print("=" * 45)
        print("1. Register new person")
        print("2. Show registered persons")
        print("3. Train face model")
        print("4. Start live face recognition")
        print("5. Delete person")
        print("6. Translate text")
        print("7. Text to speech")
        print("8. Emotion analysis")
        print("9. Create meeting notes")
        print("10. Show meetings")
        print("11. Project information")
        print("12. AI Text Assistant")
        print("13. Security Camera Monitor")
        print("14. Project Control / Backup")
        print("15. Exit")
        print("=" * 45)

    def run(self) -> None:
        while True:
            self.show_menu()
            choice = input("Choose option: ").strip()

            if choice == "1":
                register_person()

            elif choice == "2":
                list_persons()

            elif choice == "3":
                train_model()

            elif choice == "4":
                recognize_live()

            elif choice == "5":
                delete_person_menu()

            elif choice == "6":
                self.translator.translate_menu()

            elif choice == "7":
                self.speech.text_to_speech_menu()

            elif choice == "8":
                self.emotion.emotion_menu()

            elif choice == "9":
                self.meeting.create_meeting_menu()

            elif choice == "10":
                self.meeting.list_meetings_menu()

            elif choice == "11":
                print_project_info()

            elif choice == "12":
                ai_text_assistant_menu()

            elif choice == "13":
                security_monitor_menu()

            elif choice == "14":
                control_manager_menu()

            elif choice == "15":
                print("Goodbye.")
                break

            elif choice == "0":
                print("Goodbye.")
                break

            else:
                print("Invalid option. Try again.")