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
    bpm = 175
    loop_length = 16
    loop_array = list(range(loop_length)) 
    
    defaultBaseBeats = [0, 4, 8, 11, 13]
    defaultHiHatBeats = [0, 2, 4, 6, 8, 10, 12, 14]
    defaultSnareBeats = [2, 6, 7, 10, 14]
    defaultSizzleBeats = [0, 2, 4, 6, 8, 10, 12, 14]
    defaultBassGuitarBeats = [0, 2, 4, 6, 8, 10, 12, 14]
    tracks = [
        {'track_id': 1, 'beats': defaultBaseBeats, 'name': 'Bass Drum'},
        {'track_id': 2, 'beats': defaultHiHatBeats, 'name': 'Hi-Hat'},
        {'track_id': 3, 'beats': defaultSnareBeats, 'name': 'Snare Drum'},
        {'track_id': 4, 'beats': defaultSizzleBeats, 'name': 'Open Hi-Hat'},
        {'track_id': 5, 'beats': defaultBassGuitarBeats, 'name': 'Bass Guitar'},
    ]
    base_config = defaultBaseBeats
    hihat_config = defaultHiHatBeats
    snare_config = defaultSnareBeats
    sizzle_config = defaultSizzleBeats
    bass_guitar_config = defaultBassGuitarBeats
    generateAudioTrack(bpm, base_config, hihat_config, snare_config, sizzle_config, bass_guitar_config)
    
    audio_folder = os.path.join(settings.MEDIA_ROOT, 'audio')
    audio_files = glob.glob(os.path.join(audio_folder, '*final*.wav'))
    audio_files = [os.path.relpath(file, settings.MEDIA_ROOT) for file in audio_files]

    return render(request, 'landing.html', {
        'audio_files': audio_files,
        'tracks': tracks,
        'loop_array': loop_array,
        'bpm': bpm
    })
    
def generate_audio_sequence(beats_config, short_audio_clip, audio_clip, silence_clip, beats_per_measure):
    sequence = []
    for i in range(beats_per_measure):
        if i in beats_config:
            if i + 1 not in beats_config:
                sequence.append(audio_clip)
            else:
                sequence.append(short_audio_clip)
        elif i - 1 in beats_config:
            continue
        else:
            sequence.append(silence_clip)
    return sequence
  
def generateAudioTrack(bpm, bass_config, hihat_config, snare_config, sizzle_config, bass_guitar_config):
    beats_per_minute  = bpm * 2
    beats_per_measure  = 16
    ms_per_beat  = (60 * 1000) / (beats_per_minute )
    
    silent_sample = "media/audio/silence_beat.wav"
    silence_bit = AudioSegment.silent(duration=ms_per_beat)
    silence_bit.export(silent_sample, format="wav")
    
    high_bass_guitar = "media/audio/high_bass_guitar.wav"
    change_pitch("media/audio/keys/korg-esx-fx-bass-2.wav", high_bass_guitar, 0)
    
    bass_drums = process_track("bass", bass_config, "media/audio/drums/kick-big.wav", ms_per_beat)
    hihats = process_track("hihat", hihat_config, "media/audio/drums/hihat-plain.wav", ms_per_beat)
    snares = process_track("snare", snare_config, "media/audio/drums/snare-noise.wav", ms_per_beat)
    sizzles = process_track("sizzle", sizzle_config, "media/audio/drums/openhat-tight.wav", ms_per_beat)
    bass_guitar = process_track("bass_guitar", bass_guitar_config, high_bass_guitar, ms_per_beat)

    concated_bass_drums = concatenate(bass_drums)
    concated_hihats = concatenate(hihats)
    concated_snares = concatenate(snares)
    concated_sizzles = concatenate(sizzles)
    concated_bass_guitars = concatenate(bass_guitar)

    concated_bass_drums_file = "media/audio/final_base.wav"
    concated_bass_drums.export(concated_bass_drums_file, format="wav")
    concated_hihats_file = "media/audio/final_hihats.wav"
    concated_hihats.export(concated_hihats_file, format="wav")
    concated_snares_file = "media/audio/final_snares.wav"
    concated_snares.export(concated_snares_file, format="wav")
    concated_sizzles_file = "media/audio/final_sizzles.wav"
    concated_sizzles.export(concated_sizzles_file, format="wav")
    concated_bass_guitars_file = "media/audio/final_bass_guitars.wav"
    concated_bass_guitars.export(concated_bass_guitars_file, format="wav")
    
    # plot_waveform(output_file)
    
    combined_file = "media/audio/concatenated_output3.wav"
    combine_in_parallel([
        concated_bass_drums_file,
        concated_hihats_file,
        concated_snares_file,
        concated_sizzles_file,
        concated_bass_guitars_file
    ], combined_file, ((ms_per_beat - 8) * beats_per_measure))
    
    final_output = "media/audio/final_output.wav"
    create_shortened_sample(combined_file, final_output, ((ms_per_beat - 8) * beats_per_measure))
      
  
