import os
from google import genai
from google.genai import types
from pydantic import BaseModel

MODEL = 'gemini-3.1-flash-lite'

SYS_PROMPT_WITH_JSON = """
You are an expert resume parsing engine. Your job is to extract, structure, and polish raw user statements into valid JSON conforming exactly to the `ResumeInfo` schema.

### Guidelines:
1. **Extraction & Classification:** Accurately map unstructured user inputs to their respective fields (`experience`, `education`, `skillsAndTools`, etc.). Break multiple jobs or degrees into separate list items.
2. **Action-Oriented Polishing:** Rewrite casual or spoken work descriptions into crisp, ATS-friendly resume bullet points starting with strong past-tense action verbs (e.g., "Led", "Engineered", "Optimized"). Quantify metrics and outcomes wherever stated.
3. **Normalization:** Normalize colloquial dates to "YYYY" or "YYYY-MM" (or "Present" for active roles). Resolve handles into full URLs (e.g., LinkedIn, GitHub).
4. **Formatting:** Use basic inline HTML tags (`<b>`, `<strong>`) strictly where permitted (`professionalSummary`, `skillsAndTools`) for emphasis and category labeling.
5. **Fidelity:** Never hallucinate facts, metrics, or credentials not supported by the input. CRITICAL: ONLY fill in fields that the user explicitly provides information for. Leave all other fields empty, null, or unchanged. DO NOT invent dummy data to fill out the schema.
6. **Output:** Return valid JSON only, without conversational filler or Markdown fences.

Respond in the following JSON schema:
{}
"""

SYS_PROMPT_WITH_PLAINTEXT = """
You are an expert resume parsing engine. Your job is to extract, structure, and polish raw user statements into valid JSON conforming exactly to the `ResumeInfo` schema.

### Guidelines:
1. **Extraction & Classification:** Accurately map unstructured user inputs to their respective fields (`experience`, `education`, `skillsAndTools`, etc.). Break multiple jobs or degrees into separate list items.
2. **Action-Oriented Polishing:** Rewrite casual or spoken work descriptions into crisp, ATS-friendly resume bullet points starting with strong past-tense action verbs (e.g., "Led", "Engineered", "Optimized"). Quantify metrics and outcomes wherever stated.
3. **Normalization:** Normalize colloquial dates to "YYYY" or "YYYY-MM" (or "Present" for active roles). Resolve handles into full URLs (e.g., LinkedIn, GitHub).
4. **Formatting:** Use basic inline HTML tags (`<b>`, `<strong>`) strictly where permitted (`professionalSummary`, `skillsAndTools`) for emphasis and category labeling.
5. **Fidelity:** Never hallucinate facts, metrics, or credentials not supported by the input. If an optional field is missing, use its schema default.
6. **Output:** Return valid plaintext or HTML only, without conversational filler or Markdown fences.

Required field: {}
"""

from dotenv import load_dotenv
load_dotenv()

client = genai.Client()

def query_ai(str_input: str, data_model: BaseModel | None = None, required_field: str | None = None):
    system_instruction = SYS_PROMPT_WITH_JSON.format(str(data_model.model_json_schema())) if data_model else SYS_PROMPT_WITH_PLAINTEXT.format(required_field)
    
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.0,
    )
    
    if data_model:
        config.response_mime_type = "application/json"
        config.response_schema = data_model
        
    response = client.models.generate_content(
        model=MODEL,
        contents=str_input,
        config=config
    )
    
    content = response.text.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
        if content.endswith("```"):
            content = content.rsplit("\n", 1)[0]
    return content.strip()