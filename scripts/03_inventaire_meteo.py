"""
Étape 1c : inventaire des postes Météo-France (fichiers mensuels départementaux)
pour choisir les stations de précipitations et de température.

Avant : télécharger dans data/raw/ les fichiers MENSQ_49_*, MENSQ_53_*, MENSQ_72_*
(.csv.gz) depuis meteo.data.gouv.fr (« Données climatologiques de base - mensuelles »).
Lancer :  python scripts/03_inventaire_meteo.py
Sortie : data/processed/inventaire_postes_meteo.csv

Colonnes attendues (à vérifier) : NUM_POSTE, NOM_USUEL, LAT, LON, AAAAMM, RR, TM
(RR = précipitations mensuelles en mm, TM = température moyenne mensuelle en °C).
"""
from pathlib import Path
import pandas as pd

RAW, PROC = Path("data/raw"), Path("data/processed")
PROC.mkdir(parents=True, exist_ok=True)
DEBUT, FIN = 1960, 2025   # fenêtre d'analyse visée

fichiers = sorted(list(RAW.glob("MENSQ_*.csv*")))
if not fichiers:
    raise SystemExit("Aucun fichier MENSQ_* trouvé dans data/raw/. Téléchargez-les d'abord.")

frames = []
for f in fichiers:
    df = pd.read_csv(f, sep=";", compression="infer", low_memory=False)
    print(f.name, df.shape, "colonnes :", list(df.columns)[:12], "...")
    frames.append(df)
d = pd.concat(frames, ignore_index=True)

d["date"] = pd.to_datetime(d["AAAAMM"].astype(str), format="%Y%m", errors="coerce")
d = d.dropna(subset=["date"])
d = d[(d["date"].dt.year >= DEBUT) & (d["date"].dt.year <= FIN)]
n_attendu = (FIN - DEBUT + 1) * 12

def resume(g):
    out = {"nom": g["NOM_USUEL"].iloc[0], "lat": g["LAT"].iloc[0], "lon": g["LON"].iloc[0],
           "premiere_annee": g["date"].dt.year.min(), "derniere_annee": g["date"].dt.year.max()}
    for var in ("RR", "TM"):
        if var in g.columns:
            ok = g[var].notna().sum()
            out[f"pct_dispo_{var}"] = round(100 * ok / n_attendu, 1)
    return pd.Series(out)

inv = d.groupby("NUM_POSTE").apply(resume).reset_index()
inv = inv.sort_values(["pct_dispo_RR"], ascending=False)
inv.to_csv(PROC / "inventaire_postes_meteo.csv", index=False, encoding="utf-8-sig")
print(f"\n{len(inv)} postes. Fenêtre {DEBUT}-{FIN} = {n_attendu} mois attendus.")
print("\nMeilleurs postes pour les PRÉCIPITATIONS :")
print(inv.head(15).to_string(index=False))
if "pct_dispo_TM" in inv.columns:
    print("\nMeilleurs postes pour la TEMPÉRATURE :")
    print(inv.sort_values("pct_dispo_TM", ascending=False).head(10).to_string(index=False))
