"""Constitue orientation/data/entreprises.js à partir de l'API publique Recherche d'entreprises.

Source : https://recherche-entreprises.api.gouv.fr (données SIRENE / INSEE, sans authentification).
Pour chaque famille d'activités (codes NAF) et chaque région, on récupère les employeurs de
taille significative (grandes entreprises, ETI, PME de 50 salariés et plus) et leurs
établissements dans la région, ce qui donne un effectif régional approximatif.

Usage :
    python orientation/build_entreprises.py
"""
import json
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "entreprises.js"
API = "https://recherche-entreprises.api.gouv.fr/search"
PAUSE = 0.2  # l'API tolère 7 requêtes/s
PER_GROUP = 70  # employeurs conservés par famille

# Famille -> (secteur de l'enquête IESF, codes NAF). Les clés sont partagées avec le site.
GROUPS = {
    "aero_defense": ("industrie", ["30.30Z", "30.40Z", "30.11Z", "25.40Z"]),
    "mobilite": ("industrie", ["29.10Z", "29.20Z", "29.31Z", "29.32Z", "30.20Z"]),
    "chimie_sante": ("industrie", ["20.11Z", "20.13B", "20.14Z", "20.16Z", "20.59Z", "20.42Z", "21.10Z", "21.20Z", "32.50A"]),
    "electronique": ("industrie", ["26.11Z", "26.12Z", "26.20Z", "26.30Z", "26.51A", "26.51B", "27.11Z", "27.12Z", "27.20Z", "27.90Z"]),
    "mecanique": ("industrie", ["28.11Z", "28.13Z", "28.15Z", "28.22Z", "28.29B", "28.30Z", "28.41Z", "28.99B", "24.10Z", "24.42Z", "22.11Z", "23.13Z", "23.51Z"]),
    "agro": ("agriculture", ["01.11Z", "01.13Z", "01.21Z", "01.41Z", "01.50Z", "46.21Z", "10.51A", "10.51C", "10.11Z", "10.61A", "10.81Z", "10.86Z", "10.89Z", "11.07A"]),
    "energie": ("energie", ["35.11Z", "35.12Z", "35.13Z", "35.14Z", "35.21Z", "35.22Z", "35.23Z", "35.30Z", "24.46Z"]),
    "numerique": ("numerique", ["62.01Z", "62.02A", "62.02B", "62.03Z", "62.09Z", "58.29A", "58.29C", "63.11Z"]),
    "telecoms": ("telecoms", ["61.10Z", "61.20Z", "61.30Z", "61.90Z"]),
    "ingenierie": ("ingenierie", ["71.12B", "71.20B"]),
    "conseil": ("conseil", ["70.22Z"]),
    "finance": ("banque", ["64.19Z", "64.30Z", "65.11Z", "65.12Z", "66.12Z"]),
    "construction": ("btp", ["41.20A", "41.20B", "42.11Z", "42.12Z", "42.13A", "42.21Z", "42.22Z", "42.99Z", "43.21A", "43.22B"]),
    "eau_env": ("environnement", ["36.00Z", "37.00Z", "38.11Z", "38.12Z", "38.21Z", "38.22Z", "38.32Z", "39.00Z"]),
    "transports_recherche": ("tertiaire", ["72.11Z", "72.19Z", "49.10Z", "49.20Z", "49.31Z", "52.21Z", "51.10Z"]),
}

REGIONS = {"11": "idf", "24": "cvl", "27": "bfc", "28": "normandie", "32": "hdf", "44": "grand_est", "52": "pdl",
           "53": "bretagne", "75": "nouvelle_aquitaine", "76": "occitanie", "84": "ara", "93": "paca"}

# Milieu de chaque tranche d'effectif INSEE.
TRANCHE_MID = {"00": 0, "01": 1.5, "02": 4, "03": 7.5, "11": 15, "12": 35, "21": 75, "22": 150, "31": 225, "32": 375,
               "41": 750, "42": 1500, "51": 3500, "52": 7500, "53": 12000}
BIG = "32,41,42,51,52,53"     # 250 salariés et plus
MID = "21,22,31"              # 50 à 249 salariés

KEEP_UPPER = {"SA", "SAS", "SNC", "EDF", "RTE", "SNCF", "RATP", "CEA", "CNRS", "IFP", "BNP", "AXA", "GRDF", "GRT", "ST", "EADS",
              "MBDA", "IBM", "CGI", "SII", "SNEF", "SPIE", "NGE", "TSO", "ETF", "SEFI", "INRAE", "IFPEN", "ONERA", "CNES", "BRGM",
              "SAUR", "SUEZ", "EGIS", "SETEC", "LCL", "CIC", "HSBC", "BPCE", "AG", "II", "III", "SE", "SCA", "GIE", "ESN", "IT"}


