"""Génère orientation/data/stats.js à partir de l'enquête IESF 2025.

Le site « Boussole IESF » est entièrement statique : il ne lit jamais les
réponses individuelles, seulement les agrégats pondérés produits ici.
Chaque agrégat publié repose sur au moins MIN_N répondants.

Usage :
    python orientation/build_data.py                      # lit l'Excel 2025
    python orientation/build_data.py --source cache.pkl   # DataFrame brut déjà chargé (667 colonnes)
"""
import argparse
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
XLSX_2025 = HERE.parent / "OneDrive_1_17-05-2026" / "exp_Questionnaire 2025.xlsx"
OUT = HERE / "data" / "stats.js"

YEAR = 2025
MIN_N = 30
SAL_MIN, SAL_MAX = 18_000, 500_000

COLS = {
    2: "diplome", 14: "annee_diplome", 51: "annee_naissance", 60: "genre",
    69: "region", 78: "activite", 87: "lieu_travail", 95: "nature",
    99: "taille", 101: "secteur", 114: "raison_secteur", 115: "service",
    122: "manager", 125: "codir", 130: "chef_projet", 131: "expert",
    159: "canal", 160: "crainte", 168: "mobilite", 170: "canal_dernier",
    172: "sat_mobilite", 173: "nature_changement", 175: "raison_depart",
    225: "evol_salaire", 229: "teletravail", 230: "jours_tt",
    487: "ia", 506: "ia_competence", 507: "ia_formation", 551: "sat_globale",
    553: "sat_securite", 554: "sat_interet", 555: "sat_perspectives",
    556: "sat_ambiance", 557: "sat_stress", 558: "sat_charge",
    559: "sat_autonomie", 560: "sat_responsabilites", 561: "sat_sens",
    562: "sat_remuneration", 563: "sat_equilibre", 564: "sat_competences",
    565: "sat_organisation", 566: "sat_strategie", 567: "sat_rh",
    568: "sat_management", 569: "sat_propositions",
    570: "sat_reco_hierarchie", 571: "sat_reco_pairs", 572: "sat_formation",
    573: "intention_changer", 665: "poids", 666: "salaire",
}
SAT_DIMS = [v for v in COLS.values() if v.startswith("sat_") and v not in ("sat_globale", "sat_mobilite")]

# Tranches d'expérience (années depuis le diplôme) — clés partagées avec le site.
EXP_BUCKETS = [("e0", 0, 2), ("e3", 3, 5), ("e6", 6, 10), ("e11", 11, 15),
               ("e16", 16, 20), ("e21", 21, 30), ("e31", 31, 45)]
# Regroupements utilisés pour les comparaisons de secteurs.
STAGE_GROUPS = {"debut": (0, 5), "confirme": (6, 15), "experimente": (16, 30), "senior": (31, 45)}

DIPLOME = {"Ingénieur seul": "ingenieur", "Ingénieur et Docteur": "ing_docteur",
           "Master 2": "master", "Docteur seul": "docteur"}
SECTEUR = {
    "Industrie": "industrie",
    "Autres activités tertiaires": "tertiaire",
    "Sociétés de services informatiques": "numerique",
    "Electricité, Gaz": "energie",
    "Sociétés d’ingénierie ou de conseil (hors numérique)": "ingenierie",
    "Construction, BTP": "btp",
    "Banque, assurances": "banque",
    "Sociétés de conseil (Stratégie, Audit)": "conseil",
    "Télécommunications": "telecoms",
    "Agriculture, sylviculture et pêche": "agriculture",
    "Eau, environnement": "environnement",
}
TAILLE = {"TPE (1 - 49 salariés)": "tpe", "PME (50 à 249 salariés)": "pme",
          "ETI (250 - 4999 salariés)": "eti", "GE (5 000 salariés et plus)": "ge"}
