import enum
import os
import json
import base64
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from portfolio_data_classes import ResumeInfo
from primitives.tts import tts_once
from primitives.asr import start_asr_job, wait_asr_result
from primitives.llm import query_ai
import needle
from pydub import AudioSegment
from pydub.effects import speedup

app = FastAPI()

app.mount("/static", StaticFiles(directory="webUI"), name="static")

@app.get("/")
async def get_index():
    return FileResponse("webUI/index.html")

step_prompts = [
    "Would you like to build your CV step-by-step through a guided voice interview, or simply speak out your raw notes for me to structure and polish?",
    "Tell me your full name, location, contact details, and the job title you're targeting.",
    "Do you have a LinkedIn handle, GitHub username or portfolio link you’d like to include?",
    "How would you introduce yourself professionally in two or three sentences, and what are your main strengths?",
    "Walk me through your relevant past experiences — this can include traditional jobs, freelance work, side gigs, or community volunteering. What was the role, where and when was it, and what did you achieve?",
    "What is your educational background? Mention your degree or field of study, school or training program, and graduation year—or let me know if you are self-taught or currently studying.",
    "What tools and specialized skills do you use most in your day-to-day work?",
    "Are there any standout projects, licenses, or certifications you’d like to highlight?"
]

class ProfileType(enum.Enum):
    CV = 1
    PORTFOLIO = 2

class InteractionMode(enum.Enum):
    GUIDED = 1
    SCRIBE = 2

from pydantic import BaseModel, Field

class UserIntent(BaseModel):
    intent: str = Field(description="Must be exactly one of: 'PROVIDE_INFO', 'CONFIRM', 'EXIT'. Use PROVIDE_INFO if the user is giving resume details or amending previous details. Use CONFIRM if they are saying 'continue', 'yes', 'looks good'. Use EXIT if they want to stop or quit.")
    summary_of_provided_info: str = Field(default="", description="If intent is PROVIDE_INFO, summarize what the user just provided in 1 short sentence (e.g., 'I noted down your email as bob@email.com').")

class SessionData:
    def __init__(self):
        self.profileType: ProfileType = None
        self.interactionMode: InteractionMode = None
        self.currentStep: int = 0
        self.resumeInfo = ResumeInfo()
        self.state = "ASKING" # ASKING, WAITING_FOR_CONFIRM, FINAL_REVIEW, SELECT_TEMPLATE, CONFIRM_EXIT
        self.previous_state = "ASKING"
        self.last_transcript = ""
        self.answers = []

session_data = SessionData()

# Load CV metadata
try:
    with open("cv_metadata.json", "r") as f:
        cv_metadata = json.load(f)
except FileNotFoundError:
    cv_metadata = {}

