import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import requests
import re

st.set_page_config(
    page_title="IESF — Observatoire des Ingénieurs",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

PATH_2025 = r"C:\Users\duboi\Desktop\IESF\Data-main\exp_Questionnaire 2025.xlsx"
PATH_2024 = r"C:\Users\duboi\Desktop\IESF\Data-main\exp_Questionnaire_2024.xlsx"

# Columns to load from 2025 (by index → clean name)
COLS_2025 = {
    2:   "diplome",
    12:  "ecole",
    14:  "annee_diplome",
    27:  "autre_diplome",           # AB — a un autre diplôme Bac+5 (Oui/Non) ✅ vérifié
    51:  "annee_naissance",
    59:  "age",
    60:  "genre",
    63:  "nombre_enfants",          # BL — nombre d'enfants (0..5, "+ de 5") ✅ vérifié
    64:  "activites_associatives",  # BM — activités associatives (Oui/Non) ✅ vérifié
    67:  "dept_residence",
    69:  "region",
    78:  "activite",
    79:  "situation",
    87:  "lieu_travail",           # où vous travailliez : France / Europe / Asie / Afrique / Amériques / Océanie
    93:  "dept_travail",
    94:  "zone_travail",           # Ile de France ; Province ; Drom-Com (regroupement déjà fait par l'enquête)
    95:  "nature_entreprise",
    97:  "domaine_fonctionnel",
    99:  "taille",
    100: "secteur_detail",         # CW — secteur d'activité détaillé (~35 catégories) ✅ vérifié
    101: "secteur",                # CX — secteur regroupé (11 catégories) ✅ vérifié
    114: "raison_choix_secteur",   # DK — pourquoi ce secteur ✅ vérifié
    115: "service",                # DL — service / département d'emploi ✅ vérifié
    120: "cadre",
    121: "type_contrat",
    122: "responsabilites",        # DS — responsabilités hiérarchiques (Oui/Non) ✅ vérifié
    123: "nb_encadres",             # DT — nombre de personnes encadrées ✅ vérifié
    125: "membre_codir",            # DV — membre Codir/Comex/CA (Oui/Non) ✅ vérifié
    126: "resp_resultat_financier", # DW — responsable d'un résultat financier (Oui/Non) ✅ vérifié
    130: "role_chef_projet",        # EA — chef de projet (Oui/Non) ✅ vérifié
    131: "role_expert_technique",   # EB — expert technique (Oui/Non) ✅ vérifié
    136: "expertise_reco",          # EG — expertise reconnue dans l'entreprise (Oui/Non) ✅ vérifié
    157: "annee_recrutement",
    160: "crainte_emploi",          # FE — craint de perdre son emploi (Oui/Non) ✅ vérifié
    166: "nbre_chomage",            # FK — nombre de périodes de chômage connues ✅ vérifié
    168: "mobilite_5ans",
    172: "satisfaction_mobilite",   # FQ — satisfaction de la dernière mobilité (5 niveaux texte) ✅ vérifié
    211: "salaire_brut",
    216: "part_variable",
    217: "montant_variable",
    229: "teletravail",
    230: "jours_teletravail",
    487: "utilise_ia",
    488: "type_ia",
    506: "competence_ia",
    551: "satisfaction",
    # --- Sous-dimensions détaillées de satisfaction (échelle 1-5) ---------------
    # ✅ Toutes vérifiées contre le texte réel des questions (row0) du fichier
    # copie_claude.xlsx fourni. Il y en a 20 (553-572), pas 16 comme le
    # suggérait idees_graphes.md.
    553: "sat_securite_emploi",
    554: "sat_interet_taches",
    555: "sat_perspectives_carriere",
    556: "sat_ambiance",
    557: "sat_stress",                    # brut : plus haut = plus de stress perçu
    558: "sat_charge_travail",            # brut : plus haut = charge perçue plus lourde
    559: "sat_autonomie",
    560: "sat_facilite_responsabilites",
    561: "sat_sens_travail",
    562: "sat_remuneration_pct",
    563: "sat_equilibre_vie",
    564: "sat_developpement_competences",
    565: "sat_organisation",
    566: "sat_strategie_entreprise",      # corrigé (était "sat_management")
    567: "sat_gestion_rh",                # corrigé (était "sat_reconnaissance_hierarchie")
    568: "sat_style_management",          # corrigé (était "sat_reconnaissance_pairs")
    569: "sat_prise_en_compte_propositions",  # nouveau
    570: "sat_reconnaissance_hierarchie",     # nouveau (la vraie colonne)
    571: "sat_reconnaissance_pairs",          # nouveau (la vraie colonne)
    572: "sat_formation",                     # nouveau
    665: "poids",
    666: "salaire_corrige",
}

# Colonnes de satisfaction détaillée réellement disponibles (utilisé par l'onglet Mentors)
SATISFACTION_COLS = [c for c in COLS_2025.values() if c.startswith("sat_")]

TAILLE_ORDER = ["TPE (1 - 49 salariés)", "PME (50 à 249 salariés)", "ETI (250 - 4999 salariés)", "GE (5 000 salariés et plus)"]



def extract_dept_code(s):
    if pd.isna(s):
        return None
    m = re.match(r'^(\d{1,3})', str(s).strip())
    if m:
        code = m.group(1)
        return code.zfill(2) if len(code) < 3 else code
    return None

COLS_2024 = {
    2: "diplome",
    54: "age",
    55: "genre",
    111: "cadre",
    493: "poids",
    494: "salaire_corrige",
}

COLORS = {
    "Féminin": "#e377c2",
    "Masculin": "#1f77b4",
    "primary": "#003f7f",
    "secondary": "#e8505b",
}


INSERSUP_DIPLOME_MAP = {
    "Diplôme d'ingénieur": "Diplôme d'ingénieur",
    "Master / DEA / DESS": "Master LMD",
    "Master": "Master LMD",
    "Doctorat": "Doctorat",
}


@st.cache_data(ttl=86400, show_spinner=False)
def load_insersup(diplome_iesf):
    diplome_key = INSERSUP_DIPLOME_MAP.get(diplome_iesf)
    if not diplome_key:
        return None
    try:
        url = (
            "https://data.enseignementsup-recherche.gouv.fr"
            "/api/explore/v2.1/catalog/datasets/fr-esr-insersup/records"
        )
        params = {
            "where": f'diplome="{diplome_key}"',
            "limit": 200,
            "select": (
                "annee,"
                "taux_dinsertion,"
                "salaire_net_median_des_emplois_a_temps_plein,"
                "taux_emplois_cadre_ou_professions_intermediaires,"
                "taux_emplois_stables"
            ),
        }
        resp = requests.get(url, params=params, timeout=10)
        if not resp.ok:
            return None
        records = resp.json().get("results", [])
        if not records:
            return None
        df_is = pd.DataFrame(records)
        if "annee" in df_is.columns:
            df_is = df_is[df_is["annee"] == df_is["annee"].max()]
        result = {}
        field_map = {
            "taux_dinsertion": "taux_dinsertion",
            "salaire_net_median_des_emplois_a_temps_plein": "salaire_net_median",
            "taux_emplois_cadre_ou_professions_intermediaires": "taux_emplois_cadre",
            "taux_emplois_stables": "taux_emplois_stables",
        }
        for src, dst in field_map.items():
            if src in df_is.columns:
                val = pd.to_numeric(df_is[src], errors="coerce").median()
                result[dst] = None if pd.isna(val) else float(val)
        return result if result else None
    except Exception:
        return None


@st.cache_data(ttl=86400 * 7, show_spinner=False)
def load_geojson_depts():
    try:
        url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson"
        resp = requests.get(url, timeout=15)
        if resp.ok:
            return resp.json()
    except Exception:
        pass
    return None


@st.cache_data(show_spinner="Chargement des données 2025…")
def load_2025():
    df = pd.read_excel(
        PATH_2025,
        sheet_name="Questionnaire 2025",
        engine="calamine",
        usecols=list(COLS_2025.keys()),
    )
    df.columns = [COLS_2025[c] for c in list(COLS_2025.keys())]
    df = df.rename(columns=str)  # ensure strings
    # Clean salary: replace extreme values with NaN
    for col in ("salaire_brut", "salaire_corrige", "montant_variable"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] > 1_000_000, col] = np.nan
        df.loc[df[col] <= 0, col] = np.nan
    df["poids"] = pd.to_numeric(df["poids"], errors="coerce").fillna(0)
    for col in ("annee_diplome", "annee_naissance", "annee_recrutement"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["anciennete"] = (2025 - df["annee_diplome"]).where(
        df["annee_diplome"].between(1950, 2025), other=np.nan
    )
    df["dept_travail_code"] = df["dept_travail"].apply(extract_dept_code)
    df["dept_residence_code"] = df["dept_residence"].apply(extract_dept_code)
    for col in SATISFACTION_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["crainte_emploi_num"] = df["crainte_emploi"].map({"Oui": 1.0, "Non": 0.0})
    df["membre_codir_num"] = df["membre_codir"].map({"Oui": 1.0, "Non": 0.0})
    df["resp_resultat_financier_num"] = df["resp_resultat_financier"].map({"Oui": 1.0, "Non": 0.0})
    df["responsabilites_num"] = df["responsabilites"].map({"Oui": 1.0, "Non": 0.0})
    df["activites_associatives_num"] = df["activites_associatives"].map({"Oui": 1.0, "Non": 0.0})
    df["expertise_reco_num"] = df["expertise_reco"].map({"Oui": 1.0, "Non": 0.0})
    df["nb_encadres"] = pd.to_numeric(df["nb_encadres"], errors="coerce")
    df.loc[df["nb_encadres"] < 0, "nb_encadres"] = np.nan
    df.loc[df["nb_encadres"] > 2000, "nb_encadres"] = np.nan  # valeurs aberrantes
    df["nbre_chomage"] = pd.to_numeric(df["nbre_chomage"], errors="coerce")
    df.loc[df["nbre_chomage"] < 0, "nbre_chomage"] = np.nan

    # Nombre d'enfants : réponse catégorielle "0;1;2;3;4;5;+ de 5" -> numérique (6 pour "+ de 5")
    def _encode_nombre_enfants(v):
        if pd.isna(v):
            return np.nan
        s = str(v).strip()
        if s == "+ de 5":
            return 6.0
        try:
            return float(s)
        except ValueError:
            return np.nan

    df["nombre_enfants"] = df["nombre_enfants"].apply(_encode_nombre_enfants)

    # Satisfaction de la dernière mobilité : échelle texte -> 1-5
    SATISFACTION_MOBILITE_MAP = {
        "Très insatisfait": 1, "Insatisfait": 2, "Ni satisfait ni insatisfait": 3,
        "Satisfait": 4, "Très satisfait": 5,
    }
    df["satisfaction_mobilite_num"] = df["satisfaction_mobilite"].map(SATISFACTION_MOBILITE_MAP)

    # Domaine professionnel : deux variantes de la même question selon le type
    # d'employeur (domaine_fonctionnel pour certaines branches, service pour
    # les autres) -> on les fusionne pour le filtrage/matching.
    df["domaine_pro"] = df["domaine_fonctionnel"].fillna(df["service"])

    df["annee"] = 2025
    return df


@st.cache_data(show_spinner="Chargement des données 2024…")
def load_2024():
    df = pd.read_excel(
        PATH_2024,
        sheet_name="Questionnaire_2024",
        engine="calamine",
        usecols=list(COLS_2024.keys()),
        skiprows=[1],  # skip the sub-header row
    )
    df.columns = [COLS_2024[c] for c in list(COLS_2024.keys())]
    df["salaire_corrige"] = pd.to_numeric(df["salaire_corrige"], errors="coerce")
    df.loc[df["salaire_corrige"] > 1_000_000, "salaire_corrige"] = np.nan
    df.loc[df["salaire_corrige"] <= 0, "salaire_corrige"] = np.nan
    df["poids"] = pd.to_numeric(df["poids"], errors="coerce").fillna(0)
    df["annee"] = 2024
    return df


def salaire_median_pondere(df, col="salaire_corrige"):
    """Weighted median salary."""
    sub = df[[col, "poids"]].dropna()
    if sub.empty:
        return np.nan
    sub = sub.sort_values(col)
    cumw = sub["poids"].cumsum()
    half = sub["poids"].sum() / 2
    return float(sub.loc[cumw >= half, col].iloc[0])


def salaire_quantile_pondere(df, q, col="salaire_corrige"):
    sub = df[[col, "poids"]].dropna()
    if sub.empty:
        return np.nan
    sub = sub.sort_values(col)
    cumw = sub["poids"].cumsum()
    threshold = sub["poids"].sum() * q
    return float(sub.loc[cumw >= threshold, col].iloc[0])


def pct(df, col, val):
    """Weighted percentage of a value in a column."""
    total = df["poids"].sum()
    if total == 0:
        return 0
    n = df.loc[df[col] == val, "poids"].sum()
    return round(100 * n / total, 1)


def bar_chart(df, col, title, top_n=15, color=None, horizontal=True):
    counts = (
        df.groupby(col, dropna=True)["poids"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )
    counts.columns = [col, "Effectif pondéré"]
    if horizontal:
        counts = counts.sort_values("Effectif pondéré")
        fig = px.bar(
            counts,
            x="Effectif pondéré",
            y=col,
            orientation="h",
            title=title,
            color_discrete_sequence=[color or COLORS["primary"]],
        )
        fig.update_layout(yaxis_title=None, xaxis_title="Effectif pondéré", height=max(300, top_n * 30))
    else:
        fig = px.bar(
            counts,
            x=col,
            y="Effectif pondéré",
            title=title,
            color_discrete_sequence=[color or COLORS["primary"]],
        )
        fig.update_layout(xaxis_title=None, height=380)
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), title_font_size=14)
    return fig


