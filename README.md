# IESF — Observatoire des Ingénieurs & Simulateur de Carrière

Tableau de bord interactif et simulateur de carrière construits à partir des données de l'enquête annuelle IESF (Ingénieurs et Scientifiques de France), enrichis par les données ouvertes de [data.gouv.fr](https://www.data.gouv.fr).

---

## Table des matières

1. [Présentation du projet](#présentation-du-projet)
2. [Sources de données](#sources-de-données)
3. [Architecture technique](#architecture-technique)
4. [Colonnes chargées](#colonnes-chargées)
5. [Détail des onglets](#détail-des-onglets)
6. [Simulateur de carrière](#simulateur-de-carrière)
7. [Onglet Géographie & Emploi](#onglet-géographie--emploi)
8. [Onglet Marché & Mobilité](#onglet-marché--mobilité)
9. [Intégration data.gouv.fr](#intégration-datagouvfr)
10. [Lancer l'application](#lancer-lapplication)
11. [Structure du projet](#structure-du-projet)

---

## Présentation du projet

L'IESF publie chaque année une enquête auprès des ingénieurs et scientifiques français couvrant leur situation professionnelle, leurs rémunérations, leur rapport au travail et aux nouvelles technologies. Ce projet transforme ces données brutes (fichiers Excel Sphinx iQ) en un **observatoire interactif** accessible depuis un navigateur.

Les objectifs sont :

- **Analyser** la population des ingénieurs français sur les dimensions clés : profil démographique, emploi, rémunération, télétravail, IA, satisfaction.
- **Visualiser** géographiquement la répartition des ingénieurs sur le territoire français.
- **Comprendre** la dynamique du marché de l'emploi : mobilité, crainte de perte d'emploi, taille des employeurs.
- **Orienter** les jeunes ingénieurs en début de carrière grâce à un simulateur croisant les données IESF avec les données nationales InserSup (data.gouv.fr).

---

## Sources de données

### Données IESF (enquêtes 2024 et 2025)

| Fichier | Feuille | Colonnes |
|---|---|---|
| `exp_Questionnaire 2025.xlsx` | `Questionnaire 2025` | ~495 |
| `exp_Questionnaire_2024.xlsx` | `Questionnaire_2024` | ~495 |

Les données couvrent : profil (diplôme, école, année d'obtention, âge, genre), situation professionnelle (statut, secteur, taille d'entreprise, type de contrat), géographie (département de résidence et de travail), rémunération (salaire brut, part variable), conditions de travail (télétravail, responsabilités), usages technologiques (IA), mobilité professionnelle, et satisfaction.

Les données sont **pondérées** (colonne `poids`) pour être représentatives de la population réelle. Tous les calculs de médiane et de pourcentage utilisent ces poids.

### GeoJSON départements français

Chargé depuis le dépôt public `gregoiredavid/france-geojson` (GitHub) pour la carte choroplèthe. Mis en cache 7 jours.

```
https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson
```

### Données data.gouv.fr — InserSup

Le dispositif **InserSup** du Ministère de l'Enseignement supérieur mesure l'insertion professionnelle des diplômés à **30 mois** après l'obtention du diplôme. Interrogé en temps réel via l'API Open Data, mis en cache 24h.

```
https://data.enseignementsup-recherche.gouv.fr/api/explore/v2.1/catalog/datasets/fr-esr-insersup/records
```

Champs utilisés : taux d'insertion, salaire net médian, taux d'emploi cadre, taux d'emploi stable (CDI).

---

## Architecture technique

```
dashboard.py
├── Imports (streamlit, pandas, plotly, numpy, requests, re)
├── Configuration de la page (wide layout)
├── Constantes
│   ├── COLS_2025 / COLS_2024   — mapping index → nom de colonne
│   ├── TAILLE_ORDER            — ordre des tranches de taille d'entreprise
│   └── COLORS                  — palette couleurs (genre, primaire, secondaire)
├── Fonctions utilitaires
│   ├── extract_dept_code()          — extraction du code département (regex)
│   ├── load_geojson_depts()         — GeoJSON France (cache 7j)
│   ├── load_insersup()              — API InserSup data.gouv.fr (cache 24h)
│   ├── load_2025() / load_2024()    — lecture Excel + nettoyage (cache Streamlit)
│   ├── salaire_median_pondere()     — médiane pondérée
│   ├── salaire_quantile_pondere()   — quantile pondéré (P25, P75)
│   ├── pct()                        — pourcentage pondéré
│   ├── bar_chart() / pie_chart()    — graphiques génériques
│   └── salary_by_group_bar()        — médiane salariale par groupe
├── Sidebar (filtres globaux : genre, âge, secteur, situation)
├── KPI Cards (5 métriques globales)
└── 8 onglets
    ├── 👤 Profil
    ├── 🏢 Emploi & Secteurs
    ├── 💶 Rémunération
    ├── 💻 Travail & IA
    ├── 📊 Comparaison 2024-2025
    ├── 🎯 Simulateur de Carrière
    ├── 🗺️ Géographie & Emploi
    └── 📈 Marché & Mobilité
```

**Stack :**

| Bibliothèque | Usage |
|---|---|
| `streamlit 1.57` | Interface web, widgets, cache |
| `pandas` | Manipulation des données tabulaires |
| `plotly express` | Graphiques interactifs et carte choroplèthe |
| `numpy` | Calculs numériques |
| `requests` | Appels API (data.gouv.fr, GeoJSON) |
| `re` | Extraction des codes département (regex) |
| `openpyxl` | Lecture des fichiers Excel |

---

## Colonnes chargées

Le fichier 2025 contient ~495 colonnes mais seul un sous-ensemble est chargé via un dictionnaire `{index: nom}` pour limiter mémoire et temps de chargement. Le fichier 2024 utilise `skiprows=[1]` pour sauter la ligne de sous-en-tête Sphinx.

| Index | Nom interne | Description |
|---|---|---|
| 2 | `diplome` | Type de diplôme |
| 12 | `ecole` | École d'ingénieur |
| 14 | `annee_diplome` | Année d'obtention du diplôme |
| 51 | `annee_naissance` | Année de naissance |
| 59 | `age` | Tranche d'âge |
| 60 | `genre` | Genre |
| 67 | `dept_residence` | Département de résidence |
| 69 | `region` | Région de résidence |
| 78 | `activite` | Activité principale |
| 79 | `situation` | Situation professionnelle |
| 93 | `dept_travail` | Département de travail |
| 95 | `nature_entreprise` | Nature de l'organisation |
| 97 | `domaine_fonctionnel` | Domaine fonctionnel |
| 99 | `taille` | Taille de l'entreprise |
| 101 | `secteur` | Secteur d'activité (regroupé) |
| 120 | `cadre` | Statut cadre (Oui/Non) |
| 121 | `type_contrat` | Type de contrat |
| 122 | `responsabilites` | Responsabilités hiérarchiques |
| 157 | `annee_recrutement` | Année de recrutement par l'employeur actuel |
| 160 | `crainte_emploi` | Crainte de perte d'emploi |
| 168 | `mobilite_5ans` | Changement d'emploi dans les 5 dernières années |
| 211 | `salaire_brut` | Salaire brut cumulé déclaré |
| 216 | `part_variable` | Bénéficie d'une part variable |
| 217 | `montant_variable` | Montant brut de la part variable |
| 229 | `teletravail` | Pratique du télétravail |
| 230 | `jours_teletravail` | Jours de télétravail par semaine |
| 487 | `utilise_ia` | Utilise l'IA au travail |
| 488 | `type_ia` | Type d'IA utilisée |
| 506 | `competence_ia` | Auto-évaluation des compétences IA |
| 551 | `satisfaction` | Satisfaction globale au travail |
| 665 | `poids` | Poids de pondération |
| 666 | `salaire_corrige` | Salaire brut annuel corrigé (variable principale) |

**Colonnes calculées à la volée dans `load_2025()` :**

| Colonne | Calcul |
|---|---|
| `anciennete` | `2025 − annee_diplome` (borné à [0, 60]) |
| `dept_travail_code` | Code département extrait de `dept_travail` via regex, zero-paddé à 2 chiffres |
| `dept_residence_code` | Idem pour `dept_residence` |

---

## Détail des onglets

### Médiane et quantiles pondérés

Toutes les statistiques salariales utilisent le poids de pondération fourni par l'IESF :

```python
def salaire_median_pondere(df, col="salaire_corrige"):
    sub = df[[col, "poids"]].dropna().sort_values(col)
    cumw = sub["poids"].cumsum()
    return float(sub.loc[cumw >= sub["poids"].sum() / 2, col].iloc[0])

def salaire_quantile_pondere(df, q, col="salaire_corrige"):
    sub = df[[col, "poids"]].dropna().sort_values(col)
    cumw = sub["poids"].cumsum()
    return float(sub.loc[cumw >= sub["poids"].sum() * q, col].iloc[0])
```

### 👤 Profil

Distribution par diplôme, genre, tranche d'âge, région. Top 20 écoles d'ingénieurs représentées. Salaire médian par école (seuil minimum 30 répondants). Graphique empilé H/F par tranche d'âge pour visualiser l'évolution de la parité selon les générations.

### 🏢 Emploi & Secteurs

Répartition par secteur, nature d'entreprise, statut cadre, responsabilités hiérarchiques, type de contrat, activité principale.

### 💶 Rémunération

Distribution des salaires bruts, médiane par genre, médiane par tranche d'âge, médiane par secteur et nature d'entreprise. Part variable (prévalence et distribution). **Salaire médian par taille d'entreprise** (TPE → GE). **Salaire médian par ancienneté** (tranches de 3 à 10 ans calculées depuis `annee_diplome`).

### 💻 Travail & IA

Télétravail (taux global, jours/semaine, top secteurs). Usages IA (adoption, outils, adoption par âge, auto-évaluation). Satisfaction globale.

### 📊 Comparaison 2024-2025

Évolution du salaire médian brut entre 2024 et 2025. Superposition des distributions. Évolution de l'écart H/F. Évolution de la part des cadres.

---

## Simulateur de carrière

Onglet **🎯 Simulateur de Carrière**, ciblé sur les jeunes ingénieurs en début de parcours.

### Profil demandé

Genre, tranche d'âge, type de diplôme, secteur d'activité (optionnel), région (optionnelle).

### Logique d'estimation

Le simulateur filtre `df25` sur les 5 dimensions et calcule la médiane pondérée + P25 + P75.

**Repli automatique** : si le profil exact retourne < 20 répondants, le filtre région + secteur est relâché. Un message informe l'utilisateur. En dessous de 5 répondants, un avertissement invite à élargir le profil.

### Résultats affichés

- 3 métriques : P25 / médiane / P75 du salaire brut annuel
- Courbe de progression salariale par âge (genre + diplôme + secteur, toutes tranches d'âge), avec point rouge sur la position actuelle
- Indicateurs contextuels : % cadre, % télétravail, % IA — sur le même sous-ensemble de répondants
- Panel InserSup (data.gouv.fr) : taux d'insertion 30 mois, salaire net médian démarrage, % accès cadre, % CDI

---

## Onglet Géographie & Emploi

### Carte choroplèthe interactive

Trois indicateurs au choix (bascule radio) :
- **Nombre d'ingénieurs** — densité par département
- **Salaire médian brut** — heatmap salariale territoriale
- **Taux de télétravail** — disparités géographiques du remote work

Bascule **lieu de travail ↔ lieu de résidence** pour comparer là où les ingénieurs travaillent et là où ils habitent.

Implémentation avec `px.choropleth_mapbox` + GeoJSON départements + `open-street-map` comme fond de carte (aucun token Mapbox requis).

```python
fig = px.choropleth_mapbox(
    dept_df, geojson=geojson, locations="code",
    featureidkey="properties.code", color=val_col,
    mapbox_style="open-street-map",
    zoom=4.6, center={"lat": 46.5, "lon": 2.3},
)
```

### Extraction des codes département

Les valeurs brutes sont du type `"92 - Hauts-de-Seine"`. Une regex extrait le code numérique et applique un zero-padding pour correspondre aux clés GeoJSON :

```python
def extract_dept_code(s):
    m = re.match(r'^(\d{1,3})', str(s).strip())
    if m:
        code = m.group(1)
        return code.zfill(2) if len(code) < 3 else code
    return None
```

### Autres visualisations

- Top 15 départements par concentration d'ingénieurs
- Comparaison **Île-de-France vs Province** sur 3 axes : salaire médian, taux télétravail, part des cadres
- École la plus représentée par région (heatmap régionale)

---

## Onglet Marché & Mobilité

### KPIs globaux

- % d'ingénieurs ayant changé d'emploi ou de poste dans les 5 dernières années
- % craignant de perdre leur emploi dans l'année
- Ancienneté médiane (années depuis le diplôme)
- % travaillant dans un grand groupe (≥ 5 000 salariés)

### Mobilité professionnelle

Taux de mobilité sur 5 ans par secteur (min. 50 répondants). Permet d'identifier les secteurs les plus dynamiques en matière de rotation.

### Crainte de l'emploi

Taux de crainte de perte d'emploi par secteur — indicateur de sécurité perçue selon l'environnement de travail.

### Taille d'entreprise

Distribution des ingénieurs par taille (TPE / PME / ETI / GE) et taux de mobilité associé — les grandes structures retiennent-elles mieux leurs ingénieurs ?

### Courbe d'évolution salariale H/F par ancienneté

Calcul du salaire médian par tranche de 2 ans d'ancienneté, séparé par genre. Visualise si et quand l'écart salarial H/F se creuse au fil de la carrière. C'est le graphique le plus analytique du dashboard : il répond à la question *"L'écart se crée-t-il dès le départ ou s'accumule-t-il avec l'expérience ?"*

### Salaire médian par domaine fonctionnel

Classement des domaines (Recherche & Développement, Numérique, Industrie, etc.) par rémunération médiane.

---

## Intégration data.gouv.fr

### InserSup — Simulateur de carrière

Mapping des intitulés IESF vers les codes InserSup :

```python
INSERSUP_DIPLOME_MAP = {
    "Diplôme d'ingénieur": "Diplôme d'ingénieur",
    "Master / DEA / DESS": "Master LMD",
    "Master":              "Master LMD",
    "Doctorat":            "Doctorat",
}
```

Appel API avec `@st.cache_data(ttl=86400)`. En cas d'indisponibilité, retourne `None` silencieusement — l'interface affiche un message info à la place.

**Note brut/net** : le salaire IESF (`salaire_corrige`) est un salaire **brut annuel** ; le salaire InserSup est un salaire **net mensuel** médian. La distinction est explicitement affichée dans l'interface.

### GeoJSON France

Chargé depuis GitHub avec `@st.cache_data(ttl=86400 * 7)` — une semaine de cache. Fallback silencieux si indisponible (la carte est remplacée par un message info).

---

## Lancer l'application

```bash
python -m streamlit run dashboard.py
```

Accessible sur `http://localhost:8501`.

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
├── dashboard.py                          ← application principale (8 onglets)
├── README.md                             ← ce fichier
└── OneDrive_1_17-05-2026/
    ├── exp_Questionnaire 2025.xlsx       ← données IESF 2025 (~495 colonnes)
    └── exp_Questionnaire_2024.xlsx       ← données IESF 2024 (~495 colonnes)
```

Les fichiers de données sont exclus du dépôt git (`.gitignore`).

---

*Source IESF : Enquête annuelle 2024 & 2025 — Données pondérées — Questionnaire Sphinx iQ*
*Source InserSup : Ministère de l'Enseignement supérieur — [data.gouv.fr](https://www.data.gouv.fr/datasets/insertion-professionnelle-des-diplomes-des-etablissements-denseignement-superieur-dispositif-insersup)*
*GeoJSON : [gregoiredavid/france-geojson](https://github.com/gregoiredavid/france-geojson) — Licence MIT*
