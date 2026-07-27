from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import engine
from sqlmodel import Session, select, col
from app.models.models import Reviews, Summary

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/courses")
def get_courses():
    with Session(engine) as session:
        statement = select(Reviews.course_code).distinct()
        course_codes = session.exec(statement).all()
    return course_codes

@app.get("/summary/{course_code}")
def get_summary(course_code: str):
    with Session(engine) as session:
        statement = select(Summary).where(Summary.course_code == course_code)
        summary_obj = session.exec(statement).first()
        if not summary_obj:
            return {"error": "No summary found for this course"}
        return summary_obj
    