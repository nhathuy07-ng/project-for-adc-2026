import json
from main import export_cv

resume_data = {
    "fullName": "Jane Doe",
    "location": "San Francisco, CA",
    "contacts": ["(555) 123-4567", "jane.doe@email.com"],
    "targetJobTitle": "Senior Software Engineer",
    "profileURL": "linkedin.com/in/janedoe",
    "professionalSummary": "Experienced software engineer with a passion for building scalable web applications.",
    "experience": [
        {
            "jobTitle": "Lead Developer",
            "orgNameOrType": "Tech Innovators Inc.",
            "address": "San Francisco, CA",
            "startTime": "2020-01",
            "endTime": "Present",
            "highlightContribution": "Spearheaded the migration to a microservices architecture.",
            "contributions": ["Managed a team of 5 engineers.", "Improved system uptime to 99.99%."]
        }
    ],
    "education": [
        {
            "institution": "University of California, Berkeley",
            "graduationTime": "2018",
            "location": "Berkeley, CA",
            "details": ["B.S. in Computer Science", "GPA: 3.9/4.0"]
        }
    ],
    "skillsAndTools": [
        {
            "typeOfSkillsOrTools": "Programming Languages",
            "detailedSkillsOrTools": ["Python", "JavaScript", "Go", "C++"]
        }
    ]
}

with open("cv_metadata.json", "r") as f:
    cv_metadata = json.load(f)

import asyncio

for key in cv_metadata.keys():
    print(f"Testing template: {key}...")
    try:
        pdf_base64 = asyncio.run(export_cv(key, resume_data))
        if pdf_base64.startswith("Error"):
            print(f"  ❌ FAILED: {pdf_base64}")
        else:
            print("  ✅ SUCCESS (PDF generated)")
    except Exception as e:
        print(f"  ❌ CRASHED: {e}")

print("All tests complete!")