def pie_chart(df, col, title):
    counts = df.groupby(col, dropna=True)["poids"].sum().reset_index()
    counts.columns = [col, "Effectif"]
    fig = px.pie(counts, names=col, values="Effectif", title=title, hole=0.4)
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), title_font_size=14, height=340)
    return fig


def salary_box(df, group_col, title, salary_col="salaire_corrige", top_n=12):
    sub = df[[group_col, salary_col, "poids"]].dropna()
    # Keep top_n groups by respondent count
    top_groups = (
        sub.groupby(group_col)["poids"].sum().nlargest(top_n).index.tolist()
    )
    sub = sub[sub[group_col].isin(top_groups)]
    fig = px.box(
        sub,
        x=group_col,
        y=salary_col,
        title=title,
        color=group_col,
        points=False,
    )
    fig.update_layout(
        showlegend=False,
        yaxis_title="Salaire brut annuel (€)",
        xaxis_title=None,
        height=420,
        margin=dict(l=0, r=0, t=40, b=80),
        title_font_size=14,
    )
    fig.update_xaxes(tickangle=-30)
    return fig


def salary_by_group_bar(df, group_col, title, salary_col="salaire_corrige", top_n=15):
    sub = df[[group_col, salary_col, "poids"]].dropna()
    medians = []
    for g, gdf in sub.groupby(group_col):
        med = salaire_median_pondere(gdf, salary_col)
        n = gdf["poids"].sum()
        medians.append({"Groupe": g, "Médiane (€)": med, "Effectif": n})
    med_df = (
        pd.DataFrame(medians)
        .sort_values("Médiane (€)", ascending=False)
        .head(top_n)
        .sort_values("Médiane (€)")
    )
    fig = px.bar(
        med_df,
        x="Médiane (€)",
        y="Groupe",
        orientation="h",
        title=title,
        color_discrete_sequence=[COLORS["primary"]],
        text="Médiane (€)",
    )
    fig.update_traces(texttemplate="%{text:,.0f} €", textposition="outside")
    fig.update_layout(
        yaxis_title=None,
        xaxis_title="Salaire médian brut annuel (€)",
        height=max(300, top_n * 32),
        margin=dict(l=0, r=80, t=40, b=0),
        title_font_size=14,
    )
    return fig


# ── Onglet Mentors : critères de matching ──────────────────────────────────────
# Chaque critère référence une ou plusieurs colonnes, avec un "direction" :
# +1 si "plus haut = mieux", -1 si "plus bas = mieux" (ex : moins de stress).
CRITERES_MENTORS = {
    "💶 Salaire":                    {"cols": ["salaire_corrige"],                                                              "direction": [1]},
    "🎯 Sens / impact du travail":    {"cols": ["sat_sens_travail", "sat_interet_taches", "expertise_reco_num", "satisfaction_mobilite_num"], "direction": [1, 1, 1, 1]},
    "⚖️ Équilibre vie pro/perso":     {"cols": ["sat_equilibre_vie", "activites_associatives_num"],                             "direction": [1, 1]},
    "🛡️ Sécurité de l'emploi":       {"cols": ["sat_securite_emploi", "crainte_emploi_num", "nbre_chomage"],                    "direction": [1, -1, -1]},
    "🧗 Perspectives / évolution":    {"cols": ["sat_perspectives_carriere", "sat_developpement_competences", "sat_formation"],  "direction": [1, 1, 1]},
    "🤝 Ambiance & reconnaissance":   {"cols": ["sat_ambiance", "sat_reconnaissance_hierarchie", "sat_reconnaissance_pairs", "sat_prise_en_compte_propositions"], "direction": [1, 1, 1, 1]},
    "🧘 Charge de travail légère":    {"cols": ["sat_charge_travail", "sat_stress", "membre_codir_num", "resp_resultat_financier_num"], "direction": [-1, -1, -1, -1]},
    "🕊️ Autonomie":                  {"cols": ["sat_autonomie"],                                                                "direction": [1]},
    "👥 Responsabilités managériales":{"cols": ["nb_encadres"],                                                                    "direction": [1]},
    "🏛️ Qualité de l'organisation":  {"cols": ["sat_organisation", "sat_strategie_entreprise", "sat_gestion_rh", "sat_style_management"], "direction": [1, 1, 1, 1]},
}



def minmax01(series):
    """Normalise une série numérique entre 0 et 1 sur son propre échantillon.
    Les valeurs manquantes (non répondu) restent NaN — elles ne sont PAS
    remplacées par une valeur neutre, pour que le score final puisse les
    exclure proprement plutôt que de les traiter comme une vraie réponse."""
    s = pd.to_numeric(series, errors="coerce")
    lo, hi = s.min(), s.max()
    if pd.isna(lo) or pd.isna(hi):
        return s  # colonne entièrement vide : reste NaN partout
    if hi == lo:
        return pd.Series(np.where(s.notna(), 0.5, np.nan), index=series.index)
    return (s - lo) / (hi - lo)


