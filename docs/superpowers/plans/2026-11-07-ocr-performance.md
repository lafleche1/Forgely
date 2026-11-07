# OCR and reaction performance

User-authorized work: analyze Forgely and optimize reaction/OCR speed using parallel agents.
Preserve confirmed readings, ambiguity rejection, session isolation and current FM objectives.

## Implementation

- [x] OCR backend: reduce repeated discovery and identical concurrent work, bounded exact-pixel/config cache, preserve preprocessing/languages/errors.
- [x] Effects: reuse exact highlighted-line recovery, preserve changes/tooltips/retry; replace Python pixel loops with identical native Pillow operations.
- [x] UI data: cache small settings/icon metadata with filesystem invalidation; never cache away new budget events.
- [x] Window discovery: eliminate unnecessary process queries without caching stale window identity or geometry.
- [x] Capture/pipeline: cover full semantic regions, publish context changes, discard invalidated OCR, avoid fixed observer sleeps and reduce UI polling delay.
- [x] Regression tests, reproducible measurements, independent review, publish a PR after full checks.

## Verification focus

Exact pixel/config keys, cache bounds/TTL, thread failure recovery, changed highlighted
rows, current account/session generation, no lost/doubled rune events, continued GUI
responsiveness under bursts. Separate fixture/synthetic speedups from unmeasured Windows
end-to-end latency. No faster recognition configuration without accuracy evidence.

## Intégration et revue

- Revue indépendante : deux risques corrigés et testés : ancien observateur réinitialisant une nouvelle session et perte d'un événement accepté avant changement de contexte.
- Les reçus acceptés sont désormais durables et liés à l'identité confirmée d'origine ; les résultats OCR encore en cours restent invalidables. Le cache de récupération est protégé lors des accès concurrents.
- Main a reçu la référence Dofocus v22.01 (286b7e1) pendant le travail. Intégration à trois versions du fichier principal et récupération des autres fichiers modifiés ; aucune référence ni modification d'interface récente écrasée.
- Les réglages de langues, PSM et modèles OCR sont conservés. OMP_THREAD_LIMIT=1 est un défaut mesuré, remplaçable via l'environnement.
