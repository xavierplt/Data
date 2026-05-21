import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

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
    2: "diplome",
    59: "age",
    60: "genre",
    69: "region",
    78: "activite",
    79: "situation",
    95: "nature_entreprise",
    101: "secteur",
    120: "cadre",
    121: "type_contrat",
    122: "responsabilites",
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


@st.cache_data(show_spinner="Chargement des données 2025…")
def load_2025():
    df = pd.read_excel(
        PATH_2025,
        sheet_name="Questionnaire 2025",
        engine="openpyxl",
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
    df["annee"] = 2025
    return df


@st.cache_data(show_spinner="Chargement des données 2024…")
def load_2024():
    df = pd.read_excel(
        PATH_2024,
        sheet_name="Questionnaire_2024",
        engine="openpyxl",
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

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["👤 Profil", "🏢 Emploi & Secteurs", "💶 Rémunération", "💻 Travail & IA", "📊 Comparaison 2024-2025"]
)

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
