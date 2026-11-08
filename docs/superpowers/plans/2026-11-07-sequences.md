# Conseils par sequences

Choix autorise : comparer des suites de runes pour atteindre tout le jet souhaite, sans monnaie. Garder les observations reelles et virtuelles distinctes et le reglage 60/40 lorsque le reel comparable existe.

Architecture : planificateur de simulations borne dans le worker existant. Chaque premiere rune est suivie de poses adaptees au jet obtenu ; reussite du jet complet prioritaire, deficit final secondaire. Annuler les etats perimes. Le fil Tk ne fait aucune recherche.

- [x] Tests : objectif complet, preservation de l observation, reproductibilite, annulation, integration et repli.
- [x] Ajouter forgely_sequence.py : simulations courtes avec continuation par le classement existant.
- [x] Publier les sequences dans les preuves du worker et remplacer le classement de la part simulation lorsque toutes les options sont comparees.
- [x] Evaluer sur des graines distinctes et comparer au classement initial ; ne pas confondre simulation et gain reel.

Contraintes : pas de nouvelle automatisation du jeu, pas de promesse de taux reel, pas de nouvelles regles de malus sans validation. La recherche a horizon borne reste une approximation ; le classement immediat reste disponible pendant le calcul.


Implementation complementaire demandee : reprise de 25 % des episodes depuis un etat intermediaire d echec (buffer borne a 64 etats, uniquement simulation). Evaluation toujours depuis le jet initial et graines distinctes. Anciennes politiques compatibles conservees : schema Q et recompense inchanges.

Calibration de la premiere pose : distributions SC/SN/EC du meme objet, du meme jet complet et du meme puits, au moins 30 transitions. Part reelle ramenee vers le modele selon n/(n+100) ; influence OCR non verifiee multipliee par .25. Melange configure .6 reel/.4 modele. Aucune observation synthetique ne rejoint les donnees reelles. Les mecanismes de pertes et les etats suivants sans donnees restent ceux du simulateur. Une revision des donnees invalide le cache.

Recherche : 16 continuations par premiere rune, 32 si resultat incertain, horizon 8. Verification sur 32 autres graines avant publication ; rejet en cas de regression observee. Ce filtre ne prouve pas une superiorite statistique. Les politiques apprises deja validees peuvent guider les continuations, sans doubler la part reelle.

Comparatif pilote reproductible : Application/evaluer_sequences.py ; trois etats de l anneau du Cycloide, 64 sessions d evaluation par etat, graines de planification, verification et evaluation separees. 21 jets complets /192 contre 13/192, horizon 8. Le dernier cas reste 0/64 pour les deux : resultat limite, pas une garantie de gain en jeu. Le temoin est le classement heuristique sans donnees personnelles et la continuation est heuristique, pas une ancienne application complete enregistree. Rapport : docs/sequence-evaluation-2026-11-07.json.


Revue finale : la verification porte sur la premiere rune qui sera effectivement publiee, avec les memes preuves modele/reelles et les memes politiques chargees que le classement courant. Une correction ulterieure ne peut pas substituer une rune non verifiee. Les continuations excluent les actions bloquees par le modele. Tests de regression ajoutes sur ces deux cas. La recherche reste bornee et ne couvre pas toutes les preparations possibles ni tous les traitements de malus.

Validation finale : 1343 tests reussis, 25 ignores et 42 sous-tests reussis ; revue independante du correctif de selection realisee. Les tests graphiques facultatifs ne sont pas inclus dans cette execution.
