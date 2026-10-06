"""
Étapes 2-4 : séquences pluri-saisonnières (précipitations/température) et étiages (VCN3).

Prérequis : avoir lancé 02_telecharger_debits.py et 03_inventaire_meteo.py, puis
renseigné la section CONFIG ci-dessous avec les postes choisis.
Lancer depuis la racine du projet :  python scripts/04_analyse_sequences_etiages.py
Sorties : figures/*.png et data/processed/*.csv
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pymannkendall as mk

# ----------------------------- CONFIG ------------------------------------
RAW, PROC, FIG = Path("data/raw"), Path("data/processed"), Path("figures")
for p in (PROC, FIG):
    p.mkdir(parents=True, exist_ok=True)

STATION_DEBIT = "M0500620"                 # Sarthe à Spay (principale). Changer pour Chambellay/Durtal.
POSTES_PLUIE = [72000000, 53000000]        # <-- REMPLACER par les NUM_POSTE choisis (script 03)
POSTE_TEMP = 72000000                      # <-- REMPLACER
DEBUT, FIN = 1960, 2025                    # fenêtre d'analyse
REF = (1991, 2020)                         # normale de référence Météo-France
SEUIL_SEC, SEUIL_CHAUD = 1/3, 2/3          # terciles
MOIS_ETIAGE = range(6, 12)                 # juin-novembre pour le VCN3
SAISONS = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
           6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}
rng = np.random.default_rng(42)
# --------------------------------------------------------------------------


def lire_meteo():
    fich = sorted(RAW.glob("MENSQ_*.csv*"))
    d = pd.concat([pd.read_csv(f, sep=";", compression="infer", low_memory=False) for f in fich])
    d["date"] = pd.to_datetime(d["AAAAMM"].astype(str), format="%Y%m", errors="coerce")
    d = d.dropna(subset=["date"]).drop_duplicates(["NUM_POSTE", "date"])
    pluie = (d[d["NUM_POSTE"].isin(POSTES_PLUIE)].pivot(index="date", columns="NUM_POSTE", values="RR")
             .mean(axis=1, skipna=True))
    temp = d[d["NUM_POSTE"] == POSTE_TEMP].set_index("date")["TM"]
    return pluie.rename("RR"), temp.rename("TM")


def saison_annee(serie, how):
    """Agrège par saison météo ; l'hiver DJF de l'année Y inclut décembre Y-1."""
    df = serie.to_frame("v")
    df["annee"] = df.index.year + (df.index.month == 12).astype(int)
    df["saison"] = df.index.month.map(SAISONS)
    g = df.groupby(["annee", "saison"])["v"]
    out = (g.sum(min_count=3) if how == "sum" else g.apply(lambda x: x.mean() if x.count() == 3 else np.nan))
    return out.unstack("saison")[["DJF", "MAM", "JJA", "SON"]]


def spi_gamma(x):
    """SPI par ajustement d'une loi gamma (avec masse en zéro)."""
    x = x.dropna()
    q = (x == 0).mean()
    a, loc, scale = stats.gamma.fit(x[x > 0], floc=0)
    h = q + (1 - q) * stats.gamma.cdf(x, a, loc=0, scale=scale)
    return pd.Series(stats.norm.ppf(np.clip(h, 1e-6, 1 - 1e-6)), index=x.index)


def vcn3(debits_j):
    """VCN3 annuel : minimum de la moyenne glissante sur 3 jours (juin-novembre)."""
    q = debits_j.set_index("date_obs_elab")["debit_m3s"].asfreq("D")
    r = q.rolling(3, min_periods=3).mean()
    r = r[r.index.month.isin(MOIS_ETIAGE)]
    return r.groupby(r.index.year).min()


# ---------------------------- 1. Données ----------------------------------
rr, tm = lire_meteo()
qj = pd.read_csv(RAW / f"debits_{STATION_DEBIT}_QmJ.csv", parse_dates=["date_obs_elab"])
pluie_s = saison_annee(rr, "sum")
temp_s = saison_annee(tm, "mean")
annees = [a for a in pluie_s.index if DEBUT <= a <= FIN]
pluie_s, temp_s = pluie_s.loc[annees], temp_s.reindex(annees)
print("Années :", annees[0], "-", annees[-1], "| saisons de pluie manquantes :", int(pluie_s.isna().sum().sum()))

# ---------------------- 2. Anomalies, SPI, terciles -----------------------
ref = [a for a in annees if REF[0] <= a <= REF[1]]
anom_p = pluie_s - pluie_s.loc[ref].mean()
anom_t = temp_s - temp_s.loc[ref].mean()
spi = pluie_s.apply(spi_gamma)
cl_p = pluie_s.apply(lambda s: pd.cut(s.rank(pct=True), [0, SEUIL_SEC, SEUIL_CHAUD, 1.0001],
                                      labels=["sec", "normal", "humide"], include_lowest=True))
cl_t = temp_s.apply(lambda s: pd.cut(s.rank(pct=True), [0, SEUIL_SEC, SEUIL_CHAUD, 1.0001],
                                     labels=["froid", "normal", "chaud"], include_lowest=True))
anom_p.to_csv(PROC / "anomalies_precip_saisonnieres.csv")
spi.to_csv(PROC / "spi3_saisonnier.csv")

