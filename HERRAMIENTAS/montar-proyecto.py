#!/usr/bin/env python3
"""
montar-proyecto.py - Montador determinista de proyectos FilmCraft.

Lee un contrato `edit-plan.json`, valida las fuentes, crea un proyecto nativo
.fcproj, importa los medios, coloca cada clip en su pista y exporta el master
desde la propia linea de tiempo de FilmCraft.

El master exportado se normaliza despues con `remediar-audio.py` para cumplir
EBU R128. El video NO se recompone con FFmpeg: se conserva el video exportado
por FilmCraft y solo se reencoda la pista de audio.

Salidas:
  02_filmcraft/<slug>_vNN.fcproj
  02_filmcraft/edit-manifest_vNN.json
  02_filmcraft/edit-manifest.json
  03_exports/<slug>_vNN_timeline.mp4
  03_exports/<slug>_vNN_master.mp4

Uso:
  python HERRAMIENTAS/montar-proyecto.py --project PROYECTOS/mi-proyecto
  python HERRAMIENTAS/montar-proyecto.py --project ... --plan 00_brief/edit-plan.json
  python HERRAMIENTAS/montar-proyecto.py --project ... --no-export
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TICKS_PER_SECOND = 254016000000
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm", ".mxf"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".aif", ".aiff", ".ogg"}
TRACK_RE = re.compile(r"^([VA])([1-9][0-9]*)$")
DEFAULT_PLAN_PATHS = (
    Path("00_brief") / "edit-plan.json",
    Path("01_fuentes") / "edit-plan.json",
    Path("02_filmcraft") / "edit-plan.json",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_config() -> dict:
    cfg_path = Path(__file__).resolve().with_name("config.local.json")
    if not cfg_path.exists():
        raise FileNotFoundError(f"No existe {cfg_path}")
    with cfg_path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def get_filmcraft_cli() -> Path:
    env_cli = os.environ.get("FILMCRAFT_CLI")
    if env_cli and Path(env_cli).is_file():
        return Path(env_cli)
    cfg = load_config()
    cli = cfg.get("filmcraft_cli")
    if cli and Path(cli).is_file():
        return Path(cli)
    raise FileNotFoundError("No se encontro filmcraft_cli en config.local.json ni en FILMCRAFT_CLI.")


def run_cli(cli: Path, args: list[str], parse_json: bool = False):
    cmd = [str(cli)] + [str(a) for a in args]
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if res.returncode != 0:
        raise RuntimeError(
            "Fallo FilmCraft CLI:\n"
            f"  comando: {' '.join(cmd)}\n"
            f"  exit: {res.returncode}\n"
            f"  stdout: {res.stdout.strip()}\n"
            f"  stderr: {res.stderr.strip()}"
        )
    if parse_json:
        text = res.stdout.strip()
        if not text:
            raise RuntimeError(f"FilmCraft CLI no devolvio JSON para: {' '.join(cmd)}")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Respuesta JSON invalida de FilmCraft CLI: {exc}\n{text[:2000]}"
            ) from exc
    return res


def run_python(script: Path, args: list[str]):
    cmd = [sys.executable, str(script)] + [str(a) for a in args]
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"Fallo el script {script.name}:\n"
            f"  exit: {res.returncode}\n"
            f"  stdout: {res.stdout.strip()}\n"
            f"  stderr: {res.stderr.strip()}"
        )
    return res


def probe_media(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=codec_type,width,height,sample_rate,channels:format=duration",
        "-of", "json", str(path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        raise RuntimeError(f"ffprobe no pudo leer {path}: {res.stderr.strip()}")
    data = json.loads(res.stdout)
    duration_raw = data.get("format", {}).get("duration")
    if duration_raw is None:
        raise ValueError(f"No se pudo obtener duracion de {path}")
    streams = data.get("streams", [])
    return {
        "duration": float(duration_raw),
        "video": next((s for s in streams if s.get("codec_type") == "video"), None),
        "audio": next((s for s in streams if s.get("codec_type") == "audio"), None),
    }


def ensure_within(path: Path, base: Path, label: str) -> None:
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"'{label}' esta fuera de {base}: {path}") from exc


def posix_rel(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def posix_rel_or_abs(path: Path, base: Path) -> str:
    """Ruta relativa POSIX para el manifiesto; absoluta si el plan es externo."""
    try:
        return posix_rel(path, base)
    except ValueError:
        return path.resolve().as_posix()


def resolve_plan_path(project: Path, explicit: str | None) -> Path:
    if explicit:
        candidate = Path(explicit)
        if not candidate.is_absolute():
            project_candidate = project / candidate
            if project_candidate.exists():
                candidate = project_candidate
        if not candidate.exists():
            raise FileNotFoundError(f"No existe el plan indicado: {candidate}")
        return candidate.resolve()

    for rel in DEFAULT_PLAN_PATHS:
        candidate = project / rel
        if candidate.exists():
            return candidate.resolve()
    searched = ", ".join(str(p) for p in DEFAULT_PLAN_PATHS)
    raise FileNotFoundError(
        "No se encontro edit-plan.json en el proyecto. "
        f"Busque en: {searched}. El pipeline ya no monta timelines existentes por defecto."
    )


def normalized_project_slug(name: str) -> str:
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}_", "", name)
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", slug).strip("-")
    return slug or name


def resolve_source(clip: dict, project: Path, repo_root: Path) -> dict:
    source = str(clip.get("source", "")).strip()
    if not source:
        raise ValueError("Cada clip debe declarar 'source'.")
    source_path = Path(source)
    if source_path.is_absolute():
        raise ValueError(f"La fuente debe ser relativa, no absoluta: {source}")

    source_root = str(clip.get("source_root", "project")).strip().lower()
    if source_root == "project":
        base = (project / "01_fuentes").resolve()
        origin = "project"
        license_name = None
    elif source_root == "shared":
        base = (repo_root / "RECURSOS_COMPARTIDOS").resolve()
        origin = "shared"
        license_name = str(clip.get("license", "")).strip()
        if not license_name:
            raise ValueError(
                f"La fuente compartida '{source}' debe declarar 'license' para poder usarse."
            )
    else:
        raise ValueError(f"source_root invalido para '{source}': {source_root}")

    resolved = (base / source_path).resolve()
    ensure_within(resolved, base, source)
    if not resolved.is_file():
        raise FileNotFoundError(f"No existe la fuente: {resolved}")

    media = probe_media(resolved)
    rel_to_project = posix_rel(resolved, project) if origin == "project" else posix_rel(resolved, repo_root)
    return {
        "path": resolved,
        "project_rel": rel_to_project,
        "origin": origin,
        "license": license_name,
        "item_name": resolved.name,
        "media": media,
    }


def as_seconds(value, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"'{field}' debe ser numerico.") from exc
    if number < 0:
        raise ValueError(f"'{field}' no puede ser negativo.")
    return number


def validate_plan(plan: dict, plan_path: Path, project: Path, repo_root: Path) -> dict:
    if str(plan.get("schema_version", "1.0.0")) not in {"1.0.0", "1.1.0"}:
        raise ValueError(f"schema_version no soportada: {plan.get('schema_version')}")

    declared_project = plan.get("project")
    if declared_project:
        accepted = {project.name, normalized_project_slug(project.name)}
        if declared_project not in accepted:
            raise ValueError(
                f"El plan pertenece a '{declared_project}', pero el proyecto es '{project.name}'. "
                "Se rechaza un plan de otro proyecto."
            )

    sequence = plan.get("sequence") or {}
    width = int(sequence.get("width", 1920))
    height = int(sequence.get("height", 1080))
    fps = float(sequence.get("fps", 30.0))
    sample_rate = int(sequence.get("sample_rate", 48000))
    if width <= 0 or height <= 0 or fps <= 0:
        raise ValueError("La secuencia debe tener width, height y fps positivos.")
    if sample_rate != 48000:
        raise ValueError(f"FilmCraft standard exige 48000 Hz, no {sample_rate} Hz.")

    duration = as_seconds(plan.get("duration"), "duration")
    if duration <= 0:
        raise ValueError("'duration' debe ser mayor que cero.")

    tracks = plan.get("tracks")
    if not isinstance(tracks, dict) or not tracks:
        raise ValueError("El plan debe incluir un objeto 'tracks' no vacio.")

    max_video = 0
    max_audio = 0
    for track_name in tracks:
        match = TRACK_RE.match(track_name)
        if not match:
            raise ValueError(f"Pista invalida: {track_name}. Use V1..Vn o A1..An.")
        index = int(match.group(2))
        if match.group(1) == "V":
            max_video = max(max_video, index)
        else:
            max_audio = max(max_audio, index)

    video_tracks = max(int(sequence.get("video_tracks", 0) or 0), max_video)
    audio_tracks = max(int(sequence.get("audio_tracks", 0) or 0), max_audio)
    if video_tracks < 1 or audio_tracks < 1:
        raise ValueError("La secuencia necesita al menos una pista de video y una de audio.")

    normalized_tracks: dict[str, list[dict]] = {name: [] for name in tracks}
    sources: dict[str, dict] = {}
    seen_item_names: dict[str, Path] = {}

    for track_name, raw_clips in tracks.items():
        if not isinstance(raw_clips, list):
            raise ValueError(f"La pista {track_name} debe ser una lista de clips.")
        is_video = track_name.startswith("V")
        for idx, raw_clip in enumerate(raw_clips):
            if not isinstance(raw_clip, dict):
                raise ValueError(f"Clip invalido en {track_name}[{idx}].")
            source_info = resolve_source(raw_clip, project, repo_root)
            source_path = source_info["path"]
            media = source_info["media"]

            if is_video and not media["video"]:
                raise ValueError(f"{source_info['project_rel']} no tiene pista de video para {track_name}.")
            if not is_video and not media["audio"]:
                raise ValueError(f"{source_info['project_rel']} no tiene pista de audio para {track_name}.")

            item_name = source_info["item_name"]
            if item_name in seen_item_names and seen_item_names[item_name] != source_path:
                raise ValueError(
                    "FilmCraft importa por nombre de archivo; hay dos fuentes con el mismo "
                    f"nombre y distinto origen: {item_name}"
                )
            seen_item_names[item_name] = source_path

            start = as_seconds(raw_clip.get("start", 0.0), f"{track_name}[{idx}].start")
            source_in = as_seconds(raw_clip.get("in", 0.0), f"{track_name}[{idx}].in")
            if raw_clip.get("out") is None:
                source_out = float(media["duration"])
            else:
                source_out = as_seconds(raw_clip.get("out"), f"{track_name}[{idx}].out")
            if source_out <= source_in:
                raise ValueError(
                    f"{track_name}[{idx}] tiene out <= in ({source_in} >= {source_out})."
                )
            if source_out > media["duration"] + 0.05:
                raise ValueError(
                    f"{track_name}[{idx}] pide hasta {source_out:.3f}s, pero "
                    f"{source_info['project_rel']} dura {media['duration']:.3f}s."
                )
            clip_duration = source_out - source_in
            end = start + clip_duration
            if end > duration + 0.01:
                raise ValueError(
                    f"{track_name}[{idx}] termina en {end:.3f}s y supera la duracion "
                    f"del plan ({duration:.3f}s)."
                )

            normalized_tracks[track_name].append({
                "source": source_info["project_rel"],
                "source_path": source_path,
                "origin": source_info["origin"],
                "license": source_info["license"],
                "item_name": item_name,
                "start": start,
                "in": source_in,
                "out": source_out,
                "duration": clip_duration,
                "end": end,
            })

            if source_info["project_rel"] not in sources:
                sources[source_info["project_rel"]] = source_info

    for track_name, clips in normalized_tracks.items():
        clips.sort(key=lambda c: c["start"])
        for prev, curr in zip(clips, clips[1:]):
            if curr["start"] < prev["end"] - 0.01:
                raise ValueError(
                    f"Solapamiento en {track_name}: '{prev['item_name']}' y "
                    f"'{curr['item_name']}' comparten tiempo."
                )

    v1 = normalized_tracks.get("V1", [])
    if not v1:
        raise ValueError("El plan debe colocar al menos un clip en V1.")
    if not plan.get("allow_gaps", False):
        cursor = 0.0
        for clip in v1:
            if abs(clip["start"] - cursor) > 0.01:
                raise ValueError(
                    f"V1 tiene un hueco/desfase en {cursor:.3f}s; el clip "
                    f"'{clip['item_name']}' empieza en {clip['start']:.3f}s. "
                    "Use allow_gaps=true solo si el hueco es intencional."
                )
            cursor = clip["end"]
        if abs(cursor - duration) > 0.01:
            raise ValueError(
                f"V1 termina en {cursor:.3f}s, pero la duracion del plan es {duration:.3f}s."
            )

    return {
        "plan": plan,
        "plan_path": plan_path,
        "project": project,
        "repo_root": repo_root,
        "width": width,
        "height": height,
        "fps": fps,
        "sample_rate": sample_rate,
        "duration": duration,
        "video_tracks": video_tracks,
        "audio_tracks": audio_tracks,
        "sequence_name": str(sequence.get("name", "Principal")),
        "tracks": normalized_tracks,
        "sources": sources,
    }


def choose_version(project: Path, slug: str, requested: int | None) -> int:
    if requested is not None:
        if requested < 1:
            raise ValueError("La version debe ser >= 1.")
        existing = list((project / "02_filmcraft").glob(f"{slug}_v{requested:02d}*.fcproj"))
        existing += list((project / "03_exports").glob(f"{slug}_v{requested:02d}_*.mp4"))
        if existing:
            raise FileExistsError(
                f"La version v{requested:02d} ya existe. No se sobrescriben salidas. "
                "Suba de version."
            )
        return requested

    versions = []
    for folder in (project / "02_filmcraft", project / "03_exports"):
        if not folder.exists():
            continue
        for item in folder.iterdir():
            match = re.search(rf"^{re.escape(slug)}_v(\d+)", item.name)
            if match:
                versions.append(int(match.group(1)))
    return (max(versions) + 1) if versions else 1


def walk_project_items(node: dict):
    for child in node.get("children", []) or []:
        yield child
        yield from walk_project_items(child)


def inspect_project_items(cli: Path, fcproj: Path) -> dict[str, int]:
    tree = run_cli(cli, ["--project", str(fcproj), "inspect", "project", "--compact"], parse_json=True)
    root = tree.get("root", {})
    items: dict[str, int] = {}
    for child in walk_project_items(root):
        name = child.get("name")
        item_id = child.get("item")
        if name and isinstance(item_id, int):
            if name in items and items[name] != item_id:
                raise RuntimeError(f"FilmCraft tiene dos medios con el mismo nombre: {name}")
            items[name] = item_id
    return items


def build_sequence(cli: Path, fcproj: Path, data: dict) -> None:
    seq_params = {
        "name": data["sequence_name"],
        "width": data["width"],
        "height": data["height"],
        "fps": data["fps"],
        "sampleRate": data["sample_rate"],
        "video": data["video_tracks"],
        "audio": data["audio_tracks"],
        "mix": "Stereo",
        "trackType": "Standard",
    }
    run_cli(
        cli,
        ["--project", str(fcproj), "--save", "exec", "file.newSequence", json.dumps(seq_params)],
    )


def place_clips(cli: Path, fcproj: Path, data: dict) -> None:
    source_paths = [info["path"] for info in data["sources"].values()]
    if not source_paths:
        raise RuntimeError("No hay fuentes que importar.")
    run_cli(
        cli,
        ["--project", str(fcproj), "--save", "import", *[str(p) for p in source_paths]],
    )

    item_ids = inspect_project_items(cli, fcproj)
    missing = [p.name for p in source_paths if p.name not in item_ids]
    if missing:
        raise RuntimeError(f"FilmCraft no importo estos medios: {', '.join(missing)}")

    for track_name, clips in data["tracks"].items():
        for clip in clips:
            place_params = {
                "item": item_ids[clip["item_name"]],
                "track": track_name,
                "seconds": clip["start"],
                "insert": False,
                "sourceIn": int(round(clip["in"] * TICKS_PER_SECOND)),
                "duration": int(round(clip["duration"] * TICKS_PER_SECOND)),
                "video": track_name.startswith("V"),
                "audio": track_name.startswith("A"),
            }
            run_cli(
                cli,
                ["--project", str(fcproj), "--save", "exec", "timeline.place", json.dumps(place_params)],
            )


def verify_timeline(cli: Path, fcproj: Path, data: dict) -> dict:
    seq = run_cli(cli, ["--project", str(fcproj), "inspect", "sequence", "--compact"], parse_json=True)
    tolerance = max(0.02, 1.5 / max(data["fps"], 1.0))

    settings = seq.get("settings", {})
    if int(settings.get("width", 0)) != data["width"] or int(settings.get("height", 0)) != data["height"]:
        raise RuntimeError(
            f"La secuencia no tiene el tamano esperado: "
            f"{settings.get('width')}x{settings.get('height')}."
        )
    frame_rate = settings.get("frame_rate", {})
    seq_fps = float(frame_rate.get("num", 0)) / max(float(frame_rate.get("den", 1)), 1.0)
    if abs(seq_fps - data["fps"]) > 0.01:
        raise RuntimeError(f"La secuencia no tiene {data['fps']} fps: {seq_fps} fps.")

    duration = float(seq.get("duration", 0)) / TICKS_PER_SECOND
    if abs(duration - data["duration"]) > tolerance:
        raise RuntimeError(
            f"La duracion de la secuencia ({duration:.3f}s) no coincide con el plan "
            f"({data['duration']:.3f}s)."
        )

    video_tracks = seq.get("video", [])
    audio_tracks = seq.get("audio", [])
    if len(video_tracks) < data["video_tracks"] or len(audio_tracks) < data["audio_tracks"]:
        raise RuntimeError("FilmCraft no creo todas las pistas declaradas en el plan.")

    verified_tracks: dict[str, list[dict]] = {}
    for track_name, expected in data["tracks"].items():
        is_video = track_name.startswith("V")
        index = int(track_name[1:]) - 1
        actual_track = (video_tracks if is_video else audio_tracks)[index]
        actual_items = actual_track.get("items", [])
        if len(actual_items) != len(expected):
            raise RuntimeError(
                f"{track_name}: se esperaban {len(expected)} clips y FilmCraft tiene "
                f"{len(actual_items)}."
            )
        actual_normalized = []
        for item in actual_items:
            actual_normalized.append({
                "name": item.get("name"),
                "start": float(item.get("start", 0)) / TICKS_PER_SECOND,
                "sourceIn": float(item.get("sourceIn", 0)) / TICKS_PER_SECOND,
                "duration": float(item.get("duration", 0)) / TICKS_PER_SECOND,
            })
        actual_normalized.sort(key=lambda x: x["start"])
        for expected_clip, actual_clip in zip(expected, actual_normalized):
            if expected_clip["item_name"] != actual_clip["name"]:
                raise RuntimeError(
                    f"{track_name}: se esperaba '{expected_clip['item_name']}' y hay "
                    f"'{actual_clip['name']}'."
                )
            if abs(expected_clip["start"] - actual_clip["start"]) > tolerance:
                raise RuntimeError(f"{track_name}: inicio distinto para '{actual_clip['name']}'.")
            if abs(expected_clip["in"] - actual_clip["sourceIn"]) > tolerance:
                raise RuntimeError(f"{track_name}: sourceIn distinto para '{actual_clip['name']}'.")
            if abs(expected_clip["duration"] - actual_clip["duration"]) > tolerance:
                raise RuntimeError(f"{track_name}: duracion distinta para '{actual_clip['name']}'.")
            actual_clip["source_in"] = actual_clip.pop("sourceIn")
            verified_tracks.setdefault(track_name, []).append(actual_clip)

    return {
        "sequence": {
            "name": seq.get("name"),
            "width": int(settings.get("width", 0)),
            "height": int(settings.get("height", 0)),
            "fps": seq_fps,
            "sample_rate": int(settings.get("sample_rate", 0)),
            "duration_seconds": round(duration, 3),
        },
        "tracks": verified_tracks,
    }


def export_timeline(cli: Path, fcproj: Path, raw_export: Path, master: Path,
                    repo_root: Path, data: dict) -> None:
    run_cli(
        cli,
        ["--project", str(fcproj), "export", str(raw_export), "--format", "h264", "--quality", "85"],
    )
    if not raw_export.exists():
        raise RuntimeError(f"FilmCraft no genero el export de timeline: {raw_export}")

    remediar = repo_root / "HERRAMIENTAS" / "remediar-audio.py"
    if not remediar.exists():
        raise FileNotFoundError(f"No existe {remediar}")
    run_python(remediar, [str(raw_export), "--out", str(master)])
    if not master.exists():
        raise RuntimeError(f"No se genero el master normalizado: {master}")

    media = probe_media(master)
    audio = media.get("audio")
    if not audio:
        raise RuntimeError("El master no tiene pista de audio.")
    if int(audio.get("sample_rate", 0)) != 48000 or int(audio.get("channels", 0)) != 2:
        raise RuntimeError(
            "El master no es 48 kHz estereo: "
            f"{audio.get('sample_rate')} Hz, {audio.get('channels')} canales."
        )

    # No se declara un master valido solo porque el archivo exista: el mismo
    # Quality Gate que usa el pipeline se ejecuta aqui antes de firmar el
    # edit-manifest. Si el audio no alcanza EBU R128, el montaje falla.
    quality_gate = repo_root / "HERRAMIENTAS" / "auditar-calidad.py"
    if not quality_gate.exists():
        raise FileNotFoundError(f"No existe {quality_gate}")
    run_python(
        quality_gate,
        [
            str(master),
            "--width", str(data["width"]),
            "--height", str(data["height"]),
            "--fps", str(data["fps"]),
            "--channels", "2",
            "--duration", str(data["duration"]),
            "--duration-tolerance", "0.25",
        ],
    )


def build_manifest(data: dict, fcproj: Path, raw_export: Path | None, master: Path | None,
                   exported: bool, verified: dict, version: int) -> dict:
    project = data["project"]
    source_entries = []
    for rel_path, info in sorted(data["sources"].items()):
        source_entries.append({
            "path": rel_path,
            "origin": info["origin"],
            "license": info["license"],
            "size_bytes": info["path"].stat().st_size,
            "sha256": sha256_file(info["path"]),
        })

    manifest = {
        "schema_version": "1.1.0",
        "status": "ok",
        "engine": "FilmCraft CLI 0.9.0",
        "created_utc": now_utc(),
        "project": project.name,
        "version": version,
        "plan_file": posix_rel_or_abs(data["plan_path"], project),
        "plan_sha256": sha256_file(data["plan_path"]),
        "timeline_file": posix_rel(fcproj, project),
        "timeline_sha256": sha256_file(fcproj),
        "exported": exported,
        "raw_export": posix_rel(raw_export, project) if raw_export else None,
        "raw_export_sha256": sha256_file(raw_export) if raw_export and raw_export.exists() else None,
        "master_file": posix_rel(master, project) if master else None,
        "master_sha256": sha256_file(master) if master and master.exists() else None,
        "duration_seconds": data["duration"],
        "sequence": verified["sequence"],
        "tracks": verified["tracks"],
        "sources": source_entries,
        "source_policy": "01_fuentes o RECURSOS_COMPARTIDOS con licencia",
        "validation": {
            "plan_validated": True,
            "sources_validated": True,
            "timeline_verified": True,
            "master_verified": bool(exported and master and master.exists()),
            "quality_gate": "passed" if exported else None,
        },
    }
    return manifest


def write_manifest(project: Path, version: int, manifest: dict) -> Path:
    fc_dir = project / "02_filmcraft"
    fc_dir.mkdir(parents=True, exist_ok=True)
    versioned = fc_dir / f"edit-manifest_v{version:02d}.json"
    latest = fc_dir / "edit-manifest.json"
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    versioned.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    return versioned


def main() -> int:
    parser = argparse.ArgumentParser(description="Montador determinista de proyectos FilmCraft")
    parser.add_argument("--project", required=True, help="Carpeta del proyecto")
    parser.add_argument("--plan", help="Ruta a edit-plan.json (por defecto se autodetecta)")
    parser.add_argument("--version", type=int, help="Version explicita; por defecto sube a la siguiente")
    parser.add_argument("--no-export", action="store_true", help="Solo monta el timeline, no exporta")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"[ERROR] No existe el proyecto: {project}", file=sys.stderr)
        return 1

    repo_root = Path(__file__).resolve().parents[1]
    plan_path = None
    version = None
    try:
        plan_path = resolve_plan_path(project, args.plan)
        with plan_path.open("r", encoding="utf-8-sig") as f:
            plan = json.load(f)
        data = validate_plan(plan, plan_path, project, repo_root)

        slug = normalized_project_slug(project.name)
        output_cfg = plan.get("output") or {}
        if output_cfg.get("slug"):
            slug = re.sub(r"[^A-Za-z0-9._-]+", "-", str(output_cfg["slug"])).strip("-") or slug
        requested_version = args.version
        if requested_version is None and output_cfg.get("version") is not None:
            requested_version = int(output_cfg["version"])
        version = choose_version(project, slug, requested_version)

        fc_dir = project / "02_filmcraft"
        exports_dir = project / "03_exports"
        fc_dir.mkdir(parents=True, exist_ok=True)
        exports_dir.mkdir(parents=True, exist_ok=True)

        fcproj = fc_dir / f"{slug}_v{version:02d}.fcproj"
        raw_export = exports_dir / f"{slug}_v{version:02d}_timeline.mp4"
        master = exports_dir / f"{slug}_v{version:02d}_master.mp4"
        if fcproj.exists() or raw_export.exists() or master.exists():
            raise FileExistsError(
                "Las salidas de esta version ya existen. No se sobrescriben. "
                "Ejecute de nuevo para subir de version."
            )

        cli = get_filmcraft_cli()
        print("=" * 68)
        print(" [MONTADOR] FilmCraft: timeline real + export desde FilmCraft")
        print("=" * 68)
        print(f"[*] Proyecto: {project.name}")
        print(f"[*] Plan:     {posix_rel_or_abs(plan_path, project)}")
        print(f"[*] Salida:   {posix_rel(fcproj, project)} (v{version:02d})")
        print(f"[*] Secuencia: {data['width']}x{data['height']} @ {data['fps']} fps, "
              f"{data['duration']:.3f}s")

        print("[*] Creando proyecto FilmCraft...")
        run_cli(
            cli,
            ["--save-as", str(fcproj), "exec", "file.newProject", json.dumps({"name": project.name})],
        )
        build_sequence(cli, fcproj, data)

        print("[*] Importando fuentes y colocando clips...")
        place_clips(cli, fcproj, data)

        print("[*] Verificando timeline contra el plan...")
        verified = verify_timeline(cli, fcproj, data)
        print("[OK] Timeline verificado: clips, pistas, inicios y duraciones coinciden.")

        if args.no_export:
            manifest = build_manifest(data, fcproj, None, None, False, verified, version)
            manifest["status"] = "timeline_ok"
            path = write_manifest(project, version, manifest)
            print(f"[OK] Timeline montado sin export: {path}")
            return 0

        print("[*] Exportando master desde la timeline de FilmCraft...")
        export_timeline(cli, fcproj, raw_export, master, repo_root, data)
        manifest = build_manifest(data, fcproj, raw_export, master, True, verified, version)
        if master.stat().st_size <= 0:
            raise RuntimeError("El master generado esta vacio.")
        path = write_manifest(project, version, manifest)
        print(f"[OK] Master exportado y normalizado: {posix_rel(master, project)}")
        print(f"[OK] Manifiesto: {path}")
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        if plan_path and plan_path.exists():
            try:
                failure = {
                    "schema_version": "1.1.0",
                    "status": "failed",
                    "engine": "FilmCraft CLI 0.9.0",
                    "created_utc": now_utc(),
                    "project": project.name,
                    "plan_file": posix_rel_or_abs(plan_path, project),
                    "plan_sha256": sha256_file(plan_path),
                    "error": str(exc),
                }
                fc_dir = project / "02_filmcraft"
                fc_dir.mkdir(parents=True, exist_ok=True)
                (fc_dir / "edit-manifest.json").write_text(
                    json.dumps(failure, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                )
            except Exception:
                pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