def get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "boussole-iesf/1.0"}), timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 + attempt * 2)
                continue
            if e.code >= 500:
                time.sleep(1 + attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(1 + attempt)
    return {"results": []}


# SIRENE publie les noms en majuscules sans accents : on rétablit les mots les plus courants.
ACCENTS = {
    "ELECTRICITE": "Électricité", "ENERGIE": "Énergie", "ENERGIES": "Énergies", "ENERGETIQUE": "Énergétique", "RESEAU": "Réseau",
    "RESEAUX": "Réseaux", "SOCIETE": "Société", "GENERALE": "Générale", "GENERAL": "Général", "SYSTEMES": "Systèmes", "SYSTEME": "Système",
    "BATIMENT": "Bâtiment", "BATIMENTS": "Bâtiments", "SECURITE": "Sécurité", "DEVELOPPEMENT": "Développement", "INGENIERIE": "Ingénierie",
    "EQUIPEMENTS": "Équipements", "EQUIPEMENT": "Équipement", "MEDITERRANEE": "Méditerranée", "REGIE": "Régie", "DECHETS": "Déchets",
    "DEMANTELEMENT": "Démantèlement", "SPECIALISTES": "Spécialistes", "COOPERATIVE": "Coopérative", "FRANCAISE": "Française",
    "FRANCAIS": "Français", "TELECOM": "Télécom", "TELECOMS": "Télécoms", "TELECOMMUNICATIONS": "Télécommunications",
    "AERONAUTIQUE": "Aéronautique", "AERONAUTIQUES": "Aéronautiques", "DEFENSE": "Défense", "ELECTRONIQUE": "Électronique",
    "ELECTRONIQUES": "Électroniques", "ELECTRIQUE": "Électrique", "ELECTRIQUES": "Électriques", "TECHNOLOGIE": "Technologie",
    "ETUDES": "Études", "ETUDE": "Étude", "CREDIT": "Crédit", "COMPAGNIE": "Compagnie", "INDUSTRIE": "Industrie", "MECANIQUE": "Mécanique",
    "METALLURGIE": "Métallurgie", "PRODUITS": "Produits", "SERVICES": "Services", "EXPLOITATION": "Exploitation", "ENTREPRISE": "Entreprise",
    "ENTREPRISES": "Entreprises", "INTERIM": "Intérim", "STRATEGIE": "Stratégie", "EUROPEENNE": "Européenne", "EUROPEEN": "Européen",
    "AEROSPATIALE": "Aérospatiale", "PHARMACEUTIQUE": "Pharmaceutique", "LABORATOIRES": "Laboratoires", "CHIMIE": "Chimie",
    "DIRECTION": "Direction", "PREVENTION": "Prévention", "DETECTION": "Détection", "REALISATIONS": "Réalisations",
    "COMMUNICATION": "Communication", "MATERIAUX": "Matériaux", "MATERIEL": "Matériel", "MATERIELS": "Matériels", "VEHICULES": "Véhicules",
    "SIDERURGIE": "Sidérurgie", "AGRICOLE": "Agricole", "AGRICOLES": "Agricoles", "CEREALES": "Céréales", "LAITIERE": "Laitière",
    "MUTUELLE": "Mutuelle", "PREVOYANCE": "Prévoyance", "ASSURANCE": "Assurance", "ASSURANCES": "Assurances", "ECOLE": "École",
    "SCIENTIFIQUE": "Scientifique", "AEROPORTS": "Aéroports", "AEROPORT": "Aéroport", "REGIONAL": "Régional", "REGIONALE": "Régionale",
    "NUCLEAIRE": "Nucléaire", "ECOLOGIQUE": "Écologique", "THERMIQUE": "Thermique", "HYDRAULIQUE": "Hydraulique", "AEROSPACE": "Aerospace",
    "IMMOBILIERE": "Immobilière", "IMMOBILIER": "Immobilier", "MEDICAL": "Médical", "MEDICALE": "Médicale", "SANTE": "Santé",
    "CENTRALE": "Centrale", "CREATION": "Création", "OPERATIONS": "Opérations", "PRECISION": "Précision", "ELEVAGE": "Élevage",
}
SMALL = {"DE", "DU", "DES", "ET", "LA", "LE", "LES", "AUX", "EN", "D", "L", "A", "AU", "POUR", "SUR", "PAR"}


def pretty(name):
    import re
    name = re.sub(r"\s+", " ", name).strip()
    # Parenthèses : on ne garde qu'un sigle court qui n'est pas déjà dans le nom.
    def paren(m):
        inner = m.group(1).strip()
        base = name[: m.start()].upper()
        if len(inner) <= 8 and " " not in inner and inner.upper() not in base:
            return f" ({inner.upper()})"
        return ""
    name = re.sub(r"\s*\(([^)]*)\)", paren, name).strip()
    name = re.sub(r"\s+(SAS|SA|SNC|SCA|SARL|SASU)(\s|$)", r"\2", name).strip()
    words = []
    for i, w in enumerate(name.split(" ")):
        core = w.strip("()").upper()
        if "&" in w or w.startswith("("):
            words.append(w.upper())
        elif core in ACCENTS:
            words.append(ACCENTS[core])
        elif "'" in w:
            head, _, tail = w.partition("'")
            words.append(head.lower() + "'" + (ACCENTS.get(tail.upper()) or tail[:1].upper() + tail[1:].lower()))
        elif core in SMALL and i > 0:
            words.append(w.lower())
        elif core in KEEP_UPPER or (len(core) <= 4 and core.isalpha() and not set(core) & set("AEIOUY")):
            words.append(w.upper())
        else:
            words.append("-".join(ACCENTS.get(p.upper()) or (p[:1].upper() + p[1:].lower()) for p in w.split("-")))
    out = " ".join(words)
    out = re.sub(r"\b([dl]) (?=[A-ZÉÈÀ])", r"\1'", out)  # « d Électricité » -> « d'Électricité »
    out = re.sub(r"^([DL]) (?=[A-ZÉ])", r"\1'", out)
    out = re.sub(r" a (?=l'|la |le |les )", " à ", out).replace("' ", "'")
    out = re.sub(r"\b(\w(?:\.\w)+\.?)", lambda m: m.group(1).upper(), out)  # sigles à points
    return out[0].upper() + out[1:] if out else out


def main():
    companies = {}
    n_req = 0
    for group, (sector, codes) in GROUPS.items():
        for reg_code, reg_key in REGIONS.items():
            queries = [({"categorie_entreprise": "GE,ETI", "tranche_effectif_salarie": BIG}, 2),
                       ({"categorie_entreprise": "PME,ETI", "tranche_effectif_salarie": MID}, 1)]
            for extra, pages in queries:
                for page in range(1, pages + 1):
                    d = get({"activite_principale": ",".join(codes), "region": reg_code, "etat_administratif": "A",
                             "per_page": 25, "page": page, **extra})
                    n_req += 1
                    time.sleep(PAUSE)
                    for r in d.get("results", []):
                        if r.get("etat_administratif") != "A" or r.get("tranche_effectif_salarie") in (None, "NN"):
                            continue
                        siren = r["siren"]
                        c = companies.get(siren)
                        if c is None:
                            siege = r.get("siege") or {}
                            comp = r.get("complements") or {}
                            fin = r.get("finances") or {}
                            last = max(fin) if fin else None
                            nj = str(r.get("nature_juridique") or "")
                            c = companies[siren] = {
                                "id": siren, "n": pretty(r.get("nom_complet") or r.get("nom_raison_sociale") or siren),
                                "g": group, "k": sector, "naf": r.get("activite_principale"),
                                "c": r.get("categorie_entreprise"), "t": r.get("tranche_effectif_salarie"),
                                "v": (siege.get("libelle_commune") or "").title(), "rs": REGIONS.get(siege.get("region"), "autre"),
                                "ess": bool(comp.get("est_ess")), "mis": bool(comp.get("est_societe_mission")),
                                "pub": nj[:1] in ("4", "7"), "ca": (fin.get(last) or {}).get("ca") if last else None,
                                "an": (r.get("date_creation") or "")[:4] or None, "r": {},
                            }
                        staff = sum(TRANCHE_MID.get(e.get("tranche_effectif_salarie") or "", 0)
                                    for e in r.get("matching_etablissements", []) if e.get("region") == reg_code)
                        c["r"][reg_key] = max(c["r"].get(reg_key, 0), round(staff))
                    if len(d.get("results", [])) < 25:
                        break
            print(f"{group:22s} {reg_key:20s} -> {len(companies)} employeurs ({n_req} requêtes)", flush=True)

    # Garde, par famille, les employeurs les plus importants (effectif national puis présence régionale).
    by_group = {}
    for c in companies.values():
        by_group.setdefault(c["g"], []).append(c)
    kept = []
    for group, lst in by_group.items():
        lst.sort(key=lambda c: (TRANCHE_MID.get(c["t"], 0), sum(c["r"].values()), len(c["r"])), reverse=True)
        kept.extend(lst[:PER_GROUP])
    for c in kept:
        c["r"] = {k: v for k, v in c["r"].items() if v > 0} or ({c["rs"]: 0} if c["rs"] != "autre" else {})
        if c["ca"] is None:
            del c["ca"]
        for f in ("ess", "mis", "pub"):
            if not c[f]:
                del c[f]

    payload = {"source": "API Recherche d'entreprises (recherche-entreprises.api.gouv.fr), données SIRENE",
               "genere": date.today().isoformat(), "n": len(kept), "entreprises": kept}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("// Généré par build_entreprises.py — ne pas modifier à la main.\nwindow.IESF_ENTREPRISES = "
                   + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"{OUT} — {len(kept)} employeurs sur {len(companies)} trouvés, {n_req} requêtes")


if __name__ == "__main__":
    main()
