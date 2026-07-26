import os
from dotenv import load_dotenv
load_dotenv()
from app.db import engine
from sqlmodel import Session, select, col, func
from app.models.models import Reviews
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
    You are a course review summariser for NUS modules. You will be given a list of student reviews for a course. Your task is to analyse the reviews and return a JSON object with the following fields:
    {
        "overall_summary": str,
        "workload_rating": float,
        "difficulty_rating": float,
        "enjoyability_rating": float,
        "praises": list[str],
        "complaints": list[str],
        "recommendations": list[str],
        "teaching_comments": list[str],
        "assessment_comments": dict[str, str],
        "concepts": list[str]
    }

    Guidelines:
    - The overall summary should be 4-5 sentences, balanced and not overly negative — reflect both positives and negatives fairly
    - Ratings are out of 10, inferred from explicit ratings in reviews and overall sentiment
    - Extract at least 5-8 specific praises and complaints where available — avoid vague statements, be specific (e.g. instead of "high workload" say "iP and tP iterations can take multiple days even with AI assistance")
    - Use assessment component names as they appear in the reviews as keys for assessment_comments
    - Do not mention specific professor or tutor names anywhere
    - teaching_comments should focus on teaching style and effectiveness only
    - Return only valid JSON with no markdown, no backticks, no preamble
    - If there are insufficient reviews, return {"overall_summary": "Not enough reviews to generate a summary"}
    - Support every claim with specific evidence from the reviews, for example instead of 'teaching is clear and effective' say 'multiple students noted that lecture recaps helped them prepare for tutorials and the final exam'.
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
                     .limit(15))
        reviews = session.exec(statement).all()
    return reviews

def summarise_course(course_code):
    reviews = get_reviews_for_course(course_code)
    review_string = "\n".join(reviews)

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": review_string}
        ]
    )
    print(completion.choices[0].message.content)

def main():
    print(summarise_course("CS2040S"))


if __name__ == "__main__":
    main()