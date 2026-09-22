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

class SessionData:
    def __init__(self):
        self.profileType: ProfileType = None
        self.interactionMode: InteractionMode = None
        self.currentStep: int = 0
        self.resumeInfo = ResumeInfo()
        self.state = "ASKING" # ASKING or WAITING_FOR_CONFIRM
        self.last_transcript = ""

session_data = SessionData()

def get_tts_base64(text: str):
    tts_file = tts_once(text)
    sound = speedup(AudioSegment.from_wav(tts_file), 1.15)
    processed_file = tts_file.replace(".wav", "_fast.wav")
    sound.export(processed_file, format="wav")
    with open(processed_file, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

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
                
                if session_data.state == "ASKING":
                    # Process answer
                    session_data.last_transcript = transcript
                    
                    # (Optional) We could call query_ai(transcript, session_data.resumeInfo) here 
                    # to update the internal state, but for the readback we use the transcript.
                    # llm_parsed_json = query_ai(transcript, session_data.resumeInfo)
                    
                    readback = f"I noted down: {transcript}. If this is the right information, say 'continue.' Else, tell me what to change."
                    session_data.state = "WAITING_FOR_CONFIRM"
                    audio_b64 = get_tts_base64(readback)
                    
                    await websocket.send_text(json.dumps({
                        "type": "audio",
                        "text": readback,
                        "audio_data": audio_b64
                    }))
                    
                elif session_data.state == "WAITING_FOR_CONFIRM":
                    if "continue" in transcript.lower():
                        # Proceed to next question
                        confirmation_text = "Got it, moving to the next question."
                        if session_data.currentStep < len(step_prompts) - 1:
                            session_data.currentStep += 1
                        session_data.state = "ASKING"
                        
                        next_prompt = step_prompts[session_data.currentStep]
                        combined_text = f"{confirmation_text} {next_prompt}"
                        
                        audio_b64 = get_tts_base64(combined_text)
                        await websocket.send_text(json.dumps({
                            "type": "audio",
                            "text": combined_text,
                            "audio_data": audio_b64
                        }))
                    else:
                        # Handle amendment
                        session_data.last_transcript += " " + transcript
                        readback = f"I updated it to: {transcript}. If this is the right information, say 'continue.' Else, tell me what to change."
                        audio_b64 = get_tts_base64(readback)
                        
                        await websocket.send_text(json.dumps({
                            "type": "audio",
                            "text": readback,
                            "audio_data": audio_b64
                        }))
                        
    except WebSocketDisconnect:
        print("Client disconnected")
