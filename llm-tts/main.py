from IPython.display import Audio
from transformers.pipelines import pipeline
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np
from typing import Any
from scipy.io import wavfile

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
tts: Any = pipeline("text-to-speech", model="suno/bark", device="cuda")  # type: ignore[arg-type]

# Generate the audio for each chunk and collect sampling rate
audio_all = np.array([])
sampling_rate = None
for i, chunk in enumerate(chunks):
    audio = tts(chunk)
    # Capture the sampling rate from the first chunk
    if sampling_rate is None:
        sampling_rate = audio["sampling_rate"]
    audio_all = np.concatenate((audio_all, audio["audio"]), axis=None)

# Save the concatenated audio to a WAV file
if sampling_rate is None:
    raise ValueError("Sampling rate was not returned by the TTS pipeline.")

wavfile.write("dialogue_output.wav", sampling_rate, audio_all.astype(np.float32))
print("Audio saved to dialogue_output.wav")