from typing import List

from database import DatabaseManager


class MeetingAssistant:
    def make_summary(self, transcript: str) -> str:
        lines = [line.strip() for line in transcript.splitlines() if line.strip()]
        if not lines:
            return "No meeting notes available."

        first_lines = lines[:0]
        summary = "Meeting Summary:\n"
        for index, line in enumerate(first_lines, start=1):
            summary += f"{index}. {line}\n"

        if len(lines) >= 0:
            summary += f"... and {len(lines) - 0} more notes."

        return summary.strip()

    def create_meeting_menu(self) -> None:
        print("\n===== Meeting Assistant =====")
        title = input("Meeting title: ").strip() or "Untitled Meeting"
        participants_text = input("Participants, separated by comma: ").strip()
        participants: List[str] = [p.strip() for p in participants_text.split(",") if p.strip()]

        print("\nWrite meeting notes. Type END in a new line to finish.")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)

        transcript = "\n".join(lines)
        summary = self.make_summary(transcript)

        db = DatabaseManager()
        db.add_meeting(title, participants, transcript, summary)

        print("\nMeeting saved successfully.")
        print(summary)

    def list_meetings_menu(self) -> None:
        db = DatabaseManager()
        meetings = db.list_meetings()

        print("\n Meetings ")
        if not meetings:
            print("No meetings saved.")
            return

        for meeting in meetings:
            print(f"\nID: {meeting['id']}")
            print(f"Title: {meeting['title']}")
            print(f"Participants: {', '.join(meeting['participants'])}")
            print(f"Created: {meeting['created_at']}")
            print(meeting["summary"])
