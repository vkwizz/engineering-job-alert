import itertools
from typing import List, Dict

ROLE_QUERIES = [
    # B.Tech College & Placement Specific Queries
    "btech software engineer intern",
    "btech software developer fresher",
    "campus hiring software engineer",
    "software engineer intern 2026",
    "fresher software engineer",
    "graduate engineer trainee software",
    "software developer fresher 0 years",

    # Software & Web Internships / Freshers
    "software engineer intern",
    "software developer intern",
    "software engineering intern",
    "frontend developer intern",
    "backend developer intern",
    "full stack developer intern",
    "web developer intern",

    # Programming Languages
    "Python developer intern",
    "Python software engineer intern",
    "Java developer intern",
    "Java software engineer intern",

    # AI / ML / Database / Systems
    "AI engineer intern",
    "machine learning intern",
    "database engineer intern",
    "cloud engineer intern",
    "DevOps engineer intern",

    # Entry Level / Fresher Variants
    "entry level software engineer",
    "associate software engineer fresher",
    "trainee software engineer"
]

TARGET_LOCATIONS = [
    "Kerala",
    "Kochi",
    "Thiruvananthapuram",
    "Chennai",
    "Coimbatore",
    "Bangalore",
    "Bengaluru",
    "Karnataka",
    "India",
    "Remote"
]

def generate_search_matrix(max_queries: int = 20) -> List[Dict[str, str]]:
    matrix = []
    top_roles = [
        "btech software engineer intern",
        "software engineer intern",
        "software developer fresher",
        "campus hiring software engineer",
        "backend developer intern",
        "full stack developer intern",
        "Python developer intern",
        "AI engineer intern"
    ]
    
    top_locations = [
        "Kerala",
        "Kochi",
        "Bangalore",
        "Chennai"
    ]
    
    for role in top_roles:
        for loc in top_locations:
            matrix.append({"query": role, "location": loc})
            
    for role in ROLE_QUERIES:
        if len(matrix) >= max_queries:
            break
        if not any(item["query"] == role for item in matrix):
            matrix.append({"query": role, "location": "India"})

    return matrix[:max_queries]
