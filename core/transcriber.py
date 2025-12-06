from faster_whisper import WhisperModel
import os
import subprocess
import tempfile

# Use local model path (downloaded manually)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "faster-whisper-small")
model = None

def get_model():
    global model
    if model is None:
        print(f"[TRANSCRIBER] Loading Whisper model from: {MODEL_PATH}")
        model = WhisperModel(MODEL_PATH, device="cpu", compute_type="int8")
        print(f"[TRANSCRIBER] Model loaded successfully!")
    return model

def convert_to_wav(input_path: str) -> str:
    """
    Convert audio file to WAV format using FFmpeg.
    Returns path to the converted file.
    """
    output_path = input_path.rsplit('.', 1)[0] + '_converted.wav'
    
    print(f"[TRANSCRIBER] Converting {input_path} to WAV...")
    
    try:
        result = subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-ar', '16000',  # 16kHz sample rate (optimal for Whisper)
            '-ac', '1',      # Mono
            '-c:a', 'pcm_s16le',  # 16-bit PCM
            output_path
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"[TRANSCRIBER] FFmpeg error: {result.stderr}")
            return input_path  # Return original if conversion fails
            
        print(f"[TRANSCRIBER] Converted successfully to: {output_path}")
        return output_path
        
    except FileNotFoundError:
        print("[TRANSCRIBER] WARNING: FFmpeg not found, using original file")
        return input_path
    except Exception as e:
        print(f"[TRANSCRIBER] Conversion error: {e}")
        return input_path

def transcribe_audio(file_path: str) -> str:
    """
    Transcribes audio file to text.
    """
    print(f"[TRANSCRIBER] Transcribing file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"[TRANSCRIBER] ERROR: File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_size = os.path.getsize(file_path)
    print(f"[TRANSCRIBER] File size: {file_size} bytes")
    
    # Convert to WAV if needed (webm/other formats don't work well)
    wav_path = file_path
    if not file_path.endswith('.wav'):
        wav_path = convert_to_wav(file_path)
    
    # DEBUG: Save a copy for investigation
    debug_dir = os.path.join(os.path.dirname(__file__), "..", "debug_audio")
    os.makedirs(debug_dir, exist_ok=True)
    import shutil
    debug_wav = os.path.join(debug_dir, "last_recording.wav")
    debug_webm = os.path.join(debug_dir, "last_recording.webm")
    shutil.copy(wav_path, debug_wav)
    shutil.copy(file_path, debug_webm)
    print(f"[TRANSCRIBER] DEBUG: Saved copies to {debug_dir}")
    
    whisper = get_model()
    print(f"[TRANSCRIBER] Starting transcription...")
    
    segments, info = whisper.transcribe(wav_path, beam_size=5, language="fr")
    
    text = ""
    for segment in segments:
        print(f"[TRANSCRIBER] Segment: '{segment.text}' (start={segment.start:.1f}s, end={segment.end:.1f}s)")
        text += segment.text + " "
    
    # Cleanup converted file (but not debug copies)
    if wav_path != file_path and os.path.exists(wav_path) and wav_path != debug_wav:
        os.remove(wav_path)
    
    result = text.strip()
    print(f"[TRANSCRIBER] Final result: '{result}'")
    return result
