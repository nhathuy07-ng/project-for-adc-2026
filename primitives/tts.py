from pocket_tts import TTSModel
import scipy.io.wavfile
import queue
import threading
import time

tts_model = TTSModel.load_model()
voice_state = tts_model.get_state_for_audio_prompt("alba")

job_queue: queue.Queue[tuple[str, str]] = queue.Queue()
job_results: dict[str, str] = {}

def tts_loop():
    while True:
        item = job_queue.get()
        print(item)

        voice_line, job_id = item

        audio = tts_model.generate_audio(voice_state, voice_line)
        scipy.io.wavfile.write(f"tmp/audio_{job_id}.wav", tts_model.sample_rate, audio.numpy())

        job_results[job_id] = f"tmp/audio_{job_id}.wav"
        job_queue.task_done()

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