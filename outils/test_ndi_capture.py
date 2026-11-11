#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_ndi_capture.py - Test d'acquisition vidéo en temps réel via OBS Studio et NDI pour Forgely (Copie Bureau).

Ce script permet de :
1. Détecter et lister les sources NDI actives (OBS Studio).
2. Se connecter au flux NDI et recevoir les trames en mémoire vive (< 5 ms).
3. Mesurer la latence réelle, le framerate (FPS) et la résolution.
4. Afficher et découper en direct les zones de l'atelier FM de DOFUS (reliquat, jet actuel, historique).
5. Exporter des captures complètes et découpées (touche 'S') pour calibration.

Usage:
    python outils/test_ndi_capture.py [--mock] [--no-gui] [--source "OBS"]
"""

import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
WORK_DIR = ROOT_DIR / "work"

# Calibration du flux OBS sur la capture de reference 1920 x 1080.
OBS_RECTS = {
    'workshop': (318, 176, 1172, 904),
    'title': (670, 181, 822, 209),
    'identity_title': (747, 221, 789, 262),
    'history': (319, 319, 557, 869),
    'reliquat': (633, 226, 711, 255),
    'effects': (568, 307, 929, 903),
    'review_effects': (568, 307, 1024, 903),
    'current_jet': (711, 307, 929, 903),
    'modifications': (929, 307, 1024, 903),
    'runes': (1024, 307, 1153, 903),
}
ZONES = {
    name: (x1 / 1920, y1 / 1080, x2 / 1920, y2 / 1080)
    for name, (x1, y1, x2, y2) in OBS_RECTS.items()
}


def zone_bounds(name, width, height):
    x1, y1, x2, y2 = ZONES[name]
    return round(x1 * width), round(y1 * height), round(x2 * width), round(y2 * height)


def workshop_view(frame):
    height, width = frame.shape[:2]
    x1, y1, x2, y2 = zone_bounds('workshop', width, height)
    return frame[y1:y2, x1:x2]


ZONE_COLORS = {
    'history': (0, 165, 255),       # Orange
    'current_jet': (0, 255, 0),     # Vert
    'reliquat': (255, 255, 0),      # Cyan (BGR)
    'runes': (0, 255, 255),         # Jaune
    'effects': (255, 128, 0),       # Bleu ciel
    'title': (255, 0, 255),         # Magenta
    'modifications': (128, 0, 255), # Rose
}

try:
    import numpy as np
    import cv2
except ImportError as e:
    print(f"[ERREUR] Dépendance manquante : {e}")
    print("Veuillez installer OpenCV et NumPy : pip install opencv-python numpy")
    sys.exit(1)

try:
    import NDIlib as ndi
    NDI_AVAILABLE = True
except ImportError:
    NDI_AVAILABLE = False


def print_banner():
    print("=" * 70)
    print("   FORGELY (COPIE BUREAU) - Test d'acquisition temps réel OBS Studio / NDI")
    print("=" * 70)


def print_obs_help():
    print("\n" + "!" * 70)
    print("  AUCUNE SOURCE NDI DÉTECTÉE SUR LE RÉSEAU LOCAL")
    print("!" * 70)
    print("\nPour activer le flux NDI dans OBS Studio :")
    print("  1. Lancez OBS Studio.")
    print("  2. Dans votre scène, ajoutez une source 'Capture de jeu' ou 'Capture de fenêtre'")
    print("     ciblant votre fenêtre DOFUS.")
    print("  3. Allez dans la barre de menu supérieure d'OBS :")
    print("     -> Outils (Tools) > Paramètres de sortie NDI (NDI Output Settings).")
    print("  4. Cochez 'Activer la sortie principale' (Main Output).")
    print("  5. Nommez la sortie (ex: 'OBS').")
    print("  6. Cliquez sur 'OK' puis relancez ce script.")
    print("\nAstuce : Vous pouvez tester immédiatement avec une image de simulation via :")
    print("  python outils/test_ndi_capture.py --mock\n")


def discover_sources(timeout_sec=4.0):
    """Recherche toutes les sources NDI disponibles."""
    if not NDI_AVAILABLE:
        return []

    if not ndi.initialize():
        print("[ERREUR] Impossible d'initialiser NDIlib.")
        return []

    print(f"[*] Recherche des sources NDI actives ({timeout_sec:.1f}s)...")
    find_inst = ndi.find_create_v2()
    if find_inst is None:
        print("[ERREUR] Impossible de créer l'instance de recherche NDI.")
        return []

    start = time.time()
    sources = []
    while time.time() - start < timeout_sec:
        ndi.find_wait_for_sources(find_inst, 500)
        sources = ndi.find_get_current_sources(find_inst)
        if sources:
            break

    ndi.find_destroy(find_inst)
    return sources


def crop_atelier_zones(frame):
    """Découpe chaque zone d'intérêt de l'atelier à partir des ratios relatifs."""
    h, w = frame.shape[:2]
    crops = {}
    for name in ZONES:
        x1, y1, x2, y2 = zone_bounds(name, w, h)
        if x2 > x1 and y2 > y1:
            crops[name] = frame[y1:y2, x1:x2]
    return crops


def draw_zones_overlay(frame, active=True):
    """Dessine les cadres et noms des zones de l'atelier FM sur la trame."""
    if not active:
        return frame

    overlay = frame.copy()
    h, w = frame.shape[:2]

    for name in ZONES:
        x1, y1, x2, y2 = zone_bounds(name, w, h)
        color = ZONE_COLORS.get(name, (0, 255, 0))

        # Rectangle de la zone
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)

        # Étiquette
        label = f"{name}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.45
        thickness = 1
        (lw, lh), _ = cv2.getTextSize(label, font, scale, thickness)
        cv2.rectangle(overlay, (x1, max(0, y1 - lh - 4)), (x1 + lw + 6, y1), color, -1)
        cv2.putText(overlay, label, (x1 + 3, y1 - 3), font, scale, (0, 0, 0), thickness, cv2.LINE_AA)

    return overlay