def build_criteria_score(df, col, direction):
    """Renvoie une série 0-1 (ou NaN si non répondu) pour une colonne donnée,
    orientée dans le bon sens."""
    scaled = minmax01(df[col])
    return scaled if direction == 1 else (1 - scaled)


def compute_match_scores(df, weights_normalises):
    """Score de matching individuel pour chaque ligne de la cohorte.

    weights_normalises : dict {nom_critère: poids entre 0 et 1, somme = 1}.

    Gestion des questions optionnelles ("trous") : le score de chaque
    répondant est calculé UNIQUEMENT sur les critères auxquels il/elle a
    répondu, puis renormalisé sur le poids réellement couvert pour cette
    personne — plutôt que de pénaliser une non-réponse comme un mauvais score.

    Renvoie :
      - total_score : score de compatibilité 0-1 par répondant (à afficher en %)
      - detail      : DataFrame des scores 0-1 par critère (peut contenir NaN)
      - coverage    : part du budget de poids (0-1) réellement couverte par
                      les réponses de chaque personne — utile pour repérer les
                      profils qui n'ont répondu qu'à une petite partie des
                      critères demandés.
    """
    detail_cols = {}
    for critere, w in weights_normalises.items():
        cols = CRITERES_MENTORS[critere]["cols"]
        directions = CRITERES_MENTORS[critere]["direction"]
        sub_scores = [
            build_criteria_score(df, c, d)
            for c, d in zip(cols, directions)
            if c in df.columns and df[c].notna().any()
        ]
        if not sub_scores:
            continue
        # .mean(axis=1, skipna=True) : moyenne des sous-questions répondues
        # uniquement ; si aucune n'est répondue pour cette ligne -> NaN.
        detail_cols[critere] = pd.concat(sub_scores, axis=1).mean(axis=1)

    detail = pd.DataFrame(detail_cols, index=df.index)

    if detail.empty:
        return pd.Series(np.nan, index=df.index), detail, pd.Series(0.0, index=df.index)

    weights = pd.Series(weights_normalises)[detail.columns]
    # Poids appliqué par ligne : 0 là où le répondant n'a pas répondu à ce critère
    weight_matrix = detail.notna().astype(float).mul(weights, axis=1)
    coverage = weight_matrix.sum(axis=1)  # part du budget couverte, par personne
    weighted_sum = detail.fillna(0.0).mul(weights, axis=1).sum(axis=1)

    total_score = weighted_sum / coverage.replace(0, np.nan)

    return total_score, detail, coverage


# ── Curseurs de priorité à somme constante (budget de 100 points) ─────────────
MENTORS_CRITERES_LIST = list(CRITERES_MENTORS.keys())
MENTORS_BUDGET = 100


def _mentors_slider_key(critere):
    return f"mentors_w_{critere}"


def init_mentors_weights():
    """Initialise les curseurs à parts égales la première fois (somme = 100)."""
    if "mentors_weights_init" not in st.session_state:
        n = len(MENTORS_CRITERES_LIST)
        base = MENTORS_BUDGET // n
        remainder = MENTORS_BUDGET - base * n
        for i, critere in enumerate(MENTORS_CRITERES_LIST):
            val = base + (1 if i < remainder else 0)
            st.session_state[_mentors_slider_key(critere)] = val
        st.session_state["mentors_weights_init"] = True


def rebalance_mentors_weights(changed_critere):
    """Callback on_change : quand un curseur bouge, répartit la différence
    sur les autres proportionnellement à leur valeur actuelle, pour que la
    somme totale reste toujours égale à MENTORS_BUDGET."""
    changed_key = _mentors_slider_key(changed_critere)
    new_val = st.session_state[changed_key]
    new_val = max(0, min(MENTORS_BUDGET, new_val))

    autres = [c for c in MENTORS_CRITERES_LIST if c != changed_critere]
    somme_autres_avant = sum(st.session_state.get(_mentors_slider_key(c), 0) for c in autres)
    budget_restant = MENTORS_BUDGET - new_val

    alloue = 0
    for i, c in enumerate(autres):
        key = _mentors_slider_key(c)
        if i == len(autres) - 1:
            # Dernier critère : on lui donne le reste pour garantir une somme exacte
            st.session_state[key] = budget_restant - alloue
        elif somme_autres_avant > 0:
            w_actuel = st.session_state.get(key, 0)
            part = round(budget_restant * w_actuel / somme_autres_avant)
            part = max(0, min(part, budget_restant - alloue))
            st.session_state[key] = part
            alloue += part
        else:
            # Tous les autres curseurs étaient à 0 : répartition égale
            part = budget_restant // len(autres)
            st.session_state[key] = part
            alloue += part

    st.session_state[changed_key] = new_val


# ── Sidebar filters ────────────────────────────────────────────────────────────

st.sidebar.markdown("## 🔬 IESF — Filtres")

df25 = load_2025()
df24 = load_2024()

genres = ["Tous"] + sorted(df25["genre"].dropna().unique().tolist())
sel_genre = st.sidebar.selectbox("Genre", genres)

ages = ["Tous"] + sorted(df25["age"].dropna().unique().tolist())
sel_age = st.sidebar.multiselect("Tranche d'âge", ages[1:], default=[])

secteurs = ["Tous"] + sorted(df25["secteur"].dropna().unique().tolist())
sel_secteur = st.sidebar.multiselect("Secteur", secteurs[1:], default=[])

situations = ["Tous"] + sorted(df25["situation"].dropna().unique().tolist())
sel_situation = st.sidebar.selectbox("Situation", situations)

st.sidebar.markdown("---")
st.sidebar.caption("Source : IESF — Enquête annuelle 2024 & 2025")


def apply_filters(df):
    mask = pd.Series(True, index=df.index)
    if sel_genre != "Tous":
        mask &= df["genre"] == sel_genre
    if sel_age:
        mask &= df["age"].isin(sel_age)
    if sel_secteur:
        mask &= df["secteur"].isin(sel_secteur)
    if sel_situation != "Tous" and "situation" in df.columns:
        mask &= df["situation"] == sel_situation
    return df[mask]


df = apply_filters(df25)

# ── Header ─────────────────────────────────────────────────────────────────────

st.title("🔬 IESF — Observatoire des Ingénieurs & Scientifiques")
st.caption("Enquête annuelle 2025 · Données pondérées · Questionnaire Sphinx iQ")

# ── KPI Cards ──────────────────────────────────────────────────────────────────

k1, k2, k3, k4, k5 = st.columns(5)

n_total = int(df["poids"].sum())
med_sal = salaire_median_pondere(df)
pct_femmes = pct(df, "genre", "Féminin")
pct_tele = pct(df, "teletravail", "Oui")
pct_ia = pct(df, "utilise_ia", "Oui")

with k1:
    st.metric("Répondants", f"{n_total:,}".replace(",", " "))
with k2:
    st.metric("Salaire médian brut", f"{med_sal:,.0f} €".replace(",", " ") if not np.isnan(med_sal) else "N/A")
with k3:
    st.metric("Part femmes", f"{pct_femmes} %")
with k4:
    st.metric("Télétravail", f"{pct_tele} %")
with k5:
    st.metric("Utilisent l'IA", f"{pct_ia} %")

st.markdown("---")

# ── Tabs ───────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "👤 Profil",
    "🏢 Emploi & Secteurs",
    "💶 Rémunération",
    "💻 Travail & IA",
    "📊 Comparaison 2024-2025",
    "🎯 Simulateur de Carrière",
    "🗺️ Géographie & Emploi",
    "📈 Marché & Mobilité",
    "🧭 Mentors",
])

