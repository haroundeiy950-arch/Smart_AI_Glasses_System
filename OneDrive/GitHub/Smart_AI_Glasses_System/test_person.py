from person_recognition import register_person_camera, start_live_person_recognition

while True:
    print("\n Person Recognition Menu ")
    print("1. Register new person by camera")
    print("2. Live camera recognition")
    print("3. Exit")

    choice = input("Choose option: ").strip()

    if choice == "1":
        register_person_camera()

    elif choice == "2":
        start_live_person_recognition()

    elif choice == "3":
        break

    else:
        print("Invalid option.")