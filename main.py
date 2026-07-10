from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json

app = FastAPI(title="Universal Quiz Embed Server")

# Boshqa loyihalardan iframe orqali so'rov kelganda xavfsizlik blokiga tushmasligi uchun CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "quiz_platform.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Testlar jadvali (Har xil turdagi testlarni JSON formatida saqlaymiz)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_key TEXT UNIQUE, -- Masalan: ess1_unit1
            title TEXT,
            quiz_type TEXT,       -- multiple_choice, true_false, matching
            questions_json TEXT   -- Test savollari massivi
        )
    """)
    conn.commit()
    conn.close()

init_db()

class QuestionModel(BaseModel):
    question: str
    options: List[str]
    answer: str

class QuizCreate(BaseModel):
    quiz_key: str
    title: str
    quiz_type: str
    questions: List[QuestionModel]

@app.post("/api/quizzes/create")
def create_quiz(data: QuizCreate):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        questions_str = json.dumps([q.dict() for q in data.questions])
        cursor.execute(
            "INSERT INTO quizzes (quiz_key, title, quiz_type, questions_json) VALUES (?, ?, ?, ?)",
            (data.quiz_key, data.title, data.quiz_type, questions_str)
        )
        conn.commit()
        return {"status": "success", "message": "Quiz created successfully", "quiz_key": data.quiz_key}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Quiz key already exists!")
    finally:
        conn.close()

@app.get("/api/quizzes/{quiz_key}")
def get_quiz(quiz_key: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT title, quiz_type, questions_json FROM quizzes WHERE quiz_key = ?", (quiz_key,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Quiz not found")
        
    return {
        "title": row[0],
        "quiz_type": row[1],
        "questions": json.loads(row[2])
    }
