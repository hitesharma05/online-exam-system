import sqlite3

def init_db():
    conn = sqlite3.connect("exam.db")
    cursor = conn.cursor()

    # Create users table (with full_name column)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,
            role      TEXT NOT NULL DEFAULT 'student',
            full_name TEXT DEFAULT ''
        )
    """)

    # Add full_name column if it doesn't exist yet (for existing databases)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN full_name TEXT DEFAULT ''")
    except Exception:
        pass  # Column already exists — ignore

    # Create questions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            question       TEXT NOT NULL,
            option1        TEXT NOT NULL,
            option2        TEXT NOT NULL,
            option3        TEXT NOT NULL,
            option4        TEXT NOT NULL,
            correct_answer TEXT NOT NULL
        )
    """)

    # Create results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            score           INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            percentage      REAL NOT NULL,
            submitted_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Default admin account
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password, role, full_name)
        VALUES ('admin', 'admin123', 'admin', 'Administrator')
    """)

    # Default student account
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password, role, full_name)
        VALUES ('student1', 'pass123', 'student', 'Demo Student')
    """)

    # Sample questions
    sample_questions = [
        ("What does HTML stand for?",
         "Hyper Text Markup Language", "High Tech Modern Language",
         "Hyper Transfer Markup Logic", "Home Tool Markup Language",
         "Hyper Text Markup Language"),

        ("Which language is used for styling web pages?",
         "Python", "CSS", "Java", "C++",
         "CSS"),

        ("What does CPU stand for?",
         "Central Process Unit", "Computer Personal Unit",
         "Central Processing Unit", "Core Processing Unit",
         "Central Processing Unit"),

        ("Which of these is a Python web framework?",
         "Django", "Laravel", "Spring", "Rails",
         "Django"),

        ("What does SQL stand for?",
         "Structured Query Language", "Simple Question Logic",
         "System Query Language", "Structured Question List",
         "Structured Query Language"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO questions
        (question, option1, option2, option3, option4, correct_answer)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sample_questions)

    conn.commit()
    conn.close()
    print("Database initialised successfully!")

if __name__ == "__main__":
    init_db()