def get_tts_base64(text: str):
    tts_file = tts_once(text)
    sound = speedup(AudioSegment.from_wav(tts_file), 1.15)
    processed_file = tts_file.replace(".wav", "_fast.wav")
    sound.export(processed_file, format="wav")
    with open(processed_file, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

import jinja2
import pdfkit

def export_cv(template_key: str, resume_data: dict) -> str:
    template_info = cv_metadata.get(template_key)
    if not template_info:
        return "Error: Template not found."
        
    index_path = template_info["index_path"]
    template_dir = os.path.dirname(index_path)
    template_file = os.path.basename(index_path)
    
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
    template = env.get_template(template_file)
    
    cv_data = resume_data
    
    rendered_html = template.render(**cv_data)
    
    os.makedirs("exports", exist_ok=True)
    pdf_path = f"exports/cv_{int(time.time())}.pdf"
    
    try:
        pdfkit.from_string(rendered_html, pdf_path, options={"enable-local-file-access": ""})
        return f"Successfully generated PDF at {pdf_path}"
    except Exception as e:
        print(f"PDF generation failed (wkhtmltopdf missing?): {e}")
        html_path = pdf_path.replace(".pdf", ".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)
        return f"Saved as HTML at {html_path} because PDF generation failed."

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    os.makedirs("tmp", exist_ok=True)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "start":
                session_data.currentStep = 0
                session_data.state = "ASKING"
                session_data.answers = []
                current_prompt = step_prompts[session_data.currentStep]
                audio_b64 = get_tts_base64(current_prompt)
                
                await websocket.send_text(json.dumps({
                    "type": "audio",
                    "text": current_prompt,
                    "audio_data": audio_b64
                }))
                
            elif message.get("action") == "next_step":
                if session_data.currentStep < len(step_prompts) - 1:
                    session_data.currentStep += 1
                session_data.state = "ASKING"
                
                current_prompt = step_prompts[session_data.currentStep]
                audio_b64 = get_tts_base64(current_prompt)
                    
                await websocket.send_text(json.dumps({
                    "type": "audio",
                    "text": current_prompt,
                    "audio_data": audio_b64
                }))
                
            elif message.get("action") == "submit_audio":
                # Save audio to temp file
                audio_data = base64.b64decode(message.get("audio_data"))
                timestamp = str(time.time_ns())
                audio_path = f"tmp/recording_{timestamp}.webm"
                with open(audio_path, "wb") as f:
                    f.write(audio_data)
                
                # Transcribe
                print(f"Transcribing {audio_path}...")
                job_id = start_asr_job(audio_path)
                transcript = wait_asr_result(job_id)
                print(f"Transcript: {transcript}")
                
                if session_data.state in ["ASKING", "WAITING_FOR_CONFIRM"]:
                    print("Classifying intent...")
                    intent_json_str = query_ai(transcript, UserIntent)
                    try:
                        user_intent = UserIntent.model_validate_json(intent_json_str)
                    except Exception as e:
                        print("Failed to parse intent:", e)
                        user_intent = UserIntent(intent="PROVIDE_INFO", summary_of_provided_info=transcript)
                        
                    print(f"Intent classified as: {user_intent.intent}")
                    
                    if user_intent.intent == "EXIT":
                        session_data.previous_state = session_data.state
                        session_data.state = "CONFIRM_EXIT"
                        exit_msg = "Are you sure you want to exit and discard your session? Say yes to exit, or no to continue."
                        audio_b64 = get_tts_base64(exit_msg)
                        await websocket.send_text(json.dumps({
                            "type": "audio", "text": exit_msg, "audio_data": audio_b64
                        }))
                        
                    elif user_intent.intent == "CONFIRM":
                        if session_data.state == "WAITING_FOR_CONFIRM":
                            if session_data.currentStep < len(step_prompts) - 1:
                                session_data.currentStep += 1
                                session_data.state = "ASKING"
                                next_prompt = step_prompts[session_data.currentStep]
                                combined_text = f"Got it. Next question: {next_prompt}"
                                audio_b64 = get_tts_base64(combined_text)
                                await websocket.send_text(json.dumps({
                                    "type": "audio", "text": combined_text, "audio_data": audio_b64
                                }))
                            else:
                                session_data.state = "FINAL_REVIEW"
                                final_text = "Got it. We have finished all the questions. Is there anything else you want to amend before we choose a design?"
                                audio_b64 = get_tts_base64(final_text)
                                await websocket.send_text(json.dumps({
                                    "type": "audio", "text": final_text, "audio_data": audio_b64
                                }))
                        else:
                            # User confirmed without providing info, possibly skipped.
                            pass
                            
                    elif user_intent.intent == "PROVIDE_INFO":
                        print("Structuring data...")
                        prompt_input = f"Current JSON: {session_data.resumeInfo.model_dump_json()}\n\nNew User Input to merge: {transcript}"
                        try:
                            updated_json_str = query_ai(prompt_input, ResumeInfo)
                            session_data.resumeInfo = ResumeInfo.model_validate_json(updated_json_str)
                        except Exception as e:
                            print("Failed to merge info:", e)
                            
                        readback = f"{user_intent.summary_of_provided_info} If this is right, say continue. Else, tell me what to change."
                        session_data.state = "WAITING_FOR_CONFIRM"
                        audio_b64 = get_tts_base64(readback)
                        await websocket.send_text(json.dumps({
                            "type": "audio", "text": readback, "audio_data": audio_b64
                        }))
                        
                elif session_data.state == "CONFIRM_EXIT":
                    if any(word in transcript.lower() for word in ["yes", "exit", "stop", "quit", "discard", "confirm", "sure"]):
                        session_data.state = "DONE"
                        msg = "Session discarded. Goodbye!"
                        audio_b64 = get_tts_base64(msg)
                        await websocket.send_text(json.dumps({
                            "type": "audio", "text": msg, "audio_data": audio_b64
                        }))
                    else:
                        session_data.state = session_data.previous_state
                        msg = "Okay, let's continue."
                        audio_b64 = get_tts_base64(msg)
                        await websocket.send_text(json.dumps({
                            "type": "audio", "text": msg, "audio_data": audio_b64
                        }))
                        
                elif session_data.state == "FINAL_REVIEW":
                    intent_json_str = query_ai(transcript, UserIntent)
                    try:
                        user_intent = UserIntent.model_validate_json(intent_json_str)
                    except:
                        user_intent = UserIntent(intent="CONFIRM", summary_of_provided_info="")
                        
                    if user_intent.intent == "EXIT":
                        session_data.previous_state = "FINAL_REVIEW"
                        session_data.state = "CONFIRM_EXIT"
                        exit_msg = "Are you sure you want to exit and discard your session? Say yes to exit, or no to continue."
                        audio_b64 = get_tts_base64(exit_msg)
                        await websocket.send_text(json.dumps({
                            "type": "audio", "text": exit_msg, "audio_data": audio_b64
                        }))
                    elif user_intent.intent == "PROVIDE_INFO":
                        prompt_input = f"Current JSON: {session_data.resumeInfo.model_dump_json()}\n\nNew User Input to merge: {transcript}"
                        try:
                            updated_json_str = query_ai(prompt_input, ResumeInfo)
                            session_data.resumeInfo = ResumeInfo.model_validate_json(updated_json_str)
                        except:
                            pass
                        msg = f"I noted that change: {user_intent.summary_of_provided_info}. Does the rest look good?"
                        audio_b64 = get_tts_base64(msg)
                        await websocket.send_text(json.dumps({
                            "type": "audio", "text": msg, "audio_data": audio_b64
                        }))
                    else:
                        session_data.state = "SELECT_TEMPLATE"
                        options_texts = []
                        for idx, (key, info) in enumerate(cv_metadata.items()):
                            options_texts.append(f"Option {idx + 1} is {info['name']}. {info['description']}")
                            
                        templates_summary = " ".join(options_texts)
                        select_msg = f"Great! Let's choose a design. We have {len(cv_metadata)} options. {templates_summary} Which one would you prefer?"
                        audio_b64 = get_tts_base64(select_msg)
                        
                        await websocket.send_text(json.dumps({
                            "type": "audio",
                            "text": select_msg,
                            "audio_data": audio_b64
                        }))
                        
                elif session_data.state == "SELECT_TEMPLATE":
                    # Simple heuristic mapping for now instead of LLM to save latency
                    chosen_key = None
                    transcript_lower = transcript.lower()
                    for idx, (key, info) in enumerate(cv_metadata.items()):
                        # Check for option number or name keyword
                        if str(idx + 1) in transcript_lower or info['name'].lower().split()[0] in transcript_lower:
                            chosen_key = key
                            break
                            
                    if not chosen_key and cv_metadata:
                        chosen_key = list(cv_metadata.keys())[0] # Default to first if not understood
                        
                    if chosen_key:
                        session_data.state = "DONE"
                        
                        # Export
                        export_result = export_cv(chosen_key, session_data.resumeInfo.model_dump())
                        
                        final_msg = f"Perfect, I've selected that template and generated your file. {export_result}"
                        audio_b64 = get_tts_base64(final_msg)
                        
                        await websocket.send_text(json.dumps({
                            "type": "audio",
                            "text": final_msg,
                            "audio_data": audio_b64
                        }))
                        
    except WebSocketDisconnect:
        print("Client disconnected")
