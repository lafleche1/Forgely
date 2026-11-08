# Terminer et évaluer ma session

## Utilisation

Définir l'objet et les minima souhaités, puis laisser Forgely lire un jet et un puits confirmés. Le suivi de session commence automatiquement. Dans l'atelier, « Bilan de session », ou dans le détail du conseil, « Terminer et évaluer ma session », clôture un bilan local. « Exporter le bilan (.zip) » crée un paquet JSON + HTML que l'utilisateur peut joindre à une conversation. Rien n'est envoyé automatiquement.

Le dossier local `bilans_sessions`, à côté de la base d'observations Forgely, conserve les bilans. Le JSON contient l'objet, les cibles figées, le niveau, le jet de départ, la fin confirmée si disponible, les tentatives enregistrées, les prix de référence au début et les diagnostics. L'HTML est lisible hors ligne. Les textes sont échappés et aucun script externe n'est chargé.

## Ce que le rapport mesure

- L'atteinte des minima est affirmée seulement pour un jet final confirmé sur le même objet, objectif et capture. Si la lecture est en attente ou l'identité a changé : résultat final inconnu.
- Les tentatives sont bornées par deux curseurs SQLite et filtrées par objet. Les réceptions identifiées comme issues d'une autre capture sont exclues. Les actions sans rune dans la période ne sont pas attribuables à cet objet avec certitude et sont signalées séparément.
- Le coût est la somme des prix de référence figés au début pour les tentatives enregistrées, pas le prix d'achat réel, la valeur du stock ou une garantie que l'OCR a capté chaque clic. Les prix absents rendent le coût incomplet. Le budget général de l'application n'est pas remis à zéro par le bouton.
- Le détail des prévisions est journalisé avant l'arrivée du résultat. Une prévision doit avoir une frame strictement antérieure au résultat dans la même capture, concerner la rune effectivement passée et le même état complet avant la pose. Une transition complète et comptablement cohérente est nécessaire avant de la noter.
- Le score Brier est la moyenne de la somme des trois erreurs quadratiques entre SC/SN/EC prédits et résultat observé. Il va de 0 à 2 ; plus bas est meilleur. Ce n'est pas un pourcentage de fiabilité, et un petit nombre d'essais ne suffit pas pour conclure. Le rapport affiche aussi les comptes attendus et observés sur les seuls essais comparables.
- Le JSON exporté conserve les tentatives et les prévisions, leurs états avant/après disponibles, versions de modèle, frames et diagnostics pour permettre une analyse ultérieure. Il n'exporte pas la base entière, les captures d'écran ou d'autres sessions.

Un résultat reçu tardivement, une prévision manquante, une autre rune jouée ou une lecture partielle ne sont pas transformés en erreur prouvée de l'algorithme. Un échec isolé ne permet pas de distinguer malchance et mauvais conseil. Des erreurs de lecture peuvent rester cohérentes entre elles : le contrôle comptable n'est pas une certification indépendante de l'OCR.

## Comment Forgely apprend

Chaque transition réelle qualifiée continue d'être enregistrée dans `fusion_contexts` et le laboratoire est notifié. Les contextes exacts (objet/rune/jet/puits) alimentent la calibration du modèle. Le seuil minimal reste de 30 essais comparables et le prior du modèle vaut 200 essais : le bilan ne change pas silencieusement ces paramètres. Chaque nouvelle observation enrichit la base, mais les conseils ne changent que lorsque les conditions sont réunies.

Les prévisions sauvegardées sont évaluées telles qu'elles existaient avant le résultat ; elles ne sont pas reconstruites après calibration avec ce même résultat. Les nouvelles expériences peuvent influencer les conseils suivants. Cela évite de mesurer une prédiction qui connaît déjà sa réponse.

Aucun bilan n'est réimporté comme de nouvelles tentatives. Les simulations restent exclues des observations réelles et du score de validation. Cette mise à jour n'introduit pas de RL, de mélange 40/60 ou de garantie d'amélioration à chaque session.

## Limites de suivi

Les événements précédant le premier objet/objectif confirmé, perdus par la capture ou arrivant après la clôture peuvent manquer au bilan. Les valeurs et les prix d'une session sont figés dans son rapport ; les observations en base ne sont pas corrigées automatiquement. Changer d'objet, de cible, de niveau ou de capture clôture l'ancien segment sans certifier son jet final. Fermer l'application sauvegarde un segment interrompu avec fin inconnue.

Le journal d'évaluation est stocké dans des tables séparées de la même base SQLite ; la sauvegarde existante de cette base les inclut. Les fichiers JSON/HTML sont enregistrés localement. L'export est explicite et ne transmet pas de message à un tiers.
