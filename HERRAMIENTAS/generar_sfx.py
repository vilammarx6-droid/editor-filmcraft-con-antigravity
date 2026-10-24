import os
import wave
import numpy as np

OUTPUT_DIR = r"C:\Users\marx_\OneDrive\Documentos\Proyecto predeterminado\EditorVideo\RECURSOS_COMPARTIDOS\02_efectos_sonido"
SR = 48000  # 48 kHz standard for FilmCraft

def save_wav(filename, data_stereo):
    filepath = os.path.join(OUTPUT_DIR, filename)
    # Clip and convert to 16-bit PCM
    data_clipped = np.clip(data_stereo, -0.98, 0.98)
    int_data = (data_clipped * 32767).astype(np.int16)
    
    with wave.open(filepath, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(int_data.tobytes())
    print(f"Generated: {filename} ({len(int_data)/SR:.2f}s)")

# 1. Whoosh Fast (0.4s)
def gen_whoosh_fast():
    dur = 0.4
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # White noise
    noise = np.random.uniform(-1, 1, len(t))
    # Gaussian bell envelope
    env = np.exp(-((t - 0.18)**2) / (2 * (0.07**2)))
    # Pitch sweep modulation (approximate doppler band sweep)
    carrier = np.sin(2 * np.pi * (200 + 1200 * env) * t)
    audio = noise * env * 0.7 + carrier * env * 0.3
    # Stereo pan (left to right)
    pan = np.linspace(0.2, 0.8, len(t))
    left = audio * (1.0 - pan)
    right = audio * pan
    stereo = np.column_stack([left, right])
    save_wav("whoosh_fast.wav", stereo)

# 2. Whoosh Heavy / Deep (0.65s)
def gen_whoosh_heavy():
    dur = 0.65
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    noise = np.random.uniform(-1, 1, len(t))
    env = np.exp(-((t - 0.32)**2) / (2 * (0.12**2)))
    sub = np.sin(2 * np.pi * (60 + 180 * env) * t) * env
    audio = noise * env * 0.65 + sub * 0.5
    pan = np.linspace(0.1, 0.9, len(t))
    left = audio * (1.0 - pan)
    right = audio * pan
    stereo = np.column_stack([left, right])
    save_wav("whoosh_heavy.wav", stereo)

# 3. Whoosh Cinematic (0.85s)
def gen_whoosh_cinematic():
    dur = 0.85
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    noise = np.random.uniform(-1, 1, len(t))
    env = np.exp(-((t - 0.42)**2) / (2 * (0.16**2)))
    # Swept sine layer
    f = 120 + 800 * (t / dur)**2
    phase = 2 * np.pi * np.cumsum(f) / SR
    sweep = np.sin(phase) * env
    audio = (noise * env * 0.6 + sweep * 0.4)
    # Panning sweep
    pan = 0.5 + 0.4 * np.sin(np.pi * (t / dur - 0.5))
    left = audio * (1.0 - pan) * 1.2
    right = audio * pan * 1.2
    stereo = np.column_stack([left, right])
    save_wav("whoosh_cinematic.wav", stereo)

# 4. Impact Bass Hit (1.5s)
def gen_impact_bass():
    dur = 1.5
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Pitch drop from 180 Hz to 42 Hz fast (in 0.1s), then hold at 42 Hz
    f = 42 + 140 * np.exp(-t / 0.08)
    phase = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(phase)
    # Soft saturation
    sub = np.tanh(sub * 1.5)
    # Decay envelope
    env = np.exp(-t / 0.35)
    # Initial punch click
    punch = np.random.uniform(-1, 1, len(t)) * np.exp(-t / 0.015) * 0.6
    audio = (sub * env * 0.85 + punch * 0.3)
    stereo = np.column_stack([audio, audio])
    save_wav("impact_bass_hit.wav", stereo)

# 5. Impact Punch (0.6s)
def gen_impact_punch():
    dur = 0.6
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    f = 65 + 280 * np.exp(-t / 0.04)
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * np.exp(-t / 0.12)
    transient = np.random.uniform(-1, 1, len(t)) * np.exp(-t / 0.02) * 0.8
    audio = (body * 0.7 + transient * 0.4)
    stereo = np.column_stack([audio, audio])
    save_wav("impact_punch.wav", stereo)

# 6. Riser Tension 3s (3.0s)
def gen_riser_3s():
    dur = 3.0
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Exponential frequency sweep from 90 Hz to 1800 Hz
    f = 90 * (1800 / 90) ** (t / dur)
    phase = 2 * np.pi * np.cumsum(f) / SR
    saw = 2 * (phase / (2 * np.pi) - np.floor(phase / (2 * np.pi) + 0.5))
    noise = np.random.uniform(-1, 1, len(t))
    # Volume ramp up
    env = (t / dur) ** 2.2
    audio = (saw * 0.4 + noise * 0.5) * env
    # Slight stereo width
    left = audio * (0.8 + 0.2 * np.sin(2 * np.pi * 3 * t))
    right = audio * (0.8 + 0.2 * np.cos(2 * np.pi * 3 * t))
    stereo = np.column_stack([left, right])
    save_wav("riser_tension_3s.wav", stereo)

# 7. Riser Tension 1.5s (1.5s)
def gen_riser_1_5s():
    dur = 1.5
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    f = 140 * (2600 / 140) ** (t / dur)
    phase = 2 * np.pi * np.cumsum(f) / SR
    saw = 2 * (phase / (2 * np.pi) - np.floor(phase / (2 * np.pi) + 0.5))
    noise = np.random.uniform(-1, 1, len(t))
    env = (t / dur) ** 2.0
    audio = (saw * 0.45 + noise * 0.55) * env
    stereo = np.column_stack([audio, audio])
    save_wav("riser_tension_1.5s.wav", stereo)

# 8. Pop Bubble (0.14s)
def gen_pop_bubble():
    dur = 0.14
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Upward sweep 450 Hz -> 1350 Hz fast
    f = 450 + 900 * (1.0 - np.exp(-t / 0.025))
    phase = 2 * np.pi * np.cumsum(f) / SR
    sine = np.sin(phase)
    env = np.exp(-t / 0.035)
    audio = sine * env * 0.85
    stereo = np.column_stack([audio, audio])
    save_wav("pop_bubble.wav", stereo)

# 9. Pop High / Sharp (0.09s)
def gen_pop_high():
    dur = 0.09
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    f = 900 + 1600 * (1.0 - np.exp(-t / 0.015))
    phase = 2 * np.pi * np.cumsum(f) / SR
    sine = np.sin(phase)
    env = np.exp(-t / 0.02)
    audio = sine * env * 0.8
    stereo = np.column_stack([audio, audio])
    save_wav("pop_high.wav", stereo)

# 10. Camera Shutter (0.32s)
def gen_camera_shutter():
    dur = 0.32
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # First small click at t=0
    c1 = np.random.uniform(-1, 1, len(t)) * np.exp(-t / 0.008) * 0.5
    # Second loud snap at t=0.075s
    t2 = np.maximum(0, t - 0.075)
    f2 = 1200 * np.exp(-t2 / 0.02)
    phase2 = 2 * np.pi * np.cumsum(f2) / SR
    c2 = np.sin(phase2) * np.exp(-t2 / 0.035) * (t >= 0.075) * 0.9
    c2 += np.random.uniform(-1, 1, len(t)) * np.exp(-t2 / 0.012) * (t >= 0.075) * 0.4
    audio = c1 + c2
    stereo = np.column_stack([audio, audio])
    save_wav("camera_shutter.wav", stereo)

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    gen_whoosh_fast()
    gen_whoosh_heavy()
    gen_whoosh_cinematic()
    gen_impact_bass()
    gen_impact_punch()
    gen_riser_3s()
    gen_riser_1_5s()
    gen_pop_bubble()
    gen_pop_high()
    gen_camera_shutter()
    print("All 10 cinematic SFX generated successfully!")
