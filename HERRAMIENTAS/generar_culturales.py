import os
import wave
import subprocess
import numpy as np

CULTURAL_DIR = r"C:\Users\marx_\OneDrive\Documentos\Proyecto predeterminado\EditorVideo\RECURSOS_COMPARTIDOS\02_efectos_sonido\cultural_cusco_chumbivilcas"
SR = 48000

def slice_wakawaqra():
    src = os.path.join(CULTURAL_DIR, "wakawaqra_toque_tradicional_completo.wav")
    if not os.path.exists(src):
        return
        
    # 1. Llamada corta (0s a 4.2s con fade out)
    out1 = os.path.join(CULTURAL_DIR, "wakawaqra_llamada_corta.wav")
    cmd1 = ["ffmpeg", "-y", "-loglevel", "error", "-ss", "00:00:00.0", "-to", "00:00:04.2", "-i", src,
            "-af", "afade=t=out:st=3.6:d=0.6", "-ar", "48000", "-ac", "2", out1]
    subprocess.run(cmd1, check=True)
    print("Created: wakawaqra_llamada_corta.wav")

    # 2. Diana Corrida / Rodeo (4.5s a 12.5s)
    out2 = os.path.join(CULTURAL_DIR, "wakawaqra_diana_corrida.wav")
    cmd2 = ["ffmpeg", "-y", "-loglevel", "error", "-ss", "00:00:04.5", "-to", "00:00:12.5", "-i", src,
            "-af", "afade=t=in:st=0:d=0.3,afade=t=out:st=7.4:d=0.6", "-ar", "48000", "-ac", "2", out2]
    subprocess.run(cmd2, check=True)
    print("Created: wakawaqra_diana_corrida.wav")

    # 3. Remate Takanakuy (20.0s a 26.5s)
    out3 = os.path.join(CULTURAL_DIR, "wakawaqra_remate_takanakuy.wav")
    cmd3 = ["ffmpeg", "-y", "-loglevel", "error", "-ss", "00:00:20.0", "-to", "00:00:26.5", "-i", src,
            "-af", "afade=t=in:st=0:d=0.2,afade=t=out:st=6.0:d=0.5", "-ar", "48000", "-ac", "2", out3]
    subprocess.run(cmd3, check=True)
    print("Created: wakawaqra_remate_takanakuy.wav")

    # 4. Eco Andino de Montaña (Llamada con delay de valle andino)
    out4 = os.path.join(CULTURAL_DIR, "wakawaqra_eco_andino_montana.wav")
    # Echo: in_gain 0.8, out_gain 0.7, delay 450ms, decay 0.4
    cmd4 = ["ffmpeg", "-y", "-loglevel", "error", "-i", out1,
            "-af", "aecho=0.85:0.7:450|900:0.45|0.25", "-ar", "48000", "-ac", "2", out4]
    subprocess.run(cmd4, check=True)
    print("Created: wakawaqra_eco_andino_montana.wav")

def gen_pututu():
    # Pututu (conch horn) ceremonial call (5.0 seconds)
    dur = 5.2
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Pitch swell: starts around 110Hz, rises to 124Hz (lip pressure), slight vibrato, then tapers
    f_env = 110.0 + 14.0 * np.sin(np.pi * t / dur) ** 0.8
    vib = 1.2 * np.sin(2 * np.pi * 5.0 * t)  # 5Hz lip vibrato
    phase = 2 * np.pi * np.cumsum(f_env + vib) / SR
    
    # Harmonics: fundamental + rich 2nd, 3rd, 4th, 5th, 6th
    sig = (np.sin(phase) * 1.0 +
           np.sin(2 * phase) * 0.75 +
           np.sin(3 * phase) * 0.50 +
           np.sin(4 * phase) * 0.35 +
           np.sin(5 * phase) * 0.20 +
           np.sin(6 * phase) * 0.12)
           
    # Breath air noise
    noise = np.random.uniform(-1, 1, len(t)) * 0.08
    
    # Amplitude envelope: swell in 0.8s, sustain, fade out over last 1.2s
    env = np.sin(np.pi * t / dur) ** 1.3
    audio = (sig + noise) * env * 0.7
    audio = np.tanh(audio * 1.3) * 0.85
    
    # Save stereo
    stereo = np.column_stack([audio, audio])
    tmp = os.path.join(CULTURAL_DIR, "tmp_pututu.wav")
    int_data = (np.clip(stereo, -0.98, 0.98) * 32767).astype(np.int16)
    with wave.open(tmp, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(int_data.tobytes())
        
    out = os.path.join(CULTURAL_DIR, "pututu_llamada_ceremonial_inca.wav")
    # Add natural canyon echo
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", tmp,
           "-af", "aecho=0.85:0.7:550|1100:0.4|0.2", "-ar", "48000", "-ac", "2", out]
    subprocess.run(cmd, check=True)
    if os.path.exists(tmp): os.remove(tmp)
    print("Created: pututu_llamada_ceremonial_inca.wav")

