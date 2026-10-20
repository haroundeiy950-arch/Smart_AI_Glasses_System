import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "project_backups"

# ملفات ومجلدات لا نريد نسخها لأنها كبيرة أو غير مهمة
SKIP_NAMES = {
    "venv",
    "venv311",
    "__pycache__",
    ".git",
    ".idea",
    ".vscode",
    "project_backups",
}

SKIP_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".log",
    ".tmp",
}


def should_skip(path: Path) -> bool:
    for part in path.parts:
        if part in SKIP_NAMES:
            return True

    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True

    return False


def create_project_backup(reason="manual"):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}_{reason}.zip"
    backup_path = BACKUP_DIR / backup_name

    files_count = 0

    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in BASE_DIR.rglob("*"):
            if file_path.is_file() and not should_skip(file_path):
                relative_path = file_path.relative_to(BASE_DIR)
                zipf.write(file_path, relative_path)
                files_count += 1

    print("\nBackup created successfully.")
    print(f"Backup file: {backup_path}")
    print(f"Files saved: {files_count}")

    return backup_path


def list_backups():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    backups = sorted(BACKUP_DIR.glob("*.zip"), reverse=True)

    if not backups:
        print("No backups found.")
        return []

    print("\nAvailable backups:")
    for i, backup in enumerate(backups, start=1):
        size_mb = backup.stat().st_size / (1024 * 1024)
        print(f"{i}. {backup.name} - {size_mb:.2f} MB")

    return backups


def restore_backup():
    backups = list_backups()

    if not backups:
        return

    value = input("\nEnter backup number to restore: ").strip()

    if not value.isdigit():
        print("Invalid number.")
        return

    index = int(value)

    if index < 1 or index > len(backups):
        print("Backup not found.")
        return

    selected_backup = backups[index - 1]

    print("\nWARNING:")
    print("This will restore files from the backup.")
    print("Current files with the same names may be replaced.")

    confirm = input("Type YES to continue: ").strip()

    if confirm != "YES":
        print("Restore cancelled.")
        return

    # نحفظ نسخة من الوضع الحالي قبل الاسترجاع
    create_project_backup(reason="before_restore")

    with zipfile.ZipFile(selected_backup, "r") as zipf:
        zipf.extractall(BASE_DIR)

    print("\nRestore completed successfully.")
    print(f"Restored from: {selected_backup.name}")


def show_project_files():
    print("\nProject Python files:")

    files = sorted(BASE_DIR.glob("*.py"))

    if not files:
        print("No Python files found.")
        return

    for i, file in enumerate(files, start=1):
        print(f"{i}. {file.name}")


def delete_old_backups(keep_last=30):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    backups = sorted(BACKUP_DIR.glob("*.zip"), reverse=True)

    old_backups = backups[keep_last:]

    for backup in old_backups:
        try:
            backup.unlink()
        except Exception:
            pass


def auto_backup_on_start():
    """
    تعمل نسخة تلقائية عند تشغيل المشروع.
    تحفظ آخر 30 نسخة فقط حتى لا يمتلئ القرص.
    """
    backup_path = create_project_backup(reason="auto_start")
    delete_old_backups(keep_last=30)
    return backup_path


def control_manager_menu():
    while True:
        print("\n Project Control / Backup ")
        print("1. Create backup now")
        print("2. Show backups")
        print("3. Restore backup")
        print("4. Show project files")
        print("5. Back")

        choice = input("Choose option: ").strip()

        if choice == "1":
            create_project_backup(reason="manual")

        elif choice == "2":
            list_backups()

        elif choice == "3":
            restore_backup()

        elif choice == "4":
            show_project_files()

        elif choice == "5":
            break

        else:
            print("Invalid option.")


if __name__ == "__main__":
    control_manager_menu()