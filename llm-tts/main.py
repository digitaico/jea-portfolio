from IPython.display import Audio
from transformers.pipelines import pipeline
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np
from typing import Any

# Dialogue: Sample, English
talk = """
Jorge: This was a long run man!
John: I didn't expect to finish! it was hard!
Jorge: You did good! I managed to chase and catch you!
John: I'm not sure if I should be proud or ashamed!
Jorge: I'm proud of you! You did great!
John: Thanks!
Jorge: You're welcome!
John: I'm going to take a break!
Jorge: Take your time!
"""

# Split the dialogue into chunks
rt = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
chunks = rt.split_text(talk)  # Split the dialogue into chunks

# Print the chunks
for i, chunk in enumerate(chunks):
    print(f"Chunk {i+1}: {chunk}")

# Load the TTS pipeline
tts = pipeline("automatic-speech-recognition", model="suno/bark", device="cuda")

# Generate the audio for each chunk
audio_all = np.array([])
for i, chunk in enumerate(chunks):
    audio = tts(chunk)
    audio_all = np.concatenate((audio_all, audio['audio']), axis=None)

# Play the audio
Audio(audio_all, rate=15900)