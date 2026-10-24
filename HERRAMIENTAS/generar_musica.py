import os
import wave
import subprocess
import numpy as np

OUTPUT_DIR = r"C:\Users\marx_\OneDrive\Documentos\Proyecto predeterminado\EditorVideo\RECURSOS_COMPARTIDOS\01_musica"
SR = 48000

def export_mp3(wav_path, mp3_path):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", wav_path, "-b:a", "192k", mp3_path]
    subprocess.run(cmd, check=True)
    if os.path.exists(wav_path):
        os.remove(wav_path)
    print(f"Exported: {os.path.basename(mp3_path)}")

# 1. Lo-Fi Chill Study Beat (60 seconds, 75 BPM)
def gen_lofi_beat():
    bpm = 75.0
    beat_dur = 60.0 / bpm
    total_sec = 60.0
    num_samples = int(SR * total_sec)
    t = np.linspace(0, total_sec, num_samples, endpoint=False)
    
    # Vinyl crackle background
    crackle = np.random.uniform(-1, 1, num_samples)
    # Sparse crackle pops
    dust = (np.random.uniform(0, 1, num_samples) > 0.9992).astype(float) * np.random.uniform(-0.4, 0.4, num_samples)
    vinyl = (crackle * 0.015 + dust) * 0.4
    
    # Rhodes Chord Progression (Dm7 - G7 - Cmaj7 - Am7) in 4-bar cycles (16 beats)
    # Chord frequencies (Hz)
    chords = [
        [146.83, 220.0, 261.63, 349.23],  # Dm7 (D3, A3, C4, F4)
        [196.0, 246.94, 293.66, 349.23],  # G7 (G3, B3, D4, F4)
        [130.81, 196.0, 261.63, 329.63],  # Cmaj7 (C3, G3, C4, E4)
        [110.0, 164.81, 220.0, 261.63],   # Am7 (A2, E3, A3, C4)
    ]
    
    chords_track = np.zeros(num_samples)
    cycle_beats = 16
    cycle_sec = cycle_beats * beat_dur
    
    # Generate warm Rhodes electric piano tones
    for bar in range(int(total_sec / (4 * beat_dur)) + 1):
        chord_idx = bar % 4
        bar_start_t = bar * 4 * beat_dur
        bar_start_sample = int(bar_start_t * SR)
        bar_len_sample = int(4 * beat_dur * SR)
        
        chord_notes = chords[chord_idx]
        tb = np.linspace(0, 4 * beat_dur, bar_len_sample, endpoint=False)
        # Soft envelope: attack 15ms, exponential decay
        env = (1.0 - np.exp(-tb / 0.02)) * (0.4 + 0.6 * np.exp(-tb / 1.8))
        
        bar_signal = np.zeros(bar_len_sample)
        for freq in chord_notes:
            # Fundamental + soft 2nd & 3rd harmonic
            tone = (np.sin(2 * np.pi * freq * tb) * 0.6 +
                    np.sin(2 * np.pi * freq * 2 * tb) * 0.25 +
                    np.sin(2 * np.pi * freq * 3 * tb) * 0.1)
            bar_signal += tone
            
        bar_signal *= env
        end_idx = min(bar_start_sample + bar_len_sample, num_samples)
        add_len = end_idx - bar_start_sample
        if add_len > 0:
            chords_track[bar_start_sample:end_idx] += bar_signal[:add_len]
            
    chords_track = np.tanh(chords_track * 0.35) * 0.45
    
    # Lo-Fi Drum Loop (Kick, Snare, Hi-Hat)
    drums_track = np.zeros(num_samples)
    total_beats = int(total_sec / beat_dur)
    
    for beat in range(total_beats):
        bt_t = beat * beat_dur
        bt_sample = int(bt_t * SR)
        bt_mod = beat % 4
        
        # Kick on beats 0 and 2.5
        if bt_mod == 0:
            k_len = int(0.25 * SR)
            tk = np.linspace(0, 0.25, k_len, endpoint=False)
            fk = 55 + 110 * np.exp(-tk / 0.04)
            kick = np.sin(2 * np.pi * np.cumsum(fk) / SR) * np.exp(-tk / 0.09) * 0.7
            drums_track[bt_sample:min(bt_sample + k_len, num_samples)] += kick[:min(k_len, num_samples - bt_sample)]
            
        if bt_mod == 2:
            # Syncopated kick at beat 2.5
            k_start = bt_sample + int(0.5 * beat_dur * SR)
            k_len = int(0.25 * SR)
            tk = np.linspace(0, 0.25, k_len, endpoint=False)
            fk = 55 + 110 * np.exp(-tk / 0.04)
            kick = np.sin(2 * np.pi * np.cumsum(fk) / SR) * np.exp(-tk / 0.09) * 0.6
            if k_start < num_samples:
                drums_track[k_start:min(k_start + k_len, num_samples)] += kick[:min(k_len, num_samples - k_start)]

        # Soft Rim / Snare on beats 1 and 3
        if bt_mod in [1, 3]:
            s_len = int(0.18 * SR)
            ts = np.linspace(0, 0.18, s_len, endpoint=False)
            snare_noise = np.random.uniform(-1, 1, s_len) * np.exp(-ts / 0.04) * 0.35
            snare_body = np.sin(2 * np.pi * 180 * ts) * np.exp(-ts / 0.03) * 0.3
            snare = snare_noise + snare_body
            drums_track[bt_sample:min(bt_sample + s_len, num_samples)] += snare[:min(s_len, num_samples - bt_sample)]

        # Closed Hi-Hat on every 8th note
        for sub in [0, 0.5]:
            h_start = bt_sample + int(sub * beat_dur * SR)
            h_len = int(0.06 * SR)
            th = np.linspace(0, 0.06, h_len, endpoint=False)
            hat = np.random.uniform(-1, 1, h_len) * np.exp(-th / 0.015) * 0.12
            if h_start < num_samples:
                drums_track[h_start:min(h_start + h_len, num_samples)] += hat[:min(h_len, num_samples - h_start)]

    # Sub-bass (smooth 808/Moog line)
    bass_track = np.zeros(num_samples)
    bass_notes = [73.42, 98.0, 65.41, 55.0]  # D2, G2, C2, A1
    for bar in range(int(total_sec / (4 * beat_dur)) + 1):
        chord_idx = bar % 4
        bar_start_t = bar * 4 * beat_dur
        bar_start_sample = int(bar_start_t * SR)
        bar_len_sample = int(4 * beat_dur * SR)
        
        freq = bass_notes[chord_idx]
        tb = np.linspace(0, 4 * beat_dur, bar_len_sample, endpoint=False)
        env = (1.0 - np.exp(-tb / 0.03)) * (0.5 + 0.5 * np.exp(-tb / 2.5))
        bass_sig = np.sin(2 * np.pi * freq * tb) * env * 0.5
        end_idx = min(bar_start_sample + bar_len_sample, num_samples)
        add_len = end_idx - bar_start_sample
        if add_len > 0:
            bass_track[bar_start_sample:end_idx] += bass_sig[:add_len]

    # Mix tracks together
    mix = (chords_track * 0.65 + drums_track * 0.55 + bass_track * 0.5 + vinyl * 0.15)
    # Master limiter / soft clip
    mix = np.tanh(mix * 1.2) * 0.85
    
    # Smooth stereo spread
    left = mix * 0.95 + chords_track * 0.05
    right = mix * 0.95 - chords_track * 0.05
    stereo = np.column_stack([left, right])
    
    wav_tmp = os.path.join(OUTPUT_DIR, "lofi_tmp.wav")
    int_data = (np.clip(stereo, -0.98, 0.98) * 32767).astype(np.int16)
    with wave.open(wav_tmp, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(int_data.tobytes())
        
    export_mp3(wav_tmp, os.path.join(OUTPUT_DIR, "Lofi_Chill_Study_Beat.mp3"))

# 2. Ambient Documentary Pad (60 seconds, cinematic atmospheric)
def gen_ambient_documentary():
    total_sec = 60.0
    num_samples = int(SR * total_sec)
    t = np.linspace(0, total_sec, num_samples, endpoint=False)
    
    # Ethereal layered chords (F# minor - D major - A major - E major)
    chord_freqs = [
        [92.50, 138.59, 185.0, 220.0, 277.18],   # F#m (F#2, C#3, F#3, A3, C#4)
        [73.42, 146.83, 185.0, 220.0, 293.66],   # D (D2, D3, F#3, A3, D4)
        [110.0, 164.81, 220.0, 277.18, 329.63],  # A (A2, E3, A3, C#4, E4)
        [82.41, 123.47, 164.81, 246.94, 329.63]  # E (E2, B2, E3, B3, E4)
    ]
    
    mix_left = np.zeros(num_samples)
    mix_right = np.zeros(num_samples)
    
    chord_dur = 15.0  # 15s per chord
    for i in range(4):
        c_start = int(i * chord_dur * SR)
        c_len = int(chord_dur * SR)
        tc = np.linspace(0, chord_dur, c_len, endpoint=False)
        # Slow swells (fade in and fade out envelope)
        env = np.sin(np.pi * tc / chord_dur) ** 1.5
        
        freqs = chord_freqs[i]
        c_left = np.zeros(c_len)
        c_right = np.zeros(c_len)
        
        for idx, f in enumerate(freqs):
            # Subtle detune for shimmer / chorus
            detune = 0.3 * (idx % 2 * 2 - 1)
            # Gentle vibrato
            vib = np.sin(2 * np.pi * 0.2 * tc) * 0.15
            sig_l = np.sin(2 * np.pi * (f + detune + vib) * tc)
            sig_r = np.sin(2 * np.pi * (f - detune - vib) * tc)
            c_left += sig_l
            c_right += sig_r
            
        c_left *= env * 0.18
        c_right *= env * 0.18
        
        end_idx = min(c_start + c_len, num_samples)
        mix_left[c_start:end_idx] += c_left[:end_idx - c_start]
        mix_right[c_start:end_idx] += c_right[:end_idx - c_start]
        
    # Gentle warm sub-rumble
    sub = np.sin(2 * np.pi * 46.25 * t) * 0.15
    mix_left += sub
    mix_right += sub
    
    mix_left = np.tanh(mix_left * 1.1) * 0.75
    mix_right = np.tanh(mix_right * 1.1) * 0.75
    stereo = np.column_stack([mix_left, mix_right])
    
    wav_tmp = os.path.join(OUTPUT_DIR, "ambient_tmp.wav")
    int_data = (np.clip(stereo, -0.98, 0.98) * 32767).astype(np.int16)
    with wave.open(wav_tmp, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(int_data.tobytes())
        
    export_mp3(wav_tmp, os.path.join(OUTPUT_DIR, "Ambient_Documentary_Pad.mp3"))

# 3. Acoustic Warmth Minimal (45 seconds, gentle acoustic vibe)
def gen_acoustic_minimal():
    bpm = 100.0
    beat_dur = 60.0 / bpm
    total_sec = 48.0
    num_samples = int(SR * total_sec)
    t = np.linspace(0, total_sec, num_samples, endpoint=False)
    
    # Plucked acoustic guitar emulation using Karplus-Strong / filtered decaying sines
    chord_patterns = [
        [261.63, 329.63, 392.0, 523.25],  # C major
        [196.0, 246.94, 293.66, 392.0],   # G major
        [220.0, 261.63, 329.63, 440.0],   # A minor
        [174.61, 220.0, 261.63, 349.23]   # F major
    ]
    
    mix = np.zeros(num_samples)
    total_beats = int(total_sec / beat_dur)
    
    for beat in range(total_beats):
        bar = beat // 4
        chord_idx = bar % 4
        notes = chord_patterns[chord_idx]
        
        # Arpeggiate notes on 16th steps
        for step in range(4):
            note_idx = (beat * 4 + step) % len(notes)
            freq = notes[note_idx]
            n_start = int((beat * beat_dur + step * (beat_dur / 4)) * SR)
            n_len = int(0.7 * SR)
            tn = np.linspace(0, 0.7, n_len, endpoint=False)
            
            # String pluck harmonic spectrum
            pluck = (np.sin(2 * np.pi * freq * tn) * 0.6 +
                     np.sin(2 * np.pi * freq * 2 * tn) * 0.25 +
                     np.sin(2 * np.pi * freq * 3 * tn) * 0.15) * np.exp(-tn / 0.18)
            
            if n_start < num_samples:
                mix[n_start:min(n_start + n_len, num_samples)] += pluck[:min(n_len, num_samples - n_start)] * 0.25

    # Subtle shaker on 8th notes
    for beat in range(total_beats):
        for sub in [0, 0.5]:
            sh_start = int((beat * beat_dur + sub * beat_dur) * SR)
            sh_len = int(0.08 * SR)
            tsh = np.linspace(0, 0.08, sh_len, endpoint=False)
            shaker = np.random.uniform(-1, 1, sh_len) * np.exp(-tsh / 0.02) * 0.04
            if sh_start < num_samples:
                mix[sh_start:min(sh_start + sh_len, num_samples)] += shaker[:min(sh_len, num_samples - sh_start)]

    mix = np.tanh(mix * 1.2) * 0.75
    stereo = np.column_stack([mix, mix])
    
    wav_tmp = os.path.join(OUTPUT_DIR, "acoustic_tmp.wav")
    int_data = (np.clip(stereo, -0.98, 0.98) * 32767).astype(np.int16)
    with wave.open(wav_tmp, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(int_data.tobytes())
        
    export_mp3(wav_tmp, os.path.join(OUTPUT_DIR, "Acoustic_Warmth_Minimal.mp3"))

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    gen_lofi_beat()
    gen_ambient_documentary()
    gen_acoustic_minimal()
    print("All 3 music tracks generated successfully!")
