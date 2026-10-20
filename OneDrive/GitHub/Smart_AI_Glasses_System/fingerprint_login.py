import asyncio
import os

try:
    from winrt.windows.security.credentials.ui import (
        UserConsentVerifier,
        UserConsentVerifierAvailability,
        UserConsentVerificationResult,
    )

    WINRT_IMPORT_ERROR = None

except Exception as error:
    UserConsentVerifier = None
    UserConsentVerifierAvailability = None
    UserConsentVerificationResult = None
    WINRT_IMPORT_ERROR = error


async def _verify_windows_hello_async() -> bool:
    """
    التحقق من توفر Windows Hello ثم طلب المصادقة.
    """

    availability = await UserConsentVerifier.check_availability_async()

    if availability != UserConsentVerifierAvailability.AVAILABLE:
        print("\nWindows Hello is not available.")

        if availability == UserConsentVerifierAvailability.DEVICE_NOT_PRESENT:
            print("Fingerprint reader or Windows Hello device not found.")

        elif (
            availability
            == UserConsentVerifierAvailability.NOT_CONFIGURED_FOR_USER
        ):
            print("Windows Hello is not configured for this Windows account.")
            print(
                "Open Settings > Accounts > Sign-in options "
                "> Fingerprint recognition."
            )

        elif (
            availability
            == UserConsentVerifierAvailability.DISABLED_BY_POLICY
        ):
            print("Windows Hello is disabled by Windows policy.")

        elif availability == UserConsentVerifierAvailability.DEVICE_BUSY:
            print("Fingerprint reader is currently busy.")

        else:
            print(f"Availability result: {availability}")

        return False

    print("\nPlace your finger on the fingerprint reader.")

    result = await UserConsentVerifier.request_verification_async(
        "Verify your identity to open Smart AI Glasses System"
    )

    if result == UserConsentVerificationResult.VERIFIED:
        print("\nWindows Hello verification successful.")
        return True

    if result == UserConsentVerificationResult.CANCELED:
        print("\nWindows Hello verification was cancelled.")

    elif result == UserConsentVerificationResult.RETRIES_EXHAUSTED:
        print("\nToo many failed verification attempts.")

    elif result == UserConsentVerificationResult.DEVICE_BUSY:
        print("\nFingerprint reader is busy.")

    elif result == UserConsentVerificationResult.DEVICE_NOT_PRESENT:
        print("\nAuthentication device not found.")

    elif result == UserConsentVerificationResult.NOT_CONFIGURED_FOR_USER:
        print("\nWindows Hello is not configured.")

    elif result == UserConsentVerificationResult.DISABLED_BY_POLICY:
        print("\nWindows Hello is disabled by policy.")

    else:
        print(f"\nWindows Hello verification failed: {result}")

    return False


async def _verify_with_timeout(timeout_seconds: int) -> bool:
    """
    يمنع Windows Hello من تعليق البرنامج إلى الأبد.
    """

    try:
        return await asyncio.wait_for(
            _verify_windows_hello_async(),
            timeout=timeout_seconds,
        )

    except asyncio.TimeoutError:
        print()
        print(
            f"Windows Hello verification timed out after "
            f"{timeout_seconds} seconds."
        )
        return False


def verify_windows_hello(timeout_seconds: int = 30) -> bool:
    """
    الدالة الرئيسية التي يستدعيها main.py.
    """

    if os.name != "nt":
        print("Windows Hello only works on Windows.")
        return False

    if UserConsentVerifier is None:
        print("\nWindows Hello Python library is not installed.")
        print(
            "Run: python -m pip install "
            "winrt-runtime "
            "winrt-Windows.Foundation "
            "winrt-Windows.Security.Credentials.UI"
        )
        print(f"Real error: {WINRT_IMPORT_ERROR}")
        return False

    try:
        return asyncio.run(
            _verify_with_timeout(timeout_seconds)
        )

    except KeyboardInterrupt:
        print()
        print("Windows Hello verification was cancelled by the user.")
        return False

    except RuntimeError as error:
        print()
        print("Windows Hello event-loop error:")
        print(error)
        return False

    except Exception as error:
        print()
        print("Windows Hello error:")
        print(error)
        print(
            "This desktop application may require "
            "Windows Hello desktop interop."
        )
        return False


if __name__ == "__main__":
    success = verify_windows_hello(timeout_seconds=30)
    print(f"\nVerification result: {success}")