# ─── TAB 1 : PROFIL ────────────────────────────────────────────────────────────

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(bar_chart(df, "diplome", "Type de diplôme", top_n=8), use_container_width=True)
    with c2:
        st.plotly_chart(pie_chart(df, "genre", "Répartition par genre"), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        age_order = [
            "Moins de 30 ans", "De 30 à 39 ans", "De 40 à 49 ans",
            "De 50 à 64 ans", "65 et plus",
        ]
        age_counts = (
            df.groupby("age", dropna=True)["poids"]
            .sum()
            .reindex(age_order)
            .dropna()
            .reset_index()
        )
        age_counts.columns = ["age", "Effectif"]
        fig_age = px.bar(
            age_counts, x="age", y="Effectif",
            title="Distribution par tranche d'âge",
            color_discrete_sequence=[COLORS["primary"]],
        )
        fig_age.update_layout(xaxis_title=None, height=360, margin=dict(l=0, r=0, t=40, b=60), title_font_size=14)
        fig_age.update_xaxes(tickangle=-30)
        st.plotly_chart(fig_age, use_container_width=True)

    with c4:
        st.plotly_chart(bar_chart(df, "region", "Top régions de résidence", top_n=12), use_container_width=True)

    st.markdown("---")
    c5, c6 = st.columns(2)
    with c5:
        st.plotly_chart(bar_chart(df, "ecole", "Top 20 écoles d'ingénieurs représentées", top_n=20), use_container_width=True)
    with c6:
        ecole_sal = []
        for e, edf in df.groupby("ecole", dropna=True):
            if edf["poids"].sum() < 30:
                continue
            med = salaire_median_pondere(edf)
            n = int(edf["poids"].sum())
            if not np.isnan(med):
                ecole_sal.append({"École": e, "Médiane (€)": med, "Effectif pondéré": n})
        if ecole_sal:
            ecole_sal_df = pd.DataFrame(ecole_sal).sort_values("Médiane (€)", ascending=False).head(15).sort_values("Médiane (€)")
            fig_es = px.bar(
                ecole_sal_df, x="Médiane (€)", y="École", orientation="h",
                title="Salaire médian brut par école (min. 30 répondants)",
                color="Médiane (€)", color_continuous_scale="Blues",
                text="Médiane (€)",
            )
            fig_es.update_traces(texttemplate="%{text:,.0f} €", textposition="outside")
            fig_es.update_layout(showlegend=False, coloraxis_showscale=False, yaxis_title=None, height=500, margin=dict(l=0, r=80, t=40, b=0), title_font_size=14)
            st.plotly_chart(fig_es, use_container_width=True)

    st.subheader("Évolution genre par tranche d'âge")
    age_genre = (
        df.groupby(["age", "genre"], dropna=True)["poids"]
        .sum()
        .reset_index()
    )
    age_genre.columns = ["age", "genre", "Effectif"]
    age_genre = age_genre[age_genre["genre"].isin(["Masculin", "Féminin"])]
    pivot = age_genre.pivot(index="age", columns="genre", values="Effectif").fillna(0)
    pivot["total"] = pivot.sum(axis=1)
    pivot["% Féminin"] = (pivot.get("Féminin", 0) / pivot["total"] * 100).round(1)
    pivot = pivot.reindex([a for a in age_order if a in pivot.index])
    fig_gend = px.bar(
        age_genre[age_genre["genre"].isin(["Masculin", "Féminin"])],
        x="age",
        y="Effectif",
        color="genre",
        barmode="stack",
        color_discrete_map=COLORS,
        title="Répartition genre par tranche d'âge",
        category_orders={"age": age_order},
    )
    fig_gend.update_layout(xaxis_title=None, height=360, margin=dict(l=0, r=0, t=40, b=60), title_font_size=14)
    fig_gend.update_xaxes(tickangle=-30)
    st.plotly_chart(fig_gend, use_container_width=True)


# ─── TAB 2 : EMPLOI & SECTEURS ────────────────────────────────────────────────

with tab2:
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(bar_chart(df, "secteur", "Répartition par secteur", top_n=15), use_container_width=True)
    with c2:
        st.plotly_chart(bar_chart(df, "nature_entreprise", "Nature de l'entreprise", top_n=10), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(pie_chart(df, "cadre", "Statut cadre"), use_container_width=True)
    with c4:
        st.plotly_chart(pie_chart(df, "responsabilites", "Responsabilités hiérarchiques"), use_container_width=True)

    c5, c6 = st.columns(2)
    with c5:
        st.plotly_chart(bar_chart(df, "type_contrat", "Type de contrat", top_n=8), use_container_width=True)
    with c6:
        # Activité principale — simplify long labels
        df_act = df.copy()
        df_act["activite_court"] = df_act["activite"].str[:60]
        st.plotly_chart(bar_chart(df_act, "activite_court", "Activité principale", top_n=6), use_container_width=True)


# ─── TAB 3 : RÉMUNÉRATION ─────────────────────────────────────────────────────

with tab3:
    c1, c2 = st.columns(2)
    with c1:
        sal_sub = df[["salaire_corrige", "poids"]].dropna()
        fig_hist = px.histogram(
            sal_sub,
            x="salaire_corrige",
            nbins=60,
            title="Distribution des salaires bruts annuels",
            labels={"salaire_corrige": "Salaire brut annuel (€)"},
            color_discrete_sequence=[COLORS["primary"]],
        )
        fig_hist.update_layout(height=380, margin=dict(l=0, r=0, t=40, b=0), title_font_size=14)
        st.plotly_chart(fig_hist, use_container_width=True)

    with c2:
        # Salaire médian par genre
        gen_sal = []
        for g in df["genre"].dropna().unique():
            gdf = df[df["genre"] == g]
            med = salaire_median_pondere(gdf)
            if not np.isnan(med):
                gen_sal.append({"Genre": g, "Médiane (€)": med})
        if gen_sal:
            fig_gen = px.bar(
                pd.DataFrame(gen_sal).sort_values("Médiane (€)"),
                x="Genre", y="Médiane (€)",
                color="Genre",
                color_discrete_map=COLORS,
                title="Salaire médian brut par genre",
                text="Médiane (€)",
            )
            fig_gen.update_traces(texttemplate="%{text:,.0f} €", textposition="outside")
            fig_gen.update_layout(showlegend=False, height=380, margin=dict(l=0, r=0, t=40, b=0), title_font_size=14)
            st.plotly_chart(fig_gen, use_container_width=True)

    st.subheader("Salaire médian par tranche d'âge")
    age_order_sal = ["Moins de 30 ans", "De 30 à 39 ans", "De 40 à 49 ans", "De 50 à 64 ans", "65 et plus"]
    age_sal = []
    for a in age_order_sal:
        adf = df[df["age"] == a]
        med = salaire_median_pondere(adf)
        if not np.isnan(med):
            age_sal.append({"Tranche d'âge": a, "Médiane (€)": med})
    if age_sal:
        fig_age_sal = px.bar(
            pd.DataFrame(age_sal),
            x="Tranche d'âge", y="Médiane (€)",
            title="Salaire médian brut par tranche d'âge",
            color_discrete_sequence=[COLORS["primary"]],
            text="Médiane (€)",
            category_orders={"Tranche d'âge": age_order_sal},
        )
        fig_age_sal.update_traces(texttemplate="%{text:,.0f} €", textposition="outside")
        fig_age_sal.update_layout(height=360, margin=dict(l=0, r=0, t=40, b=60), title_font_size=14)
        fig_age_sal.update_xaxes(tickangle=-20)
        st.plotly_chart(fig_age_sal, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(
            salary_by_group_bar(df, "secteur", "Salaire médian brut par secteur", top_n=12),
            use_container_width=True,
        )
    with c4:
        st.plotly_chart(
            salary_by_group_bar(df, "nature_entreprise", "Salaire médian par nature d'entreprise", top_n=10),
            use_container_width=True,
        )

    st.subheader("Part variable")
    c5, c6 = st.columns(2)
    with c5:
        st.plotly_chart(pie_chart(df, "part_variable", "Bénéficiaires d'une part variable"), use_container_width=True)
    with c6:
        pv_sub = df[df["part_variable"] == "Oui"][["montant_variable", "poids"]].dropna()
        if not pv_sub.empty:
            fig_pv = px.histogram(
                pv_sub, x="montant_variable", nbins=40,
                title="Distribution de la part variable (€ brut)",
                labels={"montant_variable": "Montant brut (€)"},
                color_discrete_sequence=[COLORS["secondary"]],
            )
            fig_pv.update_layout(height=340, margin=dict(l=0, r=0, t=40, b=0), title_font_size=14)
            st.plotly_chart(fig_pv, use_container_width=True)

    st.markdown("---")
    c7, c8 = st.columns(2)
    with c7:
        taille_order_present = [t for t in TAILLE_ORDER if t in df["taille"].dropna().unique()]
        if taille_order_present:
            taille_rows = [{"Taille": t, "Médiane (€)": salaire_median_pondere(df[df["taille"] == t])} for t in taille_order_present]
            taille_rows = [r for r in taille_rows if not np.isnan(r["Médiane (€)"])]
            if taille_rows:
                fig_taille = px.bar(
                    pd.DataFrame(taille_rows), x="Taille", y="Médiane (€)",
                    title="Salaire médian brut par taille d'entreprise",
                    color="Taille", color_discrete_sequence=px.colors.sequential.Blues[2:],
                    text="Médiane (€)",
                    category_orders={"Taille": TAILLE_ORDER},
                )
                fig_taille.update_traces(texttemplate="%{text:,.0f} €", textposition="outside")
                fig_taille.update_layout(showlegend=False, height=380, margin=dict(l=0, r=0, t=40, b=80), title_font_size=14)
                fig_taille.update_xaxes(tickangle=-20)
                st.plotly_chart(fig_taille, use_container_width=True)

    with c8:
        anc_sub = df[df["anciennete"].between(0, 45)][["anciennete", "salaire_corrige", "poids"]].dropna()
        if not anc_sub.empty:
            anc_sub["Tranche (ans)"] = pd.cut(
                anc_sub["anciennete"],
                bins=[0, 3, 7, 12, 20, 30, 45],
                labels=["0-3", "4-7", "8-12", "13-20", "21-30", "31+"],
                right=False,
            )
            anc_rows = []
            for label, group in anc_sub.groupby("Tranche (ans)", observed=True):
                med = salaire_median_pondere(group.rename(columns={"salaire_corrige": "salaire_corrige"}))
                if not np.isnan(med):
                    anc_rows.append({"Ancienneté (ans depuis diplôme)": str(label), "Médiane (€)": med})
            if anc_rows:
                fig_anc = px.bar(
                    pd.DataFrame(anc_rows),
                    x="Ancienneté (ans depuis diplôme)", y="Médiane (€)",
                    title="Salaire médian brut par ancienneté",
                    color_discrete_sequence=[COLORS["primary"]],
                    text="Médiane (€)",
                )
                fig_anc.update_traces(texttemplate="%{text:,.0f} €", textposition="outside")
                fig_anc.update_layout(height=380, margin=dict(l=0, r=0, t=40, b=60), title_font_size=14)
                st.plotly_chart(fig_anc, use_container_width=True)


# ─── TAB 4 : TRAVAIL & IA ─────────────────────────────────────────────────────

with tab4:
    st.subheader("Télétravail")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(pie_chart(df, "teletravail", "Pratique du télétravail"), use_container_width=True)
    with c2:
        st.plotly_chart(bar_chart(df[df["teletravail"] == "Oui"], "jours_teletravail", "Jours de télétravail / semaine", top_n=8, horizontal=False), use_container_width=True)
    with c3:
        # Teletravail by sector
        tele_sect = []
        for s, sdf in df.groupby("secteur", dropna=True):
            total = sdf["poids"].sum()
            if total < 50:
                continue
            n_oui = sdf.loc[sdf["teletravail"] == "Oui", "poids"].sum()
            tele_sect.append({"Secteur": s, "% télétravail": round(100 * n_oui / total, 1)})
        if tele_sect:
            tele_df = pd.DataFrame(tele_sect).sort_values("% télétravail").tail(10)
            fig_ts = px.bar(tele_df, x="% télétravail", y="Secteur", orientation="h",
                            title="Télétravail par secteur (Top 10)",
                            color_discrete_sequence=[COLORS["primary"]])
            fig_ts.update_layout(yaxis_title=None, height=340, margin=dict(l=0, r=0, t=40, b=0), title_font_size=14)
            st.plotly_chart(fig_ts, use_container_width=True)

    st.subheader("Intelligence Artificielle")
    c4, c5 = st.columns(2)
    with c4:
        st.plotly_chart(pie_chart(df, "utilise_ia", "Utilisation de l'IA au travail"), use_container_width=True)
    with c5:
        st.plotly_chart(bar_chart(df[df["utilise_ia"] == "Oui"], "type_ia", "Type d'IA utilisée", top_n=8, color=COLORS["secondary"]), use_container_width=True)

    c6, c7 = st.columns(2)
    with c6:
        ia_age_order = ["Moins de 30 ans", "De 30 à 39 ans", "De 40 à 49 ans", "De 50 à 64 ans", "65 et plus"]
        # IA by age
        ia_age = []
        for a in ia_age_order:
            adf = df[df["age"] == a]
            total = adf["poids"].sum()
            if total < 20:
                continue
            n = adf.loc[adf["utilise_ia"] == "Oui", "poids"].sum()
            ia_age.append({"Âge": a, "% utilisant l'IA": round(100 * n / total, 1)})
        if ia_age:
            fig_ia_age = px.bar(
                pd.DataFrame(ia_age), x="Âge", y="% utilisant l'IA",
                title="Utilisation de l'IA par tranche d'âge",
                color_discrete_sequence=[COLORS["secondary"]],
                category_orders={"Âge": ia_age_order},
            )
            fig_ia_age.update_layout(height=360, margin=dict(l=0, r=0, t=40, b=60), title_font_size=14)
            fig_ia_age.update_xaxes(tickangle=-20)
            st.plotly_chart(fig_ia_age, use_container_width=True)

    with c7:
        st.plotly_chart(bar_chart(df, "competence_ia", "Auto-évaluation des compétences IA", top_n=8, color=COLORS["secondary"], horizontal=False), use_container_width=True)

    st.subheader("Satisfaction au travail")
    sat_counts = (
        df.groupby("satisfaction", dropna=True)["poids"]
        .sum()
        .sort_index()
        .reset_index()
    )
    sat_counts.columns = ["Satisfaction", "Effectif"]
    fig_sat = px.bar(
        sat_counts, x="Satisfaction", y="Effectif",
        title="Satisfaction globale au travail",
        color="Satisfaction",
        color_discrete_sequence=px.colors.sequential.Teal,
    )
    fig_sat.update_layout(showlegend=False, height=360, margin=dict(l=0, r=0, t=40, b=0), title_font_size=14)
    st.plotly_chart(fig_sat, use_container_width=True)


# ─── TAB 5 : COMPARAISON 2024-2025 ────────────────────────────────────────────

with tab5:
    st.subheader("Comparaison des salaires bruts médians 2024 vs 2025")

    # Apply filters to 2024 where possible
    df24_filtered = df24.copy()
    if sel_genre != "Tous":
        df24_filtered = df24_filtered[df24_filtered["genre"] == sel_genre]

    med_2024 = salaire_median_pondere(df24_filtered)
    med_2025 = salaire_median_pondere(df)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Salaire médian 2024", f"{med_2024:,.0f} €".replace(",", " ") if not np.isnan(med_2024) else "N/A")
    with c2:
        st.metric("Salaire médian 2025", f"{med_2025:,.0f} €".replace(",", " ") if not np.isnan(med_2025) else "N/A")
    with c3:
        if not np.isnan(med_2024) and not np.isnan(med_2025) and med_2024 > 0:
            delta = (med_2025 - med_2024) / med_2024 * 100
            st.metric("Évolution", f"{delta:+.1f} %")

    # Salary distribution comparison
    df_comp = pd.concat([
        df24_filtered[["salaire_corrige", "poids", "annee"]].dropna(),
        df[["salaire_corrige", "poids", "annee"]].dropna(),
    ])
    df_comp["annee"] = df_comp["annee"].astype(str)

    fig_comp = px.histogram(
        df_comp[df_comp["salaire_corrige"] < 300_000],
        x="salaire_corrige",
        color="annee",
        nbins=60,
        barmode="overlay",
        opacity=0.7,
        title="Distribution des salaires bruts 2024 vs 2025",
        labels={"salaire_corrige": "Salaire brut annuel (€)", "annee": "Année"},
        color_discrete_sequence=[COLORS["secondary"], COLORS["primary"]],
    )
    fig_comp.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0), title_font_size=14)
    st.plotly_chart(fig_comp, use_container_width=True)

    # Gender pay gap 2024 vs 2025
    st.subheader("Écart salarial H/F — évolution")
    rows = []
    for annee, dff in [("2024", df24_filtered), ("2025", df)]:
        for g in ["Masculin", "Féminin"]:
            sub = dff[dff["genre"] == g]
            med = salaire_median_pondere(sub)
            if not np.isnan(med):
                rows.append({"Année": annee, "Genre": g, "Médiane (€)": med})
    if rows:
        fig_gap = px.bar(
            pd.DataFrame(rows),
            x="Année", y="Médiane (€)",
            color="Genre",
            barmode="group",
            color_discrete_map=COLORS,
            title="Salaire médian brut H/F en 2024 et 2025",
            text="Médiane (€)",
        )
        fig_gap.update_traces(texttemplate="%{text:,.0f} €", textposition="outside")
        fig_gap.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0), title_font_size=14)
        st.plotly_chart(fig_gap, use_container_width=True)

    # Cadre status comparison
    st.subheader("Statut cadre — comparaison")
    cadre_rows = []
    for annee, dff in [("2024", df24_filtered), ("2025", df)]:
        if "cadre" in dff.columns:
            total = dff["poids"].sum()
            n_oui = dff.loc[dff["cadre"] == "Oui", "poids"].sum()
            if total > 0:
                cadre_rows.append({"Année": annee, "% cadres": round(100 * n_oui / total, 1)})
    if cadre_rows:
        fig_cadre = px.bar(
            pd.DataFrame(cadre_rows),
            x="Année", y="% cadres",
            title="Part des cadres 2024 vs 2025",
            color_discrete_sequence=[COLORS["primary"]],
            text="% cadres",
        )
        fig_cadre.update_traces(texttemplate="%{text} %", textposition="outside")
        fig_cadre.update_layout(height=340, margin=dict(l=0, r=0, t=40, b=0), title_font_size=14)
        st.plotly_chart(fig_cadre, use_container_width=True)