SERVICE = {
    "Études, recherche et conception de produits": "rd",
    "Production et activités connexes": "production",
    "Informatique, réseaux, cybersécurité, data": "it",
    "Direction générale": "direction",
    "Conseil technique": "conseil_tech",
    "Commercial": "commercial",
    "Marketing, Communication": "commercial",
    "Démarche QHSE (qualité, hygiène, sécurité, environnement)": "qhse",
    "Conseil en stratégie, audit, management, RH, finances, lobbying...": "conseil_strat",
    "Enseignement - Formation": "enseignement",
    "Administration, Gestion, Finances": "gestion",
    "RH, Relations sociales": "gestion",
    "Juridique": "gestion",
    "Transport, logistique": "supply",
    "Achats": "supply",
    "Approvisionnement": "supply",
}
CANAL = {
    "Relations professionnelles/personnelles": "relations",
    "Employeur ou cabinet de recrutement": "chasseur",
    "Candidature spontanée": "spontanee",
    "Annonce internet/presse écrite": "annonce",
    "Réseaux professionnels (LinkedIn, Viadeo…)": "linkedin",
    "Lors d’un stage": "stage",
    "Organisme public type APEC, Pôle Emploi, Place de l’emploi public": "public",
    "Réseau des anciens de mon école": "alumni",
    "Écoles/centre de formation/ ITII / CFA": "ecole",
    "Écoles / centre de formation / ITII / CFA": "ecole",
    "Organismes professionnels": "orga_pro",
    "Autre": "autre",
}
CHANGEMENT = {
    "Promotion hiérarchique avec changement de poste au sein de votre entreprise/organisation": "promotion",
    "Affectation vers un autre poste d’un même niveau hiérarchique au sein de votre entreprise/organisation": "interne",
    "Changement d’employeur sans modification du secteur d’activité": "employeur",
    "Changement d’employeur dans un autre secteur d’activité sans période de chômage": "employeur_secteur",
    "Passage du chômage à l’emploi (vous étiez en situation de chômage avant d’obtenir votre emploi actuel)": "chomage",
    "Installation à votre compte, reprise ou création d’entreprise": "creation",
    "Autre changement d’emploi": "autre",
}
RAISON_SECTEUR = {
    "L’adéquation à vos compétences": "competences",
    "Sa correspondance à vos valeurs": "valeurs",
    "D’autres raisons": "autre",
    "L’emploi dans cette région": "region",
    "Ses perspectives d’évolution": "perspectives",
    "Son niveau de rémunération": "remuneration",
}


# --------------------------------------------------------------------------- chargement
def load(source):
    if source and source.endswith(".pkl"):
        raw = pd.read_pickle(source)
        df = raw.iloc[:, sorted(COLS)]
    else:
        df = pd.read_excel(source or XLSX_2025, sheet_name=0, header=0, usecols=sorted(COLS))
    df.columns = [COLS[i] for i in sorted(COLS)]
    return df


def prepare(df):
    df = df[pd.to_numeric(df["poids"], errors="coerce") > 0].copy()
    df["poids"] = df["poids"].astype(float)
    num = lambda c: pd.to_numeric(df[c], errors="coerce")

    naissance = num("annee_naissance").where(lambda s: s.between(1935, 2008))
    df["age_num"] = YEAR - naissance
    exp = YEAR - num("annee_diplome").where(lambda s: s.between(1955, YEAR))
    exp = exp.fillna(df["age_num"] - 24)  # repli : diplôme vers 24 ans
    df["exp"] = exp.clip(0, 45)
    df["exp_bucket"] = pd.cut(df["exp"], [-1] + [b[2] for b in EXP_BUCKETS],
                              labels=[b[0] for b in EXP_BUCKETS]).astype(object)
    df["stage"] = None
    for key, (lo, hi) in STAGE_GROUPS.items():
        df.loc[df["exp"].between(lo, hi), "stage"] = key

    df["diplome_k"] = df["diplome"].map(DIPLOME).fillna("autre")
    df["secteur_k"] = df["secteur"].map(SECTEUR)
    df["taille_k"] = df["taille"].map(TAILLE)
    df["service_k"] = df["service"].map(SERVICE)
    df.loc[df["service"].notna() & df["service_k"].isna(), "service_k"] = "autre"
    df["zone"] = np.where(df["lieu_travail"].notna() & ~df["lieu_travail"].astype(str).str.startswith("France"),
                          "etranger", np.where(df["region"] == "Ile de France", "idf", "province"))
    df.loc[df["region"].isna() & df["lieu_travail"].isna(), "zone"] = None
    df["genre_k"] = df["genre"].map({"Masculin": "h", "Féminin": "f"})
    df["canal_k"] = df["canal"].map(CANAL)
    df["canal_dernier_k"] = df["canal_dernier"].map(CANAL)
    df["changement_k"] = df["nature_changement"].map(CHANGEMENT)
    df["raison_secteur_k"] = df["raison_secteur"].map(RAISON_SECTEUR)
    for c in ["manager", "codir", "chef_projet", "expert", "crainte", "mobilite", "teletravail", "ia"]:
        df[c + "_b"] = df[c].map({"Oui": 1.0, "Non": 0.0})
    df["intention_b"] = df["intention_changer"].map(
        {"Non": 0.0, "Oui": 1.0, "Oui et je suis en recherche active": 1.0})
    df["mobilite_ok_b"] = df["sat_mobilite"].map(
        {"Très satisfait": 1.0, "Satisfait": 1.0, "Ni satisfait ni insatisfait": 0.0,
         "Insatisfait": 0.0, "Très insatisfait": 0.0})
    for c in SAT_DIMS + ["sat_globale", "ia_competence"]:
        df[c] = num(c)
    sal = num("salaire")
    df["sal"] = sal.where(sal.between(SAL_MIN, SAL_MAX))
    df["actif"] = df["activite"].astype(str).str.startswith(("Salarié", "Non salarié"))
    return df


