"""
Étape 1b : télécharger les débits (mensuels QmM et journaliers QmJ) des stations
présélectionnées du bassin de la Maine, via l'API Hub'Eau, et produire un bilan
de qualité (début, fin, mois manquants).

À lancer depuis la racine du projet :  python scripts/02_telecharger_debits.py
Sorties : data/raw/debits_<code>_QmM.csv, data/raw/debits_<code>_QmJ.csv,
          data/processed/bilan_stations_debit.csv

Si une erreur apparaît (nom de paramètre, code non reconnu), copiez-la-moi.
Astuce : si un code à 8 caractères ne marche pas, essayez le code station à
10 caractères trouvé dans stations_candidates.csv (script 01).
"""
import time
from pathlib import Path
import requests
import pandas as pd

BASE = "https://hubeau.eaufrance.fr/api/v1/hydrometrie/obs_elab"
RAW, PROC = Path("data/raw"), Path("data/processed")
RAW.mkdir(parents=True, exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)

# Stations repérées dans la liste DREAL Pays de la Loire (mise en service entre parenthèses)
STATIONS = {
    "M0500620": "Sarthe à Spay (1952)",
    "M1531610": "Loir à Durtal (1960)",
    "M3630910": "Mayenne à Chambellay (1965)",
    "M3600910": "Mayenne à Château-Gontier (1969)",
    "M0680610": "Sarthe à Saint-Denis-d'Anjou (1969)",
}
DEBUT, FIN = 1950, 2026


def get_all(params):
    url, p, out = BASE, dict(params), []
    p.setdefault("size", 20000)
    while url:
        r = requests.get(url, params=p, timeout=120)
        r.raise_for_status()
        j = r.json()
        out += j.get("data", [])
        url, p = j.get("next"), None
        time.sleep(0.2)
    return out


def telecharger(code, grandeur, pas_annees):
    frames = []
    for y0 in range(DEBUT, FIN + 1, pas_annees):
        y1 = min(y0 + pas_annees - 1, FIN)
        data = get_all({"code_entite": code, "grandeur_hydro_elab": grandeur,
                        "date_debut_obs_elab": f"{y0}-01-01",
                        "date_fin_obs_elab": f"{y1}-12-31"})
        if data:
            frames.append(pd.json_normalize(data))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["date_obs_elab"] = pd.to_datetime(df["date_obs_elab"])
    # Hub'Eau fournit les débits en L/s -> conversion en m3/s (à vérifier sur une valeur connue)
    df["debit_m3s"] = df["resultat_obs_elab"] / 1000.0
    return df.sort_values("date_obs_elab").drop_duplicates("date_obs_elab")


bilan = []
for code, nom in STATIONS.items():
    print(f"\n=== {nom} [{code}] ===")
    ligne = {"code": code, "station": nom}
    try:
        m = telecharger(code, "QmM", 80)       # mensuel : tout d'un coup
        m.to_csv(RAW / f"debits_{code}_QmM.csv", index=False)
        if len(m):
            attendu = pd.period_range(m["date_obs_elab"].min(), m["date_obs_elab"].max(), freq="M")
            manquants = len(attendu) - m["date_obs_elab"].dt.to_period("M").nunique()
            ligne.update(premier_mois=m["date_obs_elab"].min().date(),
                         dernier_mois=m["date_obs_elab"].max().date(),
                         n_mois=len(m), mois_manquants=manquants,
                         pct_manquant=round(100 * manquants / len(attendu), 1))
        print(ligne)
        j = telecharger(code, "QmJ", 10)        # journalier : par tranches de 10 ans
        j.to_csv(RAW / f"debits_{code}_QmJ.csv", index=False)
        ligne["n_jours"] = len(j)
    except Exception as e:
        ligne["erreur"] = str(e)
        print("ERREUR :", e)
    bilan.append(ligne)

pd.DataFrame(bilan).to_csv(PROC / "bilan_stations_debit.csv", index=False, encoding="utf-8-sig")
print("\nBilan écrit dans data/processed/bilan_stations_debit.csv")
print(pd.DataFrame(bilan).to_string())
