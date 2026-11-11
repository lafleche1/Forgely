# Livraison locale — vidéos et raisonnement — 8 novembre 2026

## Résultat

Onglet Sessions vidéo intégré à l’entraîneur existant : MP4 locaux, aperçu et navigation temporelle, cinq zones réglables, analyse visuelle sans audio, arrêt/reprise, comparaison avant/après, correction par tableau de valeurs, rejet, rapports HTML/JSON/CSV et transmission des observations qualifiées à Forgely. Les vidéos originales restent à leur emplacement.

L’identité manuelle d’un objet illisible est disponible avec confirmation explicite de la portée. Elle ne complète aucune caractéristique manquante. Les événements multiples, les coupes et les appariements incomplets restent exclus. Le puits inconnu reste inconnu. Les corrections sont conservées à la reprise ; les analyses précédentes sont archivées lorsque les réglages changent.

La calibration conserve une provenance vidéo distincte des captures écran. Une retransmission remplace les contributions précédentes de la même vidéo, y compris après rejet. Les simulations ne deviennent pas des observations réelles. Le SC conserve le puits ; la comptabilité des SN/EC tient compte du gain nominal et des pertes constatées.

Le conseiller et l’entraîneur partagent désormais les raisons vérifiables des choix : cible, maximum naturel, gain/poids de la rune, valeur projetée et rôle du reliquat. Le conseiller expose les actions préparatoires possibles ; un mode d’entraînement par objet permet de les explorer avec un surplus limité à 3 PWR sur des lignes légères existantes. Aucun crédit de puits avant une perte, aucun bonus pour fabriquer du puits, aucune promotion automatique de ces politiques expérimentales. Le mode classique et ses archives sont conservés.

## Fichiers de production

| Fichier | Changement |
|---|---|
| Application/forgely_video_store.py | Nouveau : sessions atomiques, historique, qualification et transmission idempotente |
| Application/forgely_video_analysis.py | Nouveau : MP4, lecteurs visuels, cache versionné et appariement temporel conservateur |
| Application/forgely_video_report.py | Nouveau : rapports, fréquences et incertitude, consommation et pertes par objet |
| Application/forgely_video_ui.py | Nouveau : interface de vidéos, zones, revue et corrections |
| Application/forgely_reasoning.py | Nouveau : candidats et explications partagés |
| Application/entrainer_forgely.py | Onglets, fermeture coordonnée et option de comparaison préparatoire |
| Application/forgely_labo_live.py | Lecture des observations vidéo qualifiées et actualisation des corrections |
| Application/forgely_rl.py | Espace d’actions préparatoires optionnel, sans changement de récompense |
| Application/forgely_training.py | Mode expérimental, signature distincte et encodage exact du surplus |
| Application/forgely_decision.py | Raisons de la rune conseillée et options préparatoires expliquées |
| Application/forgely_trained_policy.py | Exclusion du nouveau domaine expérimental de l’activation en direct |
| Application/auditer_politique.py | Audit capable de recréer le mode préparatoire du modèle évalué |
| Entrainement_Forgely.exe | Lanceur natif reconstruit, utilisant les sources et .venv du PC |

L’ancien exécutable est conservé dans `.test-tmp/video-backup-20261108/Entrainement_Forgely-avant-video.exe`. Les fichiers modifiés ont une sauvegarde ; pour auditer_politique.py, l’original provient de la copie Git ayant servi à la précédente installation validée. Inventaire des chemins et SHA256 avant/après : `.test-tmp/video-delivery-inventory.json`.

## Vérifications effectuées

- Suite complète : **1 667 tests réussis, 27 ignorés, 42 sous-tests réussis**, zéro échec. Journal `.test-tmp/final-video-tests.log`.
- Les six tests du panneau vidéo passent séparément après stabilisation de leur contexte Tk partagé. La suite complète précédente avait ignoré ponctuellement un de ces cas lorsque Windows ne créait pas un nouvel écran Tk.
- MP4 synthétique traité avec le véritable OpenCV et Tesseract : objet Gelano, rune Ga Pa, PA 0 → 1, SC et puits 17 → 17 correctement reconnus et rapportés. Aucun transfert des essais synthétiques vers la base réelle.
- Cas difficiles vérifiés : persistance du journal, plusieurs tentatives rapprochées, jet mis à jour avant le journal et inversement, interruption/reprise, correction d’une rune, rejet et rétraction, puits inconnu, profil incomplet, fermeture des connexions SQLite sous Windows.
- Interface et boutons vérifiés à 1 020 × 700 et 860 × 620, ainsi que le bouton de sauvegarde de la revue.
- Compilation Python réussie. Lanceur natif compilé et auto-test terminé avec code de sortie 0.
- Deux revues indépendantes, corrections des défauts importants vérifiées par tests rouges puis verts.

Mesure locale à chaud sur un état du Cycloïde, sans capture ni OCR : médiane du conseil **0,444 ms**, percentile 95 **0,728 ms** ; avant ajout des raisons/options, médiane **0,318 ms**. Génération des options seule : médiane **0,088 ms**. Il s’agit de temps de calcul, pas d’un taux de réussite ni d’une mesure de latence de lecture en jeu. Données `.test-tmp/reasoning-performance.json`.

## Portée et limites

Les fichiers installés de DofusFM ont été inspectés statiquement, sans lancement et sans charger leurs modules. Leur documentation confirme certaines intentions de sélection ; la formule complète compilée, les seuils exacts et le taux de réussite réel restent inconnus. Aucun composant du bot n’a été incorporé, aucune fonction de clic dans le jeu n’a été ajoutée.

Les essais terminés sur les overs n’ont pas montré de gain global dans le simulateur actuel ; le mode reste donc expérimental et désactivé par défaut. Cela ne réfute pas l’intérêt d’autres stratégies pratiquées en jeu. Voir ESSAI_OVERS_TEMPORAIRES_2026-11-08.md et ANALYSE_DOFUS_FM_SERVER_2026-11-08.md.

Une vraie session MP4 annotée reste nécessaire pour mesurer la reconnaissance et l’utilité des nouvelles observations en conditions réelles. Une vidéo lisible ne garantit pas que chaque décision du joueur est optimale. L’entraînement virtuel conserve son modèle déclaré ; les observations vidéo qualifiées calibrent les estimations du conseiller sans prétendre dévoiler les probabilités du serveur.

**Publication : aucun nouveau commit ni push GitHub pour ces ajouts.** La PR précédente de fusion n’a pas été modifiée. Aucune archive distribuée, aucun ZIP/BAT existant ni dossier d’apprentissage utilisateur n’a été supprimé.