# --------------------------------------------------------------------------- statistiques pondérées
def wquantiles(values, weights, qs):
    m = ~(np.isnan(values) | np.isnan(weights))
    v, w = values[m], weights[m]
    if len(v) == 0:
        return [None] * len(qs)
    order = np.argsort(v)
    v, w = v[order], w[order]
    cw = (np.cumsum(w) - 0.5 * w) / w.sum()
    return [float(np.interp(q, cw, v)) for q in qs]


def wmedian(sub, col="sal"):
    sub = sub[sub[col].notna()]
    if len(sub) < MIN_N:
        return None
    return round(wquantiles(sub[col].values, sub["poids"].values, [0.5])[0], -2)


def wmean(sub, col, digits=3):
    sub = sub[sub[col].notna()]
    if len(sub) < MIN_N:
        return None
    return round(float(np.average(sub[col], weights=sub["poids"])), digits)


def wdist(sub, col, min_n=MIN_N):
    sub = sub[sub[col].notna()]
    if len(sub) < min_n:
        return None
    shares = sub.groupby(col)["poids"].sum() / sub["poids"].sum()
    return {k: round(float(v), 3) for k, v in shares.sort_values(ascending=False).items()}


def profile(sub):
    """Indicateurs d'environnement de travail d'un sous-groupe."""
    out = {"n": int(len(sub))}
    for key, col in [("manager", "manager_b"), ("codir", "codir_b"), ("chefProjet", "chef_projet_b"),
                     ("expert", "expert_b"), ("crainte", "crainte_b"), ("mobilite", "mobilite_b"),
                     ("teletravail", "teletravail_b"), ("ia", "ia_b"), ("intention", "intention_b"),
                     ("mobiliteReussie", "mobilite_ok_b")]:
        out[key] = wmean(sub, col)
    out["iaCompetence"] = wmean(sub, "ia_competence", 2)
    out["satGlobale"] = wmean(sub, "sat_globale", 2)
    out["sat"] = {d.removeprefix("sat_"): wmean(sub, d, 2) for d in SAT_DIMS}
    out["salaire"] = wmedian(sub)
    return out


# --------------------------------------------------------------------------- modèle salarial
FACTORS = {  # facteur -> (colonne, modalité de référence)
    "exp": ("exp_bucket", "e0"),
    "secteur": ("secteur_k", "industrie"),
    "taille": ("taille_k", "ge"),
    "zone": ("zone", "province"),
    "diplome": ("diplome_k", "ingenieur"),
    "service": ("service_k", "rd"),
    "manager": ("manager", "Non"),
    "codir": ("codir", "Non"),
}