def save_snapshot(frame, snapshot_dir):
    """Enregistre la trame complète et chaque zone découpée sur le disque."""
    snapshot_dir = Path(snapshot_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
    target_folder = snapshot_dir / f"snapshot_{timestamp}"
    target_folder.mkdir(parents=True, exist_ok=True)

    # 1. Image complète
    full_path = target_folder / "full_frame.png"
    cv2.imwrite(str(full_path), frame)

    # 2. Zones individuelles
    crops = crop_atelier_zones(frame)
    for name, crop_img in crops.items():
        crop_path = target_folder / f"zone_{name}.png"
        cv2.imwrite(str(crop_path), crop_img)

    print(f"\n[+] Snapshot enregistré avec succès dans : {target_folder}")
    print(f"    - Image complète : {frame.shape[1]}x{frame.shape[0]}")
    print(f"    - {len(crops)} zones découpées (reliquat, current_jet, history...)")
    return target_folder


def run_mock_stream(no_gui=False, snapshot_dir=None, max_frames=None):
    """Simulateur de flux pour tester sans OBS Studio ouvert."""
    print("\n[*] Mode SIMULATION activé (--mock)")
    test_image_paths = [
        WORK_DIR / "kido_normalized_current.png",
        WORK_DIR / "kido_212821_normalized.png",
        WORK_DIR / "tetrist-current_jet.png"
    ]

    base_frame = None
    for p in test_image_paths:
        if p.exists():
            base_frame = cv2.imread(str(p))
            if base_frame is not None:
                print(f"[+] Image de test chargée : {p.name} ({base_frame.shape[1]}x{base_frame.shape[0]})")
                break

    if base_frame is None:
        # Générer une image synthétique si aucun PNG de test n'est présent
        print("[!] Aucune image locale trouvée, génération d'une trame synthétique 1920x1080.")
        base_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        base_frame[:] = (35, 30, 28)
        cv2.putText(base_frame, "FORGELY MOCK STREAM", (700, 540), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (200, 200, 200), 2)

    show_zones = True
    frame_count = 0
    total_frames = 0
    t0 = time.time()
    last_fps_time = t0
    fps = 0.0

    print("\nCommandes au clavier dans la fenêtre :")
    print("  [S] : Sauvegarder la trame et les découpes dans work/ndi_captures/")
    print("  [Z] : Activer / masquer les rectangles des zones")
    print("  [Q] ou [ÉCHAP] : Quitter\n")

    while True:
        loop_start = time.time()
        frame = base_frame.copy()

        frame_count += 1
        total_frames += 1
        elapsed = time.time() - last_fps_time
        if elapsed >= 0.5:
            fps = frame_count / elapsed
            frame_count = 0
            last_fps_time = time.time()

        h, w = frame.shape[:2]
        display_frame = draw_zones_overlay(frame, active=show_zones)

        # Affichage du HUD
        hud_text = f"MOCK NDI | {w}x{h} | FPS: {fps:.1f} | Latence: {(time.time() - loop_start)*1000:.2f} ms"
        cv2.putText(display_frame, hud_text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(display_frame, "[Z] Zones ON/OFF  [S] Snapshot  [Q] Quitter", (20, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)

        if not no_gui:
            cv2.imshow("Forgely - Test NDI (Simulation)", display_frame)
            key = cv2.waitKey(16) & 0xFF
            if key in (ord('q'), ord('Q'), 27):  # Q ou Echap
                break
            elif key in (ord('s'), ord('S')):
                save_snapshot(frame, snapshot_dir or (WORK_DIR / "ndi_captures"))
            elif key in (ord('z'), ord('Z')):
                show_zones = not show_zones
        else:
            time.sleep(1 / 60)
            if total_frames % 30 == 0:
                print(f"[Console] {hud_text}")

        if max_frames and total_frames >= max_frames:
            print(f"[+] Limite de {max_frames} trames atteinte en mode test.")
            break

    if not no_gui:
        cv2.destroyAllWindows()
    print("[*] Fin de la simulation.")


def run_camera_receiver(cam_index=1, no_gui=False, snapshot_dir=None, max_frames=None):
    """Réception en direct depuis la caméra virtuelle OBS (DirectShow)."""
    print(f"\n[*] Tentative de connexion à la Caméra Virtuelle OBS (Index {cam_index})...")
    cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print(f"[!] Impossible d'ouvrir la caméra {cam_index}, essai de l'index 0...")
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cam_index = 0

    if not cap.isOpened():
        print("[ERREUR] Aucune caméra virtuelle détectée.")
        return

    # Demander la pleine résolution 1080p
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[+] Connecté à la Caméra Virtuelle OBS (Index {cam_index}) : {actual_w}x{actual_h} !")

    print("\nCommandes interactives :")
    print("  [S] : Sauvegarder instantanément la trame et les zones (work/ndi_captures/)")
    print("  [Z] : Afficher / masquer le découpage des zones DOFUS")
    print("  [Q] ou [ÉCHAP] : Quitter\n")

    show_zones = True
    zoom_atelier = False
    win_name = "Forgely - Réception OBS Studio (Caméra Virtuelle / NDI)"
    if not no_gui:
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win_name, 1280, 720)

    frame_count = 0
    total_frames = 0
    t0 = time.time()
    last_fps_time = t0
    fps = 0.0

    try:
        while True:
            frame_start = time.time()
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            recv_latency_ms = (time.time() - frame_start) * 1000

            frame_count += 1
            total_frames += 1
            elapsed = time.time() - last_fps_time
            if elapsed >= 0.5:
                fps = frame_count / elapsed
                frame_count = 0
                last_fps_time = time.time()

            h, w = frame.shape[:2]
            display_frame = draw_zones_overlay(frame, active=show_zones)

            mode_str = "ZOOM ATELIER (1:1)" if zoom_atelier else "PLEIN ECRAN"
            hud_text = f"OBS Cam Virtuelle (Cam {cam_index}) | {w}x{h} | FPS: {fps:.1f} | Latence: {recv_latency_ms:.1f} ms | Mode: {mode_str}"
            cv2.putText(display_frame, hud_text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(display_frame, "[A] Zoom Atelier  [Z] Zones ON/OFF  [S] Snapshot  [Q] Quitter", (20, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)

            if zoom_atelier:
                # Zoom pixel-perfect 1:1 sur l'atelier de forgemagie
                view_frame = workshop_view(display_frame)
            else:
                view_frame = display_frame

            if not no_gui:
                cv2.imshow(win_name, view_frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord('q'), ord('Q'), 27):
                    break
                elif key in (ord('s'), ord('S')):
                    save_snapshot(frame, snapshot_dir or (WORK_DIR / "ndi_captures"))
                elif key in (ord('z'), ord('Z')):
                    show_zones = not show_zones
                elif key in (ord('a'), ord('A'), ord('w'), ord('W')):
                    zoom_atelier = not zoom_atelier
            else:
                if total_frames % 60 == 0:
                    print(f"[Console] {hud_text}")

            if max_frames and total_frames >= max_frames:
                print(f"[+] Limite de {max_frames} trames atteinte.")
                break

    except KeyboardInterrupt:
        print("\n[*] Arrêt demandé.")
    finally:
        cap.release()
        if not no_gui:
            cv2.destroyAllWindows()
        print("[+] Flux arrêté.")


def run_ndi_receiver(source_name=None, no_gui=False, snapshot_dir=None, max_frames=None):
    """Connexion et boucle de réception principale NDI (avec bascule automatique Cam Virtuelle)."""
    sources = discover_sources(timeout_sec=2.5)

    if not sources:
        print("\n[*] Aucun flux NDI réseau détecté. Vérification de la Caméra Virtuelle OBS...")
        # Vérifier si la caméra 1 ou 0 répond
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            cap.release()
            if ret:
                print("[+] Caméra Virtuelle OBS détectée sur l'index 1 ! Bascule automatique...")
                return run_camera_receiver(cam_index=1, no_gui=no_gui, snapshot_dir=snapshot_dir, max_frames=max_frames)

        cap0 = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if cap0.isOpened():
            ret, _ = cap0.read()
            cap0.release()
            if ret:
                print("[+] Caméra détectée sur l'index 0. Bascule...")
                return run_camera_receiver(cam_index=0, no_gui=no_gui, snapshot_dir=snapshot_dir, max_frames=max_frames)

        print_obs_help()
        choice = input("Voulez-vous lancer le mode simulation avec une image locale ? (o/n) : ").strip().lower()
        if choice in ('o', 'oui', 'y', 'yes', ''):
            run_mock_stream(no_gui=no_gui, snapshot_dir=snapshot_dir, max_frames=max_frames)
        return

    print(f"\n[+] {len(sources)} source(s) NDI détectée(s) :")
    selected_source = None
    for idx, s in enumerate(sources):
        name = s.ndi_name
        print(f"    [{idx}] {name}")
        if source_name and source_name.lower() in name.lower():
            selected_source = s
        elif selected_source is None and "obs" in name.lower():
            selected_source = s

    if selected_source is None:
        selected_source = sources[0]

    print(f"\n[*] Connexion à la source : {selected_source.ndi_name}")

    recv_settings = ndi.RecvCreateV3()
    recv_settings.source_to_connect_to = selected_source
    recv_settings.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
    recv_settings.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST

    receiver = ndi.recv_create_v3(recv_settings)
    if receiver is None:
        print("[ERREUR] Échec de la création du récepteur NDI.")
        return

    print("[+] Connecté au flux NDI avec succès !")
    print("\nCommandes interactives :")
    print("  [S] : Sauvegarder instantanément la trame et les zones (work/ndi_captures/)")
    print("  [Z] : Afficher / masquer le découpage des zones DOFUS")
    print("  [Q] ou [ÉCHAP] : Quitter\n")

    show_zones = True
    zoom_atelier = False
    win_name = "Forgely - Réception NDI OBS Studio"
    if not no_gui:
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win_name, 1280, 720)

    frame_count = 0
    t0 = time.time()
    last_fps_time = t0
    fps = 0.0

    try:
        while True:
            frame_start = time.time()
            t, v, _, _ = ndi.recv_capture_v2(receiver, 1000)

            if t == ndi.FRAME_TYPE_VIDEO:
                # v.data est un buffer numpy direct (BGRA/BGRX)
                frame_bgra = np.copy(v.data)
                # Conversion rapide en BGR pour OpenCV
                frame = cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2BGR)
                recv_latency_ms = (time.time() - frame_start) * 1000

                ndi.recv_free_video_v2(receiver, v)

                frame_count += 1
                elapsed = time.time() - last_fps_time
                if elapsed >= 0.5:
                    fps = frame_count / elapsed
                    frame_count = 0
                    last_fps_time = time.time()

                h, w = frame.shape[:2]
                display_frame = draw_zones_overlay(frame, active=show_zones)

                mode_str = "ZOOM ATELIER (1:1)" if zoom_atelier else "PLEIN ECRAN"
                hud_text = f"NDI: {selected_source.ndi_name} | {w}x{h} | FPS: {fps:.1f} | Latence: {recv_latency_ms:.1f} ms | Mode: {mode_str}"
                cv2.putText(display_frame, hud_text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.putText(display_frame, "[A] Zoom Atelier  [Z] Zones ON/OFF  [S] Snapshot  [Q] Quitter", (20, h - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)

                if zoom_atelier:
                    view_frame = workshop_view(display_frame)
                else:
                    view_frame = display_frame

                if not no_gui:
                    cv2.imshow(win_name, view_frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord('q'), ord('Q'), 27):
                        break
                    elif key in (ord('s'), ord('S')):
                        save_snapshot(frame, snapshot_dir or (WORK_DIR / "ndi_captures"))
                    elif key in (ord('z'), ord('Z')):
                        show_zones = not show_zones
                    elif key in (ord('a'), ord('A'), ord('w'), ord('W')):
                        zoom_atelier = not zoom_atelier
                else:
                    if frame_count % 60 == 0:
                        print(f"[Console] {hud_text}")

            elif t == ndi.FRAME_TYPE_NONE:
                # Pas de nouvelle trame disponible pendant le timeout
                continue
            elif t == ndi.FRAME_TYPE_STATUS_CHANGE:
                print("[*] NDI : Changement d'état de la connexion.")
            elif t == ndi.FRAME_TYPE_ERROR:
                print("[ERREUR] Erreur de réception NDI.")
                break

    except KeyboardInterrupt:
        print("\n[*] Arrêt demandé par l'utilisateur.")
    finally:
        print("[*] Libération des ressources NDI...")
        ndi.recv_destroy(receiver)
        ndi.destroy()
        if not no_gui:
            cv2.destroyAllWindows()
        print("[+] Terminé.")


def read_obs_history(image, ocr):
    """Read individual OBS history rows without certifying rune outcomes."""
    import re
    from forgely_history_reader import _foreground, _runs
    from forgely_jet import norm, parse_jet

    width, height = image.size
    scale = width / 238
    wide, narrow, right = (round(x * scale) for x in (35, 56, 181))
    pixels = np.asarray(image.convert("RGB"), dtype=int)
    background = np.median(pixels, axis=(0, 1))
    mask = _foreground(pixels[:, narrow:right], background)
    rows = _runs(np.flatnonzero(mask.sum(1) >= max(2, round(3 * scale))))
    for top, bottom in rows:
        if bottom - top < max(3, round(4 * scale)):
            continue
        center = (top + bottom) // 2
        y1 = max(0, center - round(9 * scale))
        y2 = min(height, center + round(10 * scale))
        readings = set()
        for left in (narrow, wide):
            line = norm(ocr(image.crop((left, y1, right, y2))).strip())
            line = line.replace("−", "-").replace("–", "-")
            line = re.sub(r"\bdommege\b", "dommage", line)
            line = re.sub(r"\bdommages fau\b", "dommages feu", line)
            line = re.sub(r"\b(?:reliquar|refiquat)\b", "reliquat", line)
            pool = re.fullmatch(r"([+-])\s*reliquat", line)
            if pool:
                readings.add(f"{pool[1]} reliquat")
                continue
            match = re.fullmatch(r"(?:[^\s\d+=-]+\s+)?([+-]?\s*\d{1,5}\s*%?\s*[a-z][a-z ]*)", line)
            if match:
                parsed = parse_jet(match[1])
                if len(parsed) == 1:
                    stat, value = next(iter(parsed.items()))
                    readings.add(f"{value:+d} {stat}")
        yield center, next(iter(readings)) if len(readings) == 1 else None


def check_obs_history(path):
    from PIL import Image

    sys.path.insert(0, str(ROOT_DIR / "Application"))
    from runeforge_observer import extract_text

    frame = cv2.imread(str(path))
    if frame is None:
        raise SystemExit(f"Image illisible : {path}")
    history = crop_atelier_zones(frame)["history"]
    image = Image.fromarray(cv2.cvtColor(history, cv2.COLOR_BGR2RGB))
    for row, result in read_obs_history(image, extract_text):
        print(f"y={row}: {result or 'Lecture incertaine'}")


def main():
    print_banner()
    parser = argparse.ArgumentParser(description="Test d'acquisition NDI OBS Studio pour Forgely")
    parser.add_argument("--source", type=str, default=None, help="Nom ou mot-clé de la source NDI")
    parser.add_argument("--mock", action="store_true", help="Lance la simulation avec une image locale de test")
    parser.add_argument("--no-gui", action="store_true", help="Exécute sans fenêtre graphique (mode console)")
    parser.add_argument("--cam", type=int, default=None, help="Force l'utilisation directe d'un index de caméra (ex: 1 pour OBS Virtual Cam)")
    parser.add_argument("--snapshot-dir", type=str, default=None, help="Dossier d'enregistrement des snapshots")
    parser.add_argument("--frames", type=int, default=None, help="Nombre max de trames à traiter avant de quitter")
    parser.add_argument("--ocr-image", type=Path, help="Relit l'historique d'une trame OBS enregistree")
    args = parser.parse_args()
    if args.ocr_image is not None:
        check_obs_history(args.ocr_image)
        return

    snapshot_path = Path(args.snapshot_dir) if args.snapshot_dir else (WORK_DIR / "ndi_captures")
    snapshot_path.mkdir(parents=True, exist_ok=True)

    if args.mock:
        run_mock_stream(no_gui=args.no_gui, snapshot_dir=snapshot_path, max_frames=args.frames)
    elif args.cam is not None:
        run_camera_receiver(cam_index=args.cam, no_gui=args.no_gui, snapshot_dir=snapshot_path, max_frames=args.frames)
    else:
        run_ndi_receiver(source_name=args.source, no_gui=args.no_gui, snapshot_dir=snapshot_path, max_frames=args.frames)


if __name__ == "__main__":
    main()
