from pydantic import BaseModel, Field
from typing import List, Optional

class Experience(BaseModel):
    orgNameOrType: str = Field(
        ...,
        description="Name of the organization, company, client, or the nature of work if unnamed (e.g., 'BrightPath Media', 'Self-Employed / Freelance', 'Local Animal Shelter').",
    )
    address: str = Field(
        ...,
        description="Location formatted as 'City, State/Country' (e.g., 'Austin, TX'), or 'Remote' if not physically tied to a location.",
    )
    jobTitle: str = Field(
        ...,
        description="Standardized professional job title, freelance role, or volunteer position (e.g., 'Digital Marketing Specialist', 'Freelance Copywriter').",
    )
    highlightContribution: str = Field(
        ...,
        description="The single most impactful, quantifiable accomplishment or primary value delivered during this tenure (e.g., 'Boosted client ROAS by 35% and cut wasted ad spend by nearly 50%').",
    )
    contributions: List[str] = Field(
        ...,
        description="Polished resume bullet points detailing duties, initiatives, and accomplishments, written in active voice starting with strong past-tense action verbs.",
    )
    startTime: str = Field(
        ...,
        description="Estimated or stated start date, normalized to 'YYYY-MM' or 'YYYY' (e.g., '2024-03', '2021').",
    )
    endTime: str = Field(
        ...,
        description="Estimated or stated end date, normalized to 'YYYY-MM', 'YYYY', or 'Present' if currently active.",
    )


class Education(BaseModel):
    institution: str = Field(
        ...,
        description="Name of the university, college, school, bootcamp, or educational organization (e.g., 'University of Texas at Austin', 'General Assembly').",
    )
    details: List[str] = Field(
        ...,
        description="List of academic milestones or specifications, such as degree type, major/minor, GPA, honors, relevant coursework, or capstone projects (e.g., ['B.S. in Computer Science', 'GPA: 3.8/4.0', 'Magna Cum Laude']).",
    )
    graduationTime: str = Field(
        ...,
        description="Graduation year or completion date formatted as 'YYYY' or 'YYYY-MM', or estimated completion if currently enrolled (e.g., '2021', 'Expected May 2027').",
    )
    location: str = Field(
        ...,
        description="Campus location formatted as 'City, State/Country' (e.g., 'Austin, TX'), or 'Online' if remote.",
    )

class SkillsAndTools(BaseModel):
    typeOfSkillsOrTools: str = Field(
        ...,
        description="Type of core competencies, tools, frameworks, or domain areas (one item per line or entry)"
    )
    detailedSkillsOrTools: List[str] = Field(description="List of entries for the aforementioned type")



class ResumeInfo(BaseModel):
    fullName: str = Field(
        description="Candidate's full legal or preferred professional name (e.g., 'Jane Doe').",
    )
    location: Optional[str] = Field(
        None,
        description="Current residence formatted as 'City, State' or 'City, Country' (e.g., 'Austin, TX').",
    )
    contacts: List[str] = Field(
        default_factory=list,
        description="List of primary communication channels, including verified phone number and professional email (e.g., ['+1 (512) 555-0199', 'jane.doe@email.com']).",
    )
    targetJobTitle: str = Field(
        None,
        description="Targeted career title or positioning headline to appear at the top of the CV (e.g., 'Senior Full-Stack Engineer', 'Digital Marketing Specialist').",
    )
    profileURL: str = Field(
        default="",
        description="Canonical URL or professional profile link, such as LinkedIn, GitHub, personal website, or portfolio (e.g., 'https://linkedin.com/in/janedoe').",
    )
    professionalSummary: str = Field(
        default="",
        description="Compelling 2-4 sentence executive overview synthesizing core strengths, years of experience, and primary value proposition. Basic inline HTML tags (such as <b>, <strong>, <em>) are permitted for key emphasis.",
    )
    experience: List[Experience] = Field(
        default_factory=list,
        description="Chronological list of relevant professional, freelance, side project, or volunteer experiences.",
    )
    education: List[Education] = Field(
        default_factory=list,
        description="Chronological or prioritized list of degrees, bootcamps, certifications, or formal coursework.",
    )
    skillsAndTools: List[SkillsAndTools] = Field(
        default_factory=list,
        description="List of core competencies, tools, frameworks, or domain areas (one item per line or entry)",
    )