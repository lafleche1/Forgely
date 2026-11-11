"""Commandes : calibrate, run, benchmark et glyph-samples. Voir README.md."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
from time import perf_counter, perf_counter_ns
import cv2
import numpy as np
from .capture import MSSCapture
from .detection import InterfaceDetector
from .geometry import LayoutProfile, Rect
from .glyphs import GlyphReader, segment_glyphs
from .pipeline import VisionPipeline, ProfilePipeline
from .numbers import NumericReader, NumericStabilizer, calibrate_numbers


def read_image(path, gray=False):
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE if gray else cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError('Image introuvable ou illisible : '+str(path))
    return image


def write_image(path, image):
    if not cv2.imwrite(str(path), image):
        raise OSError('Impossible d’enregistrer '+str(path))


def build_pipeline(args):
    if isinstance(args.profile, list):
        from argparse import Namespace
        profiles = args.profile
        numbers = args.numbers or [None]*len(profiles)
        if len(numbers) != len(profiles):
            raise ValueError('Fournir un --numbers par --profile, dans le même ordre')
        return ProfilePipeline([build_pipeline(Namespace(**{**vars(args), 'profile':p,'numbers':n}))
                                for p,n in zip(profiles,numbers)])
    profile_path = Path(args.profile)
    profile = LayoutProfile.load(profile_path)
    reference = read_image(profile_path.parent/'anchor.png')
    reader = GlyphReader.from_directory(args.font) if getattr(args, 'font', None) else None
    ranges_path = profile_path.parent/'hsv.json'
    ranges = json.loads(ranges_path.read_text(encoding='utf8')) if ranges_path.exists() else None
    numeric = NumericReader.from_directory(args.numbers) if getattr(args,'numbers',None) else None
    return VisionPipeline(InterfaceDetector(reference, profile, args.threshold), reader, ranges, numeric,
                          adaptive_rows=getattr(args,'adaptive_rows',False))


def percentiles(values):
    return dict(zip(('p50_ms', 'p95_ms', 'p99_ms'), map(float, np.percentile(values, (50, 95, 99)))))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    calibrate = commands.add_parser('calibrate', help='Découper une vraie ancre et créer un profil')
    calibrate.add_argument('--image', required=True)
    for name in ('game', 'anchor', 'stats', 'chat'):
        calibrate.add_argument('--'+name, nargs=4, type=int, required=True, metavar=('X', 'Y', 'W', 'H'))
    calibrate.add_argument('--scale-tag', default='native')
    calibrate.add_argument('--output', required=True)
    for name in ('run', 'benchmark'):
        command = commands.add_parser(name)
        command.add_argument('--profile', required=True, action='append', help='Répétable : un profil par échelle native')
        command.add_argument('--threshold', type=float, default=.95)
        command.add_argument('--font', help='Dossier de glyphes réellement calibrés, facultatif')
        command.add_argument('--numbers', action='append', help='Un profil numérique par --profile, dans le même ordre')
        command.add_argument('--adaptive-rows', action='store_true', help='Retrouver les libellés après défilement')
        if name == 'run':
            command.add_argument('--monitor', type=int, default=1)
            command.add_argument('--region', type=int, nargs=4, metavar=('X', 'Y', 'W', 'H'))
            command.add_argument('--fps', type=float, default=60)
            command.add_argument('--frames', type=int, default=300)
            command.add_argument('--debug-dir', help='Sauvegarder seulement le premier frame détecté')
        else:
            command.add_argument('--image', required=True)
            command.add_argument('--iterations', type=int, default=100)
    samples = commands.add_parser('glyph-samples', help='Découper un masque binaire en exemples à étiqueter')
    samples.add_argument('--mask', required=True)
    samples.add_argument('--output', required=True)
    numeric = commands.add_parser('calibrate-numbers', help='Calibrer chiffres, puits et gardes de libellés')
    numeric.add_argument('--image',required=True)
    numeric.add_argument('--annotations',required=True)
    numeric.add_argument('--output',required=True)
    numeric = commands.add_parser('read-numbers', help='Lire un jet et le puits sans OCR externe')
    numeric.add_argument('--image',required=True)
    numeric.add_argument('--numbers',required=True)
    numeric.add_argument('--iterations',type=int,default=1)
    args = parser.parse_args(argv)
    cv2.setNumThreads(1)  # Éviter la concurrence de nombreux threads avec le jeu.
    try:
        if args.command == 'calibrate-numbers':
            annotations=json.loads(Path(args.annotations).read_text(encoding='utf8'))
            reader=calibrate_numbers(read_image(args.image),annotations,args.output)
            print(json.dumps(reader.read(read_image(args.image)).as_dict(),ensure_ascii=False,indent=2))
        elif args.command == 'read-numbers':
            if args.iterations<1:raise ValueError('Nombre d’itérations positif requis')
            image=read_image(args.image);reader=NumericReader.from_directory(args.numbers)
            values=[]
            for _ in range(args.iterations):
                started=perf_counter_ns();result=reader.read(image)
                values.append((perf_counter_ns()-started)/1e6)
            print(json.dumps(dict(reading=result.as_dict(),iterations=args.iterations,
                                  processing=percentiles(values)),ensure_ascii=False,indent=2))
        elif args.command == 'calibrate':
            image = read_image(args.image)
            game, anchor, stats, chat = (Rect(*getattr(args, k)) for k in ('game', 'anchor', 'stats', 'chat'))
            game.crop(image)  # Refuser un profil fondé sur une fenêtre tronquée.
            if not game.contains(anchor) or not game.contains(stats) or not game.contains(chat):
                raise ValueError('Toutes les zones doivent être dans le rectangle du jeu')
            template = anchor.crop(image).copy()
            profile = LayoutProfile(game.moved(-anchor.x, -anchor.y),
                                    stats.moved(-game.x, -game.y), chat.moved(-game.x, -game.y), args.scale_tag)
            InterfaceDetector(template, profile)  # Valider avant de sauvegarder.
            folder = Path(args.output)
            folder.mkdir(parents=True, exist_ok=True)
            write_image(folder/'anchor.png', template)
            profile.save(folder/'profile.json')
            from .masking import DEFAULT_RANGES
            (folder/'hsv.json').write_text(json.dumps(DEFAULT_RANGES, indent=2), encoding='utf8')
            print('Profil créé : '+str(folder/'profile.json'))
        elif args.command == 'glyph-samples':
            folder = Path(args.output)
            folder.mkdir(parents=True, exist_ok=True)
            entries = []
            for i, glyph in enumerate(segment_glyphs(read_image(args.mask, True))):
                name = f'sample-{i:04d}.png'
                write_image(folder/name, glyph.pixels)
                entries.append(dict(file=name, char='', line=glyph.line, box=glyph.box.tuple()))
            # Fichier volontairement distinct : les étiquettes vides ne doivent
            # jamais être chargées comme des références déjà fiables.
            (folder/'a-etiqueter.json').write_text(json.dumps({'glyphs': entries}, indent=2), encoding='utf8')
            print(f'{len(entries)} échantillons à étiqueter')
        else:
            pipeline = build_pipeline(args)
            if args.command == 'benchmark':
                if args.iterations < 1:
                    raise ValueError('Nombre d’itérations positif requis')
                image = read_image(args.image)
                pipeline.process(image)  # Préchauffage ; aucune capture dans ce test.
                durations, detected = [], 0
                for _ in range(args.iterations):
                    result = pipeline.process(image)
                    durations.append(result.processing_ns/1e6)
                    detected += result.detection is not None
                print(json.dumps(dict(scope='traitement_seul_sans_capture', detected=detected,
                                      numbers=result.numbers.as_dict() if result.numbers is not None else None,
                                      iterations=args.iterations, **percentiles(durations)), indent=2))
            else:
                region = Rect(*args.region) if args.region else None
                captures, processing, total, found, saved = [], [], [], 0, False
                numeric_candidates=numeric_stable=0
                stabilizer=NumericStabilizer()
                started = perf_counter()
                with MSSCapture(region, args.monitor) as capture:
                    for sequence,frame in enumerate(capture.frames(args.fps, args.frames),1):
                        result = pipeline.process(frame.bgr, (frame.region.x, frame.region.y))
                        stable=False
                        if result.numbers is not None and result.detection is not None:
                            numeric_candidates+=int(result.numbers.accepted)
                            stable=stabilizer.observe(result.numbers,
                                context=(tuple(str(Path(p).resolve()) for p in args.profile),
                                         result.detection.game.tuple()),
                                sequence=sequence,captured_ns=frame.started_ns)
                            numeric_stable+=int(stable)
                        else:stabilizer.reset()
                        captures.append(frame.capture_ns/1e6)
                        processing.append(result.processing_ns/1e6)
                        total.append((perf_counter_ns()-frame.started_ns)/1e6)
                        if result.detection:
                            found += 1
                            if args.debug_dir and not saved:
                                folder = Path(args.debug_dir)
                                folder.mkdir(parents=True, exist_ok=True)
                                write_image(folder/'stats.png', result.stats_bgr)
                                for color, mask in result.masks.items():
                                    write_image(folder/(color+'.png'), mask)
                                (folder/'detection.json').write_text(json.dumps(asdict(result.detection), indent=2), encoding='utf8')
                                (folder/'texts.json').write_text(json.dumps(result.texts, ensure_ascii=False, indent=2), encoding='utf8')
                                if result.numbers is not None:
                                    reading=result.numbers.as_dict();reading['temporal_confirmation']=stable
                                    (folder/'numbers.json').write_text(json.dumps(reading,ensure_ascii=False,indent=2),encoding='utf8')
                                saved = True
                elapsed = perf_counter()-started
                print(json.dumps(dict(frames=len(total), detected=found, observed_fps=len(total)/elapsed,
                                      numeric_candidate_frames=numeric_candidates,numeric_stable_frames=numeric_stable,
                                      last_numbers={**result.numbers.as_dict(),'temporal_confirmation':stable} if result.numbers is not None else None,
                                      capture=percentiles(captures), processing=percentiles(processing),
                                      capture_to_result=percentiles(total), target_ms=5,
                                      target_met_p95=percentiles(total)['p95_ms'] < 5), indent=2))
    except (ValueError, OSError, KeyError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
