import os
import wave
import subprocess
import numpy as np

MEME_SFX_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "RECURSOS_COMPARTIDOS"\02_efectos_sonido\memes_y_virales"
MEME_MUS_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "RECURSOS_COMPARTIDOS"\01_musica\memes_y_virales"
SR = 48000

def save_wav(filename, stereo_data):
    filepath = os.path.join(MEME_SFX_DIR, filename)
    data_clipped = np.clip(stereo_data, -0.98, 0.98)
    int_data = (data_clipped * 32767).astype(np.int16)
    with wave.open(filepath, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(int_data.tobytes())
    print(f"Created: {filename}")

# 1. Vine Boom Sound Effect (1.8s)
def gen_vine_boom():
    dur = 1.8
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Heavy pitch dive: starts at 95 Hz, drops to 32 Hz in 120ms, then sustained rumble
    f = 32.0 + 65.0 * np.exp(-t / 0.12)
    phase = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(phase)
    # Initial punch transient (clipped white noise)
    punch = np.random.uniform(-1, 1, len(t)) * np.exp(-t / 0.025) * 1.5
    # Heavy drive / distortion
    raw = sub * np.exp(-t / 0.45) * 1.8 + punch
    distorted = np.tanh(raw * 2.5) * 0.95
    stereo = np.column_stack([distorted, distorted])
    
    # Save temp and add massive cavern reverb with ffmpeg
    tmp = os.path.join(MEME_SFX_DIR, "tmp_vine.wav")
    save_wav("tmp_vine.wav", stereo)
    out = os.path.join(MEME_SFX_DIR, "vine_boom.wav")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", tmp,
           "-af", "aecho=0.9:0.8:60|120:0.5|0.3", "-ar", "48000", "-ac", "2", out]
    subprocess.run(cmd, check=True)
    if os.path.exists(tmp): os.remove(tmp)
    print("Created: vine_boom.wav (with cavern reverb)")

# 2. Record Scratch / Freeze Frame (0.8s)
def gen_record_scratch():
    dur = 0.8
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Scratch pitch curves: forward squeak then violent stop
    # Frequency ramps from 800Hz to 1800Hz then rapidly brakes to 0Hz
    t_brake = np.maximum(0, 0.4 - t) / 0.4
    f1 = 400 + 1600 * t_brake ** 2
    phase1 = 2 * np.pi * np.cumsum(f1) / SR
    squeal = np.sin(phase1) * (t < 0.4)
    # Vinyl friction noise
    noise = np.random.uniform(-1, 1, len(t)) * np.exp(-t / 0.35)
    rub = (squeal * 0.7 + noise * 0.4) * np.exp(-t / 0.28)
    # Second backwards scratch at t=0.42
    t2 = np.maximum(0, t - 0.42)
    f2 = 1200 * np.exp(-t2 / 0.08)
    phase2 = 2 * np.pi * np.cumsum(f2) / SR
    scratch2 = np.sin(phase2) * np.exp(-t2 / 0.12) * (t >= 0.42)
    
    audio = rub + scratch2 * 0.8
    audio = np.tanh(audio * 1.8) * 0.85
    stereo = np.column_stack([audio * 0.9, audio * 1.1])
    save_wav("record_scratch_freeze_frame.wav", stereo)

# 3. Dramatic Dun Dun Dun (3 hits: 2.8s)
def gen_dramatic_dun_dun():
    dur = 2.8
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    mix = np.zeros(len(t))
    
    # 3 orchestral hits at t=0.0s, t=0.55s, t=1.2s
    hit_times = [0.0, 0.55, 1.2]
    # Chord frequencies
    chords = [
        [130.81, 196.0, 261.63, 311.13],  # C minor (C3, G3, C4, Eb4)
        [146.83, 220.0, 293.66, 349.23],  # D minor (D3, A3, D4, F4)
        [155.56, 233.08, 311.13, 392.0]   # Eb major fortissimo (Eb3, Bb3, Eb4, G4)
    ]
    hit_durs = [0.45, 0.45, 1.5]
    
    for i in range(3):
        st = hit_times[i]
        hd = hit_durs[i]
        s_idx = int(st * SR)
        l_samples = int(hd * SR)
        th = np.linspace(0, hd, l_samples, endpoint=False)
        
        env = (1.0 - np.exp(-th / 0.01)) * np.exp(-th / (0.15 if i < 2 else 0.45))
        chord = chords[i]
        sig = np.zeros(l_samples)
        for f in chord:
            sig += (np.sin(2 * np.pi * f * th) * 0.5 +
                    np.sin(2 * np.pi * 2 * f * th) * 0.3 +
                    np.sin(2 * np.pi * 3 * f * th) * 0.2)
        # Timpani thump
        f_timp = 75 * np.exp(-th / 0.06) + 45
        timp = np.sin(2 * np.pi * np.cumsum(f_timp) / SR) * np.exp(-th / 0.2) * 0.8
        
        hit = (sig * 0.35 + timp * 0.6) * env * (1.2 if i == 2 else 0.85)
        end_idx = min(s_idx + l_samples, len(t))
        mix[s_idx:end_idx] += hit[:end_idx - s_idx]
        
    mix = np.tanh(mix * 1.3) * 0.9
    stereo = np.column_stack([mix, mix])
    save_wav("dramatic_dun_dun_dun.wav", stereo)

