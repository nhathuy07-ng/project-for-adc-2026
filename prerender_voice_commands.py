import os
import shutil
from pydub import AudioSegment
from primitives.tts import tts_once

def speedup(sound, speed=1.0):
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speed)
    })
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

commands = {
    "intro": "Please center your face in the camera. Press F to take the picture, or J to skip this step.",
    "left": "Move your head slightly to the left.",
    "right": "Move your head slightly to the right.",
    "up": "Move your head slightly up.",
    "down": "Move your head slightly down.",
    "closer": "Move closer to the camera.",
    "further": "Move further away.",
    "perfect": "Perfect. Hold still.",
    "system_start": "Welcome to CVSpeak. Press Space to begin. During the interview, press F to record, and J to skip to the next step. You can also press R to repeat the last voice line, left bracket to slow down, and right bracket to speed up.",
    "other_intent": "I didn't quite catch that. Could you please repeat?"
}

import json
# Generate CV list string dynamically
with open('cv_metadata.json', 'r') as f:
    cv_metadata = json.load(f)
    
cv_list_text = "Here are the available templates: "
for idx, info in enumerate(cv_metadata.values()):
    cv_list_text += f"{idx + 1}: {info['name']}. {info['description']} "

commands["cv_list"] = cv_list_text

os.makedirs("webUI/audio", exist_ok=True)

for key, text in commands.items():
    print(f"Generating audio for {key}...")
    tts_file = tts_once(text)
    sound = speedup(AudioSegment.from_wav(tts_file), 1.15)
    
    output_path = f"webUI/audio/{key}.wav"
    sound.export(output_path, format="wav")
    print(f"Saved {output_path}")

print("All voice commands pre-rendered successfully!")
