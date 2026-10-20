import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from settings import DATABASE_FILE, PEOPLE_JSON, create_project_folders


class DatabaseManager:
    def __init__(self, db_path=DATABASE_FILE):
        create_project_folders()
        self.db_path = str(db_path)
        self.create_tables()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def create_tables(self) -> None:
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS people (
                    person_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    person_type TEXT NOT NULL,
                    job TEXT,
                    basic_info TEXT,
                    last_notes TEXT,
                    face_folder TEXT,
                    created_at TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meetings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    participants TEXT,
                    transcript TEXT,
                    summary TEXT,
                    created_at TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT,
                    message TEXT,
                    created_at TEXT
                )
            """)

            conn.commit()

    def add_person(
        self,
        person_id: str,
        name: str,
        person_type: str = "private",
        job: str = "Not specified",
        basic_info: str = "No information",
        last_notes: str = "No notes",
        face_folder: str = ""
    ) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO people
                (person_id, name, person_type, job, basic_info, last_notes, face_folder, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                person_id,
                name,
                person_type,
                job,
                basic_info,
                last_notes,
                face_folder,
                now
            ))
            conn.commit()

        self.export_people_to_json()

    def get_person(self, person_id: str) -> Dict[str, Any]:
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT person_id, name, person_type, job, basic_info, last_notes, face_folder, created_at
                FROM people
                WHERE person_id = ?
            """, (person_id,))
            row = cursor.fetchone()

        if not row:
            return {
                "person_id": "unknown",
                "name": "Unknown Person",
                "type": "unknown",
                "job": "Unknown",
                "basic_info": "Face not registered",
                "last_notes": "No notes",
                "face_folder": "",
                "created_at": ""
            }

        return {
            "person_id": row[0],
            "name": row[1],
            "type": row[2],
            "job": row[3],
            "basic_info": row[4],
            "last_notes": row[5],
            "face_folder": row[6],
            "created_at": row[7]
        }

    def list_people(self) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT person_id, name, person_type, job, basic_info, last_notes, face_folder, created_at
                FROM people
                ORDER BY name
            """)
            rows = cursor.fetchall()

        people = []
        for row in rows:
            people.append({
                "person_id": row[0],
                "name": row[1],
                "type": row[2],
                "job": row[3],
                "basic_info": row[4],
                "last_notes": row[5],
                "face_folder": row[6],
                "created_at": row[7]
            })
        return people

    def delete_person(self, person_id: str) -> bool:
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM people WHERE person_id = ?", (person_id,))
            deleted = cursor.rowcount > 0
            conn.commit()

        self.export_people_to_json()
        return deleted

    def add_meeting(
        self,
        title: str,
        participants: List[str],
        transcript: str,
        summary: str
    ) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meetings
                (title, participants, transcript, summary, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                title,
                json.dumps(participants, ensure_ascii=False),
                transcript,
                summary,
                now
            ))
            conn.commit()

    def list_meetings(self) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, participants, transcript, summary, created_at
                FROM meetings
                ORDER BY id DESC
            """)
            rows = cursor.fetchall()

        meetings = []
        for row in rows:
            meetings.append({
                "id": row[0],
                "title": row[1],
                "participants": json.loads(row[2]) if row[2] else [],
                "transcript": row[3],
                "summary": row[4],
                "created_at": row[5]
            })
        return meetings

    def log(self, level: str, message: str) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO logs (level, message, created_at)
                VALUES (?, ?, ?)
            """, (level, message, now))
            conn.commit()

    def export_people_to_json(self) -> None:
        people = self.list_people()
        json_data = {}
        for person in people:
            person_id = person["person_id"]
            json_data[person_id] = {
                "type": person["type"],
                "name": person["name"],
                "job": person["job"],
                "basic_info": person["basic_info"],
                "last_notes": person["last_notes"],
                "face_folder": person["face_folder"],
            }

        PEOPLE_JSON.write_text(
            json.dumps(json_data, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )

    def create_sample_data(self) -> None:
        self.add_person(
            person_id="sample_ahmed",
            name="Ahmed Ali",
            person_type="private",
            job="Student / Friend",
            basic_info="University colleague",
            last_notes="AI glasses project member",
            face_folder=""
        )
