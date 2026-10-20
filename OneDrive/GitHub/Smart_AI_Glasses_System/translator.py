try:
    from deep_translator import GoogleTranslator
except Exception as e:
    GoogleTranslator = None
    DEEP_TRANSLATOR_ERROR = e


class TranslatorSystem:
    def __init__(self):
        self.languages = {
            "1": {"name": "English", "code": "en"},
            "2": {"name": "French", "code": "fr"},
            "3": {"name": "Arabic", "code": "ar"},
            "4": {"name": "Spanish", "code": "es"},
            "5": {"name": "German", "code": "de"},
            "6": {"name": "Swahili", "code": "sw"},
            "7": {"name": "Kinyarwanda / Rwanda Local", "code": "rw"},
        }

    def choose_language(self):
        print("\nChoose target language:")
        for key, value in self.languages.items():
            print(f"{key}. {value['name']}")

        choice = input("Choose language number: ").strip()

        if choice not in self.languages:
            print("Invalid language number.")
            return None

        return self.languages[choice]

    def translate_value(self, text, target_code):
        if GoogleTranslator is None:
            return (
                "deep-translator not installed.\n"
                "Run: python -m pip install deep-translator\n"
                f"Real error: {DEEP_TRANSLATOR_ERROR}"
            )

        try:
            return GoogleTranslator(source="auto", target=target_code).translate(text)
        except Exception as e:
            return f"Translation error: {e}"

    def translate_menu(self):
        print("\n Text Translator ")

        text = input("Enter text to translate: ").strip()

        if not text:
            print("Text is required.")
            return

        language = self.choose_language()

        if language is None:
            return

        print("\nTranslating...")
        print(f"Original text: {text}")
        print(f"Target language: {language['name']}")

        translated = self.translate_value(text, language["code"])

        print("\nTranslated text:")
        print(translated)

        return translated

    def translate_text(self):
        return self.translate_menu()

    def translator_menu(self):
        return self.translate_menu()

    def start_translation(self):
        return self.translate_menu()

    def run(self):
        return self.translate_menu()

    def __getattr__(self, name):
        if "translate" in name or "translator" in name:
            return self.translate_menu

        raise AttributeError(name)


def translate_text_menu():
    system = TranslatorSystem()
    return system.translate_menu()


def translate_text():
    return translate_text_menu()


def translator_menu():
    return translate_text_menu()


def start_translation():
    return translate_text_menu()


if __name__ == "__main__":
    translate_text_menu()