# ─── TAB 6 : SIMULATEUR DE CARRIÈRE ──────────────────────────────────────────

AGE_ORDER_SIM = [
    "Moins de 30 ans", "De 30 à 39 ans", "De 40 à 49 ans", "De 50 à 64 ans", "65 et plus"
]

with tab6:
    st.markdown("## 🎯 Simulateur de carrière — Jeune ingénieur")
    st.markdown(
        "Renseignez votre profil pour estimer votre rémunération et obtenir "
        "des repères de carrière issus des données IESF 2025 et de data.gouv.fr (InserSup)."
    )

    form_col, result_col = st.columns([1, 2], gap="large")

    with form_col:
        with st.form("sim_form"):
            st.subheader("Votre profil")
            sim_genre = st.radio("Genre", ["Masculin", "Féminin"], horizontal=True)
            sim_age = st.selectbox("Tranche d'âge", AGE_ORDER_SIM, index=0)
            diplomes_sim = sorted(df25["diplome"].dropna().unique().tolist())
            sim_diplome = st.selectbox("Type de diplôme", diplomes_sim)
            secteurs_opts = ["Tous"] + sorted(df25["secteur"].dropna().unique().tolist())
            sim_secteur = st.selectbox("Secteur d'activité", secteurs_opts)
            regions_opts = ["Toutes"] + sorted(df25["region"].dropna().unique().tolist())
            sim_region = st.selectbox("Région", regions_opts)
            submitted = st.form_submit_button(
                "Estimer mon salaire", type="primary", use_container_width=True
            )

    with result_col:
        if not submitted:
            st.info(
                "Renseignez votre profil dans le formulaire à gauche "
                "et cliquez sur **Estimer mon salaire**."
            )
        else:
            # Build profile filter — progressively relax if too few data points
            def build_mask(genre, age, diplome, secteur, region):
                m = (df25["genre"] == genre) & (df25["age"] == age) & (df25["diplome"] == diplome)
                if secteur != "Tous":
                    m &= df25["secteur"] == secteur
                if region != "Toutes":
                    m &= df25["region"] == region
                return m

            mask_full = build_mask(sim_genre, sim_age, sim_diplome, sim_secteur, sim_region)
            sub = df25[mask_full].dropna(subset=["salaire_corrige"])
            relaxed = False

            if len(sub) < 20:
                mask_relaxed = (
                    (df25["genre"] == sim_genre)
                    & (df25["age"] == sim_age)
                    & (df25["diplome"] == sim_diplome)
                )
                sub = df25[mask_relaxed].dropna(subset=["salaire_corrige"])
                relaxed = True

            if len(sub) < 5:
                st.warning(
                    "Pas assez de répondants pour ce profil. "
                    "Essayez d'élargir la région ou le secteur."
                )
            else:
                if relaxed:
                    st.info(
                        "Données insuffisantes pour votre région/secteur exact — "
                        "estimation élargie à tous les ingénieurs du même genre, âge et diplôme."
                    )

                med = salaire_median_pondere(sub)
                p25 = salaire_quantile_pondere(sub, 0.25)
                p75 = salaire_quantile_pondere(sub, 0.75)
                n_obs = len(sub)

                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("Fourchette basse (P25)", f"{p25:,.0f} €".replace(",", " "))
                with m2:
                    st.metric("Salaire médian brut", f"{med:,.0f} €".replace(",", " "))
                with m3:
                    st.metric("Fourchette haute (P75)", f"{p75:,.0f} €".replace(",", " "))

                st.caption(f"Basé sur {n_obs} répondants IESF 2025 avec un profil similaire au vôtre.")

                # Salary progression curve (genre + diplome + secteur, all ages)
                prog_mask = (df25["genre"] == sim_genre) & (df25["diplome"] == sim_diplome)
                if sim_secteur != "Tous":
                    prog_mask &= df25["secteur"] == sim_secteur
                prog_rows = []
                for a in AGE_ORDER_SIM:
                    adf = df25[prog_mask & (df25["age"] == a)].dropna(subset=["salaire_corrige"])
                    if len(adf) >= 5:
                        prog_rows.append({
                            "Tranche d'âge": a,
                            "Salaire médian (€)": salaire_median_pondere(adf),
                        })
                if len(prog_rows) >= 2:
                    prog_df = pd.DataFrame(prog_rows)
                    fig_prog = px.line(
                        prog_df,
                        x="Tranche d'âge", y="Salaire médian (€)",
                        title="Progression salariale au fil de la carrière — profil similaire",
                        markers=True,
                        color_discrete_sequence=[COLORS["primary"]],
                        category_orders={"Tranche d'âge": AGE_ORDER_SIM},
                    )
                    cur = prog_df[prog_df["Tranche d'âge"] == sim_age]
                    if not cur.empty:
                        fig_prog.add_scatter(
                            x=cur["Tranche d'âge"], y=cur["Salaire médian (€)"],
                            mode="markers",
                            marker=dict(size=14, color=COLORS["secondary"]),
                            name="Votre position actuelle",
                        )
                    fig_prog.update_layout(
                        height=340,
                        margin=dict(l=0, r=0, t=40, b=60),
                        title_font_size=14,
                        yaxis_tickformat=",.0f",
                        yaxis_title="Salaire médian brut annuel (€)",
                    )
                    fig_prog.update_xaxes(tickangle=-20)
                    st.plotly_chart(fig_prog, use_container_width=True)

                # Contextual indicators from IESF
                st.subheader("Indicateurs contextuels — profil similaire (IESF 2025)")
                ic1, ic2, ic3 = st.columns(3)
                total_p = sub["poids"].sum()
                with ic1:
                    n_c = sub.loc[sub["cadre"] == "Oui", "poids"].sum() if "cadre" in sub.columns else 0
                    st.metric("Statut cadre", f"{round(100 * n_c / total_p)}%" if total_p > 0 else "N/D")
                with ic2:
                    n_t = sub.loc[sub["teletravail"] == "Oui", "poids"].sum() if "teletravail" in sub.columns else 0
                    st.metric("Pratiquent le télétravail", f"{round(100 * n_t / total_p)}%" if total_p > 0 else "N/D")
                with ic3:
                    n_ia = sub.loc[sub["utilise_ia"] == "Oui", "poids"].sum() if "utilise_ia" in sub.columns else 0
                    st.metric("Utilisent l'IA", f"{round(100 * n_ia / total_p)}%" if total_p > 0 else "N/D")

            # ── datagouv InserSup panel ───────────────────────────────────────
            st.markdown("---")
            st.subheader("Données nationales à l'embauche — data.gouv.fr · InserSup")
            with st.spinner("Interrogation de data.gouv.fr…"):
                insersup = load_insersup(sim_diplome)

            if insersup:
                dg1, dg2, dg3, dg4 = st.columns(4)
                with dg1:
                    v = insersup.get("taux_dinsertion")
                    st.metric("Taux d'insertion à 30 mois", f"{v:.0f} %" if v is not None else "N/D")
                with dg2:
                    v = insersup.get("salaire_net_median")
                    st.metric(
                        "Salaire net médian démarrage",
                        f"{v:,.0f} €".replace(",", " ") if v is not None else "N/D",
                        help="Salaire net mensuel × 12 — source InserSup (30 mois après diplôme)",
                    )
                with dg3:
                    v = insersup.get("taux_emplois_cadre")
                    st.metric("Accès poste cadre", f"{v:.0f} %" if v is not None else "N/D")
                with dg4:
                    v = insersup.get("taux_emplois_stables")
                    st.metric("Emploi stable (CDI)", f"{v:.0f} %" if v is not None else "N/D")

                st.caption(
                    "Source : Ministère de l'Enseignement supérieur — Dispositif InserSup "
                    "(dernière année disponible). Le salaire InserSup est **net**, "
                    "le salaire IESF ci-dessus est **brut annuel**."
                )
            else:
                st.info(
                    "Données InserSup non disponibles pour ce type de diplôme "
                    "(couverture : Diplôme d'ingénieur, Master, Doctorat)."
                )