def gen_chillador():
    # Chillador chumbivilcano: metálico, agudo, rasgueo rápido de huaylia (8 segundos, 128 BPM)
    dur = 8.0
    bpm = 128.0
    beat_dur = 60.0 / bpm
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    
    # High steel string chords (Am, C, G, Em in high octaves: 440Hz, 523Hz, 659Hz, 880Hz, 1318Hz)
    chords = [
        [440.0, 523.25, 659.25, 880.0, 1318.5],    # Am
        [523.25, 659.25, 783.99, 1046.5, 1318.5],  # C
        [392.0, 493.88, 587.33, 783.99, 1174.6],   # G
        [329.63, 493.88, 659.25, 987.77, 1318.5]   # Em
    ]
    
    mix = np.zeros(len(t))
    total_beats = int(dur / beat_dur)
    
    for b in range(total_beats):
        chord_idx = (b // 4) % len(chords)
        chord_freqs = chords[chord_idx]
        
        # Chumbivilcano huaylia strum pattern: down-up-down triplets (triqui-trac)
        strum_subbeats = [0.0, 0.33, 0.66]
        for sub in strum_subbeats:
            s_time = b * beat_dur + sub * beat_dur
            s_idx = int(s_time * SR)
            s_len = int(0.22 * SR)
            ts = np.linspace(0, 0.22, s_len, endpoint=False)
            
            # Bright metallic harmonic spectrum
            strum = np.zeros(s_len)
            for f in chord_freqs:
                # Steel string harmonics (rich in 2nd, 3rd, 5th, 7th harmonics)
                tone = (np.sin(2 * np.pi * f * ts) * 0.4 +
                        np.sin(2 * np.pi * 2 * f * ts) * 0.35 +
                        np.sin(2 * np.pi * 3 * f * ts) * 0.25 +
                        np.sin(2 * np.pi * 4 * f * ts) * 0.15)
                strum += tone
                
            # Sharp steel pick attack
            pick = np.random.uniform(-1, 1, s_len) * np.exp(-ts / 0.008) * 0.6
            env = np.exp(-ts / 0.065)  # fast decay of chillador
            strum = (strum * 0.18 + pick * 0.3) * env
            
            end_idx = min(s_idx + s_len, len(t))
            mix[s_idx:end_idx] += strum[:end_idx - s_idx]
            
    mix = np.tanh(mix * 1.4) * 0.8
    stereo = np.column_stack([mix * 0.95, mix * 1.05])
    
    out = os.path.join(CULTURAL_DIR, "chillador_rasgueo_huaylia_chumbivilcana.wav")
    int_data = (np.clip(stereo, -0.98, 0.98) * 32767).astype(np.int16)
    with wave.open(out, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(int_data.tobytes())
    print("Created: chillador_rasgueo_huaylia_chumbivilcana.wav")

def gen_tinya_bombo():
    # Tinya / Bombo Andino tradicional (percusión de cuero de llama/oveja)
    dur = 6.0
    bpm = 110.0
    beat_dur = 60.0 / bpm
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    mix = np.zeros(len(t))
    
    total_beats = int(dur / beat_dur)
    for b in range(total_beats):
        bt_t = b * beat_dur
        b_idx = int(bt_t * SR)
        b_len = int(0.35 * SR)
        tb = np.linspace(0, 0.35, b_len, endpoint=False)
        
        # Deep skin resonance (55Hz pitch drop to 38Hz)
        f_skin = 38.0 + 35.0 * np.exp(-tb / 0.04)
        phase = 2 * np.pi * np.cumsum(f_skin) / SR
        boom = np.sin(phase) * np.exp(-tb / 0.12)
        # Wooden rim strike on alternate beats
        if b % 2 == 1:
            rim = np.random.uniform(-1, 1, b_len) * np.exp(-tb / 0.012) * 0.4
        else:
            rim = 0.0
            
        hit = boom * 0.8 + rim * 0.3
        end_idx = min(b_idx + b_len, len(t))
        mix[b_idx:end_idx] += hit[:end_idx - b_idx]
        
    mix = np.tanh(mix * 1.3) * 0.85
    stereo = np.column_stack([mix, mix])
    out = os.path.join(CULTURAL_DIR, "tinya_bombo_andino_tradicional.wav")
    int_data = (np.clip(stereo, -0.98, 0.98) * 32767).astype(np.int16)
    with wave.open(out, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(int_data.tobytes())
    print("Created: tinya_bombo_andino_tradicional.wav")

def gen_cascabeles():
    # Cascabeles de danzantes / espuelas de Qorilazo chumbivilcano (4.0s)
    dur = 4.0
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    mix = np.zeros(len(t))
    # Shake rhythm (step-shake every 0.35s)
    for s in np.arange(0, dur - 0.2, 0.35):
        s_idx = int(s * SR)
        s_len = int(0.18 * SR)
        ts = np.linspace(0, 0.18, s_len, endpoint=False)
        # High metallic jingle cluster (2800Hz, 3400Hz, 4100Hz, 5200Hz)
        jingle = (np.sin(2 * np.pi * 2800 * ts) +
                  np.sin(2 * np.pi * 3400 * ts) +
                  np.sin(2 * np.pi * 4100 * ts) +
                  np.sin(2 * np.pi * 5200 * ts)) * 0.15
        noise = np.random.uniform(-1, 1, s_len) * 0.25
        env = np.exp(-ts / 0.04) * (1.0 - np.exp(-ts / 0.005))
        shake = (jingle + noise) * env
        end_idx = min(s_idx + s_len, len(t))
        mix[s_idx:end_idx] += shake[:end_idx - s_idx]
        
    stereo = np.column_stack([mix * 0.9, mix * 1.1])
    out = os.path.join(CULTURAL_DIR, "cascabeles_espuelas_qorilazo.wav")
    int_data = (np.clip(stereo, -0.98, 0.98) * 32767).astype(np.int16)
    with wave.open(out, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(int_data.tobytes())
    print("Created: cascabeles_espuelas_qorilazo.wav")

if __name__ == "__main__":
    slice_wakawaqra()
    gen_pututu()
    gen_chillador()
    gen_tinya_bombo()
    gen_cascabeles()
    print("All cultural audio assets completed!")
