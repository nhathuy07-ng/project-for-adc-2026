const ws = new WebSocket(`ws://${window.location.host}/ws`);
const statusRegion = document.getElementById('status-region');
const transcriptRegion = document.getElementById('transcript-region');
const startBtn = document.getElementById('start-btn');
const recordBtn = document.getElementById('record-btn');
const nextBtn = document.getElementById('next-btn');
const repeatBtn = document.getElementById('repeat-btn');
const slowerBtn = document.getElementById('slower-btn');
const fasterBtn = document.getElementById('faster-btn');

let audioContext;
let currentAudioSource;
let lastPlayedBase64 = null;
let currentPlaybackRate = 1.0;
let hasStartedInterview = false;
let globalIntroAudio = null;

let mediaRecorder;
let audioChunks = [];
let isRecording = false;

function updateStatus(message) {
    statusRegion.textContent = message;
}

function playAudio(base64Data, isQuestion = false) {
    if (isQuestion) {
        lastPlayedBase64 = base64Data;
    }
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
        currentAudioSource.playbackRate.value = currentPlaybackRate;
        currentAudioSource.connect(audioContext.destination);
        currentAudioSource.start(0);
        
        currentAudioSource.onended = () => {
            updateStatus("Finished speaking. Waiting for your input.");
        };
    });
}

const videoElement = document.getElementById('video');
const canvasElement = document.getElementById('canvas');
const cameraRegion = document.getElementById('camera-region');

let inPortraitMode = false;
let frameInterval = null;
let lastGuidanceCommand = null;
let currentGuidanceAudio = null;

function playGuidanceAudio(commandName) {
    if (currentGuidanceAudio) {
        currentGuidanceAudio.pause();
        currentGuidanceAudio.currentTime = 0;
    }
    currentGuidanceAudio = new Audio(`/static/audio/${commandName}.wav`);
    currentGuidanceAudio.playbackRate = currentPlaybackRate;
    currentGuidanceAudio.play().catch(e => console.log("Audio play failed", e));
}

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'audio') {
        transcriptRegion.textContent = data.text;
        updateStatus("AI is speaking...");
        const isQuestion = data.is_question !== undefined ? data.is_question : false;
        playAudio(data.audio_data, isQuestion);
    } else if (data.type === 'take_portrait') {
        transcriptRegion.textContent = data.text;
        updateStatus("Portrait Capture Mode. Starting camera...");
        inPortraitMode = true;
        cameraRegion.style.display = 'block';
        playGuidanceAudio("intro");
        
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                videoElement.srcObject = stream;
                
                // Start streaming frames
                frameInterval = setInterval(() => {
                    if (videoElement.readyState === videoElement.HAVE_ENOUGH_DATA) {
                        const ctx = canvasElement.getContext('2d');
                        ctx.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
                        const frameData = canvasElement.toDataURL('image/jpeg', 0.5);
                        ws.send(JSON.stringify({
                            action: "video_frame",
                            image_data: frameData
                        }));
                    }
                }, 200); // 5 FPS
            })
            .catch(err => {
                console.error("Camera error:", err);
                updateStatus("Camera access denied.");
            });
    } else if (data.type === 'guidance') {
        if (data.command !== lastGuidanceCommand) {
            lastGuidanceCommand = data.command;
            updateStatus(`Guidance: ${data.command}`);
            playGuidanceAudio(data.command);
        }
    }
};

function endPortraitMode(actionButton) {
    if (frameInterval) clearInterval(frameInterval);
    const stream = videoElement.srcObject;
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    cameraRegion.style.display = 'none';
    inPortraitMode = false;
    
    let frameData = null;
    if (actionButton === 'F') {
        const ctx = canvasElement.getContext('2d');
        ctx.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
        frameData = canvasElement.toDataURL('image/jpeg', 0.8);
    }
    
    ws.send(JSON.stringify({
        action: "portrait_action",
        button: actionButton,
        image_data: frameData
    }));
    updateStatus("Processing portrait selection...");
}

