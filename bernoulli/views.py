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
    loop_length = 32
    loop_array = list(range(loop_length)) 
    
    defaultBaseBeats = [0, 4, 8, 11, 13, 16, 20, 24, 27, 29]
    defaultHiHatBeats = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
    defaultSnareBeats = [2, 6, 7, 10, 14, 18, 24, 25, 28]
    defaultSizzleBeats = [6, 14, 22, 30]
    bass_guitar_config = [
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        []
    ]
    keyboard_config = [
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        []
    ]
    base_config = defaultBaseBeats
    hihat_config = defaultHiHatBeats
    snare_config = defaultSnareBeats
    sizzle_config = defaultSizzleBeats
    
    tracks = [
        {'track_id': 1, 'beats': [defaultHiHatBeats], 'name': 'Hi-Hat'},
        {'track_id': 2, 'beats': [defaultSizzleBeats], 'name': 'Open Hi-Hat'},
        {'track_id': 3, 'beats': [defaultSnareBeats], 'name': 'Snare Drum'},
        {'track_id': 4, 'beats': [defaultBaseBeats], 'name': 'Bass Drum'},
        {'track_id': 5, 'beats': bass_guitar_config, 'name': 'Bass Guitar'},
        {'track_id': 6, 'beats': keyboard_config, 'name': 'Keyboard'},
    ]
    
    generateAudioTrack(bpm, [base_config], [hihat_config], [snare_config], [sizzle_config], bass_guitar_config, keyboard_config)
    
    audio_folder = os.path.join(settings.MEDIA_ROOT, 'audio')
    audio_files = glob.glob(os.path.join(audio_folder, '*final_output.wav'))
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
  
