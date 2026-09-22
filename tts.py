from pocket_tts import TTSModel
import scipy.io.wavfile
import queue
import threading

tts_model = TTSModel.load_model()
voice_state = tts_model.get_state_for_audio_prompt("charles")

job_queue: queue.Queue[tuple[str, str]] = queue.Queue()
job_results: dict[str, str] = {}

def tts_loop():
    while True:

        item = job_queue.get()

        voice_line, job_id = item

        audio = tts_model.generate_audio(voice_state, voice_line)
        scipy.io.wavfile.write(f"tmp/audio_{job_id}.wav", tts_model.sample_rate, audio.numpy())
        job_results[job_id] = f"tmp/audio_{job_id}.wav"
        job_queue.task_done()

job_queue.task_done
tts_thread = threading.Thread(target=tts_loop, daemon=True)
