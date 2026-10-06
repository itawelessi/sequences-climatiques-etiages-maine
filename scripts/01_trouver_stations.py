"""
Étape 1 : repérer les stations hydrométriques candidates (bassin de la Maine)
et vérifier la longueur de leurs séries de débits mensuels via l'API Hub'Eau.

Usage :  python 01_trouver_stations.py
Sortie : stations_candidates.csv  (à m'envoyer, ou à ouvrir dans Excel)

Note : les noms de champs/paramètres de l'API peuvent évoluer. Si une erreur
apparaît, copiez-la-moi : on ajuste ensemble avec la doc
https://hubeau.eaufrance.fr/page/api-hydrometrie
"""
import requests
import pandas as pd

BASE = "https://hubeau.eaufrance.fr/api/v1/hydrometrie"
DEPARTEMENTS = "49,53,72"   # Maine-et-Loire, Mayenne, Sarthe (à élargir si besoin : 41, 28 pour le Loir)


def get_all(endpoint, params):
    """Récupère toutes les pages d'un endpoint Hub'Eau."""
    url, p, out = f"{BASE}/{endpoint}", dict(params), []
    p.setdefault("size", 1000)
    while url:
        r = requests.get(url, params=p, timeout=60)
        r.raise_for_status()
        j = r.json()
        out += j.get("data", [])
        url, p = j.get("next"), None   # l'URL "next" contient déjà les paramètres
    return out


def premiere_date(code_station):
    """Date de la plus ancienne observation de débit mensuel (QmM) d'une station."""
    try:
        d = get_all("obs_elab", {"code_entite": code_station,
                                 "grandeur_hydro_elab": "QmM",
                                 "size": 1, "sort": "asc"})
        return d[0]["date_obs_elab"][:10] if d else None
    except Exception as e:
        return f"erreur: {e}"


stations = get_all("referentiel/stations", {"code_departement": DEPARTEMENTS})
df = pd.json_normalize(stations)
print("Colonnes disponibles :", list(df.columns))
print(len(df), "stations trouvées")

cols = [c for c in ["code_station", "libelle_station", "libelle_cours_eau",
                    "libelle_departement", "en_service"] if c in df.columns]
df = df[cols].drop_duplicates("code_station").reset_index(drop=True)

# Interroger la 1re date de débit pour chaque station (peut prendre quelques minutes)
df["premiere_obs_QmM"] = [premiere_date(c) for c in df["code_station"]]
df = df.sort_values("premiere_obs_QmM")
df.to_csv("stations_candidates.csv", index=False, encoding="utf-8-sig")
print(df.head(30).to_string())
print("\nFichier écrit : stations_candidates.csv")
