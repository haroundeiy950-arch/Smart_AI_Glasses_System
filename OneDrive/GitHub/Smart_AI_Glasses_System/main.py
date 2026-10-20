from settings import create_project_folders


# اسم صاحب النظام كما هو مسجل داخل known_faces
OWNER_NAME = "haroun"



# Import Security Modules

try:
    from fingerprint_login import verify_windows_hello

    FINGERPRINT_IMPORT_ERROR = None
except Exception as error:
    verify_windows_hello = None
    FINGERPRINT_IMPORT_ERROR = error


try:
    from secure_access import (
        verify_owner_face,
        capture_denied_image,
        log_access_attempt,
    )

    SECURITY_IMPORT_ERROR = None
except Exception as error:
    verify_owner_face = None
    capture_denied_image = None
    log_access_attempt = None
    SECURITY_IMPORT_ERROR = error



# Denied Access

def deny_access(reason: str, person: str = "Unknown") -> None:
    print("\n🔏🔏🔏🔏🔏🔏🔏")
    print("ACCESS DENIED")
    print(f"Reason: {reason}")
    print("🔏🔏🔏🔏🔏🔏🔏🔏")

    image_path = ""

    # فتح الكاميرا وحفظ صورة الشخص الذي حاول الدخول
    if capture_denied_image is not None:
        try:
            image_path = capture_denied_image(reason=reason)

            if image_path:
                print(f"Denied person image saved: {image_path}")

        except Exception as error:
            print(f"Could not capture denied person image: {error}")

    # تسجيل المحاولة داخل CSV
    if log_access_attempt is not None:
        try:
            log_access_attempt(
                result="DENIED",
                person=person,
                reason=reason,
                image_path=image_path,
            )

        except Exception as error:
            print(f"Could not save access log: {error}")

    print("The system will now close.")



# Owner Face Verification

def verify_face_access() -> bool:
    if verify_owner_face is None:
        print("\nFace security module is not available.")
        print(f"Real error: {SECURITY_IMPORT_ERROR}")
        return False

    print("\nFingerprint verified successfully.")
    print("Please look directly at the camera.")

    try:
        result = verify_owner_face(required_name=OWNER_NAME)

        # verify_owner_face يجب أن ترجع:
        # success, detected_name, image_path
        success, detected_name, image_path = result

    except Exception as error:
        deny_access(
            reason=f"Face verification error: {error}",
            person="Unknown",
        )
        return False

    detected_name = str(detected_name or "Unknown")
    owner_clean = OWNER_NAME.strip().lower()
    detected_clean = detected_name.strip().lower()

    if not success or detected_clean != owner_clean:
        reason = "The detected face is not the system owner."

        if log_access_attempt is not None:
            try:
                log_access_attempt(
                    result="DENIED",
                    person=detected_name,
                    reason=reason,
                    image_path=image_path or "",
                )
            except Exception as error:
                print(f"Could not save access log: {error}")

        print("\n📲📲📲📲📲📲📲📲📲📲📲")
        print("ACCESS DENIED")
        print(f"Detected person: {detected_name}")
        print("Face does not match the system owner.")

        if image_path:
            print(f"Real image saved: {image_path}")

        print("📲📲📲📲📲📲📲📲📲📲📲📲")
        return False

    # تسجيل الدخول الناجح
    if log_access_attempt is not None:
        try:
            log_access_attempt(
                result="ALLOWED",
                person=detected_name,
                reason="Fingerprint and owner face verified.",
                image_path=image_path or "",
            )
        except Exception as error:
            print(f"Could not save successful access log: {error}")

    print("\n🔏🔏🔏🔏🔏🔏🔏🔏🔏🔏🔏")
    print("ACCESS GRANTED")
    print(f"Welcome: {detected_name}")
    print("Fingerprint and face verified successfully.")
    print("🔓🔓🔓🔓🔓🔓🔓🔓🔓🔓🔓🔓")

    return True

# Main Program

def main() -> None:
    create_project_folders()

    # يمنع تشغيل النظام إذا ملف البصمة غير موجود
    if verify_windows_hello is None:
        print("\nSecurity system could not start.")
        print("File required: fingerprint_login.py")
        print(f"Real error: {FINGERPRINT_IMPORT_ERROR}")
        return

    # يمنع تشغيل النظام إذا ملف حماية الكاميرا غير موجود
    if (
        verify_owner_face is None
        or capture_denied_image is None
        or log_access_attempt is None
    ):
        print("\nSecurity system could not start.")
        print("File required: secure_access.py")
        print(f"Real error: {SECURITY_IMPORT_ERROR}")
        return

    print("\n=============================================")
    print("Smart AI Glasses Secure Login")
    print("=============================================")
    print("Windows Hello verification is required.")

    # المرحلة الأولى: Windows Hello / Fingerprint
    try:
        fingerprint_verified = verify_windows_hello()

    except Exception as error:
        deny_access(
            reason=f"Windows Hello verification error: {error}",
            person="Unknown",
        )
        return

    if not fingerprint_verified:
        deny_access(
            reason="Fingerprint or Windows Hello verification failed.",
            person="Unknown",
        )
        return

    # المرحلة الثانية: التحقق من وجه صاحب النظام
    if not verify_face_access():
        return

    # لا يتم استيراد وفتح القائمة إلا بعد نجاح التحقق الكامل
    try:
        from ui import SmartGlassesUI

        app = SmartGlassesUI()
        app.run()

    except Exception as error:
        print("\nThe main system could not start.")
        print(f"Real error: {error}")


if __name__ == "__main__":
    main()