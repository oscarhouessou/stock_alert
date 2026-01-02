import os
import subprocess

# Ensure we have Groq API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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
    
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY est requis pour la transcription.")

    client = Groq(api_key=GROQ_API_KEY)
    
    # Convert to WAV first
    wav_path = convert_to_wav(audio_path)
    
    try:
        with open(wav_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(wav_path), audio_file.read()),
                model="whisper-large-v3",
                language="fr",
                response_format="text"
            )
        return transcription.strip()
    finally:
        # Clean up
        if os.path.exists(wav_path):
            os.remove(wav_path)


def transcribe_audio(audio_path: str) -> str:
    """Main transcription function - uses Groq backend"""
    print(f"[TRANSCRIBER] Using Groq API for transcription")
    return transcribe_with_groq(audio_path)
