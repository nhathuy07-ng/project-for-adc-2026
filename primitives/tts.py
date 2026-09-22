from pocket_tts import TTSModel
import scipy.io.wavfile
import queue
import threading
import numpy as np
import time

tts_model = TTSModel.load_model()
voice_state = tts_model.get_state_for_audio_prompt("alba")

job_queue: queue.Queue[tuple[str, str]] = queue.Queue()
job_results: dict[str, str] = {}

def add_to_tts_queue(str_input):
    job_id = str(time.time())
    job_queue.put([str_input, job_id])
    return job_id

def wait_for_job_result(job_id):
    while job_id not in job_results:
        pass
    return job_results[job_id]
    
def tts_loop():
    while True:
        item = job_queue.get()
        print(item)

        voice_line, job_id = item

        audio = tts_model.generate_audio(voice_state, voice_line)
        
        scipy.io.wavfile.write(f"tmp/audio_{job_id}.wav", tts_model.sample_rate, audio.numpy())

        job_results[job_id] = f"tmp/audio_{job_id}.wav"
        job_queue.task_done()

def tts_once(voice_line):
    job_id = str(time.time())
    audio = tts_model.generate_audio(voice_state, voice_line).numpy()

    # Converting to PCM
    # Prevent digital clipping by scaling your floats safely
    audio_scaled = np.clip(audio, -1.0, 1.0)

    # Scale up to the max value of a 16-bit signed integer (32767)
    audio_int16 = (audio_scaled * 32767).astype(np.int16)   
    scipy.io.wavfile.write(f"tmp/audio_{job_id}.wav", tts_model.sample_rate, audio_int16)
    return f"tmp/audio_{job_id}.wav"

tts_thread = threading.Thread(target=tts_loop, daemon=True)
tts_thread.start()

job_queue.join()

if __name__ == "__main__":
    try:
        while True:
            job_queue.put([input(), str(time.time())])
    except KeyboardInterrupt:
        # Graceful shutdown: send sentinel
        job_queue.put(None)
        tts_thread.join()