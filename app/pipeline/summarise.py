from app.db import engine
from sqlmodel import Session, select, col, func
from app.models.models import Reviews

def get_courses_list():
    course_codes = []
    with Session(engine) as session:
        statement = select(Reviews.course_code).distinct()
        course_codes = session.exec(statement).all()
    return course_codes

def get_reviews_for_course(course_code):
    reviews = []
    with Session(engine) as session:
        statement = (select(Reviews.raw_message)
                     .where(Reviews.course_code == course_code)
                     .where(func.length(Reviews.raw_message) > 30)
                     .order_by(col(Reviews.created_at).desc())
                     .limit(20))
        reviews = session.exec(statement).all()
    return reviews