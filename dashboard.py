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

PATH_2025 = r"c:\Users\xavpl\OneDrive\Documents\IESF\Data\OneDrive_1_17-05-2026\exp_Questionnaire 2025.xlsx"
PATH_2024 = r"c:\Users\xavpl\OneDrive\Documents\IESF\Data\OneDrive_1_17-05-2026\exp_Questionnaire_2024.xlsx"

# Columns to load from 2025 (by index → clean name)
COLS_2025 = {
    2:   "diplome",
    12:  "ecole",
    14:  "annee_diplome",
    51:  "annee_naissance",
    59:  "age",
    60:  "genre",
    67:  "dept_residence",
    69:  "region",
    78:  "activite",
    79:  "situation",
    93:  "dept_travail",
    95:  "nature_entreprise",
    97:  "domaine_fonctionnel",
    99:  "taille",
    101: "secteur",
    120: "cadre",
    121: "type_contrat",
    122: "responsabilites",
    157: "annee_recrutement",
    160: "crainte_emploi",
    168: "mobilite_5ans",
    211: "salaire_brut",
    216: "part_variable",
    217: "montant_variable",
    229: "teletravail",
    230: "jours_teletravail",
    487: "utilise_ia",
    488: "type_ia",
    506: "competence_ia",
    551: "satisfaction",
    665: "poids",
    666: "salaire_corrige",
}

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

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "👤 Profil",
    "🏢 Emploi & Secteurs",
    "💶 Rémunération",
    "💻 Travail & IA",
    "📊 Comparaison 2024-2025",
    "🎯 Simulateur de Carrière",
    "🗺️ Géographie & Emploi",
    "📈 Marché & Mobilité",
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
