from transformers import pipeline
import time
import queue
import threading

pipe = pipeline("automatic-speech-recognition", model="openai/whisper-base")

job_queue: queue.Queue[tuple[str, str]] = queue.Queue()
job_results: dict[str, str] = {}

def gen_job_id():
    return str(time.time_ns())

def wait_asr_result(job_id: str):
    while job_id not in job_results:
        time.sleep(0.02)
    return job_results[job_id]

def asr_loop():
    while True:
        item = job_queue.get()

        if item is None:
            job_queue.task_done()
            break

        file_path, job_id = item
        result = pipe(file_path, return_timestamps=True)
        transcripted_text = result['text']

        job_results[job_id] = transcripted_text.strip()
        job_queue.task_done()
        print(job_results[job_id])

asr_thread = threading.Thread(target=asr_loop, daemon=True)
asr_thread.start()

if __name__ == "__main__":
    try:
        while True:
            job_queue.put([input(), str(time.time())])
            job_queue.join()
            
    except KeyboardInterrupt:
        # Graceful shutdown: send sentinel
        job_queue.put(None)
        asr_thread.join()