# 4. Cartoon Boing / Resorte Cómico (0.7s)
def gen_cartoon_boing():
    dur = 0.7
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Carrier rising from 220Hz to 680Hz
    f_carrier = 220.0 + 460.0 * (t / dur) ** 0.8
    # Jaw harp spring modulation (32Hz FM oscillation)
    mod = 80.0 * np.sin(2 * np.pi * 30.0 * t) * np.exp(-t / 0.4)
    phase = 2 * np.pi * np.cumsum(f_carrier + mod) / SR
    audio = np.sin(phase) * np.exp(-t / 0.32) * 0.85
    stereo = np.column_stack([audio, audio])
    save_wav("cartoon_boing_resorte.wav", stereo)

# 5. Cartoon Slap / Cachetada (0.35s)
def gen_cartoon_slap():
    dur = 0.35
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # High snap transient
    snap = np.random.uniform(-1, 1, len(t)) * np.exp(-t / 0.008) * 0.8
    # Body slap resonance (380Hz down to 140Hz)
    f = 140 + 240 * np.exp(-t / 0.03)
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * np.exp(-t / 0.045) * 0.6
    audio = np.tanh((snap + body) * 1.5) * 0.85
    stereo = np.column_stack([audio, audio])
    save_wav("cartoon_slap_cachetada.wav", stereo)

# 6. Bruh Sound Effect (0.65s)
def gen_bruh():
    dur = 0.65
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Formant frequencies for "Bruh" (vocal tract resonance: F1 ~ 500Hz, F2 ~ 1050Hz, pitch ~ 110Hz dropping to 70Hz)
    f_pitch = 70.0 + 40.0 * np.exp(-t / 0.15)
    phase_pitch = 2 * np.pi * np.cumsum(f_pitch) / SR
    voice = (np.sin(phase_pitch) * 0.6 +
             np.sin(2 * phase_pitch) * 0.35 +
             np.sin(3 * phase_pitch) * 0.2 +
             np.sin(4 * phase_pitch) * 0.1)
    # Vowel envelope
    env = (1.0 - np.exp(-t / 0.03)) * np.exp(-t / 0.25)
    audio = np.tanh(voice * env * 2.2) * 0.85
    stereo = np.column_stack([audio, audio])
    save_wav("bruh_sound_effect.wav", stereo)

# 7. Boxing Bell Ding Ding Ding (1.5s)
def gen_boxing_bell():
    dur = 1.5
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    mix = np.zeros(len(t))
    # 3 quick dings at t=0.0s, 0.22s, 0.44s
    for d in [0.0, 0.22, 0.44]:
        s_idx = int(d * SR)
        l_len = int(0.7 * SR)
        td = np.linspace(0, 0.7, l_len, endpoint=False)
        # Metallic inharmonic bell frequencies (1250Hz, 2480Hz, 3820Hz)
        bell = (np.sin(2 * np.pi * 1250 * td) * 0.6 +
                np.sin(2 * np.pi * 2480 * td) * 0.3 +
                np.sin(2 * np.pi * 3820 * td) * 0.15) * np.exp(-td / 0.18)
        strike = np.random.uniform(-1, 1, l_len) * np.exp(-td / 0.005) * 0.35
        ding = bell + strike
        end_idx = min(s_idx + l_len, len(t))
        mix[s_idx:end_idx] += ding[:end_idx - s_idx]
    stereo = np.column_stack([mix * 0.85, mix * 0.85])
    save_wav("boxing_bell_campana.wav", stereo)

