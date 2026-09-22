import json
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()

with open("cv_metadata.json", "r") as f:
    cv_metadata = json.load(f)

prompt_template = """You are a frontend expert. Convert the following HTML CV template into a Jinja2 template.
IMPORTANT: You MUST preserve ALL original CSS classes, HTML tags, id attributes, and the exact structural layout. DO NOT remove any HTML elements or stylesheets.
Replace the hardcoded dummy placeholder text (names, dates, bullet points) with the following Jinja2 loops and variables:

Variables available:
- `fullName`
- `location`
- `targetJobTitle`
- `profileURL`
- `contacts` (List of strings)
- `professionalSummary` (String with HTML tags, use `{{ professionalSummary | safe }}` if you output it)
- `experience` (List of dicts: `jobTitle`, `orgNameOrType`, `address`, `startTime`, `endTime`, `highlightContribution`, and `contributions` list)
- `education` (List of dicts: `institution`, `graduationTime`, `location`, and `details` list)
- `skillsAndTools` (List of dicts: `typeOfSkillsOrTools` and `detailedSkillsOrTools` list)

Use Jinja2 syntax like `{% for exp in experience %}` to iterate over the sections, and `{{ exp.jobTitle }}` to output variables. 
If a section is missing from the HTML (e.g., no skills section), do not add it. Only replace existing dummy sections with their corresponding loops.
If there are multiple hardcoded entries in a section (e.g., 3 jobs), collapse them into a SINGLE Jinja2 `{% for %}` loop that replicates the exact structure of ONE of the entries.
Ensure `{% if %}` checks are placed appropriately around sections so they don't render if the data is missing.

Return ONLY the raw HTML code. Do not include markdown codeblocks like ```html or ```.

HTML Template:
{html_content}
"""

for key, info in cv_metadata.items():
    index_path = info["index_path"]
    print(f"Processing {index_path}...")
    
    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    prompt = prompt_template.replace("{html_content}", html_content)
    
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite',
        contents=prompt
    )
    
    output = response.text.strip()
    if output.startswith("```html"):
        output = output[7:]
    if output.startswith("```"):
        output = output[3:]
    if output.endswith("```"):
        output = output[:-3]
        
    output = output.strip()
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(output)
        
    print(f"Successfully converted {index_path}\n")

print("All templates converted!")