startBtn.addEventListener('click', () => {
    updateStatus("Starting interview...");
    hasStartedInterview = true;
    if (globalIntroAudio) {
        globalIntroAudio.pause();
        globalIntroAudio.currentTime = 0;
    }
    recordBtn.disabled = false;
    nextBtn.disabled = false;
    ws.send(JSON.stringify({ action: "start" }));
});

nextBtn.addEventListener('click', () => {
    updateStatus("Requesting next step...");
    ws.send(JSON.stringify({ action: "next_step" }));
});

document.body.addEventListener('click', () => {
    if (!window.hasPlayedIntro) {
        window.hasPlayedIntro = true;
        globalIntroAudio = new Audio('/static/audio/system_start.wav');
        globalIntroAudio.playbackRate = currentPlaybackRate;
        globalIntroAudio.play().catch(e => console.log("Audio play failed", e));
    }
}, { once: true });

async function toggleRecording() {
    if (isRecording) {
        // Stop recording
        mediaRecorder.stop();
        isRecording = false;
        recordBtn.textContent = "Record (F)";
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
            recordBtn.textContent = "Stop Recording (F)";
            recordBtn.style.backgroundColor = "#ff4444"; // Visual indicator
            updateStatus("Recording... Speak now.");
        } catch (err) {
            console.error("Error accessing microphone:", err);
            updateStatus("Error accessing microphone. Please allow permissions.");
        }
    }
}

recordBtn.addEventListener('click', toggleRecording);

repeatBtn.addEventListener('click', () => {
    if (lastPlayedBase64) {
        updateStatus("Repeating AI...");
        playAudio(lastPlayedBase64);
    } else if (!hasStartedInterview && window.hasPlayedIntro) {
        updateStatus("Repeating Intro...");
        if (globalIntroAudio) {
            globalIntroAudio.pause();
            globalIntroAudio.currentTime = 0;
        } else {
            globalIntroAudio = new Audio('/static/audio/system_start.wav');
        }
        globalIntroAudio.playbackRate = currentPlaybackRate;
        globalIntroAudio.play().catch(e => console.log("Audio play failed", e));
    }
});

function updatePlaybackRate(newRate) {
    currentPlaybackRate = newRate;
    if (currentAudioSource) {
        currentAudioSource.playbackRate.value = currentPlaybackRate;
    }
    if (currentGuidanceAudio) {
        currentGuidanceAudio.playbackRate = currentPlaybackRate;
    }
    if (globalIntroAudio) {
        globalIntroAudio.playbackRate = currentPlaybackRate;
    }
    updateStatus(`Playback speed: ${currentPlaybackRate.toFixed(2)}x`);
}

slowerBtn.addEventListener('click', () => {
    updatePlaybackRate(Math.max(0.5, currentPlaybackRate - 0.25));
});

fasterBtn.addEventListener('click', () => {
    updatePlaybackRate(Math.min(2.5, currentPlaybackRate + 0.25));
});

// Global keyboard listeners for accessibility
window.addEventListener('keydown', (e) => {
    // Only capture if we aren't focused on an input element
    if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
        if (e.code === 'Space') {
            e.preventDefault();
            startBtn.click();
        } else if (e.key === 'f' || e.key === 'F') {
            e.preventDefault();
            if (inPortraitMode) {
                endPortraitMode('F');
            } else {
                recordBtn.click();
            }
        } else if (e.key === 'j' || e.key === 'J') {
            e.preventDefault();
            if (inPortraitMode) {
                endPortraitMode('J');
            } else {
                nextBtn.click();
            }
        } else if (e.key === 'r' || e.key === 'R') {
            e.preventDefault();
            repeatBtn.click();
        } else if (e.key === '[') {
            e.preventDefault();
            slowerBtn.click();
        } else if (e.key === ']') {
            e.preventDefault();
            fasterBtn.click();
        }
    }
});
