# Lecture en direct simplifiée

Après identification de l'objet (automatique ou manuelle), les deux modes
utilisent les mêmes mesures, la même validation et le même calcul de conseil.

## Mesures

La lecture des zones du jet actuel et du reliquat est la seule source de
valeurs en direct. Une ligne encadrée peut faire l'objet de deux relectures
ciblées concordantes. Aucun chiffre n'est déduit des bornes ou de l'historique.
Le lecteur expérimental de révision n'est plus exécuté ni fusionné dans chaque
analyse. Les outils de révision restent séparés ; l'apprentissage des
tentatives de forgemagie et leurs contrôles avant/après sont conservés.

## Validation

WorkshopReadings confirme chaque ligne indépendamment sur des captures
successives. Une ligne instable ne remet plus à zéro les confirmations des
autres lignes visibles. Un changement de valeur ou de reliquat expire les
mesures hors écran. Un changement d'objet et une nouvelle tentative expirent
les données qui ne sont plus valides. Le reliquat zéro reste une valeur valide.

Le conseil attend toujours un ensemble complet de valeurs confirmées. Le
message d'attente cite les caractéristiques manquantes ou le reliquat à
confirmer. Les cibles et l'identité restent séparées des valeurs actuelles.

## Historique et affichage

L'historique conserve son rôle de détection et d'apprentissage. Un résultat
réel plus récent que le jet confirmé suspend l'ancien conseil en attendant
la relecture. Un ancien résultat ne peut pas effacer une mesure plus récente.
Le calcul n'utilise plus le chemin redondant de maintien d'un ancien conseil.

## Limites de vérification

Les tests couvrent les captures fournies, les lectures partielles, le défilement,
les événements tardifs, les changements successifs et les deux modes. Une
validation de la version relancée en jeu reste distincte des tests automatisés.
Le temps gagné dépend notamment de l'OCR installé et de la capture de fenêtre ;
aucun délai instantané ou taux de reconnaissance parfait n'est garanti.