# 8. Toca Toca (La Vida Loca Loca) - Brass Hook Meme Rhythm (16 seconds, 128 BPM)
def gen_toca_toca_hook():
    bpm = 128.0
    beat_dur = 60.0 / bpm
    total_sec = 15.0
    num_samples = int(SR * total_sec)
    t = np.linspace(0, total_sec, num_samples, endpoint=False)
    
    # 4-on-the-floor Eurodance kick & upbeat open hi-hat
    drums = np.zeros(num_samples)
    total_beats = int(total_sec / beat_dur)
    
    for b in range(total_beats):
        bt = b * beat_dur
        bi = int(bt * SR)
        # Punchy 909 Kick on every beat
        tk = np.linspace(0, 0.18, int(0.18 * SR), endpoint=False)
        fk = 45.0 + 130.0 * np.exp(-tk / 0.035)
        kick = np.sin(2 * np.pi * np.cumsum(fk) / SR) * np.exp(-tk / 0.07) * 0.85
        kl = len(kick)
        if bi + kl < num_samples:
            drums[bi:bi + kl] += kick
            
        # Sizzling open hi-hat on upbeat (half-beat: +0.5)
        h_idx = bi + int(0.5 * beat_dur * SR)
        th = np.linspace(0, 0.12, int(0.12 * SR), endpoint=False)
        hat = np.random.uniform(-1, 1, len(th)) * np.exp(-th / 0.04) * 0.22
        hl = len(hat)
        if h_idx + hl < num_samples:
            drums[h_idx:h_idx + hl] += hat

    # Bouncy Saxophone / Brass Hook of "Toca Toca" (Key of F#m / A)
    # The signature bouncy meme melody: F#4 - A4 - B4 - C#5 - B4 - A4 - F#4...
    # Frequencies (Hz)
    N_Fs4 = 369.99
    N_A4  = 440.0
    N_B4  = 493.88
    N_Cs5 = 554.37
    N_D5  = 587.33
    N_E5  = 659.25
    
    # Sequence of notes and durations (in 16th notes: 1 beat = 4 16ths)
    # "Hasta la vi-da lo-ca lo-ca lo-ca lo-ca"
    melody_pattern = [
        (N_Cs5, 0.25), (N_Cs5, 0.25), (N_Cs5, 0.5),   # Has-ta la vi-da
        (N_B4, 0.25),  (N_A4, 0.25),  (N_B4, 0.5),    # lo-ca lo-ca
        (N_Cs5, 0.25), (N_Cs5, 0.25), (N_Cs5, 0.5),   # lo-ca lo-ca
        (N_A4, 0.5),   (N_Fs4, 0.5),                  # to-ca to-ca
        (N_B4, 0.25),  (N_B4, 0.25),  (N_Cs5, 0.5),   # te to-ca
        (N_A4, 0.25),  (N_Fs4, 0.25), (N_A4, 0.5)     # to-ca
    ]
    
    brass_track = np.zeros(num_samples)
    curr_time = 0.0
    
    # Repeat pattern for 15 seconds
    while curr_time < total_sec - 1.0:
        for freq, dur_beats in melody_pattern:
            note_dur_s = dur_beats * beat_dur
            n_start = int(curr_time * SR)
            n_len = int(note_dur_s * SR)
            tn = np.linspace(0, note_dur_s, n_len, endpoint=False)
            
            # Bright bouncy brass / synth sax timbre
            # Square-like odd harmonics with fast brass envelope
            sig = (np.sin(2 * np.pi * freq * tn) * 0.55 +
                   np.sin(2 * np.pi * 2 * freq * tn) * 0.3 +
                   np.sin(2 * np.pi * 3 * freq * tn) * 0.25 +
                   np.sin(2 * np.pi * 4 * freq * tn) * 0.15)
            # Staccato bite envelope
            env = (1.0 - np.exp(-tn / 0.008)) * np.exp(-tn / (note_dur_s * 0.85))
            note = sig * env * 0.45
            
            end_n = min(n_start + n_len, num_samples)
            if n_start < num_samples:
                brass_track[n_start:end_n] += note[:end_n - n_start]
            curr_time += note_dur_s
            if curr_time >= total_sec - 0.5:
                break
                
    # Bouncy offbeat bass
    bass_track = np.zeros(num_samples)
    for b in range(total_beats):
        # Offbeat bass hit at beat + 0.5
        b_idx = int((b * beat_dur + 0.5 * beat_dur) * SR)
        b_len = int(0.2 * SR)
        tb = np.linspace(0, 0.2, b_len, endpoint=False)
        bass_note = np.sin(2 * np.pi * 92.5 * tb) * np.exp(-tb / 0.08) * 0.6  # F#2 bass
        if b_idx + b_len < num_samples:
            bass_track[b_idx:b_idx + b_len] += bass_note

    mix = drums * 0.65 + brass_track * 0.7 + bass_track * 0.5
    mix = np.tanh(mix * 1.3) * 0.85
    stereo = np.column_stack([mix, mix])
    
    tmp_wav = os.path.join(MEME_MUS_DIR, "tmp_toca.wav")
    out_mp3 = os.path.join(MEME_MUS_DIR, "Toca_Toca_La_Vida_Loca_Hook.mp3")
    
    int_data = (np.clip(stereo, -0.98, 0.98) * 32767).astype(np.int16)
    with wave.open(tmp_wav, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(int_data.tobytes())
        
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", tmp_wav, "-b:a", "192k", out_mp3]
    subprocess.run(cmd, check=True)
    if os.path.exists(tmp_wav): os.remove(tmp_wav)
    print("Created: Toca_Toca_La_Vida_Loca_Hook.mp3")

if __name__ == "__main__":
    os.makedirs(MEME_SFX_DIR, exist_ok=True)
    os.makedirs(MEME_MUS_DIR, exist_ok=True)
    gen_vine_boom()
    gen_record_scratch()
    gen_dramatic_dun_dun()
    gen_cartoon_boing()
    gen_cartoon_slap()
    gen_bruh()
    gen_boxing_bell()
    gen_toca_toca_hook()
    print("All viral meme assets completed!")
