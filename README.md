# IESF — Observatoire des Ingénieurs & Simulateur de Carrière

Tableau de bord interactif et simulateur de carrière construits à partir des données de l'enquête annuelle IESF (Ingénieurs et Scientifiques de France), enrichis par les données ouvertes de [data.gouv.fr](https://www.data.gouv.fr).

---

## Table des matières

1. [Présentation du projet](#présentation-du-projet)
2. [Sources de données](#sources-de-données)
3. [Architecture technique](#architecture-technique)
4. [Détail des onglets du dashboard](#détail-des-onglets-du-dashboard)
5. [Simulateur de carrière — fonctionnement détaillé](#simulateur-de-carrière--fonctionnement-détaillé)
6. [Intégration data.gouv.fr (InserSup)](#intégration-datagouvfr--insersup)
7. [Lancer l'application](#lancer-lapplication)
8. [Structure du projet](#structure-du-projet)

---

## Présentation du projet

L'IESF publie chaque année une enquête auprès des ingénieurs et scientifiques français couvrant leur situation professionnelle, leurs rémunérations, leur rapport au travail et aux nouvelles technologies. Ce projet transforme ces données brutes (fichiers Excel Sphinx iQ) en un **observatoire interactif** accessible depuis un navigateur.

L'objectif principal est double :

- **Analyser** la population des ingénieurs français sur les dimensions clés : profil démographique, emploi, rémunération, télétravail, IA, satisfaction.
- **Orienter** les jeunes ingénieurs en début de carrière grâce à un simulateur qui croise les données IESF avec les données nationales de l'insertion professionnelle (InserSup, Ministère de l'Enseignement supérieur).

---

## Sources de données

### Données IESF (enquêtes 2024 et 2025)

| Fichier | Feuille | Répondants approx. |
|---|---|---|
| `exp_Questionnaire 2025.xlsx` | `Questionnaire 2025` | ~10 000 |
| `exp_Questionnaire_2024.xlsx` | `Questionnaire_2024` | ~10 000 |

Chaque fichier contient environ **495 colonnes** couvrant :
- Profil (diplôme, école, année de diplôme, âge, genre, nationalité)
- Situation professionnelle (statut, secteur, taille d'entreprise, nature, type de contrat)
- Rémunération (salaire brut, part variable, dividendes, avantages)
- Conditions de travail (télétravail, responsabilités, encadrement)
- Usages technologiques (IA, outils, compétences)
- Satisfaction, mobilité, logement, engagement associatif

Les données sont **pondérées** (colonne `poids`) pour être représentatives de la population réelle des ingénieurs français. Tous les calculs de médiane et de pourcentage utilisent ces poids.

### Données data.gouv.fr — InserSup

Le dispositif **InserSup** du Ministère de l'Enseignement supérieur mesure l'insertion professionnelle des diplômés du supérieur à **30 mois** après l'obtention du diplôme. Les données sont interrogées en temps réel via l'API Open Data :

```
https://data.enseignementsup-recherche.gouv.fr/api/explore/v2.1/catalog/datasets/fr-esr-insersup/records
```

Champs utilisés :
- `taux_dinsertion` — % de diplômés en emploi à 30 mois
- `salaire_net_median_des_emplois_a_temps_plein` — salaire net médian mensuel
- `taux_emplois_cadre_ou_professions_intermediaires` — % accédant à des postes cadres
- `taux_emplois_stables` — % en CDI ou fonction publique

---

## Architecture technique

```
dashboard.py          ← application Streamlit unique (tous les onglets)
├── Chargement des données
│   ├── load_2025()       # lecture Excel 2025, nettoyage, cache Streamlit
│   ├── load_2024()       # idem pour 2024
│   └── load_insersup()   # appel API data.gouv.fr, cache 24h
├── Fonctions utilitaires
│   ├── salaire_median_pondere()     # médiane pondérée par poids
│   ├── salaire_quantile_pondere()   # quantile pondéré (P25, P75)
│   ├── pct()                        # pourcentage pondéré d'une valeur
│   ├── bar_chart()                  # graphique barres horizontal/vertical
│   ├── pie_chart()                  # graphique camembert
│   └── salary_by_group_bar()        # médiane salariale par groupe
├── Sidebar (filtres globaux)
│   ├── Genre
│   ├── Tranche d'âge
│   ├── Secteur
│   └── Situation professionnelle
└── Onglets (tabs)
    ├── 👤 Profil
    ├── 🏢 Emploi & Secteurs
    ├── 💶 Rémunération
    ├── 💻 Travail & IA
    ├── 📊 Comparaison 2024-2025
    └── 🎯 Simulateur de Carrière
```

**Stack :**

| Bibliothèque | Usage |
|---|---|
| `streamlit 1.57` | Interface web, widgets, cache |
| `pandas` | Manipulation des données tabulaires |
| `plotly express` | Graphiques interactifs |
| `numpy` | Calculs numériques |
| `requests` | Appels API data.gouv.fr |
| `openpyxl` | Lecture des fichiers Excel |

---

## Détail des onglets du dashboard

### Chargement sélectif des colonnes

Les fichiers Excel contiennent ~495 colonnes, mais seul un sous-ensemble est chargé via un dictionnaire `{index_colonne: nom_propre}`. Cela réduit la mémoire et le temps de chargement.

```python
COLS_2025 = {
    2: "diplome",
    59: "age",
    60: "genre",
    69: "region",
    78: "activite",
    101: "secteur",
    120: "cadre",
    211: "salaire_brut",
    666: "salaire_corrige",  # salaire pondéré et corrigé par IESF
    ...
}
```

Le fichier 2024 utilise `skiprows=[1]` pour sauter la ligne de sous-en-tête Sphinx.

### Médiane pondérée

Toutes les médianes salariales sont **pondérées** pour respecter la représentativité de l'échantillon :

```python
def salaire_median_pondere(df, col="salaire_corrige"):
    sub = df[[col, "poids"]].dropna().sort_values(col)
    cumw = sub["poids"].cumsum()
    half = sub["poids"].sum() / 2
    return float(sub.loc[cumw >= half, col].iloc[0])
```

Le même principe s'applique aux quantiles P25 et P75 (utilisés dans le simulateur).

### Onglet 1 — Profil

Distribution par diplôme, genre, tranche d'âge, région. Graphique empilé H/F par tranche d'âge pour visualiser l'évolution de la parité selon les générations.

### Onglet 2 — Emploi & Secteurs

Répartition par secteur d'activité, nature d'entreprise, statut cadre, responsabilités hiérarchiques, type de contrat, activité principale.

### Onglet 3 — Rémunération

Distribution des salaires bruts annuels, médiane par genre, médiane par tranche d'âge, médiane par secteur et nature d'entreprise. Part variable : prévalence et distribution des montants.

### Onglet 4 — Travail & IA

Pratique du télétravail (taux global, jours/semaine, top secteurs). Usages de l'IA : taux d'adoption, types d'outils utilisés, adoption par tranche d'âge, auto-évaluation des compétences. Satisfaction globale au travail.

### Onglet 5 — Comparaison 2024-2025

Évolution du salaire médian brut entre 2024 et 2025 (variation en %). Superposition des distributions salariales. Évolution de l'écart H/F. Évolution de la part des cadres.

---

## Simulateur de carrière — fonctionnement détaillé

### Objectif

Permettre à un jeune ingénieur en début de carrière de saisir son profil et d'obtenir :
1. Une **estimation salariale personnalisée** basée sur les répondants IESF avec un profil similaire
2. Une **courbe de progression** montrant comment le salaire évolue au fil de la carrière pour ce profil
3. Des **indicateurs contextuels** (% cadre, % télétravail, % IA) pour ce profil
4. Des **repères nationaux** à l'embauche issus du dispositif InserSup (data.gouv.fr)

### Variables de profil

| Variable | Valeurs |
|---|---|
| Genre | Masculin / Féminin |
| Tranche d'âge | Moins de 30 ans / De 30 à 39 ans / ... |
| Type de diplôme | Valeurs issues de la colonne `diplome` IESF 2025 |
| Secteur d'activité | Valeurs issues de la colonne `secteur` IESF 2025 (optionnel) |
| Région | Valeurs issues de la colonne `region` IESF 2025 (optionnel) |

### Logique d'estimation salariale

Le simulateur filtre le dataframe IESF 2025 sur les 5 dimensions du profil et calcule la médiane pondérée ainsi que les quantiles P25 et P75.

**Mécanisme de repli automatique** : si le profil exact retourne moins de 20 répondants (cas fréquent pour une combinaison région + secteur précise), le filtre sur la région et le secteur est relâché. L'utilisateur en est informé par un message. En dessous de 5 répondants, un avertissement invite à élargir le profil.

```python
# Filtre complet (genre + âge + diplôme + secteur + région)
mask_full = build_mask(sim_genre, sim_age, sim_diplome, sim_secteur, sim_region)
sub = df25[mask_full].dropna(subset=["salaire_corrige"])

# Repli si trop peu de données
if len(sub) < 20:
    mask_relaxed = (df25["genre"] == sim_genre) & (df25["age"] == sim_age) & (df25["diplome"] == sim_diplome)
    sub = df25[mask_relaxed].dropna(subset=["salaire_corrige"])
```

### Courbe de progression

La courbe est calculée en filtrant par **genre + diplôme + secteur** (sans filtre sur l'âge), puis en calculant la médiane pondérée pour chaque tranche d'âge disposant d'au moins 5 répondants. Un point rouge met en évidence la position actuelle de l'utilisateur.

### Indicateurs contextuels

Sur le même sous-ensemble de répondants, le simulateur calcule les taux pondérés :
- Statut cadre (`cadre == "Oui"`)
- Télétravail (`teletravail == "Oui"`)
- Utilisation de l'IA (`utilise_ia == "Oui"`)

---

## Intégration data.gouv.fr — InserSup

### Mapping des types de diplômes

Les intitulés IESF sont mappés vers les codes InserSup :

```python
INSERSUP_DIPLOME_MAP = {
    "Diplôme d'ingénieur": "Diplôme d'ingénieur",
    "Master / DEA / DESS": "Master LMD",
    "Master":              "Master LMD",
    "Doctorat":            "Doctorat",
}
```

### Appel API et cache

La fonction `load_insersup()` est décorée avec `@st.cache_data(ttl=86400)` : les données sont récupérées une fois par type de diplôme et mises en cache pendant 24 heures. En cas d'indisponibilité de l'API, la fonction retourne `None` silencieusement et un message info s'affiche à la place des métriques.

```python
@st.cache_data(ttl=86400, show_spinner=False)
def load_insersup(diplome_iesf):
    diplome_key = INSERSUP_DIPLOME_MAP.get(diplome_iesf)
    if not diplome_key:
        return None
    try:
        resp = requests.get(url, params=params, timeout=10)
        # filtre sur l'année la plus récente disponible
        # moyenne des établissements pour le type de diplôme sélectionné
        ...
    except Exception:
        return None
```

### Note brut / net

Le salaire IESF (`salaire_corrige`) est un **salaire brut annuel**. Le salaire InserSup est un **salaire net mensuel** (médiane nationale à 30 mois). Cette distinction est explicitement mentionnée dans l'interface pour éviter toute confusion dans la comparaison.

---

## Lancer l'application

```bash
# Depuis le répertoire du projet
python -m streamlit run dashboard.py
```

L'application est accessible sur `http://localhost:8501`.

**Dépendances :**

```
streamlit>=1.57
pandas
plotly
numpy
requests
openpyxl
```

---

## Structure du projet

```
Data/
├── dashboard.py                          ← application principale
├── README.md                             ← ce fichier
└── OneDrive_1_17-05-2026/
    ├── exp_Questionnaire 2025.xlsx       ← données IESF 2025
    └── exp_Questionnaire_2024.xlsx       ← données IESF 2024
```

Les fichiers de données sont exclus du dépôt git (`.gitignore`).

---

*Source IESF : Enquête annuelle 2024 & 2025 — Données pondérées — Questionnaire Sphinx iQ*
*Source InserSup : Ministère de l'Enseignement supérieur, de la Recherche et de l'Espace — [data.gouv.fr](https://www.data.gouv.fr/datasets/insertion-professionnelle-des-diplomes-des-etablissements-denseignement-superieur-dispositif-insersup)*
