"""Catalogue DOFUS local: mapping ID objet -> ID icône, sans deviner les noms.

Ce module n'identifie pas encore les objets à partir des captures d'écran.
"""
from __future__ import annotations
import csv
from functools import lru_cache
from pathlib import Path

CATALOGUE = Path(__file__).with_name("catalogue_objets_icones.csv")

@lru_cache(maxsize=1)
def charger_catalogue():
    resultat = {}
    with CATALOGUE.open("r", encoding="utf-8-sig", newline="") as fichier:
        for ligne in csv.DictReader(fichier, delimiter=";"):
            identifiant = int(ligne["item_id"])
            resultat[identifiant] = {
                "item_id": identifiant,
                "icon_id": int(ligne["icon_id"]),
                "name_id": int(ligne["name_id"]),
                "type_id": int(ligne["type_id"]),
                "niveau": int(ligne["niveau"]),
                "sprite_present": ligne["sprite_present"] == "oui",
                "fichier_sprite": ligne["fichier_sprite"],
            }
    return resultat

def fiche_objet(item_id):
    return charger_catalogue().get(int(item_id))

def objets_par_icone(icon_id):
    """Une même icône peut être partagée par plusieurs objets."""
    return [v for v in charger_catalogue().values() if v["icon_id"] == int(icon_id)]
