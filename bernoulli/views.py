import json
import random
import os
import ast
import glob
from pedalboard import Pedalboard, Chorus, Reverb, Distortion, Delay
from pedalboard.io import AudioFile
from django.shortcuts import render, redirect
from django.conf import settings
from pydub import AudioSegment
import matplotlib.pyplot as plt
import numpy as np
AudioSegment.converter = "C:\ffmpeg\ffmpeg\bin\ffmpeg.exe"

def landing(request):
    
    generateAudioTrack()
    
    audio_folder = os.path.join(settings.MEDIA_ROOT, 'audio')
    audio_files = glob.glob(os.path.join(audio_folder, '*.wav'))
    audio_files = [os.path.relpath(file, settings.MEDIA_ROOT) for file in audio_files]

    return render(request, 'landing.html', {'audio_files': audio_files})
  
def generateAudioTrack():
    beatsPerMinute = 500
    beatsPerMeasure = 32
    msPerBeat = (60 * 1000) / (beatsPerMinute)
    
    bd= "media/audio/temp_base.wav"
    shorten_audio("media/audio/drums/kick-big.wav", bd, msPerBeat)
    hh = "media/audio/temp_hihat.wav"
    shorten_audio("media/audio/drums/hihat-plain.wav", hh, msPerBeat)
    sn = "media/audio/temp_snare.wav"
    shorten_audio("media/audio/drums/snare-smasher.wav", sn, msPerBeat)
    si = "media/audio/silence_beat.wav"
    silence_bit = AudioSegment.silent(duration=msPerBeat)
    silence_bit.export(si, format="wav")

    bass_config = [0, 4, 6, 12, 16, 20, 22, 28]
    bass_drums = []
    for i in range(beatsPerMeasure - 1):
        if i in bass_config:
            bass_drums.append(bd)
        else:
            bass_drums.append(si)
    hihat_config = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
    hihats = []
    for i in range(beatsPerMeasure - 1):
        if i in hihat_config:
            hihats.append(hh)
        else:
            hihats.append(si)
    snare_config = [2, 10, 18, 26]
    snares = []
    for i in range(beatsPerMeasure - 1):
        if i in snare_config:
            snares.append(sn)
        else:
            snares.append(si)
    
    concated_bass_drums = concatenate(bass_drums)
    concated_hihats = concatenate(hihats)
    concated_snares = concatenate(snares)

    concated_bass_drums_file = "media/audio/concatenated_base.wav"
    concated_bass_drums.export(concated_bass_drums_file, format="wav")
    concated_hihats_file = "media/audio/concatenated_hihats.wav"
    concated_hihats.export(concated_hihats_file, format="wav")
    concated_snares_file = "media/audio/concatenated_snares.wav"
    concated_snares.export(concated_snares_file, format="wav")
    
    # plot_waveform(output_file)
    
    combined_file = "media/audio/concatenated_output3.wav"
    combine_in_parallel([concated_bass_drums_file, concated_hihats_file, concated_snares_file], combined_file, ((msPerBeat - 8) * beatsPerMeasure))
    
    final_output = "media/audio/final_output.wav"
    shorten_audio(combined_file, final_output, ((msPerBeat - 8) * beatsPerMeasure))
      
  
def cloneWithEffect():
  board = Pedalboard([Distortion(), Delay(delay_seconds:=0.25), Chorus(), Reverb(room_size=1.0)])
  with AudioFile('media/audio/hihat-acoustic01.wav') as f:
    with AudioFile('media/audio/test.wav', 'w', f.samplerate, f.num_channels) as o:
      while f.tell() < f.frames:
        chunk = f.read(f.samplerate)
        
        effected = board(chunk, f.samplerate, reset=False)
        
        o.write(effected)
        
def concatenate(audio_files, crossfade_ms=5):
    combined = AudioSegment.empty()

    first_audio = AudioSegment.from_file(audio_files[0])
    sample_rate = first_audio.frame_rate
    num_channels = first_audio.channels

    for idx, file in enumerate(audio_files):
        audio = AudioSegment.from_file(file)

        if audio.frame_rate != sample_rate or audio.channels != num_channels:
            audio = audio.set_frame_rate(sample_rate).set_channels(num_channels)

        if idx > 0:
            combined = combined.append(audio, crossfade=crossfade_ms)
        else:
            combined += audio

    return combined

def shorten_audio(input_file, output_file, target_length_ms):
    audio = AudioSegment.from_file(input_file)
    if len(audio) < target_length_ms:
        silence_duration_ms = target_length_ms - len(audio)
        silence = AudioSegment.silent(duration=silence_duration_ms)
        audio = audio + silence
    
    audio = audio[:target_length_ms]
    
    samples = np.array(audio.get_array_of_samples())
    samples = samples.astype(np.float32) / (2 ** (audio.sample_width * 8 - 1))

    with AudioFile(output_file, 'w', samplerate=audio.frame_rate, num_channels=audio.channels) as f:
        f.write(samples)
        
def combine_in_parallel(audio_files, output_file, duration=None):
    combined = AudioSegment.from_file(audio_files[0])

    if duration:
        combined = combined[:duration]

    for file in audio_files[1:]:
        audio = AudioSegment.from_file(file)

        if duration:
            audio = audio[:duration]

        combined = combined.overlay(audio)

    combined.export(output_file, format="wav")
    
def plot_waveform(input_file):
  audio = AudioSegment.from_file(input_file)
  samples = np.array(audio.get_array_of_samples())
  
  plt.figure(figsize=(10, 4))
  plt.plot(samples)
  plt.title(f'Waveform of {input_file}')
  plt.xlabel('Sample')
  plt.ylabel('Amplitude')
  plt.show()
  
def update_audio(request):
    generateAudioTrack()
    
    audio_folder = os.path.join(settings.MEDIA_ROOT, 'audio')
    audio_files = glob.glob(os.path.join(audio_folder, '*.wav'))
    audio_files = [os.path.relpath(file, settings.MEDIA_ROOT) for file in audio_files]
    
    return render(request, 'landing.html', {'audio_files': audio_files})