# Correctifs de l'audit du 8 novembre 2026

Autorisation : « fais tout ça », sur les cinq correctifs proposés dans le chat.

Base : dossier local v22.16, sans métadonnées Git ; ce dossier n'est pas assimilé
au commit GitHub 71b40277. Les originaux des fichiers touchés sont conservés dans
`before/`. Ne pas modifier les observations, préférences ni politiques existantes.

## Choix retenus

Étendre les interfaces existantes plutôt que remplacer les moteurs. Le conseil
des objectifs mesurés reçoit les mêmes sources que celui du plan enregistré,
uniquement avec identité confirmée, snapshot stable et profil compatible.
Sans identité confirmée, garder le conseil sur les lectures sans emprunter les
données d'un autre équipement.

Les phases de puits restent des préférences parmi les candidats autorisés.
Si aucune rune préférée ne convient, reprendre les candidats légaux. Puits 1–5 :
petites runes préférées, repli explicite si nécessaire (dont restauration PA/PM),
poids non couvert affiché ; aucune hypothèse de poids gratuit ni over imposé.

La trace du classement expose score de base, mélange effectif, séquences,
économie, phase et choix final. Les pourcentages théoriques ne deviennent pas
des probabilités officielles. Une nouvelle version du sélecteur invalide les
anciens audits. Auditer le sélecteur final sur graines indépendantes, politique
figée, sans promotion automatique. Étendre la validation à toutes les politiques
et lier l'audit au contenu effectif (Q et visites compris).

## Exécution et vérification

1. Reproduire les blocages et le contournement de l'apprentissage avec des tests.
2. Unifier les sources de conseil et vérifier l'influence sur une rune finale.
3. Corriger les replis, les limites 1/5/20/51 et la restauration PA/PM.
4. Ajouter une trace structurée et une explication du classement réel.
5. Ajouter l'audit reproductible du sélecteur final, sans activation automatique.
6. Exécuter tests ciblés puis suite complète ; conserver résultats, empreintes
   et limites dans ce dossier. Réviser les échecs existants sans les masquer.

Pas de publication GitHub ni remplacement des exécutables dans cette étape :
les changements et résultats doivent d'abord être vérifiés dans cet espace.
