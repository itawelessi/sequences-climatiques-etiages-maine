# Séquences climatiques pluri-saisonnières et étiages dans le bassin de la Maine
**Analyse des observations 1970-2021 et lecture à l'horizon 2050**

Projet personnel exploratoire, inspiré de la démarche prospective *Transition(s) 2050* de l'ADEME et de sa méthodologie par étapes (cas d'étude, seuils observés, impacts, projections, sensibilité). Auteur : Essowèdéou Ignace TAWELESSI (Master STE, CRASTE-LF, Rabat).

## Question
Les déficits de pluie des saisons qui précèdent l'été (hiver, printemps) et la chaleur estivale permettent-ils d'expliquer la sévérité des étiages dans le bassin de la Maine (Sarthe, Mayenne, Loir) ? Les séquences « hiver sec puis printemps sec » sont-elles plus fréquentes, et ont-elles un effet visible sur les étiages ?

## Données
- **CAMELS-FR** (INRAE, Recherche Data Gouv, DOI 10.57745/WH7FJR) : séries journalières 1970-2021 de débits et de variables climatiques (SAFRAN / SIM2, Météo-France) agrégées par bassin versant.
- 5 stations : Sarthe à Saint-Denis-d'Anjou (`M068061010`, station principale), Sarthe à Neuville-sur-Sarthe (`M025061010`), Mayenne à Chambellay (`M363091010`), Mayenne à Château-Gontier (`M360091010`), Loir à Durtal (`M153161010`).
- L'archive (≈ 345 Mo) n'est pas versionnée : la télécharger depuis le DOI et la placer dans `data/raw/CAMELS_FR_time_series.zip`.

## Méthode
1. **Climat saisonnier** : précipitations (somme) et température (moyenne) par saison (DJF, MAM, JJA, SON ; l'hiver de l'année Y inclut décembre Y-1), 1971-2021.
2. **Seuils** : anomalies par rapport à la normale 1991-2020 ; indice SPI (loi gamma) par saison ; terciles.
3. **Étiage** : VCN3 annuel (minimum de la moyenne glissante sur 3 jours, juin-novembre), année écartée si moins de 95 % des jours ont un débit valide.
4. **Modèles** : régression de log(VCN3) sur les SPI d'hiver, de printemps et d'été et sur l'anomalie de température d'été (variables standardisées, erreurs robustes HC3) ; modèle « précurseurs » (hiver + printemps seuls) avec R² en validation croisée leave-one-out ; corrélations de rang de Spearman.
5. **Séquences** : A = hiver sec et printemps sec (tercile inférieur) ; B = A + été chaud (tercile supérieur) ; test de Mann-Whitney unilatéral sur le VCN3.
6. **Tendances** : Mann-Kendall et pente de Sen.
7. **Robustesse** : avec et sans 1976 ; avec et sans deux années atypiques d'une seule station (Saint-Denis 1974, Neuville 2009).

## Résultats principaux (version sans exclusion de données)
- **Les pluies saisonnières expliquent l'étiage.** Le modèle complet donne un R² de 0,52 à 0,75 selon la station (0,43 à 0,66 en validation croisée).
- **Les précurseurs seuls (hiver + printemps) ont un pouvoir prédictif réel** : R² de 0,34 à 0,45, et de 0,16 à 0,36 en validation croisée. Retirer 1976 ne modifie pas le signe ni l'ordre de grandeur des coefficients.
- **La chaleur estivale n'a un effet propre net que sur la Mayenne** (coefficient d'environ −0,20 par écart-type, p ≤ 0,003, robuste sans 1976). Sur la Sarthe et le Loir, il est proche de zéro une fois la pluie d'été prise en compte, même si la corrélation de rang avec le VCN3 est négative sur 4 stations sur 5.
- **Les séquences A sont associées à des VCN3 médians inférieurs de 25 à 39 %**, mais ce résultat est **fragile** : sans 1976, p = 0,04 à 0,11 selon la station (6 à 8 années seulement).
- **Tendances 1971-2021** : la température d'été augmente (+0,03 à +0,05 °C par an, p ≤ 0,001) ; aucune tendance détectable des pluies saisonnières ni du VCN3 (Loir à Durtal : p = 0,078, légère baisse).
- **Sensibilité aux exclusions** : écarter Saint-Denis 1974 et Neuville 2009 augmente le R² de ces deux stations (0,52 → 0,59 et 0,60 → 0,73) sans changer les conclusions.

