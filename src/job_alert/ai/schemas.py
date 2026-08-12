from pydantic import BaseModel
from typing import Optional

class JobClassification(BaseModel):
    student_eligible: bool = True
    is_internship: bool = True
    is_graduate_role: bool = True
    is_target_technical_role: bool = True
    excluded_role: bool = False
    technical_domain: Optional[str] = "Software Engineering"
    role_family: Optional[str] = "Software Engineering"
    summary: Optional[str] = "Matches engineering student criteria."
