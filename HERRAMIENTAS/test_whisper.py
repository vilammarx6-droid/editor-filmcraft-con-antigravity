import os
import sys
import subprocess
from faster_whisper import WhisperModel

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("Loading Whisper model...")
model = WhisperModel("tiny", device="cpu", compute_type="int8")

script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(script_dir, ".."))
proj_dir = os.path.join(repo_root, "PROYECTOS", "2026-10-26_aniversario-ccollana-condes")
v_dir = os.path.join(proj_dir, "01_fuentes", "video")
a_dir = os.path.join(proj_dir, "01_fuentes", "audio")

target_clips = ["20260824_163006.mp4", "20260824_163834.mp4", "20260824_172800.mp4", "20260824_173750.mp4"]

out_log = os.path.join(proj_dir, "05_logs", "transcripcion_entrevistas.txt")

with open(out_log, "w", encoding="utf-8") as out_f:
    for c in target_clips:
        video_path = os.path.join(v_dir, c)
        if not os.path.exists(video_path):
            continue
        audio_tmp = os.path.join(a_dir, f"transcribe_{c}.wav")
        header = f"\n=======================================================\n Transcribiendo audio de: {c}\n=======================================================\n"
        print(header)
        out_f.write(header)
        
        # Extraer todo el audio (hasta 320s)
        subprocess.run(["ffmpeg", "-y", "-ss", "0", "-i", video_path, "-t", "320", "-ar", "16000", "-ac", "1", audio_tmp], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        segments, info = model.transcribe(audio_tmp, language="es")
        for s in segments:
            text = s.text.strip()
            line = f"[{s.start:6.1f}s -> {s.end:6.1f}s] {text}\n"
            print(line, end="")
            out_f.write(line)
            out_f.flush()

print(f"\n[OK] Transcripción completa guardada en: {out_log}")
