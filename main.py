import os
import librosa
from librosa import display
import matplotlib.pyplot as plt

os.environ["LIBROSA_DATA_DIR"] = "data_files"


array, sampling_rate = librosa.load(librosa.ex("trumpet"))

plt.figure(figsize=(12, 2))
display.waveshow(array, sr=sampling_rate)
plt.show()

print(sampling_rate)