# ---------------------------- 3. Séquences --------------------------------
A = (cl_p["DJF"] == "sec") & (cl_p["MAM"] == "sec")                     # déficit hiver + printemps
B = A & (cl_t["JJA"] == "chaud")                                         # + été chaud
seq = pd.DataFrame({"A_hiver_printemps_secs": A, "B_A_plus_ete_chaud": B})
seq.to_csv(PROC / "sequences_par_annee.csv")
n = len(annees)
print(f"\nSéquence A : {A.sum()} années (attendu si indépendance ≈ {n/9:.1f})")
print(f"Séquence B : {B.sum()} années (attendu si indépendance ≈ {n/27:.1f})")
dec = seq.groupby((seq.index // 10) * 10).sum()
print("\nFréquence par décennie :\n", dec)
dec.to_csv(PROC / "sequences_par_decennie.csv")

# ---------------------------- 4. Étiages ----------------------------------
v = vcn3(qj).rename("VCN3")
v = v[(v.index >= DEBUT) & (v.index <= FIN)]
d = seq.join(v, how="inner").dropna(subset=["VCN3"])
d.to_csv(PROC / "vcn3_et_sequences.csv")

res = {}
for col in seq.columns:
    g1, g0 = d.loc[d[col], "VCN3"], d.loc[~d[col], "VCN3"]
    if len(g1) >= 3:
        u = stats.mannwhitneyu(g1, g0, alternative="less")
        diffs = [np.median(rng.choice(g1, len(g1))) - np.median(rng.choice(g0, len(g0))) for _ in range(5000)]
        res[col] = dict(n_avec=len(g1), med_avec=g1.median(), med_sans=g0.median(),
                        p_mannwhitney=u.pvalue, ic95_diff_mediane=np.percentile(diffs, [2.5, 97.5]).round(2).tolist())
print("\nVCN3 : années avec séquence vs sans (test unilatéral : étiage plus sévère)")
print(pd.DataFrame(res).T.to_string())

tend = {}
for nom, s in [("VCN3", d["VCN3"]), ("Temp. été (JJA)", temp_s["JJA"].dropna()),
               ("Précip. hiver (DJF)", pluie_s["DJF"].dropna()), ("Précip. printemps (MAM)", pluie_s["MAM"].dropna())]:
    r = mk.original_test(s.values)
    tend[nom] = dict(tendance=r.trend, p=round(r.p, 3), pente_par_an=round(r.slope, 4))
print("\nTendances (Mann-Kendall, pente de Sen) :\n", pd.DataFrame(tend).T.to_string())
pd.DataFrame(tend).T.to_csv(PROC / "tendances_mann_kendall.csv")

# ---------------------------- 5. Figures ----------------------------------
# Fig 1 : frise des saisons
fig, ax = plt.subplots(figsize=(11, 3.2))
col = {"sec": "#c0392b", "normal": "#ecf0f1", "humide": "#2980b9"}
for i, s in enumerate(["DJF", "MAM"]):
    for a in annees:
        c = cl_p.loc[a, s]
        ax.add_patch(plt.Rectangle((a, i), 1, 1, color=col.get(c, "#ffffff"), lw=0))
for a in annees:
    c = cl_t.loc[a, "JJA"]
    ax.add_patch(plt.Rectangle((a, 2), 1, 1, color={"chaud": "#e67e22", "normal": "#ecf0f1", "froid": "#5dade2"}.get(c, "#fff"), lw=0))
for a in seq.index[seq["B_A_plus_ete_chaud"]]:
    ax.plot(a + 0.5, 3.3, "v", color="k")
ax.set_xlim(annees[0], annees[-1] + 1); ax.set_ylim(0, 3.7)
ax.set_yticks([0.5, 1.5, 2.5]); ax.set_yticklabels(["Précip. hiver", "Précip. printemps", "Temp. été"])
ax.set_title("Saisons extrêmes par année (rouge : sec, orange : chaud, bleu : humide/froid ; ▼ = séquence B)")
fig.tight_layout(); fig.savefig(FIG / "fig1_frise_saisons.png", dpi=160); plt.close(fig)

# Fig 2 : VCN3 et séquences
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(d.index, d["VCN3"], "-o", ms=3, color="gray", label="VCN3")
ax.scatter(d.index[d["A_hiver_printemps_secs"]], d.loc[d["A_hiver_printemps_secs"], "VCN3"], color="#e67e22", zorder=3, label="Séquence A")
ax.scatter(d.index[d["B_A_plus_ete_chaud"]], d.loc[d["B_A_plus_ete_chaud"], "VCN3"], color="#c0392b", zorder=4, label="Séquence B")
ax.set_ylabel("VCN3 (m³/s)"); ax.set_title(f"Étiage annuel (VCN3) – station {STATION_DEBIT}")
ax.legend(); fig.tight_layout(); fig.savefig(FIG / "fig2_vcn3_sequences.png", dpi=160); plt.close(fig)

# Fig 3 : boîtes à moustaches
fig, ax = plt.subplots(figsize=(6, 4))
groupes = [d.loc[~d["A_hiver_printemps_secs"], "VCN3"], d.loc[d["A_hiver_printemps_secs"] & ~d["B_A_plus_ete_chaud"], "VCN3"],
           d.loc[d["B_A_plus_ete_chaud"], "VCN3"]]
ax.boxplot([g for g in groupes if len(g)], labels=[l for g, l in zip(groupes, ["Sans A", "A seule", "B"]) if len(g)])
ax.set_ylabel("VCN3 (m³/s)"); ax.set_title("Sévérité d'étiage selon la séquence")
fig.tight_layout(); fig.savefig(FIG / "fig3_vcn3_par_sequence.png", dpi=160); plt.close(fig)
print("\nFigures écrites dans figures/")
