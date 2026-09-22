const ws = new WebSocket(`ws://${window.location.host}/ws`);
const statusRegion = document.getElementById('status-region');
const transcriptRegion = document.getElementById('transcript-region');
const startBtn = document.getElementById('start-btn');
const recordBtn = document.getElementById('record-btn');
const nextBtn = document.getElementById('next-btn');

let audioContext;
let currentAudioSource;

let mediaRecorder;
let audioChunks = [];
let isRecording = false;

function updateStatus(message) {
    statusRegion.textContent = message;
}

function playAudio(base64Data) {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    // Stop current audio if playing
    if (currentAudioSource) {
        currentAudioSource.stop();
    }

    const binaryString = window.atob(base64Data);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }

    audioContext.decodeAudioData(bytes.buffer, function(buffer) {
        currentAudioSource = audioContext.createBufferSource();
        currentAudioSource.buffer = buffer;
        currentAudioSource.connect(audioContext.destination);
        currentAudioSource.start(0);
        
        currentAudioSource.onended = () => {
            updateStatus("Finished speaking. Waiting for your input.");
        };
    });
}

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'audio') {
        transcriptRegion.textContent = data.text;
        updateStatus("AI is speaking...");
        playAudio(data.audio_data);
    }
};

startBtn.addEventListener('click', () => {
    updateStatus("Starting interview...");
    ws.send(JSON.stringify({ action: "start" }));
});

nextBtn.addEventListener('click', () => {
    updateStatus("Requesting next step...");
    ws.send(JSON.stringify({ action: "next_step" }));
});

async function toggleRecording() {
    if (isRecording) {
        // Stop recording
        mediaRecorder.stop();
        isRecording = false;
        recordBtn.textContent = "Record (F or J)";
        recordBtn.style.backgroundColor = ""; // Reset style
        updateStatus("Recording stopped. Processing...");
    } else {
        // Stop any playing audio
        if (currentAudioSource) {
            currentAudioSource.stop();
        }
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.addEventListener("dataavailable", event => {
                audioChunks.push(event.data);
            });
            
            mediaRecorder.addEventListener("stop", () => {
                const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = function() {
                    const base64data = reader.result.split(',')[1];
                    ws.send(JSON.stringify({
                        action: "submit_audio",
                        audio_data: base64data
                    }));
                };
                // Stop all tracks to release microphone
                stream.getTracks().forEach(track => track.stop());
            });
            
            mediaRecorder.start();
            isRecording = true;
            recordBtn.textContent = "Stop Recording (F or J)";
            recordBtn.style.backgroundColor = "#ff4444"; // Visual indicator
            updateStatus("Recording... Speak now.");
        } catch (err) {
            console.error("Error accessing microphone:", err);
            updateStatus("Error accessing microphone. Please allow permissions.");
        }
    }
}

recordBtn.addEventListener('click', toggleRecording);

// Global keyboard listeners for accessibility
window.addEventListener('keydown', (e) => {
    // Only capture if we aren't focused on an input element
    if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
        if (e.code === 'Space') {
            e.preventDefault();
            startBtn.click();
        } else if (e.key === 'f' || e.key === 'F' || e.key === 'j' || e.key === 'J') {
            e.preventDefault();
            recordBtn.click();
        }
    }
});
