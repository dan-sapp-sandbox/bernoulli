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
    loop_length = 16
    loop_array = list(range(loop_length)) 
    
    defaultBaseBeats = [0, 4, 8, 11, 13]
    defaultHiHatBeats = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    defaultSnareBeats = [2, 6, 10, 14]
    tracks = [
        {'track_id': 1, 'beats': defaultBaseBeats, 'name': 'Bass Drum'},
        {'track_id': 2, 'beats': defaultHiHatBeats, 'name': 'Hi-Hat'},
        {'track_id': 3, 'beats': defaultSnareBeats, 'name': 'Snare Drum'},
    ]
    base_config = defaultBaseBeats
    hihat_config = defaultHiHatBeats
    snare_config = defaultSnareBeats
    generateAudioTrack(base_config, hihat_config, snare_config)
    
    audio_folder = os.path.join(settings.MEDIA_ROOT, 'audio')
    audio_files = glob.glob(os.path.join(audio_folder, '*.wav'))
    audio_files = [os.path.relpath(file, settings.MEDIA_ROOT) for file in audio_files]

    return render(request, 'landing.html', {
        'audio_files': audio_files,
        'tracks': tracks,
        'loop_array': loop_array
    })
    
def generate_audio_sequence(beats_config, audio_clip, silence_clip, beats_per_measure):
    return [
        audio_clip if i in beats_config else silence_clip
        for i in range(beats_per_measure)
    ]
  
def generateAudioTrack(bass_config, hihat_config, snare_config):
    beats_per_minute  = 400
    beats_per_measure  = 16
    ms_per_beat  = (60 * 1000) / (beats_per_minute )
    
    bd= "media/audio/temp_base.wav"
    shorten_audio("media/audio/drums/kick-big.wav", bd, ms_per_beat)
    hh = "media/audio/temp_hihat.wav"
    shorten_audio("media/audio/drums/hihat-plain.wav", hh, ms_per_beat)
    sn = "media/audio/temp_snare.wav"
    shorten_audio("media/audio/drums/snare-smasher.wav", sn, ms_per_beat)
    si = "media/audio/silence_beat.wav"
    silence_bit = AudioSegment.silent(duration=ms_per_beat)
    silence_bit.export(si, format="wav")
    
    bass_drums = generate_audio_sequence(bass_config, bd, si, beats_per_measure)
    hihats = generate_audio_sequence(hihat_config, hh, si, beats_per_measure)
    snares = generate_audio_sequence(snare_config, sn, si, beats_per_measure)

    
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
    combine_in_parallel([concated_bass_drums_file, concated_hihats_file, concated_snares_file], combined_file, ((ms_per_beat - 8) * beats_per_measure))
    
    final_output = "media/audio/final_output.wav"
    shorten_audio(combined_file, final_output, ((ms_per_beat - 8) * beats_per_measure))
      
  
def cloneWithEffect():
  board = Pedalboard([Distortion(), Delay(delay_seconds:=0.25), Chorus(), Reverb(room_size=1.0)])
  with AudioFile('media/audio/hihat-acoustic01.wav') as f:
    with AudioFile('media/audio/test.wav', 'w', f.samplerate, f.num_channels) as o:
      while f.tell() < f.frames:
        chunk = f.read(f.samplerate)
        
        effected = board(chunk, f.samplerate, reset=False)
        
        o.write(effected)
        
def concatenate(audio_files, crossfade_ms=5):
    combined = AudioSegment.from_file(audio_files[0])
    
    sample_rate = combined.frame_rate
    num_channels = combined.channels

    for file in audio_files[1:]:
        audio = AudioSegment.from_file(file)
        
        if audio.frame_rate != sample_rate or audio.channels != num_channels:
            audio = audio.set_frame_rate(sample_rate).set_channels(num_channels)
        
        combined = combined.append(audio, crossfade=crossfade_ms)
    
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
    base_beats = request.POST.getlist('track-1')
    hihat_beats = request.POST.getlist('track-2')
    snare_beats = request.POST.getlist('track-3')
    bass_config = list(map(int, base_beats))
    hihat_config = list(map(int, hihat_beats))
    snare_config = list(map(int, snare_beats))
    
    generateAudioTrack(bass_config, hihat_config, snare_config)
    tracks = [
        {'track_id': 1, 'beats': bass_config, 'name': 'Bass Drum'},
        {'track_id': 2, 'beats': hihat_config, 'name': 'Hi-Hat'},
        {'track_id': 3, 'beats': snare_config, 'name': 'Snare Drum'},
    ]
    loop_length = 16
    loop_array = list(range(loop_length)) 
    
    audio_folder = os.path.join(settings.MEDIA_ROOT, 'audio')
    audio_files = glob.glob(os.path.join(audio_folder, '*.wav'))
    audio_files = [os.path.relpath(file, settings.MEDIA_ROOT) for file in audio_files]
    
    return render(request, 'landing.html', {
        'audio_files': audio_files,
        'tracks': tracks,
        'loop_array': loop_array
    })