def fit_model(df, extra=None):
    """Moindres carrés pondérés sur log(salaire) — effets principaux uniquement."""
    factors = dict(FACTORS, **(extra or {}))
    cols = [c for c, _ in factors.values()]
    d = df[df["actif"] & df["sal"].notna()].dropna(subset=cols)
    blocks, names = [np.ones((len(d), 1))], [("_", "intercept")]
    for fname, (col, ref) in factors.items():
        for level in sorted(d[col].unique()):
            if level == ref:
                continue
            blocks.append((d[col] == level).values.astype(float)[:, None])
            names.append((fname, level))
    X = np.hstack(blocks)
    y = np.log(d["sal"].values)
    sw = np.sqrt(d["poids"].values)
    beta, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    resid = y - X @ beta
    r2 = 1 - np.average(resid**2, weights=d["poids"]) / np.average((y - np.average(y, weights=d["poids"]))**2, weights=d["poids"])
    # Contribution moyenne de chaque facteur : utilisée quand le visiteur ne le renseigne pas.
    w = d["poids"].values
    mean_contrib = {}
    for fname in factors:
        idx = [i for i, (f, _) in enumerate(names) if f == fname]
        mean_contrib[fname] = round(float(np.average(X[:, idx] @ beta[idx], weights=w)), 4)
    coefs = {}
    for (fname, level), b in zip(names, beta):
        if fname == "_":
            continue
        key = {"Oui": "oui"}.get(level, level)
        coefs.setdefault(fname, {})[key] = round(float(b), 4)
    qs = [i / 20 for i in range(1, 20)]
    resid_q = {}
    for b, _, _ in EXP_BUCKETS:
        m = (d["exp_bucket"] == b).values
        resid_q[b] = [round(v, 4) for v in wquantiles(resid[m], d["poids"].values[m], qs)]
    return {"intercept": round(float(beta[0]), 4), "coefs": coefs, "moyenne": mean_contrib, "residQ": resid_q,
            "n": int(len(d)), "r2": round(float(r2), 3)}