def cloneWithEffect():
  board = Pedalboard([Distortion(), Delay(delay_seconds:=0.25), Chorus(), Reverb(room_size=1.0)])
  with AudioFile('media/audio/hihat-acoustic01.wav') as f:
    with AudioFile('media/audio/test.wav', 'w', f.samplerate, f.num_channels) as o:
      while f.tell() < f.frames:
        chunk = f.read(f.samplerate)
        
        effected = board(chunk, f.samplerate, reset=False)
        
        o.write(effected)
        
def change_pitch(input_file, output_file, semitones):
    try:
        audio = AudioSegment.from_file(input_file)
        
        playback_rate = 2 ** (semitones / 12.0)
        
        shifted_audio = audio._spawn(audio.raw_data, overrides={
            "frame_rate": int(audio.frame_rate * playback_rate)
        }).set_frame_rate(audio.frame_rate)
        
        shifted_audio.export(output_file, format="wav")
        return output_file
    except Exception as e:
        print(f"Error changing pitch: {e}")
        return None
        
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
           
def create_shortened_sample(input_file, output_file, target_length_ms):
    try:
        audio = AudioSegment.from_file(input_file)
        if len(audio) < target_length_ms:
            silence_duration = target_length_ms - len(audio)
            silence = AudioSegment.silent(duration=silence_duration)
            audio += silence
        audio = audio[:target_length_ms]
        audio.export(output_file, format="wav")
        return output_file
    except Exception as e:
        print(f"Error creating shortened sample: {e}")
        return None

def process_track(track_name, beats_config, base_file, ms_per_beat):
    short_sample = f"media/audio/short_{track_name}.wav"
    reg_sample = f"media/audio/reg_{track_name}.wav"
    silent_sample = "media/audio/silence_beat.wav"

    create_shortened_sample(base_file, short_sample, ms_per_beat)
    create_shortened_sample(base_file, reg_sample, ms_per_beat * 2)

    return generate_audio_sequence(beats_config, short_sample, reg_sample, silent_sample, 16)


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
    
# def plot_waveform(input_file):
#     audio = AudioSegment.from_file(input_file)
#     samples = np.array(audio.get_array_of_samples())
    
#     plt.figure(figsize=(10, 4))
#     plt.plot(samples)
#     plt.title(f'Waveform of {input_file}')
#     plt.xlabel('Sample')
#     plt.ylabel('Amplitude')
#     plt.show()
  
def update_audio(request):
    bpm = request.POST.get('bpm')
    base_beats = request.POST.getlist('track-1')
    hihat_beats = request.POST.getlist('track-2')
    snare_beats = request.POST.getlist('track-3')
    sizzle_beats = request.POST.getlist('track-4')
    bass_guitar_beats = request.POST.getlist('track-5')
    
    bpm = int(bpm)
    bass_config = list(map(int, base_beats))
    hihat_config = list(map(int, hihat_beats))
    snare_config = list(map(int, snare_beats))
    sizzle_config = list(map(int, sizzle_beats))
    bass_guitar_config = list(map(int, bass_guitar_beats))
    
    generateAudioTrack(bpm, bass_config, hihat_config, snare_config, sizzle_config, bass_guitar_config)
    tracks = [
        {'track_id': 1, 'beats': bass_config, 'name': 'Bass Drum'},
        {'track_id': 2, 'beats': hihat_config, 'name': 'Hi-Hat'},
        {'track_id': 3, 'beats': snare_config, 'name': 'Snare Drum'},
        {'track_id': 4, 'beats': sizzle_config, 'name': 'Open Hi-Hat'},
        {'track_id': 5, 'beats': bass_guitar_config, 'name': 'Bass Guitar'},
    ]
    loop_length = 16
    loop_array = list(range(loop_length)) 
    
    audio_folder = os.path.join(settings.MEDIA_ROOT, 'audio')
    audio_files = glob.glob(os.path.join(audio_folder, '*final*.wav'))
    audio_files = [os.path.relpath(file, settings.MEDIA_ROOT) for file in audio_files]
    
    return render(request, 'landing.html', {
        'audio_files': audio_files,
        'tracks': tracks,
        'loop_array': loop_array,
        'bpm': bpm
    })