def generateAudioTrack(bpm, bass_config, hihat_config, snare_config, sizzle_config, bass_guitar_config, keyboard_config):
    beats_per_minute  = bpm * 2
    beats_per_measure  = 32
    ms_per_beat  = (60 * 1000) / (beats_per_minute )
    
    silent_sample = "media/audio/silence_beat.wav"
    silence_bit = AudioSegment.silent(duration=ms_per_beat)
    silence_bit.export(silent_sample, format="wav")
    
    for i in range(13, 0, -1):
        change_pitch(
            "media/audio/keys/korg-esx-fx-bass-2.wav", 
            f"media/audio/bass_guitar/pitch{i}.wav", 
            i
        )
        change_pitch(
            "media/audio/keys/krushfunk-synth-key-loud-2.wav", 
            f"media/audio/keys/pitch{i}.wav", 
            i
        )

    bass_guitar_tone_samples = [
        f"media/audio/bass_guitar/pitch{i}.wav" for i in range(13, -1, -1)
    ]
    keyboard_tone_samples = [
        f"media/audio/keys/pitch{i}.wav" for i in range(13, -1, -1)
    ]
    
    bass_drums = process_track("bass", bass_config[0], "media/audio/drums/kick-big.wav", ms_per_beat)
    hihats = process_track("hihat", hihat_config[0], "media/audio/drums/hihat-plain.wav", ms_per_beat)
    snares = process_track("snare", snare_config[0], "media/audio/drums/snare-noise.wav", ms_per_beat)
    sizzles = process_track("sizzle", sizzle_config[0], "media/audio/drums/openhat-tight.wav", ms_per_beat)
    bass_guitar = [
        process_track("bass-guitar-0", bass_guitar_config[0], bass_guitar_tone_samples[0], ms_per_beat),
        process_track("bass-guitar-1", bass_guitar_config[1], bass_guitar_tone_samples[1], ms_per_beat),
        process_track("bass-guitar-2", bass_guitar_config[2], bass_guitar_tone_samples[2], ms_per_beat),
        process_track("bass-guitar-3", bass_guitar_config[3], bass_guitar_tone_samples[3], ms_per_beat),
        process_track("bass-guitar-4", bass_guitar_config[4], bass_guitar_tone_samples[4], ms_per_beat),
        process_track("bass-guitar-5", bass_guitar_config[5], bass_guitar_tone_samples[5], ms_per_beat),
        process_track("bass-guitar-6", bass_guitar_config[6], bass_guitar_tone_samples[6], ms_per_beat),
        process_track("bass-guitar-7", bass_guitar_config[7], bass_guitar_tone_samples[7], ms_per_beat),
        process_track("bass-guitar-8", bass_guitar_config[8], bass_guitar_tone_samples[8], ms_per_beat),
        process_track("bass-guitar-9", bass_guitar_config[9], bass_guitar_tone_samples[9], ms_per_beat),
        process_track("bass-guitar-10", bass_guitar_config[10], bass_guitar_tone_samples[10], ms_per_beat),
        process_track("bass-guitar-11", bass_guitar_config[11], bass_guitar_tone_samples[11], ms_per_beat),
        process_track("bass-guitar-12", bass_guitar_config[12], bass_guitar_tone_samples[12], ms_per_beat),
    ]
    keyboard = [
        process_track("keyboard-0", keyboard_config[0], keyboard_tone_samples[0], ms_per_beat),
        process_track("keyboard-1", keyboard_config[1], keyboard_tone_samples[1], ms_per_beat),
        process_track("keyboard-2", keyboard_config[2], keyboard_tone_samples[2], ms_per_beat),
        process_track("keyboard-3", keyboard_config[3], keyboard_tone_samples[3], ms_per_beat),
        process_track("keyboard-4", keyboard_config[4], keyboard_tone_samples[4], ms_per_beat),
        process_track("keyboard-5", keyboard_config[5], keyboard_tone_samples[5], ms_per_beat),
        process_track("keyboard-6", keyboard_config[6], keyboard_tone_samples[6], ms_per_beat),
        process_track("keyboard-7", keyboard_config[7], keyboard_tone_samples[7], ms_per_beat),
        process_track("keyboard-8", keyboard_config[8], keyboard_tone_samples[8], ms_per_beat),
        process_track("keyboard-9", keyboard_config[9], keyboard_tone_samples[9], ms_per_beat),
        process_track("keyboard-10", keyboard_config[10], keyboard_tone_samples[10], ms_per_beat),
        process_track("keyboard-11", keyboard_config[11], keyboard_tone_samples[11], ms_per_beat),
        process_track("keyboard-12", keyboard_config[12], keyboard_tone_samples[12], ms_per_beat),
    ]

    concated_bass_drums = concatenate(bass_drums)
    concated_hihats = concatenate(hihats)
    concated_snares = concatenate(snares)
    concated_sizzles = concatenate(sizzles)
    concated_bass_guitars = [
        concatenate(bass_guitar[0]),
        concatenate(bass_guitar[1]),
        concatenate(bass_guitar[2]),
        concatenate(bass_guitar[3]),
        concatenate(bass_guitar[4]),
        concatenate(bass_guitar[5]),
        concatenate(bass_guitar[6]),
        concatenate(bass_guitar[7]),
        concatenate(bass_guitar[8]),
        concatenate(bass_guitar[9]),
        concatenate(bass_guitar[10]),
        concatenate(bass_guitar[11]),
        concatenate(bass_guitar[12]),
    ]
    concated_keyboard = [
        concatenate(keyboard[0]),
        concatenate(keyboard[1]),
        concatenate(keyboard[2]),
        concatenate(keyboard[3]),
        concatenate(keyboard[4]),
        concatenate(keyboard[5]),
        concatenate(keyboard[6]),
        concatenate(keyboard[7]),
        concatenate(keyboard[8]),
        concatenate(keyboard[9]),
        concatenate(keyboard[10]),
        concatenate(keyboard[11]),
        concatenate(keyboard[12]),
    ]

    concated_bass_drums_file = "media/audio/final_base.wav"
    concated_bass_drums.export(concated_bass_drums_file, format="wav")
    concated_hihats_file = "media/audio/final_hihats.wav"
    concated_hihats.export(concated_hihats_file, format="wav")
    concated_snares_file = "media/audio/final_snares.wav"
    concated_snares.export(concated_snares_file, format="wav")
    concated_sizzles_file = "media/audio/final_sizzles.wav"
    concated_sizzles.export(concated_sizzles_file, format="wav")
    concated_bass_guitars[0].export("media/audio/bass_guitar/final-0.wav", format="wav")
    concated_bass_guitars[1].export("media/audio/bass_guitar/final-1.wav", format="wav")
    concated_bass_guitars[2].export("media/audio/bass_guitar/final-2.wav", format="wav")
    concated_bass_guitars[3].export("media/audio/bass_guitar/final-3.wav", format="wav")
    concated_bass_guitars[4].export("media/audio/bass_guitar/final-4.wav", format="wav")
    concated_bass_guitars[5].export("media/audio/bass_guitar/final-5.wav", format="wav")
    concated_bass_guitars[6].export("media/audio/bass_guitar/final-6.wav", format="wav")
    concated_bass_guitars[7].export("media/audio/bass_guitar/final-7.wav", format="wav")
    concated_bass_guitars[8].export("media/audio/bass_guitar/final-8.wav", format="wav")
    concated_bass_guitars[9].export("media/audio/bass_guitar/final-9.wav", format="wav")
    concated_bass_guitars[10].export("media/audio/bass_guitar/final-10.wav", format="wav")
    concated_bass_guitars[11].export("media/audio/bass_guitar/final-11.wav", format="wav")
    concated_bass_guitars[12].export("media/audio/bass_guitar/final-12.wav", format="wav")
    
    concated_keyboard[0].export("media/audio/keys/final-0.wav", format="wav")
    concated_keyboard[1].export("media/audio/keys/final-1.wav", format="wav")
    concated_keyboard[2].export("media/audio/keys/final-2.wav", format="wav")
    concated_keyboard[3].export("media/audio/keys/final-3.wav", format="wav")
    concated_keyboard[4].export("media/audio/keys/final-4.wav", format="wav")
    concated_keyboard[5].export("media/audio/keys/final-5.wav", format="wav")
    concated_keyboard[6].export("media/audio/keys/final-6.wav", format="wav")
    concated_keyboard[7].export("media/audio/keys/final-7.wav", format="wav")
    concated_keyboard[8].export("media/audio/keys/final-8.wav", format="wav")
    concated_keyboard[9].export("media/audio/keys/final-9.wav", format="wav")
    concated_keyboard[10].export("media/audio/keys/final-10.wav", format="wav")
    concated_keyboard[11].export("media/audio/keys/final-11.wav", format="wav")
    concated_keyboard[12].export("media/audio/keys/final-12.wav", format="wav")
    
    # plot_waveform(output_file)
    
    combined_file = "media/audio/concatenated_output3.wav"
    combine_in_parallel([
        concated_bass_drums_file,
        concated_hihats_file,
        concated_snares_file,
        concated_sizzles_file,
        "media/audio/bass_guitar/final-0.wav",
        "media/audio/bass_guitar/final-1.wav",
        "media/audio/bass_guitar/final-2.wav",
        "media/audio/bass_guitar/final-3.wav",
        "media/audio/bass_guitar/final-4.wav",
        "media/audio/bass_guitar/final-5.wav",
        "media/audio/bass_guitar/final-6.wav",
        "media/audio/bass_guitar/final-7.wav",
        "media/audio/bass_guitar/final-8.wav",
        "media/audio/bass_guitar/final-9.wav",
        "media/audio/bass_guitar/final-10.wav",
        "media/audio/bass_guitar/final-11.wav",
        "media/audio/bass_guitar/final-12.wav",
        "media/audio/keys/final-0.wav",
        "media/audio/keys/final-1.wav",
        "media/audio/keys/final-2.wav",
        "media/audio/keys/final-3.wav",
        "media/audio/keys/final-4.wav",
        "media/audio/keys/final-5.wav",
        "media/audio/keys/final-6.wav",
        "media/audio/keys/final-7.wav",
        "media/audio/keys/final-8.wav",
        "media/audio/keys/final-9.wav",
        "media/audio/keys/final-10.wav",
        "media/audio/keys/final-11.wav",
        "media/audio/keys/final-12.wav",
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

    return generate_audio_sequence(beats_config, short_sample, reg_sample, silent_sample, 32)


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
    hihat_beats = request.POST.getlist('track-0-1')
    sizzle_beats = request.POST.getlist('track-0-2')
    snare_beats = request.POST.getlist('track-0-3')
    base_beats = request.POST.getlist('track-0-4')
    bass_guitar_config = [
        list(map(int,request.POST.getlist('track-0-5'))),
        list(map(int,request.POST.getlist('track-1-5'))),
        list(map(int,request.POST.getlist('track-2-5'))),
        list(map(int,request.POST.getlist('track-3-5'))),
        list(map(int,request.POST.getlist('track-4-5'))),
        list(map(int,request.POST.getlist('track-5-5'))),
        list(map(int,request.POST.getlist('track-6-5'))),
        list(map(int,request.POST.getlist('track-7-5'))),
        list(map(int,request.POST.getlist('track-8-5'))),
        list(map(int,request.POST.getlist('track-9-5'))),
        list(map(int,request.POST.getlist('track-10-5'))),
        list(map(int,request.POST.getlist('track-11-5'))),
        list(map(int,request.POST.getlist('track-12-5'))),
    ]
    keyboard_config = [
        list(map(int,request.POST.getlist('track-0-6'))),
        list(map(int,request.POST.getlist('track-1-6'))),
        list(map(int,request.POST.getlist('track-2-6'))),
        list(map(int,request.POST.getlist('track-3-6'))),
        list(map(int,request.POST.getlist('track-4-6'))),
        list(map(int,request.POST.getlist('track-5-6'))),
        list(map(int,request.POST.getlist('track-6-6'))),
        list(map(int,request.POST.getlist('track-7-6'))),
        list(map(int,request.POST.getlist('track-8-6'))),
        list(map(int,request.POST.getlist('track-9-6'))),
        list(map(int,request.POST.getlist('track-10-6'))),
        list(map(int,request.POST.getlist('track-11-6'))),
        list(map(int,request.POST.getlist('track-12-6'))),
    ]
    
    bpm = int(bpm)
    hihat_config = list(map(int, hihat_beats))
    sizzle_config = list(map(int, sizzle_beats))
    snare_config = list(map(int, snare_beats))
    bass_config = list(map(int, base_beats))
    
    generateAudioTrack(
        bpm,
        [bass_config],
        [hihat_config],
        [snare_config],
        [sizzle_config],
        bass_guitar_config,
        keyboard_config
    )
    tracks = [
        {'track_id': 1, 'beats': [hihat_config], 'name': 'Hi-Hat'},
        {'track_id': 2, 'beats': [sizzle_config], 'name': 'Open Hi-Hat'},
        {'track_id': 3, 'beats': [snare_config], 'name': 'Snare Drum'},
        {'track_id': 4, 'beats': [bass_config], 'name': 'Bass Drum'},
        {'track_id': 5, 'beats': bass_guitar_config, 'name': 'Bass Guitar'},
        {'track_id': 6, 'beats': keyboard_config, 'name': 'Keyboard'},
    ]
    loop_length = 32
    loop_array = list(range(loop_length)) 
    
    audio_folder = os.path.join(settings.MEDIA_ROOT, 'audio')
    audio_files = glob.glob(os.path.join(audio_folder, '*final_output.wav'))
    audio_files = [os.path.relpath(file, settings.MEDIA_ROOT) for file in audio_files]
    
    return render(request, 'landing.html', {
        'audio_files': audio_files,
        'tracks': tracks,
        'loop_array': loop_array,
        'bpm': bpm
    })