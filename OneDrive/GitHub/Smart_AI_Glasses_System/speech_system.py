from pathlib import Path
import tempfile
import time
import os
import asyncio

try:
    import pyttsx3
except Exception as e:
    pyttsx3 = None
    PYTTSX3_ERROR = e

try:
    from gtts import gTTS
except Exception as e:
    gTTS = None
    GTTS_ERROR = e

try:
    import edge_tts
except Exception as e:
    edge_tts = None
    EDGE_TTS_ERROR = e

try:
    from playsound import playsound
except Exception:
    playsound = None


class SpeechSystem:
    def __init__(self):
        self.languages = {
            "1": {"name": "English", "code": "en", "edge_locale": "en-US"},
            "2": {"name": "French", "code": "fr", "edge_locale": "fr-FR"},
            "3": {"name": "Arabic", "code": "ar", "edge_locale": "ar-SA"},
            "4": {"name": "Spanish", "code": "es", "edge_locale": "es-ES"},
            "5": {"name": "German", "code": "de", "edge_locale": "de-DE"},
            "6": {"name": "Swahili", "code": "sw", "edge_locale": "sw-KE"},
            "7": {"name": "Kinyarwanda / Rwanda Local", "code": "rw", "edge_locale": "rw-RW"},
        }

        self.engine = None

        if pyttsx3 is not None:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", 150)
            except Exception:
                self.engine = None

    def choose_language(self):
        print("\nChoose voice language:")
        for key, value in self.languages.items():
            print(f"{key}. {value['name']}")

        choice = input("Choose language number: ").strip()

        if choice not in self.languages:
            print("Invalid language number.")
            return None

        return self.languages[choice]

    def play_audio(self, audio_file):
        if playsound is not None:
            playsound(str(audio_file))
        else:
            os.startfile(str(audio_file))

    def speak_offline(self, text):
        if self.engine is None:
            print("Offline text to speech not available.")
            if pyttsx3 is None:
                print(f"pyttsx3 error: {PYTTSX3_ERROR}")
            return

        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Offline speech error: {e}")

    async def speak_edge_async(self, text, edge_locale):
        if edge_tts is None:
            print("edge-tts not installed.")
            print("Run: python -m pip install edge-tts")
            return False

        try:
            voices = await edge_tts.list_voices()

            selected_voice = None

            # نبحث عن صوت بنفس اللغة
            for voice in voices:
                locale = voice.get("Locale", "")
                short_name = voice.get("ShortName", "")
                friendly_name = voice.get("FriendlyName", "")

                if locale.lower() == edge_locale.lower():
                    selected_voice = short_name
                    break

                if edge_locale.lower().startswith("rw") and (
                    "kinyarwanda" in friendly_name.lower()
                    or "rwanda" in friendly_name.lower()
                    or locale.lower().startswith("rw")
                ):
                    selected_voice = short_name
                    break

            if selected_voice is None:
                print(f"No Edge voice found for locale: {edge_locale}")
                return False

            temp_dir = Path(tempfile.gettempdir())
            audio_file = temp_dir / f"smart_glasses_edge_voice_{int(time.time())}.mp3"

            communicate = edge_tts.Communicate(text, selected_voice)
            await communicate.save(str(audio_file))

            self.play_audio(audio_file)
            return True

        except Exception as e:
            print(f"Edge TTS error: {e}")
            return False

    def speak_edge(self, text, edge_locale):
        return asyncio.run(self.speak_edge_async(text, edge_locale))

    def speak_gtts(self, text, lang_code):
        if gTTS is None:
            print("gTTS not installed.")
            print("Run: python -m pip install gTTS")
            return False

        try:
            temp_dir = Path(tempfile.gettempdir())
            audio_file = temp_dir / f"smart_glasses_gtts_voice_{int(time.time())}.mp3"

            tts = gTTS(text=text, lang=lang_code, slow=False)
            tts.save(str(audio_file))

            self.play_audio(audio_file)
            return True

        except Exception as e:
            print(f"gTTS error: {e}")
            return False

    def speak(self, text, lang_code="en", edge_locale="en-US"):
        if not text:
            print("Text is required.")
            return

        # أولًا نجرب Edge TTS لأنه يدعم أصوات أكثر
        ok = self.speak_edge(text, edge_locale)

        if ok:
            return

        # لو اللغة Kinyarwanda وما لقينا صوت، ما نقرأ إنجليزي
        if lang_code == "rw":
            print("لم أجد صوت Kinyarwanda في Edge TTS.")
            print("ما حأقرأ بالإنجليزي بدلها.")
            print("الحل: نحتاج خدمة TTS تدعم Kinyarwanda أو Voice model خاص.")
            return

        # باقي اللغات نجرب gTTS
        ok = self.speak_gtts(text, lang_code)

        if ok:
            return

        # آخر حل offline
        self.speak_offline(text)

    def text_to_speech_menu(self):
        print("\n===== Text To Speech =====")

        text = input("Enter text to read: ").strip()

        if not text:
            print("Text is required.")
            return

        language = self.choose_language()

        if language is None:
            return

        print(f"Reading using: {language['name']}")
        self.speak(text, language["code"], language["edge_locale"])

    def text_to_speech(self):
        return self.text_to_speech_menu()

    def speak_menu(self):
        return self.text_to_speech_menu()

    def start_text_to_speech(self):
        return self.text_to_speech_menu()

    def run(self):
        return self.text_to_speech_menu()

    def __getattr__(self, name):
        if "speech" in name or "speak" in name or "voice" in name or "tts" in name:
            return self.text_to_speech_menu

        raise AttributeError(name)


def text_to_speech_menu():
    system = SpeechSystem()
    return system.text_to_speech_menu()


def text_to_speech():
    return text_to_speech_menu()


def speak_menu():
    return text_to_speech_menu()


def start_text_to_speech():
    return text_to_speech_menu()


def speak_text(text, lang_code="en"):
    system = SpeechSystem()

    locale_map = {
        "en": "en-US",
        "fr": "fr-FR",
        "ar": "ar-SA",
        "es": "es-ES",
        "de": "de-DE",
        "sw": "sw-KE",
        "rw": "rw-RW",
    }

    edge_locale = locale_map.get(lang_code, "en-US")
    return system.speak(text, lang_code, edge_locale)


if __name__ == "__main__":
    text_to_speech_menu()