## Limites
- **Période 1970-2021** : l'étiage de 2022 n'est pas dans les données.
- **Stations non indépendantes** : elles partagent le même climat et donc les mêmes années de séquence ; cinq stations ne valent pas cinq preuves.
- **Séquence B** : trois années seulement (1976, 1997, 2017) ; les tests à 4 stations reposent sur ces mêmes 3 années (Loir à Durtal : 2 années, non testé) et ne constituent pas un résultat établi.
- **Pluie d'été** : simultanée à l'étiage, ce n'est pas un précurseur ; d'où le modèle « précurseurs ».
- **Bas débits** : valeurs répétées et résolution limitée de la mesure (par exemple 233 L/s pendant 5 jours à Chambellay en 1976) ; les VCN3 extrêmes sont peu précis.
- **Anomalies de station** : Saint-Denis 1974 et Neuville 2009 sont atypiques par rapport aux autres stations ; leur origine (mesure, prélèvement, phénomène réel) n'est pas établie.
- **Influences humaines** (barrages, prélèvements) non analysées ; réanalyse SAFRAN, pas des mesures de stations.
- Plusieurs dizaines de tests ont été réalisés : certaines p-values proches de 0,05 sont à prendre avec prudence.

## Lecture à l'horizon 2050 : test de sensibilité (illustratif, non une prévision)
Méthode « delta » : la variabilité observée 1971-2021 est conservée, et on lui applique le changement que le modèle associe à un décalage de la température d'été (ΔT) et des pluies d'hiver et de printemps (facteur f). L'incertitude des coefficients est propagée par 5 000 tirages (intervalle à 90 %). Indicateur de décision : probabilité annuelle de passer sous le seuil sévère historique (10e centile du VCN3 observé), soit 10 % par construction sans changement.

- **Sarthe à Saint-Denis-d'Anjou** : le VCN3 médian varie à peu près proportionnellement aux pluies d'hiver et de printemps (environ −9 % pour −10 % de pluie, −18 % pour −20 %) ; la température d'été n'a pas d'effet détecté.
- **Mayenne (Chambellay, Château-Gontier)** : à pluies inchangées, +2 °C d'été réduit le VCN3 médian d'environ un tiers (−32 et −33 %) ; la fréquence des étiages sévères passe de 10 % à 34 % et 24 % des années (environ 1 année sur 3 à 4).
- **Sarthe à Neuville et Loir à Durtal** : effet de la chaleur incertain (intervalles incluant zéro) ; scénario +3 °C et −20 % de pluie : étiages sévères environ 1 année sur 4 à 5 (26 % et 22 %).
- Pour le scénario +3 °C et −20 % de pluie, les valeurs de la Mayenne (64 % et 69 % des années) sortent du domaine d'observation du modèle et ne doivent pas être prises au pied de la lettre.

**Précautions de lecture.** Les scénarios sont des décalages arbitraires de la distribution 1971-2021 (déjà marquée par un réchauffement estival), pas des projections régionalisées (DRIAS, Explore2). La relation estimée porte sur les variations d'une année à l'autre : elle ne garantit pas la réponse des débits à un réchauffement tendanciel. Aucune tendance des étiages n'est observée alors que la température d'été a augmenté, ce qui invite à la prudence sur l'effet de la chaleur. Les usages de l'eau (prélèvements, irrigation, barrages) ne sont pas modélisés ; ils distinguent pourtant les scénarios de Transition(s) 2050, qui partagent la même hypothèse climatique.

## Reproduire
```
pip install -r requirements.txt
python scripts/05_inspecter_camels.py        # inspection de l'archive
python scripts/06_analyse_camels.py          # analyse (APPLIQUER_EXCLUSIONS = False pour la version principale)
python scripts/07_robustesse_et_figures.py   # robustesse et figures
python scripts/08_sensibilite_2050.py        # test de sensibilité (figures camels_fig5, camels_fig6)
```
Sorties : `data/processed/camels_*.csv` et `figures/camels_*.png`.
