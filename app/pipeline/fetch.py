
import httpx

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
    