# ─── TAB 7 : GÉOGRAPHIE & EMPLOI ─────────────────────────────────────────────

with tab7:
    st.markdown("## 🗺️ Géographie & Emploi")

    geo_col, map_col = st.columns([1, 3])

    with geo_col:
        st.markdown("### Paramètres")
        map_metric = st.radio(
            "Indicateur affiché",
            ["Nombre d'ingénieurs", "Salaire médian (€)", "Taux de télétravail (%)"],
            index=0,
        )
        map_scope = st.radio("Territoire", ["Lieu de travail", "Lieu de résidence"], index=0)
        st.markdown("---")
        st.caption(
            "La carte représente les ingénieurs travaillant "
            "ou résidant dans chaque département selon le filtre global."
        )

    with map_col:
        dept_col = "dept_travail_code" if map_scope == "Lieu de travail" else "dept_residence_code"
        dept_label_col = "dept_travail" if map_scope == "Lieu de travail" else "dept_residence"

        dept_sub = df[[dept_col, dept_label_col, "salaire_corrige", "teletravail", "poids"]].copy()
        dept_sub = dept_sub[dept_sub[dept_col].notna()]

        dept_rows = []
        for code, gdf in dept_sub.groupby(dept_col):
            count = gdf["poids"].sum()
            if count < 5:
                continue
            med_sal = salaire_median_pondere(gdf)
            total_p = gdf["poids"].sum()
            n_tele = gdf.loc[gdf["teletravail"] == "Oui", "poids"].sum()
            pct_tele = round(100 * n_tele / total_p, 1) if total_p > 0 else 0
            label = gdf[dept_label_col].dropna().mode()
            label = label.iloc[0] if not label.empty else code
            dept_rows.append({
                "code": code,
                "label": label,
                "count": round(count),
                "salaire": med_sal if not np.isnan(med_sal) else None,
                "teletravail": pct_tele,
            })

        dept_df = pd.DataFrame(dept_rows)

        metric_col_map = {
            "Nombre d'ingénieurs": ("count", "Ingénieurs", "Blues"),
            "Salaire médian (€)": ("salaire", "Salaire médian (€)", "RdYlGn"),
            "Taux de télétravail (%)": ("teletravail", "Télétravail (%)", "Teal"),
        }
        val_col, val_label, colorscale = metric_col_map[map_metric]

        geojson = load_geojson_depts()
        if geojson and not dept_df.empty:
            fig_map = px.choropleth_mapbox(
                dept_df.dropna(subset=[val_col]),
                geojson=geojson,
                locations="code",
                featureidkey="properties.code",
                color=val_col,
                color_continuous_scale=colorscale,
                mapbox_style="open-street-map",
                zoom=4.6,
                center={"lat": 46.5, "lon": 2.3},
                opacity=0.75,
                hover_name="label",
                hover_data={val_col: True, "code": False},
                labels={val_col: val_label},
                title=f"{map_metric} par département",
            )
            fig_map.update_layout(
                height=520,
                margin=dict(l=0, r=0, t=40, b=0),
                coloraxis_colorbar=dict(title=val_label, thickness=12),
                title_font_size=15,
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("Carte indisponible — GeoJSON non chargé ou données insuffisantes.")

    st.markdown("---")
    col_geo1, col_geo2 = st.columns(2)

    with col_geo1:
        if not dept_df.empty:
            top_dept = dept_df.nlargest(15, "count")[["label", "count", "salaire"]].copy()
            top_dept.columns = ["Département", "Ingénieurs", "Salaire médian (€)"]
            fig_top = px.bar(
                top_dept.sort_values("Ingénieurs"),
                x="Ingénieurs", y="Département", orientation="h",
                title="Top 15 départements — concentration d'ingénieurs",
                color="Ingénieurs", color_continuous_scale="Blues",
                text="Ingénieurs",
            )
            fig_top.update_traces(texttemplate="%{text:.0f}", textposition="outside")
            fig_top.update_layout(showlegend=False, coloraxis_showscale=False, yaxis_title=None, height=480, margin=dict(l=0, r=40, t=40, b=0), title_font_size=14)
            st.plotly_chart(fig_top, use_container_width=True)

    with col_geo2:
        idf_regions = ["Île-de-France"]
        df["zone"] = df["region"].apply(
            lambda r: "Île-de-France" if str(r) in idf_regions else "Province" if pd.notna(r) else None
        )
        zone_rows = []
        for zone in ["Île-de-France", "Province"]:
            zdf = df[df["zone"] == zone]
            if zdf["poids"].sum() < 10:
                continue
            med = salaire_median_pondere(zdf)
            n_tele = zdf.loc[zdf["teletravail"] == "Oui", "poids"].sum()
            pct_tele = round(100 * n_tele / zdf["poids"].sum(), 1)
            n_cadre = zdf.loc[zdf["cadre"] == "Oui", "poids"].sum()
            pct_cadre = round(100 * n_cadre / zdf["poids"].sum(), 1)
            zone_rows.append({"Zone": zone, "Salaire médian (€)": med, "Télétravail (%)": pct_tele, "Cadres (%)": pct_cadre})

        if zone_rows:
            zone_df = pd.DataFrame(zone_rows)
            fig_zone = px.bar(
                zone_df, x="Zone", y="Salaire médian (€)",
                color="Zone", color_discrete_sequence=[COLORS["secondary"], COLORS["primary"]],
                title="Île-de-France vs Province — salaire médian brut",
                text="Salaire médian (€)",
            )
            fig_zone.update_traces(texttemplate="%{text:,.0f} €", textposition="outside")
            fig_zone.update_layout(showlegend=False, height=260, margin=dict(l=0, r=0, t=40, b=0), title_font_size=14)
            st.plotly_chart(fig_zone, use_container_width=True)

            fig_zone2 = px.bar(
                zone_df.melt(id_vars="Zone", value_vars=["Télétravail (%)", "Cadres (%)"]),
                x="Zone", y="value", color="variable", barmode="group",
                title="Télétravail & statut cadre — IDF vs Province",
                text="value",
                color_discrete_sequence=[COLORS["primary"], COLORS["secondary"]],
                labels={"value": "%", "variable": ""},
            )
            fig_zone2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_zone2.update_layout(height=260, margin=dict(l=0, r=0, t=40, b=0), title_font_size=14)
            st.plotly_chart(fig_zone2, use_container_width=True)

    st.markdown("---")
    st.subheader("Top écoles d'ingénieurs par région de résidence")
    ecole_region = (
        df.groupby(["region", "ecole"], dropna=True)["poids"]
        .sum()
        .reset_index()
    )
    ecole_region = ecole_region.sort_values("poids", ascending=False)
    top_regions_ecole = ecole_region.groupby("region").head(1).nlargest(12, "poids")
    fig_er = px.bar(
        top_regions_ecole.sort_values("poids"),
        x="poids", y="region", color="ecole", orientation="h",
        title="École la plus représentée par région (effectif pondéré)",
        labels={"poids": "Effectif", "region": "", "ecole": "École"},
        height=420,
    )
    fig_er.update_layout(margin=dict(l=0, r=0, t=40, b=0), title_font_size=14, legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig_er, use_container_width=True)


# ─── TAB 8 : MARCHÉ & MOBILITÉ ───────────────────────────────────────────────

with tab8:
    st.markdown("## 📈 Marché de l'Emploi & Mobilité Professionnelle")

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    total_w = df["poids"].sum()
    with k1:
        n_mob = df.loc[df["mobilite_5ans"] == "Oui", "poids"].sum()
        st.metric("Mobilité sur 5 ans", f"{round(100 * n_mob / total_w, 1)} %", help="Ont changé d'emploi ou de poste dans les 5 dernières années")
    with k2:
        n_cr = df.loc[df["crainte_emploi"] == "Oui", "poids"].sum()
        st.metric("Craignent de perdre leur emploi", f"{round(100 * n_cr / total_w, 1)} %")
    with k3:
        anc_med = df["anciennete"].median()
        st.metric("Ancienneté médiane", f"{anc_med:.0f} ans" if not np.isnan(anc_med) else "N/A", help="Années écoulées depuis le diplôme")
    with k4:
        taille_order_present = [t for t in TAILLE_ORDER if t in df["taille"].dropna().unique()]
        if taille_order_present:
            ge_pct = round(100 * df.loc[df["taille"] == "GE (5 000 salariés et plus)", "poids"].sum() / total_w, 1)
            st.metric("Dans un grand groupe (GE)", f"{ge_pct} %")

    st.markdown("---")
    col_m1, col_m2 = st.columns(2)

    with col_m1:
        mob_sect = []
        for s, sdf in df.groupby("secteur", dropna=True):
            total_s = sdf["poids"].sum()
            if total_s < 50:
                continue
            n_oui = sdf.loc[sdf["mobilite_5ans"] == "Oui", "poids"].sum()
            mob_sect.append({"Secteur": s, "% mobilité 5 ans": round(100 * n_oui / total_s, 1)})
        if mob_sect:
            mob_df = pd.DataFrame(mob_sect).sort_values("% mobilité 5 ans", ascending=False).head(12).sort_values("% mobilité 5 ans")
            fig_mob = px.bar(
                mob_df, x="% mobilité 5 ans", y="Secteur", orientation="h",
                title="Mobilité professionnelle sur 5 ans par secteur",
                color="% mobilité 5 ans", color_continuous_scale="Oranges",
                text="% mobilité 5 ans",
            )
            fig_mob.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_mob.update_layout(showlegend=False, coloraxis_showscale=False, yaxis_title=None, height=420, margin=dict(l=0, r=40, t=40, b=0), title_font_size=14)
            st.plotly_chart(fig_mob, use_container_width=True)

    with col_m2:
        cr_sect = []
        for s, sdf in df.groupby("secteur", dropna=True):
            total_s = sdf["poids"].sum()
            if total_s < 50:
                continue
            n_cr = sdf.loc[sdf["crainte_emploi"] == "Oui", "poids"].sum()
            cr_sect.append({"Secteur": s, "% crainte emploi": round(100 * n_cr / total_s, 1)})
        if cr_sect:
            cr_df = pd.DataFrame(cr_sect).sort_values("% crainte emploi", ascending=False).head(12).sort_values("% crainte emploi")
            fig_cr = px.bar(
                cr_df, x="% crainte emploi", y="Secteur", orientation="h",
                title="Crainte de perte d'emploi par secteur",
                color="% crainte emploi", color_continuous_scale="Reds",
                text="% crainte emploi",
            )
            fig_cr.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_cr.update_layout(showlegend=False, coloraxis_showscale=False, yaxis_title=None, height=420, margin=dict(l=0, r=40, t=40, b=0), title_font_size=14)
            st.plotly_chart(fig_cr, use_container_width=True)

    st.markdown("---")
    col_m3, col_m4 = st.columns(2)

    with col_m3:
        taille_order_present = [t for t in TAILLE_ORDER if t in df["taille"].dropna().unique()]
        if taille_order_present:
            fig_taille_dist = px.bar(
                pd.DataFrame([
                    {"Taille": t, "Effectif": df.loc[df["taille"] == t, "poids"].sum()}
                    for t in taille_order_present
                ]),
                x="Taille", y="Effectif",
                title="Distribution par taille d'entreprise",
                color="Taille", color_discrete_sequence=px.colors.sequential.Blues[2:],
                category_orders={"Taille": TAILLE_ORDER},
                text="Effectif",
            )
            fig_taille_dist.update_traces(texttemplate="%{text:.0f}", textposition="outside")
            fig_taille_dist.update_layout(showlegend=False, height=340, margin=dict(l=0, r=0, t=40, b=80), title_font_size=14)
            fig_taille_dist.update_xaxes(tickangle=-20)
            st.plotly_chart(fig_taille_dist, use_container_width=True)

            # Mobilité by taille
            mob_taille = []
            for t in taille_order_present:
                tdf = df[df["taille"] == t]
                total_t = tdf["poids"].sum()
                if total_t < 20:
                    continue
                n_oui = tdf.loc[tdf["mobilite_5ans"] == "Oui", "poids"].sum()
                mob_taille.append({"Taille": t, "% mobilité": round(100 * n_oui / total_t, 1)})
            if mob_taille:
                fig_mob_taille = px.bar(
                    pd.DataFrame(mob_taille),
                    x="Taille", y="% mobilité",
                    title="Mobilité sur 5 ans par taille d'entreprise",
                    color_discrete_sequence=[COLORS["secondary"]],
                    text="% mobilité",
                    category_orders={"Taille": TAILLE_ORDER},
                )
                fig_mob_taille.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig_mob_taille.update_layout(height=320, margin=dict(l=0, r=0, t=40, b=80), title_font_size=14)
                fig_mob_taille.update_xaxes(tickangle=-20)
                st.plotly_chart(fig_mob_taille, use_container_width=True)

    with col_m4:
        anc_sal_sub = df[df["anciennete"].between(0, 40)][["anciennete", "salaire_corrige", "genre", "poids"]].dropna()
        if not anc_sal_sub.empty:
            anc_sal_sub["Ancienneté"] = anc_sal_sub["anciennete"].astype(int)
            anc_agg = (
                anc_sal_sub.groupby(["Ancienneté", "genre"])
                .apply(lambda g: salaire_median_pondere(g.rename(columns={"salaire_corrige": "salaire_corrige"})), include_groups=False)
                .reset_index()
            )
            anc_agg.columns = ["Ancienneté", "Genre", "Salaire médian (€)"]
            anc_agg = anc_agg[anc_agg["Genre"].isin(["Masculin", "Féminin"])].dropna()
            if not anc_agg.empty:
                anc_smooth = anc_agg.groupby(["Genre", pd.cut(anc_agg["Ancienneté"], bins=range(0, 42, 2))]).apply(
                    lambda g: g["Salaire médian (€)"].mean(), include_groups=False
                ).reset_index()
                anc_smooth.columns = ["Genre", "Tranche", "Salaire médian (€)"]
                anc_smooth["Ancienneté (centre)"] = anc_smooth["Tranche"].apply(lambda x: x.mid if hasattr(x, "mid") else np.nan)
                anc_smooth = anc_smooth.dropna(subset=["Ancienneté (centre)", "Salaire médian (€)"])
                fig_anc_g = px.line(
                    anc_smooth.sort_values("Ancienneté (centre)"),
                    x="Ancienneté (centre)", y="Salaire médian (€)",
                    color="Genre",
                    color_discrete_map=COLORS,
                    title="Évolution salariale H/F selon l'ancienneté",
                    markers=False,
                    labels={"Ancienneté (centre)": "Années depuis le diplôme"},
                )
                fig_anc_g.update_layout(height=360, margin=dict(l=0, r=0, t=40, b=0), title_font_size=14, yaxis_tickformat=",.0f", yaxis_title="Salaire médian brut (€)")
                st.plotly_chart(fig_anc_g, use_container_width=True)

        st.plotly_chart(
            salary_by_group_bar(df, "domaine_fonctionnel", "Salaire médian par domaine fonctionnel", top_n=12),
            use_container_width=True,
        )


# ─── TAB 9 : MENTORS — TRAJECTOIRE PAR AFFINITÉ ──────────────────────────────

with tab9:
    st.markdown("## 🧭 Mentors — Trouve les profils qui te ressemblent... dans quelques années")
    st.caption(
        "Indique ce qui compte le plus pour toi, et découvre les profils de "
        "l'enquête IESF plus expérimentés qui correspondent le mieux à tes priorités."
    )

    m_c1, m_c2 = st.columns(2)
    with m_c1:
        m_ecart = st.slider(
            "Ancienneté visée pour les profils recherchés (années depuis le diplôme)",
            min_value=0, max_value=40, value=(8, 15), key="mentors_ecart",
            help="La fourchette d'ancienneté des profils que tu veux voir apparaître dans les résultats.",
        )
    with m_c2:
        m_localisation = st.selectbox(
            "Localisation (optionnel)",
            ["Peu importe", "Île-de-France", "Province", "International"],
            key="mentors_localisation",
            help="Île-de-France / Province : lieu de travail en France. International : hors France.",
        )

    st.markdown("### Ce qui compte le plus pour toi")
    st.caption(
        "Répartis 100 points entre les critères : monter un curseur fait "
        "automatiquement baisser les autres, pour que le total reste toujours à 100."
    )

    init_mentors_weights()

    m_cols_sliders = st.columns(2)
    for i, critere in enumerate(MENTORS_CRITERES_LIST):
        with m_cols_sliders[i % 2]:
            st.slider(
                critere, 0, 100,
                key=_mentors_slider_key(critere),
                on_change=rebalance_mentors_weights,
                args=(critere,),
            )

    m_weights_raw = {c: st.session_state[_mentors_slider_key(c)] for c in MENTORS_CRITERES_LIST}
    m_total_w = sum(m_weights_raw.values())
    st.caption(f"Total réparti : {m_total_w} / {MENTORS_BUDGET} points")

    COVERAGE_MIN = 0.8  # seuil minimum de réponse aux critères pondérés

    if m_total_w == 0:
        st.warning("Mets au moins un curseur au-dessus de 0 pour lancer la recherche.")
    else:
        m_weights = {k: v / m_total_w for k, v in m_weights_raw.items()}

        ecart_min, ecart_max = m_ecart
        cohorte = df25[
            (df25["anciennete"] >= ecart_min) & (df25["anciennete"] <= ecart_max)
        ].copy()

        if m_localisation == "Île-de-France":
            cohorte = cohorte[cohorte["zone_travail"] == "Ile de France"]
        elif m_localisation == "Province":
            cohorte = cohorte[cohorte["zone_travail"] == "Province"]
        elif m_localisation == "International":
            cohorte = cohorte[cohorte["lieu_travail"] != "France (Métropolitaine et Outre-mer)"]

        # --- Garde-fous qualité : on exige un minimum d'informations ---
        # salaire corrigé obligatoire + au moins secteur OU domaine/service renseigné
        cohorte = cohorte[cohorte["salaire_corrige"].notna()]
        cohorte = cohorte[cohorte["secteur"].notna() | cohorte["domaine_pro"].notna()]

        if len(cohorte) < 5:
            st.error(
                f"Seulement {len(cohorte)} répondant(s) avec salaire et secteur/domaine "
                "renseignés pour cette fourchette d'ancienneté. Essaie de l'élargir."
            )
        else:
            scores, detail, coverage = compute_match_scores(cohorte, m_weights)
            cohorte = cohorte.assign(_match_score=scores, _coverage=coverage)

            # --- Garde-fou qualité : au moins 80% des critères pondérés répondus ---
            cohorte_ok = cohorte[cohorte["_coverage"] >= COVERAGE_MIN]

            if len(cohorte_ok) < 5:
                st.error(
                    f"Seulement {len(cohorte_ok)} répondant(s) ont répondu à au moins "
                    f"{int(COVERAGE_MIN * 100)}% des critères pondérés. Essaie d'élargir "
                    "la fourchette d'ancienneté ou de réduire le nombre de critères "
                    "sur lesquels tu mets du poids."
                )
            else:
                st.caption(
                    f"{len(cohorte_ok)} profils analysés (salaire et secteur/domaine "
                    f"renseignés, au moins {int(COVERAGE_MIN * 100)}% des critères "
                    "pondérés répondus)."
                )

                top_n = min(15, len(cohorte_ok))
                top_matches = cohorte_ok.sort_values("_match_score", ascending=False).head(top_n)

                mk1, mk2, mk3, mk4 = st.columns(4)
                with mk1:
                    compat_moyenne = top_matches["_match_score"].mean() * 100
                    st.metric("Compatibilité moyenne", f"{compat_moyenne:.0f} %",
                              help="Score de correspondance pondéré, calculé uniquement sur les critères auxquels chaque personne a répondu.")
                with mk2:
                    st.metric("% en télétravail", f"{pct(top_matches, 'teletravail', 'Oui')} %")
                with mk3:
                    st.metric("Ancienneté médiane (top matchs)", f"{top_matches['anciennete'].median():.0f} ans")
                with mk4:
                    couverture_moyenne = top_matches["_coverage"].mean() * 100
                    st.metric("Fiabilité moyenne", f"{couverture_moyenne:.0f} %",
                              help="Part de tes critères pondérés auxquels les profils affichés ont effectivement répondu.")

                st.markdown("#### Portraits inspirants")
                top_matches_affichage = top_matches.assign(
                    compatibilite=(top_matches["_match_score"] * 100).round(0),
                    fiabilite=(top_matches["_coverage"] * 100).round(0),
                )

                def _role_desc(row):
                    cp = row.get("role_chef_projet") == "Oui"
                    et = row.get("role_expert_technique") == "Oui"
                    if cp and et:
                        return "Chef de projet & Expert technique"
                    if cp:
                        return "Chef de projet"
                    if et:
                        return "Expert technique"
                    return "Autre"

                top_matches_affichage["role"] = top_matches_affichage.apply(_role_desc, axis=1)

                colonnes_affichage = [
                    c for c in [
                        "compatibilite", "fiabilite", "ecole", "role", "secteur_detail",
                        "domaine_pro", "nature_entreprise", "taille", "dept_residence",
                        "salaire_corrige", "anciennete", "nb_encadres",
                    ] if c in top_matches_affichage.columns
                ]
                st.dataframe(
                    top_matches_affichage[colonnes_affichage]
                    .rename(columns={
                        "compatibilite": "Compatibilité (%)",
                        "fiabilite": "Fiabilité (%)",
                        "role": "Rôle",
                        "secteur_detail": "secteur (détail)",
                        "domaine_pro": "domaine_fonctionnel",
                        "dept_residence": "département de résidence",
                    })
                    .sort_values("Compatibilité (%)", ascending=False)
                    .reset_index(drop=True),
                    use_container_width=True,
                )
                st.caption(
                    "Compatibilité : à quel point ce profil correspond à tes priorités "
                    "(calculé seulement sur ce qu'il/elle a répondu). Fiabilité : part "
                    "de tes critères pondérés auxquels cette personne a répondu."
                )
