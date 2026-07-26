
from datetime import datetime
import os
import asyncio
from dotenv import load_dotenv
from sqlmodel import Session, select
from sqlalchemy import func
from app.models.models import Reviews
from app.db import engine
load_dotenv()
import httpx    

DISQUS_API_KEY = os.getenv("DISQUS_API_KEY")

async def get_courses_list_for_ay(academic_year: str):
    """
    Fetches the list of courses for a given academic year from the NUSMods API.

    academic_year: str
        The academic year in the format "YYYY-YYYY" (e.g., "2023-2024").
    """

    try:

        url = f"https://api.nusmods.com/v2/{academic_year}/moduleList.json"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

        courses_list = [course["moduleCode"] for course in response.json()]
        return courses_list

    except httpx.HTTPStatusError as e:
        print(f"Failed to fetch courses: {e}")
        return []
    
    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}: {e}")
        return []
    
async def get_new_reviews_for_course(course_code: str, since: datetime | None):
    """
    Fetches the new reviews for a given course code from the NUSMods API.

    course_code: str
        The course code (e.g., "CS1010").
    since: datetime | None
        The date from which to fetch reviews.
    """
    try:
        posts = []
        async with httpx.AsyncClient() as client:
            hasNext = True
            cursor = ""
            request_count = 0
            while hasNext: 
                url = f"https://disqus.com/api/3.0/threads/listPosts.json?api_key={DISQUS_API_KEY}&forum=nusmods-prod&thread:ident={course_code}&cursor={cursor}&since={since.isoformat() if since else ''}"

                response = await client.get(url)
                response.raise_for_status()
                request_count += 1

                json_response = response.json()

                for post in json_response["response"]:
                    if not post["isSpam"] and not post["isDeleted"]:
                        posts.append({
                            "course_code": course_code,
                            "raw_message": post["raw_message"],
                            "created_at": datetime.fromisoformat(post["createdAt"]),
                            "disqus_id": post["id"],
                            "likes": post["likes"],
                            "parent_disqus_id": post["parent"]
                        })

                hasNext = json_response["cursor"]["hasNext"]
                if hasNext:
                    cursor = json_response["cursor"]["next"]
        return (posts, request_count)
                
    except httpx.HTTPStatusError as e:
        print(f"Failed to fetch reviews for {course_code}: {e}")
        return ([], 0)

    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}: {e}")
        return ([], 0)

async def main():
    courses = await get_courses_list_for_ay("2026-2027")
    request_count = 0

    with Session(engine) as session:
        for course in courses:
            statement = select(func.max(Reviews.created_at)).where(Reviews.course_code == course)
            since = session.exec(statement).first()
            
            reviews, req_count = await get_new_reviews_for_course(course, since)
            request_count += req_count

            for review in reviews:
                review_obj = Reviews(**review)
                session.add(review_obj)
                    
            session.commit()
            print(f"Fetched {len(reviews)} reviews for course {course}")
           
            if request_count >= 1000:
                print("Reached 1000 requests, stopping to avoid rate limit.")
                await asyncio.sleep(60*60)  # Sleep for 60 seconds to avoid hitting the rate limit
                request_count = 0  # Reset request count after sleeping
            
if __name__ == "__main__":
    asyncio.run(main())
    