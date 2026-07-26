import os
from dotenv import load_dotenv
load_dotenv()
import re
import time
import json_repair
import json
from app.db import engine
from sqlmodel import Session, select, col, func
from app.models.models import Reviews, Summary
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



# helper function
def parse_llm_json(llm_output: str) -> dict:
    try:
        # Step 1: Use regex to extract the text between the first '{' and last '}'
        match = re.search(r"(\{.*\})", llm_output, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in the LLM response.")
            
        json_string = match.group(1)
        
        # Step 2: Attempt standard parsing first
        return json.loads(json_string)
        
    except json.JSONDecodeError:
        # Step 3: Fallback to json_repair if the LLM missed a comma or quote
        print("Standard parsing failed. Attempting to repair malformed JSON...")
        return json_repair.loads(json_string)


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

    summary_json = parse_llm_json(completion.choices[0].message.content)
    print(summary_json)
    return summary_json

def save_course_summary(course_code):
    with Session(engine) as session:
        existing = session.exec(select(Summary).where(Summary.course_code == course_code)).first()
        if existing:
            print(f"Skipping {course_code} - summary already exists")
            return
        summary_json = summarise_course(course_code)

        if summary_json.get("overall_summary") == "Not enough reviews to generate a summary":
            print(f"Skipping {course_code} - not enough reviews")
            return
        
        summary_obj = Summary(course_code=course_code, **summary_json)
        session.add(summary_obj)
        session.commit()

def main():
    course_list = get_courses_list()
    for course_code in course_list:
        try:
            print(f"Summarising {course_code}")
            save_course_summary(course_code)
        except Exception as e:
            print(f"Failed to summarise {course_code}: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()