# project-for-adc-2026

0. Installing dependencies
```
python -m venv .venv
.venv/bin/activate
```

1. Building and preparing Microsoft VibeVoice ASR

```bash
mkdir vibeasr-build && cd vibeasr-build
git clone --recursive https://github.com/microsoft/VibeASR.cpp.git
cd VibeASR.cpp

# Build
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc)

cd ../..

# Download pre-quantized models
pip install huggingface_hub
huggingface-cli download microsoft/VibeVoice-ASR-BitNet --local-dir models/vibeasr

# Copy executables to the vibeasr_bin dir
cp -r vibeasr-build/VibeASR.cpp/build/bin -r vibeasr_bin
```

2. Testing the VibeVoice inference server
```bash
./vibeasr_bin/asr_stream_server --vae-model models/vibeasr/vibeasr-vae-encoder-i8_s.gguf --lm-model models/vibeasr/vibeasr-lm-i2_s-embed-q6_k.gguf
```