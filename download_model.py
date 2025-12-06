#!/usr/bin/env python3
"""
Pre-download the Whisper 'tiny' model
"""
import os

print("=" * 50)
print("Starting download of Whisper model 'small'...")
print("This only needs to be done once (~500MB).")
print("=" * 50)

print("\nLoading faster-whisper...")
from faster_whisper import WhisperModel

print("Initializing model (downloading if needed)...")
model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

print("\n" + "=" * 50)
print("✅ Model downloaded and ready!")
print("=" * 50)
print("\nYou can now run: ./run.sh")