# --------------------------------------------------------------------------- agrégats
def build(df):
    act = df[df["actif"]]
    sal = act[act["sal"].notna()]
    qs = [i / 20 for i in range(1, 20)]

    # Courbe de carrière : fenêtre glissante de ±1 an autour de chaque année d'expérience.
    curve = []
    for e in range(0, 41):
        win = sal[sal["exp"].between(e - 1, e + 1)]
        if len(win) >= MIN_N:
            p25, p50, p75 = wquantiles(win["sal"].values, win["poids"].values, [0.25, 0.5, 0.75])
            curve.append({"exp": e, "p25": round(p25, -2), "p50": round(p50, -2), "p75": round(p75, -2), "n": int(len(win))})

    buckets = {}
    for b, lo, hi in EXP_BUCKETS:
        sub = act[act["exp_bucket"] == b]
        subsal = sub[sub["sal"].notna()]
        entry = profile(sub)
        entry["range"] = [lo, hi]
        entry["salQ"] = [round(v, -2) for v in wquantiles(subsal["sal"].values, subsal["poids"].values, qs)]
        entry["canal"] = wdist(sub, "canal_k")
        entry["changement"] = wdist(sub, "changement_k")
        entry["raisonDepart"] = wdist(sub, "raison_depart")
        entry["evolSalaire"] = wdist(sub, "evol_salaire")
        # Écart femmes / hommes brut, médianes.
        f, h = wmedian(subsal[subsal["genre_k"] == "f"]), wmedian(subsal[subsal["genre_k"] == "h"])
        entry["ecartFH"] = round(f / h - 1, 3) if f and h else None
        # Rémunération selon la dernière mobilité (5 dernières années).
        entry["salParChangement"] = {
            "aucun": wmedian(subsal[subsal["mobilite"] == "Non"]),
            "interne": wmedian(subsal[subsal["changement_k"].isin(["promotion", "interne"])]),
            "promotion": wmedian(subsal[subsal["changement_k"] == "promotion"]),
            "employeur": wmedian(subsal[subsal["changement_k"].isin(["employeur", "employeur_secteur"])]),
        }
        # Management vs expertise.
        roles = {
            "manager": sub[(sub["manager_b"] == 1) & (sub["expert_b"] == 0)],
            "expert": sub[(sub["expert_b"] == 1) & (sub["manager_b"] == 0)],
            "hybride": sub[(sub["expert_b"] == 1) & (sub["manager_b"] == 1)],
            "autre": sub[(sub["expert_b"] == 0) & (sub["manager_b"] == 0)],
        }
        entry["roles"] = {k: {"n": int(len(v)), "salaire": wmedian(v), "satGlobale": wmean(v, "sat_globale", 2),
                              "equilibre": wmean(v, "sat_equilibre", 2), "stress": wmean(v, "sat_stress", 2),
                              "interet": wmean(v, "sat_interet", 2)} for k, v in roles.items()}
        buckets[b] = entry

    stage_sectors = {}
    for s in SECTEUR.values():
        sub = act[act["secteur_k"] == s]
        entry = profile(sub)
        entry["salParEtape"] = {k: wmedian(sub[sub["stage"] == k]) for k in STAGE_GROUPS}
        entry["raisonChoix"] = wdist(sub, "raison_secteur_k")
        entry["public"] = wmean(sub.assign(pub=(sub["nature"] == "Etat, secteur public").astype(float)
                                           .where(sub["nature"].notna())), "pub")
        stage_sectors[s] = entry

    services = {}
    for s in sorted(set(SERVICE.values())) + ["autre"]:
        sub = act[act["service_k"] == s]
        entry = profile(sub)
        entry["salParEtape"] = {k: wmedian(sub[sub["stage"] == k]) for k in STAGE_GROUPS}
        services[s] = entry

    tailles = {t: {"salParEtape": {k: wmedian(act[(act["taille_k"] == t) & (act["stage"] == k)]) for k in STAGE_GROUPS},
                   **profile(act[act["taille_k"] == t])} for t in TAILLE.values()}
    zones = {z: {"salParEtape": {k: wmedian(act[(act["zone"] == z) & (act["stage"] == k)]) for k in STAGE_GROUPS},
                 **profile(act[act["zone"] == z])} for z in ["idf", "province", "etranger"]}

    # Retour à l'emploi : canal utilisé par celles et ceux sortis du chômage.
    sortis = df[df["changement_k"] == "chomage"]
    retour = {"n": int(len(sortis)), "canal": wdist(sortis, "canal_dernier_k"),
              "mobiliteReussie": wmean(sortis, "mobilite_ok_b"),
              "parEtape": {k: wdist(sortis[sortis["stage"] == k], "canal_dernier_k") for k in STAGE_GROUPS}}
    chercheurs = df[df["activite"].astype(str).str.startswith("En recherche")]
    retour["partChercheurs"] = {k: wmean(df[df["stage"] == k].assign(r=df["activite"].astype(str).str.startswith("En recherche").astype(float)), "r")
                                for k in STAGE_GROUPS}
    retour["nChercheurs"] = int(len(chercheurs))

    etudiants = df[df["activite"].astype(str).str.startswith("En poursuite")]

    model = fit_model(df)
    model_genre = fit_model(df, {"genre": ("genre_k", "h")})
    model["ecartFHAjuste"] = model_genre["coefs"].get("genre", {}).get("f")

    return {
        "meta": {"source": "Enquête IESF 2025 (situation au 31/12/2024)", "annee": YEAR,
                 "repondants": int(len(df)), "actifs": int(len(act)), "avecSalaire": int(len(sal)),
                 "etudiants": int(len(etudiants)), "minN": MIN_N, "genere": date.today().isoformat(),
                 "salaire": "Rémunération brute annuelle corrigée (fixe + variable), en euros"},
        "global": profile(act),
        "curve": curve,
        "buckets": buckets,
        "secteurs": stage_sectors,
        "services": services,
        "tailles": tailles,
        "zones": zones,
        "retour": retour,
        "model": model,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", help="Excel 2025 ou pickle du DataFrame brut")
    args = ap.parse_args()
    df = prepare(load(args.source))
    stats = build(df)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(stats, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text("// Généré par build_data.py — ne pas modifier à la main.\nwindow.IESF_STATS = " + payload + ";\n",
                   encoding="utf-8")
    m = stats["model"]
    print(f"{OUT} — {len(payload) // 1024} Ko ; modèle n={m['n']} R²={m['r2']} ; écart F/H ajusté={m['ecartFHAjuste']}")


if __name__ == "__main__":
    main()
