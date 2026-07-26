import os
from dotenv import load_dotenv
load_dotenv()
import asyncio
from os import lo
from app.db import engine
from sqlmodel import Session, select, col, func
from app.models.models import Reviews
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
    You are a course review summariser for NUS modules. You will be given a list of student reviews for a course. Your task is to analyse the reviews and return a JSON object with the following fields:
    {
    overall_summary: str,
    workload_rating: float,
    difficulty_rating: float,
    enjoyability_rating: float,
    praises: list[str],
    complaints: list[str],
    recommendations: list[str],
    teaching_comments: list[str],
    assessment_comments: dict[str, str],
    concepts: list[str]
    }

    Guidelines:
    - the overall summary should be 3-4 sentences long
    - the rating is out of 10, calculate it using the values provided in the reviews as well as overall sentiment analysis.
    -  Present the reviews as objectively as possible.
    - Do not mention specific professor or tutor’s name
    - teaching_comments should be able out teaching style and effectiveness not a description of who is teaching
    - Return only valid JSON with no markdown, no backticks, no preamble
    - If there are no reviews or insufficient information simply say ‘Not enough reviews to generate summary’
"""

def get_courses_list():
    with Session(engine) as session:
        statement = select(Reviews.course_code).distinct()
        course_codes = session.exec(statement).all()
    return course_codes

def get_reviews_for_course(course_code):
    with Session(engine) as session:
        statement = (select(Reviews.raw_message)
                     .where(Reviews.course_code == course_code)
                     .where(func.length(Reviews.raw_message) > 30)
                     .order_by(col(Reviews.created_at).desc())
                     .limit(20))
        reviews = session.exec(statement).all()
    return reviews

async def summarise_course(course_code):
    reviews = await get_reviews_for_course(course_code)
    review_string = "\n".join(reviews)

def main():
    print(get_courses_list())
    print(type(get_reviews_for_course("CS2103T")))


if __name__ == "__main__":
    main()