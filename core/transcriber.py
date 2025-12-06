import os
import subprocess
import tempfile

# Check if we're in production (Groq) or local (faster-whisper)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
USE_GROQ = GROQ_API_KEY is not None

# Get script directory for relative paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, "..", "models", "faster-whisper-small")
DEBUG_DIR = os.path.join(SCRIPT_DIR, "..", "debug_audio")

# Ensure debug directory exists
os.makedirs(DEBUG_DIR, exist_ok=True)


def convert_to_wav(input_path: str) -> str:
    """Convert audio file to WAV format using ffmpeg"""
    output_path = input_path.replace('.webm', '_converted.wav')
    
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-ar', '16000',
        '-ac', '1',
        '-c:a', 'pcm_s16le',
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[TRANSCRIBER] FFmpeg error: {result.stderr}")
        raise Exception(f"FFmpeg conversion failed: {result.stderr}")
    
    return output_path


def transcribe_with_groq(audio_path: str) -> str:
    """Use Groq Whisper API for transcription (production)"""
    from groq import Groq
    
    client = Groq(api_key=GROQ_API_KEY)
    
    # Convert to WAV first
    wav_path = convert_to_wav(audio_path)
    
    with open(wav_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(wav_path), audio_file.read()),
            model="whisper-large-v3",
            language="fr",
            response_format="text"
        )
    
    # Clean up
    if os.path.exists(wav_path):
        os.remove(wav_path)
    
    return transcription.strip()


def transcribe_with_whisper(audio_path: str) -> str:
    """Use local faster-whisper model for transcription (local development)"""
    from faster_whisper import WhisperModel
    
    print(f"[TRANSCRIBER] Transcribing file: {audio_path}")
    print(f"[TRANSCRIBER] File size: {os.path.getsize(audio_path)} bytes")
    
    # Convert to WAV
    print(f"[TRANSCRIBER] Converting {audio_path} to WAV...")
    wav_path = convert_to_wav(audio_path)
    print(f"[TRANSCRIBER] Converted successfully to: {wav_path}")
    
    # Save debug copies
    import shutil
    shutil.copy(audio_path, os.path.join(DEBUG_DIR, "last_recording.webm"))
    shutil.copy(wav_path, os.path.join(DEBUG_DIR, "last_recording.wav"))
    print(f"[TRANSCRIBER] DEBUG: Saved copies to {DEBUG_DIR}")
    
    # Load model
    print(f"[TRANSCRIBER] Loading Whisper model from: {MODEL_PATH}")
    model = WhisperModel(MODEL_PATH, device="cpu", compute_type="int8")
    print("[TRANSCRIBER] Model loaded successfully!")
    
    # Transcribe
    print("[TRANSCRIBER] Starting transcription...")
    segments, info = model.transcribe(wav_path, language="fr", beam_size=5)
    
    text_parts = []
    for segment in segments:
        print(f"[TRANSCRIBER] Segment: '{segment.text}' (start={segment.start:.1f}s, end={segment.end:.1f}s)")
        text_parts.append(segment.text)
    
    full_text = " ".join(text_parts).strip()
    print(f"[TRANSCRIBER] Final result: '{full_text}'")
    
    # Clean up WAV
    if os.path.exists(wav_path):
        os.remove(wav_path)
    
    return full_text


def transcribe_audio(audio_path: str) -> str:
    """Main transcription function - chooses backend based on environment"""
    print(f"[TRANSCRIBER] Using: {'Groq API' if USE_GROQ else 'faster-whisper (local)'}")
    
    if USE_GROQ:
        return transcribe_with_groq(audio_path)
    else:
        return transcribe_with_whisper(audio_path)
