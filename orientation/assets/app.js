/* Boussole IESF — parcours d'orientation et bilan personnalisé.
   Toutes les statistiques viennent de window.IESF_STATS (généré par build_data.py). */
(() => {
  "use strict";

  const S = window.IESF_STATS;
  const NOW = new Date().getFullYear();
  const STORE_KEY = "boussole-iesf-v1";

  // ------------------------------------------------------------------ utilitaires
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const nf = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 });
  const eur = (v) => (v == null ? "—" : nf.format(Math.round(v / 100) * 100) + " €");
  const keur = (v) => (v == null ? "—" : nf.format(Math.round(v / 1000)) + " k€");
  const pct = (v, d = 0) => (v == null ? "—" : (v * 100).toFixed(d).replace(".", ",") + " %");
  const signed = (v, d = 0) => (v == null ? "—" : (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v * 100).toFixed(d).replace(".", ",") + " %");
  const note = (v) => (v == null ? "—" : v.toFixed(1).replace(".", ",") + "/5");
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const sum = (arr) => arr.reduce((a, b) => a + b, 0);

  const store = {
    load() { try { return JSON.parse(localStorage.getItem(STORE_KEY)) || null; } catch { return null; } },
    save(v) { try { localStorage.setItem(STORE_KEY, JSON.stringify(v)); } catch { /* stockage indisponible */ } },
    clear() { try { localStorage.removeItem(STORE_KEY); } catch { /* idem */ } },
  };

  // ------------------------------------------------------------------ référentiels
  const SECTEURS = {
    industrie: ["Industrie", "Industrie (transport, chimie, pharma, machines…)"],
    energie: ["Énergie", "Énergie (électricité, gaz)"],
    numerique: ["Numérique & ESN", "Numérique, ESN, éditeurs de logiciels"],
    ingenierie: ["Ingénierie", "Ingénierie, bureaux d'études"],
    conseil: ["Conseil", "Conseil (stratégie, audit, management)"],
    banque: ["Banque & assurance", "Banque, assurance, finance"],
    btp: ["Construction & BTP", "Construction, BTP"],
    telecoms: ["Télécoms", "Télécommunications"],
    environnement: ["Eau & environnement", "Eau, environnement"],
    agriculture: ["Agriculture", "Agriculture, forêt, pêche"],
    tertiaire: ["Autres services", "Autres services (recherche, enseignement, public, transport…)"],
  };
  const SERVICES = {
    rd: "Études, R&D, conception", production: "Production, industrialisation", it: "Informatique, data, cybersécurité",
    conseil_tech: "Conseil technique, expertise", qhse: "Qualité, HSE", supply: "Achats, logistique, supply chain",
    commercial: "Commercial, marketing", gestion: "Gestion, finance, RH, juridique", conseil_strat: "Conseil en stratégie, management",
    direction: "Direction générale", enseignement: "Enseignement, formation", autre: "Autre fonction",
  };
  const TAILLES = { tpe: ["TPE", "moins de 50 salariés"], pme: ["PME", "50 à 249 salariés"], eti: ["ETI", "250 à 4 999 salariés"], ge: ["Grand groupe", "5 000 salariés et plus"] };
  const ZONES = { idf: "Île-de-France", province: "Autre région de France", etranger: "À l'étranger" };
  const DIPLOMES = {
    ingenieur: ["Diplôme d'ingénieur", "Titre d'ingénieur (CTI)"], ing_docteur: ["Ingénieur et docteur", "Titre d'ingénieur + doctorat"],
    master: ["Master 2", "Master scientifique"], docteur: ["Doctorat", "Sans titre d'ingénieur"], autre: ["Autre", "Autre formation scientifique"],
  };
  const CANAUX = {
    relations: "Relations pro ou perso", chasseur: "Contacté par un employeur ou un cabinet", spontanee: "Candidature spontanée",
    annonce: "Annonce en ligne ou presse", linkedin: "Réseaux professionnels (LinkedIn…)", stage: "À l'issue d'un stage",
    public: "APEC, France Travail, emploi public", alumni: "Réseau des anciens", ecole: "École, CFA", orga_pro: "Organismes professionnels", autre: "Autre",
  };
  const SAT = {
    securite: "Sécurité de l'emploi", interet: "Intérêt du travail", perspectives: "Perspectives de carrière", ambiance: "Ambiance",
    stress: "Niveau de stress", charge: "Charge de travail", autonomie: "Autonomie", responsabilites: "Exercice des responsabilités",
    sens: "Sens du travail", remuneration: "Rémunération", equilibre: "Équilibre vie pro / perso", competences: "Développement des compétences",
    organisation: "Organisation", strategie: "Stratégie de l'entreprise", rh: "Gestion RH", management: "Style de management",
    propositions: "Prise en compte de vos idées", reco_hierarchie: "Reconnaissance de la hiérarchie", reco_pairs: "Reconnaissance des pairs",
    formation: "Accès à la formation",
  };
  const RESSENTI = ["interet", "sens", "remuneration", "perspectives", "reco_hierarchie", "equilibre", "stress"];

  const REGIONS = {
    idf: "Île-de-France", ara: "Auvergne-Rhône-Alpes", occitanie: "Occitanie", nouvelle_aquitaine: "Nouvelle-Aquitaine",
    paca: "Provence-Alpes-Côte d'Azur", grand_est: "Grand Est", hdf: "Hauts-de-France", pdl: "Pays de la Loire",
    bretagne: "Bretagne", normandie: "Normandie", cvl: "Centre-Val de Loire", bfc: "Bourgogne-Franche-Comté",
  };
  const zoneOf = (region) => (!region ? null : region === "idf" ? "idf" : region === "etranger" ? "etranger" : "province");

  // Familles d'employeurs (clés partagées avec build_entreprises.py) -> [libellé, secteur de l'enquête, icône].
  const GROUPS = {
    aero_defense: ["Aéronautique, spatial & défense", "industrie", "plane"],
    mobilite: ["Automobile & ferroviaire", "industrie", "train"],
    chimie_sante: ["Chimie, pharma & santé", "industrie", "flask"],
    electronique: ["Électronique & électrotechnique", "industrie", "circuit"],
    mecanique: ["Mécanique, métallurgie & matériaux", "industrie", "gear"],
    energie: ["Énergie", "energie", "bolt"],
    numerique: ["Numérique & logiciel", "numerique", "code"],
    telecoms: ["Télécoms & réseaux", "telecoms", "antenna"],
    ingenierie: ["Ingénierie, contrôle & essais", "ingenierie", "ruler"],
    conseil: ["Conseil", "conseil", "briefcase"],
    finance: ["Banque & assurance", "banque", "bank"],
    construction: ["Construction & infrastructures", "btp", "building"],
    eau_env: ["Eau, déchets & environnement", "environnement", "drop"],
    agro: ["Agriculture & agroalimentaire", "agriculture", "leaf"],
    transports_recherche: ["Recherche & opérateurs de transport", "tertiaire", "atom"],
  };
  const SIZES = { ge: ["Grand groupe", "5 000 salariés et plus"], eti: ["ETI", "250 à 4 999 salariés"], pme: ["PME", "50 à 249 salariés"] };
  const NATURES = { any: "Peu importe", prive: "Privé", public: "Public" };
  const ROLES = { any: "Peu importe", expert: "Expertise", manager: "Management" };
  const LEVELS = ["Indifférent", "Important", "Essentiel"];
  const TRANCHE_MID = { "21": 75, "22": 150, "31": 225, "32": 375, "41": 750, "42": 1500, "51": 3500, "52": 7500, "53": 12000 };
  const TRANCHE_LABEL = { "21": "50 à 99", "22": "100 à 199", "31": "200 à 249", "32": "250 à 499", "41": "500 à 999", "42": "1 000 à 1 999", "51": "2 000 à 4 999", "52": "5 000 à 9 999", "53": "10 000 et plus" };
  const PRIO_ICON = { remuneration: "coins", evolution: "growth", equilibre: "scale", sens: "heart", securite: "shield", ambiance: "people", autonomie: "compass", serenite: "wave", innovation: "chip" };

  // Pictogrammes au trait, 24×24.
  const ICONS = {
    coins: '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/>',
    growth: '<path d="M4 18l6-6 4 4 6-8"/><path d="M15 8h5v5"/>',
    scale: '<path d="M12 4v16M7 20h10M5 7h14"/><path d="M5 7l-3 6a3 3 0 0 0 6 0zM19 7l-3 6a3 3 0 0 0 6 0z"/>',
    heart: '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
    shield: '<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/>',
    people: '<circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M15 14.5c3 0 6 2 6 5.5"/>',
    compass: '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
    wave: '<path d="M3 10c3-4 6-4 9 0s6 4 9 0"/><path d="M3 16c3-4 6-4 9 0s6 4 9 0"/>',
    chip: '<rect x="7" y="7" width="10" height="10" rx="2"/><path d="M10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4M17 10h4M17 14h4"/>',
    plane: '<path d="M21 15l-8-4V5a1 1 0 0 0-2 0v6l-8 4v2l8-2v4l-2 1.5V21l3-1 3 1v-1.5L13 18v-4l8 2z"/>',
    train: '<rect x="6" y="3" width="12" height="13" rx="3"/><path d="M6 10h12M9 20l-2 2M15 20l2 2M9 13h.01M15 13h.01"/>',
    flask: '<path d="M9 3h6M10 3v6L4.2 19a1.5 1.5 0 0 0 1.3 2h13a1.5 1.5 0 0 0 1.3-2L14 9V3"/><path d="M7 15h10"/>',
    circuit: '<path d="M3 12h4l2-5 4 10 2-5h6"/>',
    gear: '<circle cx="12" cy="12" r="3.2"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
    bolt: '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    code: '<path d="M8 8l-5 4 5 4M16 8l5 4-5 4M14 4l-4 16"/>',
    antenna: '<path d="M12 12v9M8 21h8"/><circle cx="12" cy="10" r="2"/><path d="M7.8 5.8a6 6 0 0 0 0 8.4M16.2 5.8a6 6 0 0 1 0 8.4"/>',
    ruler: '<path d="M4 20L12 4l8 16"/><path d="M7 14h10"/><circle cx="12" cy="4" r="1.2"/>',
    briefcase: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18"/>',
    bank: '<path d="M3 10l9-6 9 6M5 10v8M9 10v8M15 10v8M19 10v8M3 21h18"/>',
    building: '<path d="M4 21V9l6-4v16M10 21h10V11l-6-3"/><path d="M14 13h2M14 17h2M6 13h2M6 17h2"/>',
    drop: '<path d="M12 3s7 7.5 7 12a7 7 0 0 1-14 0c0-4.5 7-12 7-12z"/>',
    leaf: '<path d="M5 21c0-9 5-15 15-16-1 10-7 15-15 16z"/><path d="M5 21l8-8"/>',
    atom: '<circle cx="12" cy="12" r="1.6"/><ellipse cx="12" cy="12" rx="10" ry="4"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(120 12 12)"/>',
    pin: '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    star: '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
    target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
    users: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/>',
  };
  const icon = (name, cls = "ico") => `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ""}</svg>`;

  const PRIORITES = {
    remuneration: { label: "Bien gagner ma vie", m: ["sal", "sat.remuneration"] },
    evolution: { label: "Évoluer et apprendre", m: ["sat.perspectives", "sat.competences"] },
    equilibre: { label: "Équilibre vie pro / perso", m: ["sat.equilibre", "tt"] },
    sens: { label: "Donner du sens à mon travail", m: ["sat.sens"] },
    securite: { label: "Sécurité de l'emploi", m: ["sat.securite", "noCrainte"] },
    ambiance: { label: "Ambiance et management", m: ["sat.ambiance", "sat.management"] },
    autonomie: { label: "Autonomie", m: ["sat.autonomie"] },
    serenite: { label: "Moins de stress", m: ["sat.stress", "sat.charge"] },
    innovation: { label: "Technique, innovation, IA", m: ["ia", "sat.interet"] },
  };
  const METRICS = {
    sal: { label: "Salaire médian", get: (s, g) => s.salParEtape?.[g] ?? s.salaire, fmt: keur },
    tt: { label: "Télétravail", get: (s) => s.teletravail, fmt: (v) => pct(v) },
    noCrainte: { label: "Craint pour son emploi", get: (s) => (s.crainte == null ? null : 1 - s.crainte), fmt: (v) => pct(1 - v) },
    ia: { label: "Utilise l'IA", get: (s) => s.ia, fmt: (v) => pct(v) },
  };
  const metric = (key) => METRICS[key] || { label: SAT[key.slice(4)], get: (s) => s.sat?.[key.slice(4)], fmt: note };

  const STAGES = {
    etudiant: {
      label: "En formation", range: "Élève ou étudiant", group: "debut", bucket: "e0",
      pitch: "Votre enjeu : choisir un premier poste en connaissance de cause et bien le négocier.",
      objectives: [
        ["Choisir un secteur", "Comparer salaires d'embauche et conditions de travail."],
        ["Décrocher le bon stage", "C'est le premier canal d'accès au premier emploi."],
        ["Connaître sa valeur", "Arriver en entretien avec une fourchette réaliste."],
      ],
      projets: { cdi: "Décrocher un premier CDI en France", international: "Démarrer à l'international (VIE…)", these: "Faire une thèse", creer: "Créer une entreprise", indecis: "Je ne sais pas encore" },
    },
    debut: {
      label: "Premier poste", range: "0 à 5 ans d'expérience", group: "debut",
      pitch: "Votre enjeu : vous situer, apprendre vite et réussir votre première mobilité.",
      objectives: [
        ["Se situer", "Vérifier que votre salaire suit le marché."],
        ["Monter en compétences", "Choisir les missions qui construisent votre profil."],
        ["Préparer la première mobilité", "Promotion interne ou changement d'employeur."],
      ],
      projets: { progresser: "Progresser chez mon employeur", changer: "Changer d'employeur", secteur: "Changer de secteur", international: "Partir à l'étranger", these: "Reprendre des études ou une thèse" },
    },
    confirme: {
      label: "Confirmé", range: "6 à 15 ans d'expérience", group: "confirme",
      pitch: "Votre enjeu : choisir votre voie, management ou expertise, et accélérer.",
      objectives: [
        ["Choisir sa voie", "Management, expertise ou les deux."],
        ["Accélérer sa rémunération", "C'est la décennie où les écarts se creusent."],
        ["Garder l'équilibre", "Charge de travail et vie personnelle."],
      ],
      projets: { manager: "Devenir manager", expert: "Devenir expert reconnu", changer: "Changer d'employeur", reconversion: "Me reconvertir", creer: "Créer ou reprendre une entreprise" },
    },
    experimente: {
      label: "Expérimenté", range: "16 à 30 ans d'expérience", group: "experimente",
      pitch: "Votre enjeu : peser sur les décisions, garder du sens et rester employable.",
      objectives: [
        ["Viser la direction", "Codir, responsabilité d'un résultat."],
        ["Se renouveler", "Retrouver de l'intérêt et du sens."],
        ["Rester employable", "IA, nouvelles compétences, réseau."],
      ],
      projets: { direction: "Accéder à la direction (codir)", expert: "Rester expert et transmettre", reconversion: "Changer de voie, retrouver du sens", independant: "Devenir consultant ou indépendant", equilibre: "Ralentir, privilégier l'équilibre" },
    },
    senior: {
      label: "Senior", range: "Plus de 30 ans d'expérience", group: "senior",
      pitch: "Votre enjeu : valoriser votre expertise, la transmettre et préparer la suite.",
      objectives: [
        ["Valoriser son expertise", "Rôles d'expert, de conseil ou de mentor."],
        ["Transmettre", "Former la relève, documenter le savoir."],
        ["Préparer la transition", "Fin de carrière et retraite progressive."],
      ],
      projets: { poursuivre: "Poursuivre dans mon poste", transmettre: "Transmettre (mentorat, tutorat)", independant: "Conseil ou indépendance", retraite: "Préparer une retraite progressive", engagement: "M'engager (associatif, enseignement)" },
    },
  };
  const STAGE_ORDER = ["etudiant", "debut", "confirme", "experimente", "senior"];
  const BUCKETS = [["e0", 0, 2], ["e3", 3, 5], ["e6", 6, 10], ["e11", 11, 15], ["e16", 16, 20], ["e21", 21, 30], ["e31", 31, 99]];

  const SITUATIONS = {
    etudes: ["En études", "École d'ingénieur, master, doctorat"],
    salarie: ["Salarié(e)", "CDI, CDD, fonctionnaire"],
    independant: ["Indépendant(e) ou dirigeant(e)", "À votre compte, gérant, associé"],
    recherche: ["En recherche d'emploi", "Sans activité en ce moment"],
  };

  const EXAMPLE = {
    age: 34, situation: "salarie", genre: "f", diplome: "ingenieur", anneeDiplome: NOW - 10, region: "occitanie", zone: "province",
    secteur: "industrie", service: "rd", taille: "ge", manager: "non", codir: "non", ia: "oui", salaire: 52000,
    ressenti: { interet: 4, sens: 4, remuneration: 2, perspectives: 2, reco_hierarchie: 3, equilibre: 4, stress: 3 },
  };
  const EXAMPLE_SCENARIOS = [
    { name: "Rester à Toulouse", weights: { evolution: 2, equilibre: 2, remuneration: 1 }, themes: ["aero_defense", "electronique"], sizes: ["ge", "eti"],
      nature: "any", ess: false, regions: ["occitanie"], service: "rd", role: "manager", projet: "manager" },
    { name: "Viser Paris", weights: { remuneration: 2, evolution: 1, innovation: 1 }, themes: ["aero_defense", "energie", "numerique"], sizes: ["ge"],
      nature: "any", ess: false, regions: ["idf"], service: "rd", role: "manager", projet: "changer" },
  ];

  const blankScenario = (name, a = {}) => ({
    name, weights: { evolution: 1, remuneration: 1, equilibre: 1 }, themes: [], sizes: [], nature: "any", ess: false,
    regions: REGIONS[a.region] ? [a.region] : [], service: a.situation === "etudes" ? null : a.service || null, role: "any", projet: null,
  });

  // ------------------------------------------------------------------ état
  const saved = store.load() || {};
  let answers = saved.answers || {};
  let scenarios = Array.isArray(saved.scenarios) && saved.scenarios.length ? saved.scenarios : [];
  let active = clamp(saved.active || 0, 0, Math.max(0, scenarios.length - 1));
  let favorites = Array.isArray(saved.favorites) ? saved.favorites : [];
  // Anciennes réponses (une seule liste de priorités) : converties en premier scénario.
  if (!scenarios.length && answers.situation) {
    const sc = blankScenario("Scénario A", answers);
    if (answers.priorites?.length) sc.weights = Object.fromEntries(answers.priorites.map((p) => [p, 2]));
    if (answers.projet) sc.projet = answers.projet;
    scenarios = [sc];
  }
  let isExample = false;
  let stepIndex = 0;
  let stepDir = "fwd";
  const ui = { sort: "match", favOnly: false, shown: 12 };

  function persist() {
    if (!isExample) store.save({ answers, scenarios, active, favorites });
  }
  const current = () => scenarios[active] || (scenarios[0] = blankScenario("Scénario A", answers));
  function ensureScenarios() {
    if (!scenarios.length) scenarios = [blankScenario("Scénario A", answers)];
    active = clamp(active, 0, scenarios.length - 1);
  }

  // ------------------------------------------------------------------ profil calculé
  function computeProfile(a) {
    const age = Number(a.age) || null;
    let exp = a.anneeDiplome ? NOW - Number(a.anneeDiplome) : age ? age - 24 : 0;
    if (a.situation === "etudes") exp = 0;
    exp = clamp(Math.round(exp), 0, 45);
    let stage;
    if (a.situation === "etudes") stage = "etudiant";
    else if ((age && age >= 60) || exp > 30) stage = "senior";
    else if (exp <= 5) stage = "debut";
    else if (exp <= 15) stage = "confirme";
    else stage = "experimente";
    const bucket = stage === "etudiant" ? "e0" : BUCKETS.find(([, lo, hi]) => exp >= lo && exp <= hi)[0];
    return { age, exp, stage, bucket, group: STAGES[stage].group, st: STAGES[stage], b: S.buckets[bucket] };
  }

  const stageFromAnswers = (a) => computeProfile(a).stage;

  // Modèle log-linéaire : log(salaire) = constante + effets principaux + résidu.
  function predict(a, bucket, over = {}) {
    const m = S.model;
    const lv = {
      exp: bucket, secteur: a.secteur, taille: a.situation === "independant" ? null : a.taille, zone: a.zone,
      diplome: a.diplome, service: a.service,
      manager: a.manager === "oui" ? "oui" : a.manager === "non" ? "Non" : null,
      codir: a.codir === "oui" ? "oui" : a.codir === "non" ? "Non" : null, ...over,
    };
    let x = m.intercept;
    for (const f of Object.keys(m.moyenne)) {
      const level = lv[f];
      if (level == null || level === "") x += m.moyenne[f];
      else x += m.coefs[f]?.[level] ?? 0; // modalité de référence => 0
    }
    const r = m.residQ[bucket];
    return { x, q: (i) => Math.exp(x + r[i]), p25: Math.exp(x + r[4]), p50: Math.exp(x + r[9]), p75: Math.exp(x + r[14]), p10: Math.exp(x + r[1]), p90: Math.exp(x + r[17]) };
  }

  function percentileOf(salaire, pred, bucket) {
    const r = Math.log(salaire) - pred.x;
    const arr = S.model.residQ[bucket];
    if (r <= arr[0]) return 0.04;
    if (r >= arr[arr.length - 1]) return 0.96;
    for (let i = 1; i < arr.length; i++) {
      if (r <= arr[i]) return (i + (r - arr[i - 1]) / (arr[i] - arr[i - 1])) / 20;
    }
    return 0.96;
  }

  const coef = (f, level) => (level == null ? null : S.model.coefs[f]?.[level] ?? 0);

  // Classement des secteurs selon les priorités pondérées (1 = important, 2 = essentiel) : moyenne pondérée de z-scores.
  function rankSectors(weights, group) {
    const keys = Object.keys(SECTEURS).filter((k) => S.secteurs[k]);
    const given = Object.fromEntries(Object.entries(weights || {}).filter(([k, v]) => v > 0 && PRIORITES[k]));
    const W = Object.keys(given).length ? given : { remuneration: 1, evolution: 1, equilibre: 1 };
    const prios = Object.keys(W).sort((x, y) => W[y] - W[x]);
    const metricKeys = [...new Set(prios.flatMap((p) => PRIORITES[p].m))];
    const z = {};
    for (const mk of metricKeys) {
      const M = metric(mk);
      const vals = keys.map((k) => M.get(S.secteurs[k], group));
      const ok = vals.filter((v) => v != null);
      const mean = sum(ok) / ok.length;
      const sd = Math.sqrt(sum(ok.map((v) => (v - mean) ** 2)) / ok.length) || 1;
      z[mk] = Object.fromEntries(keys.map((k, i) => [k, vals[i] == null ? 0 : (vals[i] - mean) / sd]));
    }
    const totalW = sum(prios.map((p) => W[p]));
    const rows = keys.map((k) => {
      const perPrio = prios.map((p) => W[p] * sum(PRIORITES[p].m.map((mk) => z[mk][k])) / PRIORITES[p].m.length);
      return { key: k, score: sum(perPrio) / totalW };
    });
    rows.sort((a, b) => b.score - a.score);
    const lo = rows[rows.length - 1].score, hi = rows[0].score;
    rows.forEach((r) => {
      r.fit = hi === lo ? 1 : (r.score - lo) / (hi - lo);
      r.norm = 0.12 + 0.88 * r.fit;
    });
    return { rows, prios, metricKeys, weights: W, isDefault: !Object.keys(given).length };
  }

  // ------------------------------------------------------------------ employeurs : adéquation avec un scénario
  const ENT = (window.IESF_ENTREPRISES && window.IESF_ENTREPRISES.entreprises) || [];
  const ENT_BY_ID = new Map(ENT.map((c) => [c.id, c]));
  const sizeOf = (c) => ({ GE: "ge", ETI: "eti", PME: "pme" }[c.c] || "pme");
  const staffIn = (c, regions) => sum(regions.map((r) => c.r[r] || 0));

  function scoreCompanies(sc, ranking) {
    const fit = Object.fromEntries(ranking.rows.map((r) => [r.key, r.fit]));
    return ENT.map((c) => {
      let wsum = 0, acc = 0;
      const why = [], miss = [];
      const add = (w, v, ok, ko) => { wsum += w; acc += w * v; if (v >= 0.5 && ok) why.push(ok); if (v < 0.5 && ko) miss.push(ko); };
      const f = fit[c.k] ?? 0.5;
      add(3, f, f >= 0.6 ? "Secteur bien placé sur vos priorités" : null, f < 0.35 ? "Secteur moins bien noté sur vos priorités" : null);
      if (sc.themes.length) add(3, sc.themes.includes(c.g) ? 1 : 0, GROUPS[c.g]?.[0], "Hors de vos domaines");
      let local = 0;
      if (sc.regions.length) {
        const present = sc.regions.filter((r) => r in c.r);
        local = staffIn(c, sc.regions);
        const v = !present.length ? 0 : local >= 500 ? 1 : local >= 100 ? 0.85 : 0.7;
        const where = present.map((r) => REGIONS[r]).slice(0, 2).join(", ");
        add(2.5, v, present.length ? `Présent en ${where}${local >= 50 ? ` (≈ ${nf.format(Math.round(local / 50) * 50)} salariés)` : ""}` : null, "Pas d'établissement repéré dans vos régions");
      }
      if (sc.sizes.length) add(1.5, sc.sizes.includes(sizeOf(c)) ? 1 : 0, SIZES[sizeOf(c)][0], `${SIZES[sizeOf(c)][0]}, hors de vos tailles`);
      if (sc.nature === "public") add(1.5, c.pub ? 1 : 0, "Employeur public", "Employeur privé");
      if (sc.nature === "prive") add(1.5, c.pub ? 0 : 1, null, "Employeur public");
      if (sc.ess) add(1.5, c.ess ? 1 : 0, "Économie sociale et solidaire", null);
      return { c, score: Math.round((100 * acc) / wsum), why, miss, local };
    }).sort((x, y) => y.score - x.score || (TRANCHE_MID[y.c.t] || 0) - (TRANCHE_MID[x.c.t] || 0) || y.local - x.local);
  }

  // Salaire visé dans un scénario : premier secteur du classement, avec la taille, la zone, la fonction et le rôle choisis.
  function scenarioSalary(sc, ranking) {
    const P = computeProfile(answers);
    const etu = P.stage === "etudiant";
    const top = ranking.rows[0].key;
    const zones = [...new Set(sc.regions.map(zoneOf))];
    const zone = sc.regions.length ? (zones.length === 1 ? zones[0] : null) : answers.zone;
    const taille = sc.sizes.length ? (sc.sizes.length === 1 ? sc.sizes[0] : null) : answers.taille;
    const manager = sc.role === "manager" ? "oui" : sc.role === "expert" || etu ? "non" : answers.manager;
    const pred = predict({ ...answers, secteur: top, taille, zone, service: sc.service || answers.service, manager, codir: etu ? "non" : answers.codir }, P.bucket);
    const now = etu ? null : answers.salaire || predict(answers, P.bucket).p50;
    return { pred, top, now };
  }

  // Indicateurs moyens des trois premiers secteurs d'un classement.
  function topSectorIndicators(ranking, group) {
    const top = ranking.rows.slice(0, 3).map((r) => S.secteurs[r.key]);
    const avg = (get) => { const v = top.map(get).filter((x) => x != null); return v.length ? sum(v) / v.length : null; };
    return {
      equilibre: avg((s) => s.sat.equilibre), sens: avg((s) => s.sat.sens), perspectives: avg((s) => s.sat.perspectives),
      teletravail: avg((s) => s.teletravail), crainte: avg((s) => s.crainte), salaire: avg((s) => s.salParEtape?.[group] ?? s.salaire),
    };
  }

  const initials = (name) => {
    const acro = name.match(/\(([A-Z0-9&.]{2,8})\)/);
    if (acro) return acro[1].replace(/\./g, "").slice(0, 3);
    const words = name.split(/[\s-]+/).filter((w) => w.length > 2 && !/^(de|du|des|la|le|les|et|aux|pour)$/i.test(w));
    return (words.length > 1 ? words[0][0] + words[1][0] : (words[0] || name).slice(0, 2)).toUpperCase();
  };
  const hueOf = (g) => (Object.keys(GROUPS).indexOf(g) * 47 + 200) % 360;

  // ------------------------------------------------------------------ navigation
  const VIEWS = { home: "view-home", wizard: "view-wizard", explore: "view-explore", compare: "view-compare", results: "view-results", method: "view-method" };
  const HASH = { home: "accueil", wizard: "profil", explore: "criteres", compare: "comparer", results: "bilan", method: "methode" };

  // Barre des phases, commune au parcours, à l'exploration, à la comparaison et au bilan.
  function phaseBar(cur) {
    const ok = !!answers.situation;
    const items = [["wizard", "Votre profil", "Phase 1"], ["explore", "Ce qui compte", "Phase 2"], ["compare", "Comparer", "Vos scénarios"], ["results", "Bilan détaillé", "Synthèse"]];
    const idx = items.findIndex(([v]) => v === cur);
    return `<nav class="phasebar" aria-label="Étapes du parcours"><ol>${items.map(([v, l, s], i) => `
      <li class="${i === idx ? "current" : ""}${ok && i < idx ? " done" : ""}">
        <button type="button" data-goto="${v}" ${!ok && i > 0 ? "disabled" : ""} ${i === idx ? 'aria-current="step"' : ""}>
          <span class="ph-n">${ok && i < idx ? "✓" : i + 1}</span><span class="ph-t"><small>${s}</small>${l}</span>
        </button></li>`).join("")}</ol></nav>`;
  }

  function go(view) {
    if (view === "wizard") return startWizard();
    if (!answers.situation) return startWizard();
    ensureScenarios();
    if (view === "explore") renderExplore();
    if (view === "compare") renderCompare();
    if (view === "results") renderResults();
    show(view);
  }

  function show(view, { push = true } = {}) {
    for (const [k, id] of Object.entries(VIEWS)) $("#" + id).hidden = k !== view;
    if (push && location.hash.slice(1) !== HASH[view]) history.pushState(null, "", "#" + HASH[view]);
    document.body.dataset.view = view;
    window.scrollTo({ top: 0 });
    if (view === "method") renderMethod();
    if (view === "results" && careerChart.last) careerChart(...careerChart.last);
    window.BoussoleMotion?.refresh(document);
  }

  function loadExample() {
    isExample = true;
    answers = { ...EXAMPLE };
    scenarios = EXAMPLE_SCENARIOS.map((s) => JSON.parse(JSON.stringify(s)));
    active = 0;
    favorites = scoreCompanies(scenarios[0], rankSectors(scenarios[0].weights, "confirme")).slice(0, 2).map((x) => x.c.id);
  }

  function route() {
    const h = location.hash.slice(1);
    const has = !!answers.situation;
    if (h === "methode") show("method", { push: false });
    else if (h === "exemple") { loadExample(); renderExplore(); show("explore", { push: false }); }
    else if ((h === "profil" || h === "parcours")) { renderStep(); show("wizard", { push: false }); }
    else if (h === "criteres" && has) { ensureScenarios(); renderExplore(); show("explore", { push: false }); }
    else if (h === "comparer" && has) { ensureScenarios(); renderCompare(); show("compare", { push: false }); }
    else if (h === "bilan" && has) { ensureScenarios(); renderResults(); show("results", { push: false }); }
    else show("home", { push: false });
  }

  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => (t.hidden = true), 2600);
  }

  // ------------------------------------------------------------------ accueil
  function renderHome() {
    $$("[data-stat='actifs']").forEach((el) => (el.textContent = nf.format(Math.floor(S.meta.actifs / 1000) * 1000)));
    $$("[data-stat='source']").forEach((el) => (el.textContent = S.meta.source));
    const at = (e) => S.curve.find((c) => c.exp === e)?.p50;
    const items = [
      ["etudiant", "À l'embauche", "0 an", at(0)],
      ["debut", "Premier poste", "3 ans", at(3)],
      ["confirme", "Confirmé", "10 ans", at(10)],
      ["experimente", "Expérimenté", "22 ans", at(22)],
      ["senior", "Senior", "35 ans", at(35)],
    ];
    const max = Math.max(...items.map((i) => i[3]));
    const you = answers.situation ? stageFromAnswers(answers) : null;
    $("#trail-list").innerHTML = items.map(([k, name, exp, v], i) => `
      <li class="trail-item${k === you ? " is-you" : ""}">
        <span class="trail-dot" aria-hidden="true">${k === you ? "●" : i + 1}</span>
        <div><div class="trail-name">${name}${k === you ? " · vous" : ""}</div><div class="trail-meta">${exp} d'expérience</div></div>
        <span class="trail-sal">${keur(v)}</span>
        <span class="trail-bar" aria-hidden="true"><span style="width:${(v / max) * 100}%"></span></span>
      </li>`).join("");
    $("#stage-cards").innerHTML = STAGE_ORDER.map((k, i) => {
      const st = STAGES[k];
      return `<article class="stage-card${k === you ? " is-you" : ""}"><span class="stage-num">${String(i + 1).padStart(2, "0")}</span>
        <span class="stage-range">${st.range}</span><h3>${st.label}</h3>
        <ul>${st.objectives.map(([t]) => `<li>${t}</li>`).join("")}</ul></article>`;
    }).join("");
    const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    set("stat-rep", nf.format(S.meta.repondants));
    set("stat-emb", keur(at(0)));
    set("stat-top", keur(at(35)));
    set("stat-stage", pct(S.buckets.e0.canal?.stage));
  }

  // ------------------------------------------------------------------ parcours
  // Phase 1 : uniquement le profil. Ce qui compte pour la personne se règle en phase 2.
  function steps() {
    const list = ["vous", "formation"];
    if (answers.situation !== "etudes") list.push("poste");
    if (answers.situation === "salarie" || answers.situation === "independant") list.push("ressenti");
    return list;
  }
  const STEP_LABEL = { vous: "Vous", formation: "Formation", poste: "Poste", ressenti: "Ressenti" };

  const choiceGroup = (name, options, { type = "radio", value, compact = false, max } = {}) => `
    <div class="choices${compact ? " compact" : ""}" ${max ? `data-max="${max}"` : ""}>
      ${Object.entries(options).map(([k, v]) => {
        const [title, sub] = Array.isArray(v) ? v : [v];
        const checked = type === "radio" ? value === k : (value || []).includes(k);
        const id = `${name}-${k}`;
        return `<div class="choice"><input type="${type}" id="${id}" name="${name}" value="${k}" ${checked ? "checked" : ""}>
          <label for="${id}"><b>${esc(title)}</b>${sub ? `<small>${esc(sub)}</small>` : ""}</label></div>`;
      }).join("")}
    </div>`;

  const select = (id, options, value, placeholder = "Je préfère ne pas préciser") => `
    <select class="select" id="${id}" name="${id}">
      <option value="">${placeholder}</option>
      ${Object.entries(options).map(([k, v]) => `<option value="${k}" ${value === k ? "selected" : ""}>${esc(Array.isArray(v) ? v[1] ? `${v[0]} · ${v[1]}` : v[0] : v)}</option>`).join("")}
    </select>`;

  const ouiNon = { oui: "Oui", non: "Non" };

  function stepContent(step) {
    const a = answers;
    switch (step) {
      case "vous": return {
        eyebrow: "Commençons", title: "Qui êtes-vous ?",
        intro: "Votre âge et votre situation déterminent votre étape de carrière, et donc les questions et les conseils qui suivent.",
        body: `
          <div class="field-row">
            <div class="field"><label for="age">Votre âge</label>
              <div class="input-unit"><input class="input" id="age" name="age" type="number" inputmode="numeric" min="16" max="75" value="${esc(a.age ?? "")}" placeholder="Ex. 29" required><span>ans</span></div></div>
            <div class="field"><label for="region">Où vivez-vous ? <span class="opt">facultatif</span></label>
              ${select("region", { ...REGIONS, etranger: "À l'étranger" }, a.region)}
              <p class="hint">Sert à vous comparer à des ingénieurs de la même zone.</p></div>
          </div>
          <fieldset class="field"><legend>Votre situation aujourd'hui</legend>${choiceGroup("situation", SITUATIONS, { value: a.situation })}</fieldset>
          <div class="field" style="max-width:360px"><label for="genre">Genre <span class="opt">facultatif</span></label>
            ${select("genre", { f: "Femme", h: "Homme" }, a.genre)}
            <p class="hint">Sert uniquement à vous informer des écarts de rémunération observés.</p></div>`,
      };
      case "formation": {
        const etu = a.situation === "etudes";
        return {
          eyebrow: "Formation", title: etu ? "Votre formation en cours" : "Votre formation",
          intro: etu ? "Indiquez le diplôme que vous préparez et l'année où vous comptez l'obtenir." : "L'année du diplôme permet de calculer votre expérience et de vous comparer à votre génération.",
          body: `
            <fieldset class="field"><legend>${etu ? "Diplôme préparé" : "Diplôme le plus élevé"}</legend>${choiceGroup("diplome", DIPLOMES, { value: a.diplome })}</fieldset>
            <div class="field"><label for="anneeDiplome">${etu ? "Année d'obtention prévue" : "Année d'obtention du premier diplôme"} <span class="opt">facultatif</span></label>
              <input class="input mono" id="anneeDiplome" name="anneeDiplome" type="number" inputmode="numeric" min="1960" max="${NOW + 6}" value="${esc(a.anneeDiplome ?? "")}" placeholder="Ex. ${NOW - 5}" style="max-width:220px">
              ${etu ? "" : `<p class="hint">Sans réponse, l'expérience est estimée à partir de l'âge (diplôme vers 24 ans).</p>`}</div>`,
        };
      }
      case "poste": {
        const rech = a.situation === "recherche";
        const indep = a.situation === "independant";
        return {
          eyebrow: rech ? "Votre dernier poste" : "Votre poste", title: rech ? "Parlez-nous de votre dernier poste" : "Votre poste actuel",
          intro: "Ces informations servent à vous comparer à des profils vraiment proches du vôtre. Tout est facultatif.",
          body: `
            <div class="field-row">
              <div class="field"><label for="secteur">Secteur</label>${select("secteur", Object.fromEntries(Object.entries(SECTEURS).map(([k, v]) => [k, v[1]])), a.secteur)}</div>
              <div class="field"><label for="service">Fonction</label>${select("service", SERVICES, a.service)}</div>
            </div>
            <div class="field-row">
              ${indep ? "" : `<div class="field"><label for="taille">Taille de l'entreprise</label>${select("taille", TAILLES, a.taille)}</div>`}
              <fieldset class="field"><legend>Vous encadrez une équipe ?</legend>${choiceGroup("manager", ouiNon, { value: a.manager, compact: true })}</fieldset>
            </div>
            <div class="field-row">
              <fieldset class="field"><legend>Membre d'un comité de direction ?</legend>${choiceGroup("codir", ouiNon, { value: a.codir, compact: true })}</fieldset>
            </div>
            <div class="field-row">
              <div class="field"><label for="salaire">${rech ? "Dernier salaire brut annuel" : "Salaire brut annuel"} <span class="opt">facultatif</span></label>
                <div class="input-unit"><input class="input" id="salaire" name="salaire" type="number" inputmode="numeric" min="10000" max="600000" step="500" value="${esc(a.salaire ?? "")}" placeholder="Ex. 48000"><span>€/an</span></div>
                <p class="hint">Fixe + variable, avant impôts et cotisations. Reste sur votre appareil.</p></div>
              <fieldset class="field"><legend>Vous utilisez l'IA dans votre travail ?</legend>${choiceGroup("ia", ouiNon, { value: a.ia, compact: true })}</fieldset>
            </div>`,
        };
      }
      case "ressenti": {
        const r = a.ressenti || {};
        return {
          eyebrow: "Ressenti", title: "Comment vivez-vous votre travail ?",
          intro: "Notez votre satisfaction de 1 (pas du tout satisfait) à 5 (très satisfait). On la comparera à celle de vos pairs, qui ont répondu à la même question.",
          body: `<div>${RESSENTI.map((d) => `
            <div class="scale-row" role="radiogroup" aria-label="${esc(SAT[d])}">
              <span class="scale-label">${SAT[d]}</span>
              <div class="scale">${[1, 2, 3, 4, 5].map((n) => `<div class="choice"><input type="radio" id="r-${d}-${n}" name="r-${d}" value="${n}" ${Number(r[d]) === n ? "checked" : ""}><label for="r-${d}-${n}">${n}</label></div>`).join("")}</div>
            </div>`).join("")}
            <div class="scale-legend"><span>1 = pas du tout satisfait</span><span>5 = très satisfait</span></div></div>`,
        };
      }
    }
  }

  function renderStep() {
    const list = steps();
    stepIndex = clamp(stepIndex, 0, list.length - 1);
    const step = list[stepIndex];
    const c = stepContent(step);
    $("#progress-steps").innerHTML = list.map((s, i) => `<li class="${i < stepIndex ? "done" : i === stepIndex ? "current" : ""}"><span>${STEP_LABEL[s]}</span></li>`).join("");
    $("#wizard-phasebar").innerHTML = phaseBar("wizard");
    $("#wizard-eyebrow").textContent = `Phase 1 · Étape ${stepIndex + 1} sur ${list.length} · ${c.eyebrow}`;
    $("#wizard-title").textContent = c.title;
    $("#wizard-intro").textContent = c.intro;
    $("#wizard-body").innerHTML = c.body;
    $("#wizard-error").hidden = true;
    $("#btn-back").textContent = stepIndex === 0 ? "Accueil" : "Retour";
    $("#btn-next").innerHTML = stepIndex === list.length - 1 ? 'Phase 2 : ce qui compte pour vous <span class="arr" aria-hidden="true">→</span>' : "Continuer";
    const card = $("#wizard-form");
    card.dataset.dir = stepDir;
    card.classList.remove("step-in");
    void card.offsetWidth; // relance l'animation d'entrée
    card.classList.add("step-in");
    enforceMax();
  }

  function enforceMax() {
    $$("#wizard-body .choices[data-max]").forEach((group) => {
      const max = Number(group.dataset.max);
      const boxes = $$("input[type=checkbox]", group);
      const n = boxes.filter((b) => b.checked).length;
      boxes.forEach((b) => (b.disabled = !b.checked && n >= max));
    });
  }

  function readStep() {
    const form = $("#wizard-form");
    const fd = new FormData(form);
    const step = steps()[stepIndex];
    const num = (k) => (fd.get(k) === "" || fd.get(k) == null ? null : Number(fd.get(k)));
    const str = (k) => fd.get(k) || null;
    const next = { ...answers };
    if (step === "vous") Object.assign(next, { age: num("age"), genre: str("genre"), situation: str("situation"), region: str("region"), zone: zoneOf(str("region")) });
    if (step === "formation") Object.assign(next, { diplome: str("diplome"), anneeDiplome: num("anneeDiplome") });
    if (step === "poste") Object.assign(next, {
      secteur: str("secteur"), service: str("service"), taille: str("taille"),
      manager: str("manager"), codir: str("codir"), ia: str("ia"), salaire: num("salaire"),
    });
    if (step === "ressenti") next.ressenti = Object.fromEntries(RESSENTI.map((d) => [d, num("r-" + d)]).filter(([, v]) => v));
    return next;
  }

  function validate(step, a) {
    if (step === "vous") {
      if (!a.age || a.age < 16 || a.age > 75) return "Indiquez votre âge (entre 16 et 75 ans).";
      if (!a.situation) return "Choisissez votre situation actuelle.";
    }
    if (step === "formation" && a.anneeDiplome != null) {
      if (a.anneeDiplome < 1960 || a.anneeDiplome > NOW + 6) return `L'année du diplôme doit être comprise entre 1960 et ${NOW + 6}.`;
      if (a.situation !== "etudes" && a.anneeDiplome > NOW) return "Pour une année future, choisissez la situation « En études ».";
      if (a.age && a.anneeDiplome - (NOW - a.age) < 17) return "L'année du diplôme ne correspond pas à votre âge. Vérifiez-la.";
    }
    if (step === "poste" && a.salaire != null && (a.salaire < 10000 || a.salaire > 600000)) return "Le salaire doit être un montant brut annuel, par exemple 48000.";
    return null;
  }

  function onSubmit(e) {
    e.preventDefault();
    const list = steps();
    const step = list[stepIndex];
    const next = readStep();
    const err = validate(step, next);
    if (err) { const el = $("#wizard-error"); el.textContent = err; el.hidden = false; return; }
    answers = next;
    isExample = false;
    if (stepIndex < steps().length - 1) {
      persist();
      stepIndex++;
      stepDir = "fwd";
      renderStep();
      window.scrollTo({ top: 0 });
    } else {
      ensureScenarios();
      persist();
      renderExplore({ intro: true });
      show("explore");
    }
  }

  function startWizard(reset = false) {
    if (reset || isExample) {
      const s = reset ? {} : store.load() || {};
      answers = s.answers || {};
      scenarios = s.scenarios || [];
      active = s.active || 0;
      favorites = s.favorites || [];
      isExample = false;
    }
    stepIndex = 0;
    stepDir = "fwd";
    renderStep();
    show("wizard");
  }

  // ------------------------------------------------------------------ phase 2 : ce qui compte (critères en direct)
  const setOn = (el, on) => { el.classList.toggle("is-on", on); el.setAttribute("aria-pressed", String(on)); };
  const toggleIn = (arr, v) => { const i = arr.indexOf(v); if (i >= 0) arr.splice(i, 1); else arr.push(v); };

  function profileCard() {
    const a = answers;
    const P = computeProfile(a);
    const etu = P.stage === "etudiant";
    const pred = etu ? null : predict(a, P.bucket);
    const pctile = a.salaire && pred ? percentileOf(a.salaire, pred, P.bucket) : null;
    const lines = [
      a.age ? `${a.age} ans` : null, etu ? "En formation" : `${P.exp} an${P.exp > 1 ? "s" : ""} d'expérience`,
      a.diplome ? DIPLOMES[a.diplome][0] : null, a.secteur ? SECTEURS[a.secteur][0] : null, a.service ? SERVICES[a.service] : null,
      a.region ? REGIONS[a.region] || "À l'étranger" : null,
    ].filter(Boolean);
    return `<div class="pcard">
      <div class="pcard-top"><span class="pcard-eyebrow">Phase 1 · Votre profil</span><button type="button" class="link-btn" data-goto="wizard">Modifier</button></div>
      <div class="pcard-stage"><span class="stage-chip">${esc(P.st.label)}</span>${a.situation === "recherche" ? '<span class="tag">En recherche d\'emploi</span>' : ""}</div>
      <p class="pcard-lines">${lines.map(esc).join(" · ")}</p>
      ${pred ? `<div class="pcard-sal"><span>Fourchette de vos pairs aujourd'hui</span><b>${keur(pred.p25)} – ${keur(pred.p75)}</b>${pctile != null ? `<em>Votre salaire : ${Math.round(pctile * 100)}<sup>e</sup> centile</em>` : ""}</div>` : ""}
    </div>`;
  }

  function scenarioBar(where) {
    const L = "ABC";
    return `<div class="sc-bar">
      <div class="sc-tabs" role="tablist" aria-label="Vos scénarios">
        ${scenarios.map((s, i) => `<button type="button" role="tab" class="sc-tab${i === active ? " is-active" : ""}" aria-selected="${i === active}" data-sc="${i}">
          <span class="sc-letter">${L[i]}</span><span class="sc-name">${esc(s.name)}</span></button>`).join("")}
        ${scenarios.length < 3 ? `<button type="button" class="sc-add" data-action="sc-add"><span aria-hidden="true">+</span> Nouveau scénario</button>` : ""}
      </div>
      <div class="sc-tools">
        ${where === "explore"
          ? `<label class="sc-rename" for="sc-name"><span class="sr-only">Nom du scénario</span><input class="input" id="sc-name" value="${esc(current().name)}" maxlength="40"></label>
             ${scenarios.length > 1 ? `<button type="button" class="btn btn-ghost" data-action="sc-delete">Supprimer</button>` : ""}
             <button type="button" class="btn btn-primary" data-goto="compare">Comparer${scenarios.length > 1 ? ` les ${scenarios.length} scénarios` : ""} <span class="arr" aria-hidden="true">→</span></button>`
          : `<button type="button" class="btn btn-ghost" data-goto="explore">Ajuster les critères</button>
             <button type="button" class="btn btn-primary" data-goto="results">Bilan détaillé <span class="arr" aria-hidden="true">→</span></button>`}
      </div>
    </div>`;
  }

  function criteriaHtml(P) {
    const g = (id, title, hint, body) => `<section class="crit-group" id="cg-${id}">
      <header><h2>${title} <span class="cg-count" data-count="${id}"></span></h2><p>${hint}</p></header>${body}</section>`;
    return [
      g("prio", "Vos priorités", "Touchez une carte pour régler son importance : indifférent, important, essentiel.",
        `<div class="prio-grid">${Object.entries(PRIORITES).map(([k, p]) => `
          <button type="button" class="prio-tile" data-prio="${k}">${icon(PRIO_ICON[k], "pt-ico")}<b>${esc(p.label)}</b>
            <span class="pt-lvl" aria-hidden="true"><i></i><i></i></span><small class="pt-txt"></small></button>`).join("")}</div>`),
      g("dom", "Les domaines qui vous attirent", "Aucun choix = tous les domaines.",
        `<div class="dom-grid">${Object.entries(GROUPS).map(([k, [label, , ic]]) => `
          <button type="button" class="dom-tile" data-dom="${k}" style="--h:${hueOf(k)}">${icon(ic, "dom-ico")}<span>${esc(label)}</span></button>`).join("")}</div>`),
      g("emp", "Le type d'employeur", "Taille, statut et valeurs.",
        `<div class="chip-row">${Object.entries(SIZES).map(([k, [l, s]]) => `<button type="button" class="chip" data-size="${k}"><b>${l}</b><small>${s}</small></button>`).join("")}</div>
         <div class="seg" role="group" aria-label="Public ou privé">${Object.entries(NATURES).map(([k, l]) => `<button type="button" data-nature="${k}">${l}</button>`).join("")}</div>
         <button type="button" class="chip chip-wide" data-ess="">${icon("heart", "ico-s")}<b>Économie sociale et solidaire</b><small>Coopératives, mutuelles</small></button>`),
      g("reg", "Où voulez-vous travailler ?", "Les employeurs implantés dans ces régions passent devant.",
        `<div class="reg-grid"><button type="button" class="chip" data-region=""><b>Toute la France</b></button>${Object.entries(REGIONS).map(([k, l]) => `<button type="button" class="chip" data-region="${k}"><b>${esc(l)}</b></button>`).join("")}</div>`),
      g("role", "Le poste visé", "Change le salaire visé de ce scénario.",
        `<div class="seg" role="group" aria-label="Rôle visé">${Object.entries(ROLES).map(([k, l]) => `<button type="button" data-role="${k}">${l}</button>`).join("")}</div>
         <label class="field" for="sc-service"><span class="fl">Métier</span>${select("sc-service", SERVICES, current().service, "Pas de préférence")}</label>`),
      g("projet", "Votre projet", `Propositions adaptées à votre étape : ${esc(P.st.label.toLowerCase())}.`,
        `<div class="chip-row">${Object.entries(P.st.projets).map(([k, l]) => `<button type="button" class="chip" data-projet="${k}"><b>${esc(l)}</b></button>`).join("")}</div>`),
    ].join("");
  }

  function syncCriteria() {
    const sc = current();
    $$(".prio-tile").forEach((el) => {
      const w = sc.weights[el.dataset.prio] || 0;
      el.dataset.lvl = w;
      el.setAttribute("aria-label", `${PRIORITES[el.dataset.prio].label} : ${LEVELS[w]}`);
      $(".pt-txt", el).textContent = LEVELS[w];
    });
    $$(".dom-tile").forEach((el) => setOn(el, sc.themes.includes(el.dataset.dom)));
    $$("[data-size]").forEach((el) => setOn(el, sc.sizes.includes(el.dataset.size)));
    $$("[data-nature]").forEach((el) => setOn(el, sc.nature === el.dataset.nature));
    $$("[data-ess]").forEach((el) => setOn(el, !!sc.ess));
    $$("[data-region]").forEach((el) => setOn(el, el.dataset.region ? sc.regions.includes(el.dataset.region) : !sc.regions.length));
    $$("[data-role]").forEach((el) => setOn(el, sc.role === el.dataset.role));
    $$("[data-projet]").forEach((el) => setOn(el, sc.projet === el.dataset.projet));
    const nPrio = Object.values(sc.weights).filter((w) => w > 0).length;
    const counts = {
      prio: nPrio ? `${nPrio} retenue${nPrio > 1 ? "s" : ""}` : "par défaut", dom: sc.themes.length ? String(sc.themes.length) : "tous",
      emp: [sc.sizes.length, sc.nature !== "any", sc.ess].filter(Boolean).length || "", reg: sc.regions.length || "France",
      role: sc.role !== "any" ? ROLES[sc.role] : "", projet: sc.projet ? "1" : "",
    };
    $$("[data-count]").forEach((el) => { el.textContent = counts[el.dataset.count] ?? ""; el.hidden = !el.textContent; });
  }

  function renderExplore({ intro = false } = {}) {
    ensureScenarios();
    const P = computeProfile(answers);
    $("#view-explore").innerHTML = `
      <div class="wrap explore${intro ? " is-intro" : ""}">
        ${phaseBar("explore")}
        ${isExample ? `<p class="example-flag">Exemple fictif : une ingénieure R&D de 34 ans à Toulouse, avec deux scénarios à comparer. <button type="button" class="link-btn" data-action="restart">Faire mon propre parcours</button></p>` : ""}
        <header class="ex-head">
          <p class="eyebrow">Phase 2 · Ce qui compte pour vous</p>
          <h1 id="explore-title">Réglez vos critères, les résultats suivent</h1>
          <p class="lede">Chaque changement met à jour les secteurs et les employeurs proposés. Créez plusieurs scénarios pour comparer vos options.</p>
        </header>
        ${scenarioBar("explore")}
        <div class="ex-grid">
          <aside class="crit" aria-label="Vos critères">${profileCard()}${criteriaHtml(P)}</aside>
          <div class="out" id="outcomes" aria-live="polite"></div>
        </div>
        <button type="button" class="peek" id="peek" data-scroll="outcomes" aria-label="Voir les résultats"></button>
      </div>`;
    syncCriteria();
    renderOutcomes();
  }

  function sectorCard(r, i, ranking, group) {
    const s = S.secteurs[r.key];
    const ms = [...new Set(ranking.prios.map((p) => PRIORITES[p].m[0]))].slice(0, 3);
    return `<article class="sec-card" data-flip="s-${r.key}">
      <div class="sec-top"><span class="sec-rank">${i + 1}</span><h3>${esc(SECTEURS[r.key][0])}</h3></div>
      <div class="fit" aria-hidden="true"><span style="width:${Math.round(r.norm * 100)}%"></span></div>
      <dl>${ms.map((mk) => { const M = metric(mk); const v = M.get(s, group); return `<div><dt>${esc(M.label)}</dt><dd>${v == null ? "—" : M.fmt(v)}</dd></div>`; }).join("")}</dl>
    </article>`;
  }

  function companyCard({ c, score, why, miss }) {
    const P = computeProfile(answers);
    const s = S.secteurs[c.k];
    const fav = favorites.includes(c.id);
    const nReg = Object.keys(c.r).length;
    const cls = score >= 75 ? "hi" : score >= 50 ? "mid" : "lo";
    const grp = GROUPS[c.g] || ["", "", "chip"];
    return `<article class="co-card" data-flip="c-${c.id}">
      <div class="co-top">
        <span class="mono-tile" style="--h:${hueOf(c.g)}" aria-hidden="true">${esc(initials(c.n))}</span>
        <div class="co-id"><h3 title="${esc(c.n)}">${esc(c.n)}</h3>
          <p>${icon("pin", "ico-s")}${esc(c.v || "")}${nReg > 1 ? ` · ${nReg} régions` : ""}</p></div>
        <div class="ring ${cls}" role="img" aria-label="Adéquation ${score} %"><svg viewBox="0 0 36 36" aria-hidden="true"><circle class="ring-bg" cx="18" cy="18" r="15.9"/><circle class="ring-fg" cx="18" cy="18" r="15.9" pathLength="100" stroke-dasharray="${score} 100"/></svg><b>${score}</b></div>
      </div>
      <div class="co-tags"><span class="tag">${icon(grp[2], "ico-s")}${esc(grp[0])}</span><span class="tag">${SIZES[sizeOf(c)][0]} · ${TRANCHE_LABEL[c.t] || "?"} sal.</span>${c.ess ? '<span class="tag ess">ESS</span>' : ""}${c.pub ? '<span class="tag pub">Public</span>' : ""}</div>
      <ul class="co-why">${why.slice(0, 3).map((w) => `<li>${esc(w)}</li>`).join("")}${miss.slice(0, 1).map((w) => `<li class="miss">${esc(w)}</li>`).join("")}</ul>
      <div class="co-foot">
        <span class="co-stat"><b>${keur(s?.salParEtape?.[P.group] ?? s?.salaire)}</b> médiane du secteur à votre étape</span>
        <div class="co-actions">
          <button type="button" class="fav-btn${fav ? " is-on" : ""}" data-fav="${c.id}" aria-pressed="${fav}" aria-label="${fav ? "Retirer des favoris" : "Ajouter aux favoris"}">${icon("star")}</button>
          <a class="co-link" href="https://annuaire-entreprises.data.gouv.fr/entreprise/${c.id}" target="_blank" rel="noopener">Fiche officielle ↗</a>
        </div>
      </div>
    </article>`;
  }

  // Animation FLIP : les cartes glissent vers leur nouvelle place quand le classement change.
  function flipFirst(root) {
    const m = new Map();
    $$("[data-flip]", root).forEach((el) => m.set(el.dataset.flip, el.getBoundingClientRect()));
    return m;
  }
  function flipLast(root, first) {
    if (!document.documentElement.classList.contains("anim") || !first.size) return;
    $$("[data-flip]", root).forEach((el) => {
      const a = first.get(el.dataset.flip), b = el.getBoundingClientRect();
      if (a) {
        const dx = a.left - b.left, dy = a.top - b.top;
        if (Math.abs(dx) > 1 || Math.abs(dy) > 1) el.animate([{ transform: `translate(${dx}px, ${dy}px)` }, { transform: "none" }], { duration: 480, easing: "cubic-bezier(.2,.8,.2,1)" });
      } else el.animate([{ opacity: 0, transform: "translateY(10px) scale(.97)" }, { opacity: 1, transform: "none" }], { duration: 380, easing: "ease-out" });
    });
  }

  function renderOutcomes() {
    const box = $("#outcomes");
    if (!box) return;
    const sc = current();
    const P = computeProfile(answers);
    const ranking = rankSectors(sc.weights, P.group);
    const scored = scoreCompanies(sc, ranking);
    const sal = scenarioSalary(sc, ranking);
    const strong = scored.filter((x) => x.score >= 70).length;
    let list = ui.favOnly ? scored.filter((x) => favorites.includes(x.c.id)) : scored;
    if (ui.sort === "size") list = [...list].sort((x, y) => (TRANCHE_MID[y.c.t] || 0) - (TRANCHE_MID[x.c.t] || 0) || y.score - x.score);
    if (ui.sort === "local") list = [...list].sort((x, y) => y.local - x.local || y.score - x.score);
    const shown = list.slice(0, ui.shown);
    const first = flipFirst(box);
    const delta = sal.now ? sal.pred.p50 / sal.now - 1 : null;
    box.innerHTML = `
      <div class="snap">
        <div class="snap-tile snap-main">
          <span class="snap-l">${icon("coins", "ico-s")}Salaire visé dans ce scénario</span>
          <b class="snap-v">${keur(sal.pred.p50)}</b>
          <span class="snap-sub">50 % entre ${keur(sal.pred.p25)} et ${keur(sal.pred.p75)}</span>
          ${delta != null ? `<span class="snap-delta ${delta >= 0 ? "up" : "down"}">${signed(delta)} par rapport à ${answers.salaire ? "votre salaire" : "votre situation estimée"}</span>` : ""}
        </div>
        <div class="snap-tile"><span class="snap-l">${icon("target", "ico-s")}Secteur n° 1</span><b class="snap-v snap-v-s">${esc(SECTEURS[ranking.rows[0].key][0])}</b>
          <span class="snap-sub">puis ${ranking.rows.slice(1, 3).map((r) => esc(SECTEURS[r.key][0])).join(" et ")}</span></div>
        <div class="snap-tile"><span class="snap-l">${icon("users", "ico-s")}Employeurs très compatibles</span><b class="snap-v">${nf.format(strong)}</b>
          <span class="snap-sub">adéquation de 70 % ou plus, sur ${nf.format(ENT.length)}</span></div>
      </div>
      <section class="out-sec" aria-labelledby="sec-title">
        <div class="out-h"><h2 id="sec-title">Secteurs en tête</h2><p>Selon vos priorités${ranking.isDefault ? " (par défaut : rémunération, évolution, équilibre)" : ""}, d'après les réponses des ingénieurs à l'enquête IESF 2025.</p></div>
        <div class="sec-cards">${ranking.rows.slice(0, 4).map((r, i) => sectorCard(r, i, ranking, P.group)).join("")}</div>
      </section>
      <section class="out-sec" aria-labelledby="co-title">
        <div class="out-h out-h-row">
          <div><h2 id="co-title">Employeurs à explorer</h2><p>${nf.format(list.length)} employeur${list.length > 1 ? "s" : ""}${ui.favOnly ? " en favoris" : ""}, du plus au moins compatible avec ce scénario.</p></div>
          <div class="co-tools">
            <label class="sr-only" for="co-sort">Trier les employeurs</label>
            <select class="select" id="co-sort">
              <option value="match" ${ui.sort === "match" ? "selected" : ""}>Trier par adéquation</option>
              <option value="local" ${ui.sort === "local" ? "selected" : ""}>Trier par présence dans vos régions</option>
              <option value="size" ${ui.sort === "size" ? "selected" : ""}>Trier par effectif</option>
            </select>
            <button type="button" class="chip${ui.favOnly ? " is-on" : ""}" data-action="fav-only" aria-pressed="${ui.favOnly}">${icon("star", "ico-s")}<b>Favoris <span data-fav-count>${favorites.length}</span></b></button>
          </div>
        </div>
        ${!ENT.length ? `<p class="empty">La liste des employeurs n'est pas disponible. Lancez <code>python orientation/build_entreprises.py</code>.</p>`
          : shown.length ? `<div class="co-grid">${shown.map(companyCard).join("")}</div>`
          : `<p class="empty">${ui.favOnly ? "Aucun favori pour l'instant : touchez l'étoile d'une carte pour l'ajouter." : "Aucun employeur ne correspond."}</p>`}
        ${list.length > ui.shown ? `<div class="more-row"><button type="button" class="btn btn-ghost" data-action="more">Afficher 12 employeurs de plus</button></div>` : ""}
      </section>
      <p class="fine src">Employeurs : ${esc(window.IESF_ENTREPRISES?.source || "")}, extraction du ${esc(window.IESF_ENTREPRISES?.genere || "")}. Les chiffres affichés sur une carte sont ceux de son secteur dans l'enquête IESF, pas ceux de l'entreprise.</p>`;
    flipLast(box, first);
    const peek = $("#peek");
    if (peek) {
      peek.innerHTML = `<span><small>Salaire visé</small><b>${keur(sal.pred.p50)}</b></span><span><small>Très compatibles</small><b>${nf.format(strong)}</b></span><span class="peek-go">Résultats ↓</span>`;
      peek.classList.remove("bump"); void peek.offsetWidth; peek.classList.add("bump");
    }
  }

  let pending = 0;
  function scheduleRefresh() {
    cancelAnimationFrame(pending);
    pending = requestAnimationFrame(() => {
      const v = document.body.dataset.view;
      if (v === "explore") renderOutcomes();
      if (v === "compare") renderCompare();
    });
  }
  function updateScenario(mutate) {
    mutate(current());
    persist();
    syncCriteria();
    scheduleRefresh();
  }
  function refreshView() {
    const v = document.body.dataset.view;
    if (v === "explore") renderExplore();
    else if (v === "compare") renderCompare();
    else if (v === "results") renderResults();
  }

  // ------------------------------------------------------------------ comparer les scénarios
  function renderCompare() {
    ensureScenarios();
    const P = computeProfile(answers);
    const L = "ABC";
    const cols = scenarios.map((sc) => {
      const ranking = rankSectors(sc.weights, P.group);
      const scored = scoreCompanies(sc, ranking);
      return { sc, ranking, scored, byId: new Map(scored.map((x) => [x.c.id, x.score])), sal: scenarioSalary(sc, ranking), ind: topSectorIndicators(ranking, P.group), top: scored.slice(0, 5) };
    });
    const multi = cols.length > 1;
    const common = multi ? cols[0].top.map((x) => x.c.id).filter((id) => cols.every((col) => col.top.some((y) => y.c.id === id))) : [];
    const maxSal = Math.max(...cols.map((c) => c.sal.pred.p75));
    const chips = (sc) => [
      ...Object.entries(sc.weights).filter(([, w]) => w > 0).sort((a, b) => b[1] - a[1]).map(([k, w]) => `<span class="tag${w === 2 ? " strong" : ""}">${icon(PRIO_ICON[k], "ico-s")}${esc(PRIORITES[k].label)}</span>`),
      ...sc.themes.map((g) => `<span class="tag">${icon(GROUPS[g][2], "ico-s")}${esc(GROUPS[g][0])}</span>`),
      ...(sc.regions.length ? sc.regions.map((r) => `<span class="tag">${icon("pin", "ico-s")}${esc(REGIONS[r])}</span>`) : [`<span class="tag">${icon("pin", "ico-s")}Toute la France</span>`]),
      ...sc.sizes.map((s) => `<span class="tag">${SIZES[s][0]}</span>`),
      sc.role !== "any" ? `<span class="tag">${ROLES[sc.role]}</span>` : "", sc.nature !== "any" ? `<span class="tag">${NATURES[sc.nature]}</span>` : "",
      sc.ess ? '<span class="tag ess">ESS</span>' : "",
    ].join("");
    const INDS = [
      ["equilibre", "Équilibre vie pro / perso", note, 5], ["sens", "Sens du travail", note, 5], ["perspectives", "Perspectives de carrière", note, 5],
      ["teletravail", "Pratiquent le télétravail", (v) => pct(v), 1], ["crainte", "Craignent pour leur emploi", (v) => pct(v), 0.2, true],
    ];
    const best = (key, low) => {
      if (!multi) return -1;
      const vals = cols.map((c) => c.ind[key]);
      const target = low ? Math.min(...vals) : Math.max(...vals);
      return vals.filter((v) => v === target).length === 1 ? vals.indexOf(target) : -1;
    };
    const salBest = multi ? cols.map((c) => c.sal.pred.p50).indexOf(Math.max(...cols.map((c) => c.sal.pred.p50))) : -1;

    const col = (c, i) => `
      <article class="cmp-col${i === active ? " is-active" : ""}">
        <header class="cmp-head"><span class="sc-letter">${L[i]}</span><h2>${esc(c.sc.name)}</h2>
          <button type="button" class="link-btn" data-action="sc-edit" data-i="${i}">Modifier</button></header>
        <div class="cmp-cell cmp-chips">${chips(c.sc)}</div>
        <div class="cmp-cell cmp-sal${i === salBest ? " is-best" : ""}">
          <span class="cmp-l">Salaire visé</span><b>${keur(c.sal.pred.p50)}</b>
          <span class="cmp-range"><span style="left:${(c.sal.pred.p25 / maxSal) * 100}%;width:${((c.sal.pred.p75 - c.sal.pred.p25) / maxSal) * 100}%"></span><i style="left:${(c.sal.pred.p50 / maxSal) * 100}%"></i></span>
          <small>${keur(c.sal.pred.p25)} – ${keur(c.sal.pred.p75)}${c.sal.now ? ` · ${signed(c.sal.pred.p50 / c.sal.now - 1)} par rapport à aujourd'hui` : ""}</small>
        </div>
        <div class="cmp-cell"><span class="cmp-l">Secteurs en tête</span>
          <ol class="cmp-sectors">${c.ranking.rows.slice(0, 3).map((r) => `<li><span>${esc(SECTEURS[r.key][0])}</span><span class="fit"><span style="width:${Math.round(r.norm * 100)}%"></span></span></li>`).join("")}</ol></div>
        <div class="cmp-cell"><span class="cmp-l">Ce que vivent les ingénieurs de ces secteurs</span>
          <dl class="cmp-ind">${INDS.map(([k, l, fmt, max, low]) => `<div class="${best(k, low) === i ? "is-best" : ""}"><dt>${l}</dt><dd>${fmt(c.ind[k])}</dd>
            <span class="ind-bar"><span style="width:${clamp(((c.ind[k] ?? 0) / max) * 100, 0, 100)}%"></span></span></div>`).join("")}</dl></div>
        <div class="cmp-cell"><span class="cmp-l">Employeurs en tête</span>
          <ul class="cmp-cos">${c.top.map((x) => `<li class="${common.includes(x.c.id) ? "is-common" : ""}">
            <span class="mono-tile sm" style="--h:${hueOf(x.c.g)}" aria-hidden="true">${esc(initials(x.c.n))}</span>
            <span class="cmp-co-n">${esc(x.c.n)}${common.includes(x.c.id) ? '<small>Dans tous vos scénarios</small>' : ""}</span><b>${x.score}</b></li>`).join("")}</ul></div>
      </article>`;

    const favRows = favorites.map((id) => ENT_BY_ID.get(id)).filter(Boolean);
    $("#view-compare").innerHTML = `
      <div class="wrap compare">
        ${phaseBar("compare")}
        <header class="ex-head">
          <p class="eyebrow">Comparer vos choix</p>
          <h1 id="compare-title">${multi ? "Vos scénarios côte à côte" : "Créez un deuxième scénario pour comparer"}</h1>
          <p class="lede">${multi ? "Les meilleures valeurs de chaque ligne sont signalées. Modifiez un scénario pour voir la comparaison changer." : "Dupliquez votre scénario, changez quelques critères (une autre région, d'autres priorités) et comparez les résultats ici."}</p>
        </header>
        ${scenarioBar("compare")}
        <div class="cmp-grid" style="--n:${multi ? cols.length : 2}">
          ${cols.map(col).join("")}
          ${!multi ? `<button type="button" class="cmp-ghost" data-action="sc-add"><span>+</span><b>Créer le scénario B</b><small>à partir de « ${esc(cols[0].sc.name)} »</small></button>` : ""}
        </div>
        <section class="fav-cmp" aria-labelledby="fav-title">
          <div class="out-h"><h2 id="fav-title">${icon("star", "ico-s")} Vos employeurs favoris</h2>
            <p>${favRows.length ? "Leur adéquation avec chacun de vos scénarios, et les chiffres de leur secteur." : "Touchez l'étoile d'une carte employeur en phase 2 pour l'ajouter ici."}</p></div>
          ${favRows.length ? `<div class="table-wrap"><table class="data fav-table">
            <thead><tr><th>Employeur</th><th>Domaine</th><th>Taille</th><th>Implantations</th>${cols.map((c, i) => `<th class="n">Scénario ${L[i]}</th>`).join("")}<th class="n">Médiane du secteur</th><th class="n">Équilibre</th><th><span class="sr-only">Retirer</span></th></tr></thead>
            <tbody>${favRows.map((c) => {
              const s = S.secteurs[c.k];
              const regs = Object.entries(c.r).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([k]) => REGIONS[k]).filter(Boolean);
              return `<tr><td><span class="fav-name"><span class="mono-tile sm" style="--h:${hueOf(c.g)}" aria-hidden="true">${esc(initials(c.n))}</span>${esc(c.n)}</span></td>
                <td>${esc(GROUPS[c.g]?.[0] || "")}</td><td>${SIZES[sizeOf(c)][0]}</td><td>${esc(regs.join(", "))}${Object.keys(c.r).length > 3 ? "…" : ""}</td>
                ${cols.map((col) => { const v = col.byId.get(c.id) ?? 0; return `<td class="n"><span class="pill ${v >= 75 ? "hi" : v >= 50 ? "mid" : "lo"}">${v}</span></td>`; }).join("")}
                <td class="n">${keur(s?.salParEtape?.[P.group] ?? s?.salaire)}</td><td class="n">${note(s?.sat.equilibre)}</td>
                <td><button type="button" class="link-btn" data-fav="${c.id}" aria-label="Retirer ${esc(c.n)} des favoris">Retirer</button></td></tr>`;
            }).join("")}</tbody></table></div>` : ""}
        </section>
      </div>`;
  }

  // ------------------------------------------------------------------ graphiques
  function careerChart(el, opts) {
    careerChart.last = [el, opts];
    const { perso, you, youExp, startExp } = opts;
    // Sans animation (ou déjà animé), la courbe est dessinée d'emblée ; sinon motion.js ouvre le masque.
    const drawn = !document.documentElement.classList.contains("anim") || el.dataset.drawn === "1";
    el.classList.add("chart-draw");
    // Dessiné à la largeur réelle du conteneur pour garder un texte lisible sur mobile.
    const W = Math.max(300, Math.round(el.clientWidth || 720)), narrow = W < 520;
    const H = narrow ? 260 : 300, m = { l: 50, r: narrow ? 74 : 92, t: 22, b: 40 };
    const data = S.curve;
    const xMax = 40;
    const yTop = Math.max(...data.map((d) => d.p75), you ?? 0, ...(perso ? data.map((d) => d.p50 * perso) : [0]));
    const yMax = Math.ceil((yTop * 1.05) / 20000) * 20000;
    const sx = (e) => m.l + (e / xMax) * (W - m.l - m.r);
    const sy = (v) => H - m.b - (v / yMax) * (H - m.t - m.b);
    const line = (pts) => pts.map((p, i) => `${i ? "L" : "M"}${sx(p[0]).toFixed(1)},${sy(p[1]).toFixed(1)}`).join("");
    const band = line(data.map((d) => [d.exp, d.p75])) + data.slice().reverse().map((d) => `L${sx(d.exp).toFixed(1)},${sy(d.p25).toFixed(1)}`).join("") + "Z";
    const persoPts = perso ? data.filter((d) => d.exp >= startExp).map((d) => [d.exp, d.p50 * perso]) : [];
    const yTicks = []; for (let v = 0; v <= yMax; v += narrow ? 40000 : 20000) yTicks.push(v);
    const xTicks = narrow ? [0, 10, 20, 30, 40] : [0, 5, 10, 15, 20, 25, 30, 35, 40];
    const last = data[data.length - 1];
    const youY = you != null ? sy(you) : null;
    // Étiquettes directes en bout de courbe, écartées si elles se chevauchent.
    let medLabelY = sy(last.p50), persoLabelY = persoPts.length ? sy(persoPts[persoPts.length - 1][1]) : null;
    if (persoLabelY != null && Math.abs(persoLabelY - medLabelY) < 16) {
      if (persoLabelY < medLabelY) persoLabelY = medLabelY - 16; else persoLabelY = medLabelY + 16;
    }
    el.innerHTML = `
      <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Salaire brut annuel selon les années d'expérience : médiane et zone entre le 1er et le 3e quartile${you != null ? ", avec votre position" : ""}.">
        <g class="grid">${yTicks.map((v) => `<line x1="${m.l}" x2="${W - m.r}" y1="${sy(v)}" y2="${sy(v)}"/>`).join("")}</g>
        <g class="axis">
          ${yTicks.map((v) => `<text x="${m.l - 8}" y="${sy(v) + 4}" text-anchor="end">${v / 1000} k€</text>`).join("")}
          ${xTicks.map((e) => `<text x="${sx(e)}" y="${H - m.b + 18}" text-anchor="middle">${e}</text>`).join("")}
          <text x="${(m.l + W - m.r) / 2}" y="${H - 4}" text-anchor="middle">années depuis le diplôme</text>
        </g>
        <defs><clipPath id="plot-clip"><rect class="plot-reveal" x="0" y="0" height="${H}" width="${drawn ? W : 0}"/></clipPath></defs>
        <g clip-path="url(#plot-clip)">
          <path class="band" d="${band}"/>
          <path class="median" d="${line(data.map((d) => [d.exp, d.p50]))}"/>
          ${persoPts.length > 1 ? `<path class="perso" d="${line(persoPts)}"/>` : ""}
          <text class="label route" x="${sx(last.exp) + 8}" y="${medLabelY + 4}">Médiane</text>
          ${persoPts.length > 1 ? `<text class="label blaze" x="${sx(last.exp) + 8}" y="${persoLabelY + 4}">Votre profil</text>` : ""}
        </g>
        ${you != null ? `<g class="you-mark"><circle class="you-halo" cx="${sx(youExp)}" cy="${youY}" r="7"/><circle class="you-dot" cx="${sx(youExp)}" cy="${youY}" r="7"/>
          <text class="label blaze" x="${sx(youExp)}" y="${youY - 14}" text-anchor="middle">Vous</text></g>` : ""}
        <line class="cross" x1="0" x2="0" y1="${m.t}" y2="${H - m.b}" visibility="hidden"/>
        <rect class="hit" x="${m.l}" y="${m.t}" width="${W - m.l - m.r}" height="${H - m.t - m.b}"/>
      </svg>
      <div class="tooltip" hidden></div>`;
    const svg = $("svg", el), cross = $(".cross", el), tip = $(".tooltip", el), hit = $(".hit", el);
    const move = (ev) => {
      const r = svg.getBoundingClientRect();
      const vx = ((ev.clientX - r.left) / r.width) * W;
      const e = clamp(Math.round(((vx - m.l) / (W - m.l - m.r)) * xMax), 0, last.exp);
      const d = data.find((p) => p.exp === e);
      if (!d) return;
      cross.setAttribute("x1", sx(e)); cross.setAttribute("x2", sx(e)); cross.setAttribute("visibility", "visible");
      tip.hidden = false;
      tip.style.left = (sx(e) / W) * r.width + "px";
      tip.style.top = (sy(d.p75) / H) * r.height + "px";
      tip.innerHTML = `${e} an${e > 1 ? "s" : ""} d'expérience<br>Médiane <b>${keur(d.p50)}</b> · 50 % entre <b>${keur(d.p25)}</b> et <b>${keur(d.p75)}</b>${perso && e >= startExp ? `<br>Votre profil <b>${keur(d.p50 * perso)}</b>` : ""}`;
    };
    hit.addEventListener("pointermove", move);
    hit.addEventListener("pointerleave", () => { tip.hidden = true; cross.setAttribute("visibility", "hidden"); });
  }

  const bars = (rows, { fmt = (v) => pct(v), max } = {}) => {
    const mx = max ?? Math.max(...rows.map((r) => r.v));
    return `<div class="bars">${rows.map((r) => `
      <div class="bar-row${r.you ? " is-you" : ""}" title="${esc(r.l)} : ${esc(fmt(r.v))}">
        <span class="bar-l">${esc(r.l)}</span>
        <span class="bar-t"><span style="width:${clamp((r.v / mx) * 100, 0, 100)}%"></span></span>
        <span class="bar-v">${fmt(r.v)}</span>
      </div>`).join("")}</div>`;
  };

  const kpi = (v, l, you = false) => `<div class="kpi${you ? " is-you" : ""}"><span class="kpi-v">${v}</span><span class="kpi-l">${l}</span></div>`;

  // ------------------------------------------------------------------ bilan
  function renderResults() {
    ensureScenarios();
    const sc = current();
    const P = computeProfile(answers);
    const { stage, st, bucket, b, group } = P;
    const etu = stage === "etudiant";
    const ranking = rankSectors(sc.weights, group);
    // Le bilan combine le profil (phase 1) et le scénario actif (phase 2).
    const themeSectors = [...new Set(sc.themes.map((g) => GROUPS[g][1]))];
    const a = {
      ...answers, projet: sc.projet,
      secteursVises: (themeSectors.length ? themeSectors : ranking.rows.slice(0, 2).map((r) => r.key)).slice(0, 3),
      service: answers.service || sc.service,
      zone: answers.zone || (sc.regions.length ? zoneOf(sc.regions[0]) : null),
    };
    const rech = a.situation === "recherche";
    const pred = etu ? predict({ ...a, secteur: a.secteursVises?.[0] ?? null, manager: "non", codir: "non" }, "e0") : predict(a, bucket);
    const pctile = a.salaire && !etu ? percentileOf(a.salaire, pred, bucket) : null;
    const scored = scoreCompanies(sc, ranking);
    const sections = [];

    // --- En-tête
    const expTxt = etu ? "en formation" : `${P.exp} an${P.exp > 1 ? "s" : ""} d'expérience`;
    const head = `
      <header class="report-head">
        <p class="eyebrow">Votre bilan · scénario « ${esc(sc.name)} » · ${esc(S.meta.source)}</p>
        <h1 id="results-title">${esc(st.label)}${rech ? ", en recherche d'emploi" : ""}</h1>
        <p class="lede">${esc(st.pitch)} Vous êtes comparé${a.genre === "f" ? "e" : ""} aux ingénieurs ${etu ? "diplômés depuis moins de 3 ans" : `ayant ${b.range[0]} à ${Math.min(b.range[1], 45)} ans d'expérience`} (${nf.format(b.n)} répondants).</p>
        <div class="objectives">${st.objectives.map(([t, d]) => `<div class="objective"><b>${t}</b><span>${d}</span></div>`).join("")}</div>
      </header>`;

    // --- Rémunération
    if (etu) {
      const vises = a.secteursVises?.length ? a.secteursVises : [];
      const rows = Object.keys(SECTEURS).map((k) => ({ k, v: predict({ ...a, secteur: k, manager: "non", codir: "non" }, "e0").p50 }))
        .sort((x, y) => y.v - x.v).map((r) => ({ l: SECTEURS[r.k][0], v: r.v, you: vises.includes(r.k) }));
      const main = predict({ ...a, secteur: vises[0] ?? null, manager: "non", codir: "non" }, "e0");
      sections.push(["salaire", "Votre salaire d'embauche", `
        <div class="block-head"><h2>Votre salaire d'embauche</h2>
          <p>Estimation pour un premier poste${vises[0] ? ` en ${esc(SECTEURS[vises[0]][0].toLowerCase())}` : ""}${a.zone ? `, ${esc(ZONES[a.zone].toLowerCase())}` : ""}, d'après les jeunes diplômés de 0 à 2 ans.</p></div>
        <div class="kpis">${kpi(keur(main.p25), "Bas de fourchette (25 % gagnent moins)")}${kpi(keur(main.p50), "Médiane : votre prétention de référence", true)}${kpi(keur(main.p75), "Haut de fourchette (25 % gagnent plus)")}</div>
        <div><p class="subhead">Salaire médian d'embauche estimé selon le secteur</p>
          ${bars(rows, { fmt: keur })}
          <p class="block-note" style="margin-top:10px">En orange, les secteurs que vous avez choisis. Même métier, même région et même type de diplôme pour tous les secteurs.</p></div>`]);
    } else {
      const lo = pred.p10, hi = pred.p90;
      const pos = (v) => clamp(((v - lo) / (hi - lo)) * 100, 0, 100);
      let verdict = "";
      if (pctile != null) {
        const p = Math.round(pctile * 100);
        const cls = p < 35 ? "warn" : p >= 65 ? "good" : "";
        const txt = p < 35
          ? `Votre salaire est dans le bas de la fourchette : environ ${p} % des profils comparables gagnent moins que vous. L'écart avec la médiane est de ${eur(pred.p50 - a.salaire)} par an.`
          : p >= 65 ? `Vous êtes bien placé${a.genre === "f" ? "e" : ""} : environ ${p} % des profils comparables gagnent moins que vous.`
          : `Vous êtes dans la moyenne : environ ${p} % des profils comparables gagnent moins que vous.`;
        verdict = `<div class="verdict ${cls}"><span class="verdict-icon" aria-hidden="true">${cls === "warn" ? "!" : cls === "good" ? "✓" : "i"}</span><p>${txt}</p></div>`;
      }
      const gender = a.genre === "f" && S.model.ecartFHAjuste != null
        ? `<p class="block-note">À profil identique (expérience, secteur, taille, région, fonction, responsabilités), les ingénieures déclarent en moyenne ${pct(-(Math.exp(S.model.ecartFHAjuste) - 1), 1)} de moins que leurs homologues masculins. À votre étape, l'écart entre les médianes brutes est de ${pct(Math.abs(b.ecartFH ?? 0))}. La fourchette ci-dessus ne tient pas compte du genre : c'est celle à laquelle vous pouvez prétendre.</p>` : "";
      sections.push(["salaire", "Votre rémunération", `
        <div class="block-head"><h2>Votre rémunération face à vos pairs</h2>
          <p>Fourchette estimée pour un profil comme le vôtre : même expérience${a.secteur ? ", même secteur" : ""}${a.taille ? ", même taille d'entreprise" : ""}${a.zone ? ", même zone" : ""}${a.service ? ", même fonction" : ""}${a.manager ? ", même niveau de responsabilité" : ""}.</p></div>
        <div class="kpis">${kpi(keur(pred.p25), "1er quartile")}${kpi(keur(pred.p50), "Médiane des profils comparables")}${kpi(keur(pred.p75), "3e quartile")}${a.salaire ? kpi(keur(a.salaire), rech ? "Votre dernier salaire" : "Votre salaire", true) : ""}</div>
        <div class="ruler" aria-hidden="true">
          <div class="ruler-track">
            <div class="ruler-iqr" style="left:${pos(pred.p25)}%;right:${100 - pos(pred.p75)}%"></div>
            <div class="ruler-med" style="left:${pos(pred.p50)}%"></div>
            ${a.salaire ? `<div class="ruler-you" style="left:${pos(a.salaire)}%"><span>Vous · ${keur(a.salaire)}</span><i></i></div>` : ""}
            <span class="ruler-tick" style="left:0%;transform:none;text-align:left"><b>${keur(lo)}</b>10 %</span>
            <span class="ruler-tick" style="left:${pos(pred.p50)}%"><b>${keur(pred.p50)}</b>médiane</span>
            <span class="ruler-tick" style="left:100%;transform:translateX(-100%);text-align:right"><b>${keur(hi)}</b>90 %</span>
          </div>
        </div>
        ${verdict || `<p class="block-note">Renseignez votre salaire pour voir où vous vous situez dans cette fourchette.</p>`}
        ${gender}`]);
    }

    // --- Trajectoire
    const ratio = etu ? predict({ ...a, secteur: a.secteursVises?.[0] ?? null, manager: "non", codir: "non" }, "e0").p50 / S.buckets.e0.salQ[9] : pred.p50 / b.salQ[9];
    const at = (e) => S.curve.find((c) => c.exp === clamp(e, 0, S.curve[S.curve.length - 1].exp))?.p50;
    const proj = [5, 10].map((d) => ({ d, v: at(P.exp + d) * ratio })).filter((p) => P.exp + p.d <= 40);
    sections.push(["trajectoire", "Votre trajectoire", `
      <div class="block-head"><h2>Votre trajectoire salariale</h2>
        <p>Salaire brut annuel des ingénieurs selon l'expérience. La ligne pointillée prolonge la courbe pour un profil comme le vôtre, si les autres paramètres ne changent pas.</p></div>
      <div class="legend"><span><i class="l-band"></i>50 % des ingénieurs</span><span><i class="l-med"></i>Médiane</span><span><i class="l-perso"></i>Votre profil</span>${!etu ? `<span><i class="l-you"></i>Vous aujourd'hui</span>` : ""}</div>
      <div class="chart" id="career-chart"></div>
      ${proj.length ? `<div class="kpis">${proj.map((p) => kpi(keur(p.v), `Médiane attendue dans ${p.d} ans (${P.exp + p.d} ans d'expérience)`)).join("")}${kpi(signed(at(P.exp + 10) / at(P.exp) - 1), "Progression médiane sur 10 ans à votre étape")}</div>` : ""}
      <p class="block-note">Courbe tracée à partir des ${nf.format(S.meta.avecSalaire)} répondants ayant déclaré leur rémunération. Ce sont des générations différentes à un même moment, pas le suivi d'une même personne.</p>`]);

    // --- Leviers
    if (etu) {
      const lv = [];
      if (a.zone !== "idf") lv.push({ t: "Commencer en Île-de-France", d: "Salaires plus élevés, mais un coût du logement nettement supérieur.", v: Math.exp(coef("zone", "idf") - (coef("zone", a.zone) ?? 0)) - 1 });
      lv.push({ t: "Viser un grand groupe plutôt qu'une PME", d: "À secteur et métier égaux.", v: Math.exp(-coef("taille", "pme")) - 1 });
      lv.push({ t: "Viser un grand groupe plutôt qu'une TPE ou une start-up", d: "Les petites structures compensent parfois par l'autonomie et l'equity.", v: Math.exp(-coef("taille", "tpe")) - 1 });
      if (a.zone !== "etranger") lv.push({ t: "Démarrer à l'étranger", d: "Avant coût de la vie et fiscalité locale, qui varient beaucoup d'un pays à l'autre.", v: Math.exp(coef("zone", "etranger") - (coef("zone", a.zone) ?? 0)) - 1 });
      sections.push(["leviers", "Ce qui fait varier", leversBlock("Ce qui fait varier votre salaire d'embauche", "Écart de salaire à profil égal par ailleurs, estimé par le modèle.", lv)]);
    } else {
      sections.push(["leviers", "Vos leviers", leversBlock("Vos leviers de progression", "Gain de salaire associé à chaque changement, à profil égal par ailleurs. Ce sont des écarts observés, pas des garanties.", careerLevers(a), mobilityHtml(b))]);
    }

    // --- Management vs expertise
    if (["confirme", "experimente"].includes(stage) || ["manager", "expert"].includes(a.projet)) {
      const R = b.roles;
      const cur = a.manager === "oui" ? "manager" : null;
      const role = (k, t, d) => `<div class="role${cur === k || a.projet === k ? " is-you" : ""}"><h3>${t}</h3><p class="fine">${d}</p><dl>
        <div><dt>Salaire médian</dt><dd>${keur(R[k].salaire)}</dd></div>
        <div><dt>Satisfaction globale</dt><dd>${note(R[k].satGlobale)}</dd></div>
        <div><dt>Intérêt du travail</dt><dd>${note(R[k].interet)}</dd></div>
        <div><dt>Équilibre de vie</dt><dd>${note(R[k].equilibre)}</dd></div>
        <div><dt>Stress (satisfaction)</dt><dd>${note(R[k].stress)}</dd></div></dl></div>`;
      sections.push(["voie", "Management ou expertise", `
        <div class="block-head"><h2>Management ou expertise ?</h2>
          <p>Ce que vivent les ingénieurs de votre tranche d'expérience selon leur rôle. Les notes de satisfaction vont de 1 à 5 ; plus elles sont hautes, mieux c'est vécu.</p></div>
        <div class="roles">${role("manager", "Manager", "Encadre une équipe, n'est pas expert technique.")}${role("expert", "Expert", "Expertise reconnue, sans équipe à encadrer.")}${role("hybride", "Les deux", "Manager et expert technique à la fois.")}</div>`]);
    }

    // --- Secteurs
    const cur = etu ? a.secteursVises || [] : a.secteur ? [a.secteur] : [];
    const showMetrics = [...new Set(ranking.prios.map((p) => PRIORITES[p].m[0]))];
    sections.push(["secteurs", "Secteurs à explorer", `
      <div class="block-head"><h2>Les secteurs qui correspondent à vos priorités</h2>
        <p>Classement selon ${ranking.prios.map((p) => `« ${PRIORITES[p].label.toLowerCase()} »`).join(", ")}${ranking.isDefault ? " (priorités par défaut)" : ""}. Salaires à votre étape de carrière, satisfaction notée sur 5 par les ingénieurs du secteur.</p></div>
      <div class="table-wrap"><table class="data">
        <thead><tr><th>#</th><th>Secteur</th><th>Adéquation</th>${showMetrics.map((mk) => `<th class="n">${esc(metric(mk).label)}</th>`).join("")}</tr></thead>
        <tbody>${ranking.rows.map((r, i) => `<tr class="${cur.includes(r.key) ? "is-you" : ""}">
          <td class="rank">${i + 1}</td><td>${esc(SECTEURS[r.key][0])}${cur.includes(r.key) ? ` <span class="tag you">${etu ? "votre choix" : "votre secteur"}</span>` : ""}</td>
          <td><span class="score"><span style="width:${(r.norm * 100).toFixed(0)}%"></span></span></td>
          ${showMetrics.map((mk) => { const M = metric(mk); const v = M.get(S.secteurs[r.key], group); return `<td class="n">${v == null ? "—" : M.fmt(v)}</td>`; }).join("")}
        </tr>`).join("")}</tbody></table></div>`]);

    // --- Employeurs
    if (ENT.length) {
      const favs = favorites.map((id) => scored.find((x) => x.c.id === id)).filter(Boolean);
      const top = scored.filter((x) => !favorites.includes(x.c.id)).slice(0, Math.max(3, 6 - favs.length));
      sections.push(["employeurs", "Employeurs à explorer", `
        <div class="block-head"><h2>Employeurs à explorer</h2>
          <p>${favs.length ? "Vos favoris, puis les employeurs les plus compatibles" : "Les employeurs les plus compatibles"} avec le scénario « ${esc(sc.name)} ». Données SIRENE ; les chiffres sont ceux du secteur dans l'enquête IESF.</p></div>
        <div class="co-grid co-grid-report">${[...favs, ...top].map(companyCard).join("")}</div>`]);
    }

    // --- Ressenti
    const rated = a.ressenti && Object.keys(a.ressenti).length;
    if (rated) {
      const rows = RESSENTI.filter((d) => a.ressenti[d] && b.sat[d] != null).map((d) => ({ d, me: a.ressenti[d], peer: b.sat[d], gap: a.ressenti[d] - b.sat[d] }));
      const x = (v) => ((v - 1) / 4) * 100;
      sections.push(["ressenti", "Votre ressenti", `
        <div class="block-head"><h2>Votre ressenti comparé à vos pairs</h2>
          <p>Vos notes face à la moyenne des ingénieurs de votre tranche d'expérience. Les écarts négatifs importants sont repris dans votre plan d'action.</p></div>
        <div class="legend"><span><i class="l-you"></i>Vous</span><span><i class="l-you" style="background:var(--route)"></i>Moyenne de vos pairs</span></div>
        <div class="dots">
          <div class="dots-head"><span></span><span class="scale-ticks"><span>1</span><span>2</span><span>3</span><span>4</span><span>5</span></span><span style="text-align:right">écart</span></div>
          ${rows.map((r) => `<div class="dot-row" title="${esc(SAT[r.d])} : vous ${r.me}/5, pairs ${note(r.peer)}">
            <span>${SAT[r.d]}</span>
            <span class="dot-track"><span class="dot-gap" style="left:${Math.min(x(r.me), x(r.peer))}%;width:${Math.abs(x(r.me) - x(r.peer))}%"></span>
              <span class="dot peer" style="left:${x(r.peer)}%"></span><span class="dot me" style="left:${x(r.me)}%"></span></span>
            <span class="dot-delta ${r.gap <= -0.5 ? "neg" : r.gap >= 0.5 ? "pos" : ""}">${(r.gap > 0 ? "+" : r.gap < 0 ? "−" : "") + Math.abs(r.gap).toFixed(1).replace(".", ",")}</span>
          </div>`).join("")}
        </div>`]);
    } else {
      const dims = Object.entries(b.sat).filter(([, v]) => v != null).sort((x, y) => x[1] - y[1]);
      const low = dims.slice(0, 5), high = dims.slice(-4).reverse();
      sections.push(["ressenti", "Le vécu à cette étape", `
        <div class="block-head"><h2>${etu ? "Ce qu'en disent les jeunes diplômés" : "Le vécu des ingénieurs à votre étape"}</h2>
          <p>Satisfaction moyenne notée de 1 à 5 par les ingénieurs ${etu ? "diplômés depuis moins de 3 ans" : "de votre tranche d'expérience"}.</p></div>
        <div class="cols-2">
          <div><p class="subhead">Points les mieux notés</p>${bars(high.map(([k, v]) => ({ l: SAT[k], v })), { fmt: note, max: 5 })}</div>
          <div><p class="subhead">Points de vigilance</p>${bars(low.map(([k, v]) => ({ l: SAT[k], v })), { fmt: note, max: 5 })}</div>
        </div>`]);
    }

    // --- Marché
    const canal = rech ? (S.retour.parEtape[group] || S.retour.canal) : b.canal;
    const canalRows = Object.entries(canal || {}).filter(([k]) => k !== "autre").slice(0, 7).map(([k, v]) => ({ l: CANAUX[k] || k, v }));
    const secIa = !etu && a.secteur ? S.secteurs[a.secteur]?.ia : null;
    sections.push(["marche", rech ? "Retrouver un emploi" : "Le marché à votre étape", `
      <div class="block-head"><h2>${rech ? "Comment les ingénieurs retrouvent un emploi" : etu ? "Comment les jeunes diplômés trouvent leur poste" : "Le marché de l'emploi à votre étape"}</h2>
        <p>${rech ? `Canal principal utilisé par ${nf.format(S.retour.n)} ingénieurs passés du chômage à l'emploi${S.retour.parEtape[group] ? " à une étape de carrière comparable" : ""}.` : "Comment vos pairs ont eu connaissance de leur emploi actuel, et leur rapport à la mobilité."}</p></div>
      <div class="kpis">
        ${rech ? kpi(pct(S.retour.mobiliteReussie), "sont satisfaits du poste retrouvé") : kpi(pct(b.mobilite), "ont changé de poste ou d'employeur en 5 ans")}
        ${kpi(pct(b.intention), "envisagent de changer d'employeur")}
        ${kpi(pct(b.crainte), "craignent de perdre leur emploi dans l'année")}
        ${kpi(pct(b.ia), "utilisent l'IA dans leur travail")}
        ${secIa != null ? kpi(pct(secIa), `utilisent l'IA dans votre secteur`) : ""}
      </div>
      <div><p class="subhead">${rech ? "Canal qui a permis de retrouver un emploi" : "Comment ils ont trouvé leur poste actuel"}</p>${bars(canalRows)}</div>`]);

    // --- Plan d'action
    const plan = buildPlan(a, P, pred, pctile, ranking);
    if (ENT.length && scored[0]) {
      const names = scored.slice(0, 3).map((x) => x.c.n);
      plan.splice(Math.min(2, plan.length), 0, { when: "Ce mois-ci", t: "Prenez contact avec trois employeurs ciblés",
        d: `D'après vos critères : ${names.map(esc).join(", ")}. Repérez un ingénieur de chacun sur LinkedIn ou via votre réseau d'anciens et demandez-lui 20 minutes d'échange sur son quotidien.` });
      plan.length = Math.min(plan.length, 7);
    }
    sections.push(["plan", "Votre plan d'action", `
      <div class="block-head"><h2>Votre plan d'action</h2><p>Classé par ordre de priorité, à partir de vos réponses et des données de vos pairs.</p></div>
      <ol class="plan">${plan.map((p) => `<li><div><span class="when">${esc(p.when)}</span><h3>${esc(p.t)}</h3><p>${p.d}</p></div></li>`).join("")}</ol>`]);

    // --- Sommaire latéral
    const facts = [
      ["Étape", `${st.label} · ${expTxt}`],
      ["Âge", a.age ? `${a.age} ans` : null],
      ["Formation", a.diplome ? DIPLOMES[a.diplome][0] : null],
      [etu ? "Pistes" : "Secteur", etu ? (a.secteursVises || []).map((k) => SECTEURS[k][0]).join(", ") || null : a.secteur ? SECTEURS[a.secteur][0] : null],
      ["Fonction", a.service ? SERVICES[a.service] : null],
      ["Zone", a.zone ? ZONES[a.zone] : null],
      ["Projet", a.projet && st.projets[a.projet] ? st.projets[a.projet] : null],
    ].filter(([, v]) => v);
    $("#results-phase").innerHTML = phaseBar("results");
    $("#results").innerHTML = `
      <aside class="summary" aria-label="Résumé de votre profil">
        <div class="summary-card">
          <span class="stage-chip">${esc(st.label)}</span>
          ${isExample ? `<p class="example-flag">Exemple fictif : une ingénieure R&D de 34 ans. Faites votre propre parcours pour obtenir votre bilan.</p>` : ""}
          <dl class="facts">${facts.map(([k, v]) => `<div><dt>${k}</dt><dd>${esc(v)}</dd></div>`).join("")}<div><dt>Scénario</dt><dd>${esc(sc.name)}</dd></div></dl>
          <div class="summary-actions">
            ${isExample ? `<button class="btn btn-primary" type="button" data-action="restart">Faire mon parcours</button>` : `<button class="btn btn-primary" type="button" data-goto="explore">Ajuster mes critères</button>`}
            ${isExample ? "" : `<button class="btn btn-ghost" type="button" data-goto="wizard">Modifier mon profil</button>`}
            <button class="btn btn-ghost" type="button" data-action="copy">Copier la synthèse</button>
            ${isExample ? "" : `<button class="btn btn-ghost" type="button" data-action="restart">Recommencer à zéro</button>`}
          </div>
        </div>
        <nav class="toc" aria-label="Sections du bilan">${sections.map(([id, t]) => `<a href="#s-${id}" data-scroll="s-${id}">${t}</a>`).join("")}</nav>
      </aside>
      <div class="report">${head}${sections.map(([id, , html]) => `<section class="block" id="s-${id}">${html}</section>`).join("")}
        <p class="block-note">Estimations indicatives fondées sur les réponses déclaratives et pondérées de l'enquête IESF 2025 (situation au 31/12/2024). <a href="#methode" data-nav="method">Méthode et limites</a>.</p>
      </div>`;

    careerChart($("#career-chart"), {
      perso: ratio, startExp: P.exp,
      you: etu ? null : a.salaire || pred.p50, youExp: P.exp,
    });
    renderResults.summaryText = summaryText(a, P, pred, pctile, ranking, plan, scored, sc);
    renderHome();
  }

  function leversBlock(title, sub, levers, extra = "") {
    const list = levers.filter((l) => l.v > 0.02).sort((x, y) => y.v - x.v).slice(0, 6);
    const max = Math.max(...list.map((l) => l.v), 0.01);
    return `<div class="block-head"><h2>${title}</h2><p>${sub}</p></div>
      ${list.length ? `<div class="levers">${list.map((l) => `<div class="lever"><b>${esc(l.t)}</b><span class="delta">${signed(l.v)}</span>
        <span class="lever-track" aria-hidden="true"><span style="width:${(l.v / max) * 100}%"></span></span><small>${esc(l.d)}</small></div>`).join("")}</div>`
        : `<p>Votre profil cumule déjà la plupart des leviers de rémunération mesurés : la progression passera surtout par l'expérience et le périmètre de vos responsabilités.</p>`}
      ${extra}`;
  }

  function careerLevers(a) {
    const P = computeProfile(a);
    const L = [];
    const delta = (f, to, from) => Math.exp((coef(f, to) ?? 0) - (from == null ? S.model.moyenne[f] : coef(f, from) ?? 0)) - 1;
    if (a.manager !== "oui" && P.stage !== "senior") L.push({ t: "Encadrer une équipe", d: "Prendre des responsabilités hiérarchiques, à poste et entreprise comparables.", v: delta("manager", "oui", a.manager === "non" ? "Non" : null) });
    if (a.codir !== "oui" && P.stage !== "debut") L.push({ t: "Entrer dans un comité de direction", d: "Codir, Comex ou conseil d'administration.", v: delta("codir", "oui", a.codir === "non" ? "Non" : null) });
    if (a.situation !== "independant" && a.taille && a.taille !== "ge") L.push({ t: "Rejoindre un grand groupe", d: `Par rapport à votre ${TAILLES[a.taille][0]} actuelle.`, v: delta("taille", "ge", a.taille) });
    if (a.zone === "province") L.push({ t: "Travailler en Île-de-France", d: "À comparer au coût du logement, nettement plus élevé.", v: delta("zone", "idf", "province") });
    if (a.zone && a.zone !== "etranger") L.push({ t: "Partir à l'étranger", d: "Avant coût de la vie et fiscalité locale.", v: delta("zone", "etranger", a.zone) });
    const sect = Object.keys(SECTEURS).filter((k) => k !== a.secteur).map((k) => ({ k, v: delta("secteur", k, a.secteur || null) })).sort((x, y) => y.v - x.v).slice(0, 2);
    sect.forEach((s) => L.push({ t: `Changer pour : ${SECTEURS[s.k][0].toLowerCase()}`, d: a.secteur ? `Par rapport à ${SECTEURS[a.secteur][0].toLowerCase()}, à fonction égale.` : "Par rapport à la moyenne des secteurs.", v: s.v }));
    const serv = Object.keys(SERVICES).filter((k) => k !== a.service && k !== "autre" && k !== "direction").map((k) => ({ k, v: delta("service", k, a.service || null) })).sort((x, y) => y.v - x.v).slice(0, 2);
    serv.forEach((s) => L.push({ t: `Évoluer vers : ${SERVICES[s.k].toLowerCase()}`, d: "Changement de fonction, dans le même secteur.", v: s.v }));
    return L;
  }

  function mobilityHtml(b) {
    const m = b.salParChangement;
    if (!m?.aucun) return "";
    const rows = [["Pas de changement en 5 ans", m.aucun], ["Promotion interne", m.promotion], ["Changement d'employeur", m.employeur]].filter(([, v]) => v);
    return `<div><p class="subhead">Salaire médian à votre étape selon la dernière mobilité</p>
      ${bars(rows.map(([l, v]) => ({ l, v })), { fmt: keur })}
      <p class="block-note" style="margin-top:10px">Chez les ingénieurs, la promotion interne s'accompagne en général d'un salaire plus élevé que le changement d'employeur. Changer d'entreprise sert plutôt à gagner en intérêt ou en perspectives.</p></div>`;
  }

  // ------------------------------------------------------------------ plan d'action
  function buildPlan(a, P, pred, pctile, ranking) {
    const { stage, b, group } = P;
    const out = [];
    const add = (when, t, d) => out.push({ when, t, d });
    const top = ranking.rows.slice(0, 2).map((r) => SECTEURS[r.key][0].toLowerCase());
    const B = S.buckets;
    const rech = a.situation === "recherche";

    if (rech) {
      const c = Object.entries(S.retour.parEtape[group] || S.retour.canal).filter(([k]) => k !== "autre").slice(0, 3);
      add("Cette semaine", "Concentrez vos candidatures sur les canaux qui marchent",
        `Pour les ingénieurs qui ont retrouvé un emploi à votre étape, les trois premiers canaux sont : ${c.map(([k, v]) => `${CANAUX[k].toLowerCase()} (${pct(v)})`).join(", ")}. Mettez votre profil LinkedIn à jour et prévenez votre réseau.`);
      add("Ce mois-ci", "Faites-vous accompagner",
        "L'APEC propose un accompagnement gratuit aux cadres en recherche d'emploi. Les associations d'anciens élèves et les associations régionales d'ingénieurs (membres d'IESF) organisent aussi des groupes de retour à l'emploi.");
      const safe = Object.keys(SECTEURS).filter((k) => S.secteurs[k].crainte != null && k !== a.secteur).sort((x, y) => S.secteurs[x].crainte - S.secteurs[y].crainte).slice(0, 2);
      add("Dans les 3 mois", "Élargissez à des secteurs voisins",
        `Les secteurs où les ingénieurs craignent le moins pour leur emploi : ${safe.map((k) => `${SECTEURS[k][0].toLowerCase()} (${pct(S.secteurs[k].crainte)} seulement)`).join(" et ")}. Vos compétences s'y transposent souvent plus facilement qu'on ne le croit.`);
    }

    if (stage === "etudiant") {
      add("Ce semestre", "Visez un stage dans un secteur qui vous correspond",
        `${pct(B.e0.canal?.stage)} des diplômés de 0 à 2 ans ont obtenu leur poste à l'issue d'un stage : c'est le premier canal d'embauche. Au vu de vos priorités, regardez en priorité ${top.join(" et ")}.`);
      const e = predict({ ...a, secteur: a.secteursVises?.[0] ?? null, manager: "non", codir: "non" }, "e0");
      const projetTxt = {
        cdi: ["Avant vos entretiens", "Préparez votre prétention salariale", `Pour votre profil, la fourchette d'embauche va de ${keur(e.p25)} à ${keur(e.p75)} brut annuel, médiane ${keur(e.p50)}. Annoncez un chiffre proche de la médiane et justifiez-le par vos stages et projets.`],
        international: ["Cette année", "Regardez le VIE et les premiers postes à l'étranger", `À profil égal, les ingénieurs travaillant à l'étranger déclarent ${signed(Math.exp(coef("zone", "etranger")) - 1)} par rapport à la province, avant coût de la vie. Le VIE (Business France) est la porte d'entrée la plus courante.`],
        these: ["Avant de choisir", "Choisissez une thèse pour le projet, pas pour le salaire", `À profil égal, les ingénieurs-docteurs déclarent une rémunération proche de celle des ingénieurs (${signed(Math.exp(coef("diplome", "ing_docteur")) - 1, 1)}). La thèse se justifie pour la R&D et la recherche. Une thèse CIFRE garde un pied dans l'industrie.`],
        creer: ["Cette année", "Testez votre projet dans l'incubateur de votre école", "Profitez du statut étudiant-entrepreneur (PEPITE) pour tester votre idée sans risque. Un premier poste de quelques années peut aussi financer le projet et construire votre réseau."],
        indecis: ["Cette année", "Multipliez les expériences courtes", "Un stage dans un secteur, un projet ou une alternance dans un autre : comparez les métiers de l'intérieur avant de choisir. Le classement des secteurs ci-dessus vous donne un point de départ."],
      }[a.projet || "indecis"];
      add(...projetTxt);
      add("Dès maintenant", "Construisez votre réseau",
        `Les relations professionnelles pèsent de plus en plus avec l'expérience : ${pct(B.e0.canal?.relations)} des postes chez les jeunes diplômés, ${pct(B.e21.canal?.relations)} après 20 ans de carrière. Réseau des anciens, forums, associations d'ingénieurs : commencez tôt.`);
      add("Pendant vos études", "Formez-vous aux outils d'IA",
        `${pct(B.e0.ia)} des jeunes diplômés utilisent déjà l'IA dans leur travail. Savoir l'utiliser pour analyser des données, prototyper ou documenter fait partie des attentes des recruteurs.`);
      return out.slice(0, 6);
    }

    // Salaire
    if (pctile != null && pctile < 0.35 && !rech) {
      add("Avant votre prochain entretien annuel", "Préparez une demande d'augmentation argumentée",
        `La médiane des profils comparables au vôtre est de ${eur(pred.p50)}, soit ${eur(pred.p50 - a.salaire)} de plus que votre salaire. Présentez vos résultats chiffrés et cette référence de marché.`);
    } else if (pctile != null && pctile >= 0.65 && !rech) {
      add("Cette année", "Sécurisez votre avance par les compétences",
        "Votre salaire est au-dessus de celui de vos pairs. La suite se joue sur votre périmètre : responsabilités, projets visibles et expertise rare.");
    }
    if (a.genre === "f" && !rech) {
      add("À chaque négociation", "Appuyez-vous sur des références chiffrées",
        `À profil identique, l'écart de salaire observé entre ingénieures et ingénieurs est de ${pct(-(Math.exp(S.model.ecartFHAjuste) - 1), 1)}. La fourchette de ce bilan, qui ne dépend pas du genre, est une base solide pour négocier.`);
    }

    // Projet
    const m = b.salParChangement;
    const roles = b.roles;
    const projet = {
      progresser: ["Dans les 12 mois", "Préparez une promotion interne", `À votre étape, les ingénieurs promus en interne ont un salaire médian de ${keur(m.promotion)}, contre ${keur(m.aucun)} sans changement. Demandez un entretien de carrière et fixez des objectifs concrets.`],
      changer: ["Dans les 6 mois", "Préparez votre changement d'employeur", `${pct(b.intention)} de vos pairs y pensent aussi. Les canaux les plus efficaces à votre étape : ${Object.entries(b.canal).filter(([k]) => k !== "autre").slice(0, 3).map(([k]) => CANAUX[k].toLowerCase()).join(", ")}. Négociez à partir de la médiane de ce bilan.`],
      secteur: ["Dans les 6 mois", "Préparez un changement de secteur", `Au vu de vos priorités, ${top.join(" et ")} ressortent en tête. Identifiez les compétences transposables et parlez à des ingénieurs de ces secteurs.`],
      international: ["Dans l'année", "Préparez une expérience à l'étranger", `À profil égal, les ingénieurs à l'étranger déclarent ${signed(Math.exp(coef("zone", "etranger") - (coef("zone", a.zone) ?? S.model.moyenne.zone)) - 1)} de rémunération, avant coût de la vie. Commencez par la mobilité interne de votre groupe si elle existe.`],
      these: ["Dans l'année", "Évaluez l'intérêt d'une thèse ou d'un diplôme complémentaire", "Une thèse CIFRE ou un mastère spécialisé se justifie par un projet précis (R&D, recherche, changement de domaine). Vérifiez qu'il est finançable par votre employeur ou via votre CPF."],
      manager: ["Dans les 12 mois", "Préparez votre passage au management", `À votre étape, les managers ont un salaire médian de ${keur(roles.manager.salaire)}, contre ${keur(roles.expert.salaire)} pour les experts. Encadrez d'abord un stagiaire ou une équipe projet, et demandez une formation au management.`],
      expert: ["Dans les 12 mois", "Faites reconnaître votre expertise", `Les experts de votre tranche notent l'intérêt de leur travail ${note(roles.expert.interet)} et leur équilibre de vie ${note(roles.expert.equilibre)}. Publiez, formez vos collègues, visez une filière expert si votre entreprise en a une.`],
      reconversion: ["Dans les 6 mois", "Testez votre reconversion avant de sauter", "Faites un bilan de compétences (finançable par le CPF), rencontrez des personnes du métier visé, puis testez-le par une mission ou un projet associatif."],
      creer: ["Dans l'année", "Préparez la création ou la reprise", "Réseaux d'accompagnement (Réseau Entreprendre, BPI, incubateurs d'écoles) et maintien partiel des droits au chômage après rupture conventionnelle : sécurisez la transition."],
      direction: ["Dans les 2 ans", "Visez un comité de direction", `À profil égal, siéger dans un codir est associé à ${signed(Math.exp(coef("codir", "oui")) - 1)} de rémunération. Prenez la responsabilité d'un résultat financier ou d'un projet transverse visible.`],
      independant: ["Dans l'année", "Préparez votre activité de conseil", "Constituez vos trois premières références clients avant de partir, et comparez portage salarial et création de société."],
      equilibre: ["Cette année", "Réorganisez votre temps de travail", `${pct(S.secteurs[a.secteur]?.teletravail ?? b.teletravail)} des ingénieurs ${a.secteur ? "de votre secteur" : "de votre étape"} concernés pratiquent le télétravail. Le temps partiel, le forfait jours ou une mutation interne sont aussi des pistes.`],
      poursuivre: ["Cette année", "Gardez votre expertise à jour", "Formation continue, veille, communautés professionnelles : restez la référence sur votre domaine."],
      transmettre: ["Cette année", "Organisez la transmission de votre savoir", "Tutorat, mentorat de jeunes ingénieurs, documentation : proposez un rôle formalisé à votre employeur. Les associations d'ingénieurs cherchent aussi des mentors."],
      retraite: ["Dans les 2 ans", "Préparez une retraite progressive", "Faites le point sur vos droits (info-retraite.fr), étudiez la retraite progressive et le cumul emploi-retraite, qui permettent de continuer une activité de conseil ou d'enseignement."],
      engagement: ["Dans l'année", "Mettez votre expérience au service des autres", "Enseignement, jurys, associations d'ingénieurs, promotion des sciences auprès des jeunes : votre expérience est recherchée."],
    }[a.projet];
    if (projet) add(...projet);

    // Ressenti
    const lows = Object.entries(a.ressenti || {}).filter(([d, v]) => b.sat[d] != null && v - b.sat[d] <= -0.7).sort((x, y) => (x[1] - b.sat[x[0]]) - (y[1] - b.sat[y[0]]));
    const dimAction = {
      interet: ["Retrouvez de l'intérêt dans vos missions", "Proposez de prendre en charge un projet transverse ou nouveau. Si le contenu du poste ne peut pas évoluer, c'est un signal fort pour envisager une mobilité."],
      sens: ["Réalignez votre travail sur vos valeurs", `Les secteurs où les ingénieurs trouvent le plus de sens : ${Object.keys(SECTEURS).filter((k) => S.secteurs[k].sat.sens != null).sort((x, y) => S.secteurs[y].sat.sens - S.secteurs[x].sat.sens).slice(0, 2).map((k) => SECTEURS[k][0].toLowerCase()).join(" et ")}.`],
      remuneration: ["Remettez votre rémunération sur la table", `Vos pairs notent leur rémunération ${note(b.sat.remuneration)} en moyenne. Comparez votre salaire à la fourchette de ce bilan et regardez aussi le variable, l'intéressement et les avantages.`],
      perspectives: ["Clarifiez vos perspectives", "Demandez un entretien de carrière avec votre manager ou les RH : quel poste dans 2 à 3 ans, avec quelles étapes ? Sans réponse claire, la mobilité externe devient une option."],
      reco_hierarchie: ["Rendez votre travail plus visible", "Faites un point régulier avec votre manager sur vos résultats chiffrés et présentez vos réussites en réunion d'équipe."],
      equilibre: ["Protégez votre équilibre de vie", `Négociez des jours de télétravail (${pct(b.teletravail)} de vos pairs concernés le pratiquent) et fixez des limites claires sur les horaires.`],
      stress: ["Réduisez la pression", "Identifiez les sources de stress (charge, urgences, relations), parlez-en à votre manager et, si besoin, à la médecine du travail. Un stress durable est un motif légitime de mobilité."],
    };
    lows.slice(0, 2).forEach(([d]) => add("Ce trimestre", ...dimAction[d]));

    // Étape
    const byStage = {
      debut: [["Cette année", "Préparez votre première mobilité", `${pct(b.mobilite)} des ingénieurs de votre tranche ont déjà changé de poste ou d'employeur. Au bout de 2 à 3 ans, faites le point : promotion interne (${keur(m.promotion)} de médiane) ou nouvel employeur.`]],
      confirme: [["Dans les 2 ans", "Choisissez votre voie", `${pct(b.manager)} des ingénieurs de votre tranche encadrent une équipe et ${pct(b.expert)} sont reconnus comme experts. Les deux voies se valent en satisfaction : choisissez selon ce qui vous motive.`]],
      experimente: [["Cette année", "Restez employable", `${pct(b.ia)} de vos pairs utilisent déjà l'IA. Une formation courte, une certification ou un rôle de référent sur un sujet émergent entretiennent votre valeur sur le marché.`]],
      senior: [["Cette année", "Valorisez votre expérience", `Seuls ${pct(b.intention)} des ingénieurs de plus de 30 ans d'expérience envisagent de changer d'employeur. Pour vous, l'enjeu est moins de bouger que de faire reconnaître votre expertise : mentorat, rôle de référent, conseil.`]],
    }[stage] || [];
    byStage.forEach((x) => add(...x));

    if (a.ia !== "oui" && stage !== "senior") add("Dans les 6 mois", "Formez-vous aux outils d'IA", `${pct(b.ia)} des ingénieurs de votre tranche utilisent l'IA dans leur travail. Commencez par vos tâches répétitives : synthèse, code, analyse de données.`);
    add("En continu", "Entretenez votre réseau", `Les relations professionnelles sont le premier canal d'accès à l'emploi à votre étape (${pct(b.canal?.relations)} des postes). Gardez le contact avec vos anciens collègues et votre association d'anciens élèves.`);

    const seen = new Set();
    return out.filter((p) => !seen.has(p.t) && seen.add(p.t)).slice(0, 7);
  }

  function summaryText(a, P, pred, pctile, ranking, plan, scored, sc) {
    const lines = [
      `Mon bilan Boussole IESF : ${P.st.label}${P.stage === "etudiant" ? "" : `, ${P.exp} ans d'expérience`} (scénario « ${sc.name} »)`,
      P.stage === "etudiant"
        ? `Salaire d'embauche estimé : ${keur(pred.p25)} à ${keur(pred.p75)} (médiane ${keur(pred.p50)})`
        : `Fourchette pour mon profil : ${keur(pred.p25)} à ${keur(pred.p75)} (médiane ${keur(pred.p50)})${pctile != null ? `, je me situe vers le ${Math.round(pctile * 100)}e centile` : ""}`,
      `Secteurs en tête pour mes priorités : ${ranking.rows.slice(0, 3).map((r) => SECTEURS[r.key][0]).join(", ")}`,
      ...(scored.length ? [`Employeurs à explorer : ${scored.slice(0, 5).map((x) => `${x.c.n} (${x.score} %)`).join(", ")}`] : []),
      "Plan d'action :",
      ...plan.map((p, i) => `${i + 1}. ${p.t} (${p.when.toLowerCase()})`),
      `Source : ${S.meta.source}.`,
    ];
    return lines.join("\n");
  }

  // ------------------------------------------------------------------ méthode
  function renderMethod() {
    const m = S.model;
    $("#method-body").innerHTML = `
      <p>La Boussole s'appuie sur l'enquête annuelle d'Ingénieurs et Scientifiques de France. ${nf.format(S.meta.repondants)} réponses pondérées décrivent la situation au 31 décembre 2024, dont ${nf.format(S.meta.actifs)} ingénieurs en activité et ${nf.format(S.meta.avecSalaire)} ayant déclaré une rémunération exploitable.</p>
      <h2>Étapes de carrière</h2>
      <p>L'expérience est comptée en années depuis le premier diplôme (ou estimée à partir de l'âge, avec un diplôme vers 24 ans). Étapes : premier poste (0 à 5 ans), confirmé (6 à 15 ans), expérimenté (16 à 30 ans), senior (au-delà de 30 ans ou à partir de 60 ans). Les étudiants sont comparés aux diplômés de 0 à 2 ans.</p>
      <h2>Estimation du salaire</h2>
      <ul>
        <li>Rémunération brute annuelle corrigée (fixe + variable), comprise entre 18 000 et 500 000 €.</li>
        <li>Régression pondérée sur le logarithme du salaire, sur ${nf.format(m.n)} répondants : tranche d'expérience, secteur, taille d'entreprise, zone (Île-de-France, autre région, étranger), diplôme, fonction, encadrement et appartenance à un comité de direction. Le modèle explique ${pct(m.r2)} de la variance.</li>
        <li>La fourchette affichée applique au profil la distribution des écarts observés dans la même tranche d'expérience. Le genre n'intervient pas dans l'estimation.</li>
        <li>Les « leviers » sont les écarts de salaire associés à un changement de caractéristique, toutes choses égales par ailleurs. Ce sont des corrélations, pas des effets garantis.</li>
      </ul>
      <h2>Autres indicateurs</h2>
      <ul>
        <li>Toutes les moyennes, médianes et parts sont pondérées par le poids de redressement de l'enquête, et ne sont publiées qu'au-delà de ${S.meta.minN} répondants.</li>
        <li>Les questions de satisfaction (notes de 1 à 5), d'usage de l'IA et d'intention de mobilité n'ont été posées qu'à une partie des répondants : leurs résultats reposent sur des effectifs plus faibles.</li>
        <li>Le télétravail est mesuré parmi les répondants concernés par la question.</li>
        <li>La courbe de trajectoire compare des générations différentes à une même date. Elle ne suit pas des personnes dans le temps.</li>
      </ul>
      <h2>Employeurs proposés</h2>
      <ul>
        <li>${nf.format(ENT.length)} employeurs issus de l'API publique Recherche d'entreprises (recherche-entreprises.api.gouv.fr, données SIRENE de l'INSEE), extraits le ${esc(window.IESF_ENTREPRISES?.genere || "—")} : entreprises de 50 salariés et plus dans quinze familles d'activités qui emploient des ingénieurs, avec leurs établissements par région.</li>
        <li>L'adéquation (0 à 100) combine le classement du secteur selon vos priorités, vos domaines, la présence d'établissements dans vos régions, la taille, le statut public ou privé et l'appartenance à l'économie sociale et solidaire. Seuls les critères que vous avez réglés comptent.</li>
        <li>Les chiffres affichés sur une carte (salaire, satisfaction) sont ceux de son secteur dans l'enquête IESF. Aucune note propre à une entreprise n'est inventée. L'effectif régional est une estimation tirée des tranches d'effectif des établissements.</li>
        <li>Une entreprise peut apparaître sous plusieurs entités juridiques (filiales d'un même groupe), comme dans le répertoire SIRENE.</li>
      </ul>
      <h2>Confidentialité</h2>
      <p>Vos réponses restent dans votre navigateur. Elles ne sont envoyées nulle part et vous pouvez les effacer avec « Recommencer à zéro ».</p>
      <p class="fine">Données générées le ${esc(S.meta.genere)}.</p>`;
  }

  // ------------------------------------------------------------------ événements
  document.addEventListener("click", async (e) => {
    const t = e.target.closest("[data-action], [data-nav], [data-scroll]");
    if (!t) return;
    const act = t.dataset.action;
    if (t.dataset.scroll) { e.preventDefault(); document.getElementById(t.dataset.scroll)?.scrollIntoView({ behavior: "smooth", block: "start" }); return; }
    if (t.dataset.nav) { e.preventDefault(); show(t.dataset.nav); return; }
    if (act === "start") { if (answers.situation && !isExample) go("explore"); else startWizard(); }
    if (act === "back") { if (stepIndex === 0) show("home"); else { stepIndex--; stepDir = "back"; renderStep(); } }
    if (act === "example") { loadExample(); renderExplore({ intro: true }); show("explore"); }
    if (act === "edit") startWizard();
    if (act === "restart") { store.clear(); isExample = false; answers = {}; startWizard(true); }
    if (act === "sc-add" && scenarios.length < 3) {
      const copy = JSON.parse(JSON.stringify(current()));
      copy.name = `Scénario ${"ABC"[scenarios.length]}`;
      scenarios.push(copy);
      active = scenarios.length - 1;
      persist();
      go("explore");
      toast(`${copy.name} créé : changez ses critères, puis comparez`);
    }
    if (act === "sc-delete" && scenarios.length > 1) {
      const name = current().name;
      scenarios.splice(active, 1);
      active = Math.max(0, active - 1);
      persist();
      refreshView();
      toast(`« ${name} » supprimé`);
    }
    if (act === "sc-edit") { active = Number(t.dataset.i) || 0; persist(); go("explore"); }
    if (act === "more") { ui.shown += 12; renderOutcomes(); }
    if (act === "fav-only") { ui.favOnly = !ui.favOnly; ui.shown = 12; renderOutcomes(); }
    if (act === "copy") {
      const text = renderResults.summaryText || "";
      try { await navigator.clipboard.writeText(text); toast("Synthèse copiée"); }
      catch {
        const ta = Object.assign(document.createElement("textarea"), { value: text });
        ta.className = "input"; ta.rows = 10; ta.readOnly = true;
        t.after(ta); ta.select();
        toast("Sélectionnez le texte puis copiez-le");
      }
    }
  });
  // Phase 2 : cartes de critères, onglets de scénarios, favoris, navigation entre phases.
  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-goto],[data-sc],[data-fav],[data-prio],[data-dom],[data-size],[data-nature],[data-ess],[data-region],[data-role],[data-projet]");
    if (!t || t.disabled) return;
    const d = t.dataset;
    if ("goto" in d) { go(d.goto); return; }
    if ("sc" in d) { active = Number(d.sc); ui.shown = 12; persist(); refreshView(); return; }
    if ("fav" in d) {
      toggleIn(favorites, d.fav);
      persist();
      const on = favorites.includes(d.fav);
      $$(`[data-fav="${d.fav}"].fav-btn`).forEach((b) => { b.classList.toggle("is-on", on); b.setAttribute("aria-pressed", String(on)); b.setAttribute("aria-label", on ? "Retirer des favoris" : "Ajouter aux favoris"); });
      $$("[data-fav-count]").forEach((el) => (el.textContent = favorites.length));
      if (ui.favOnly || document.body.dataset.view === "compare") scheduleRefresh();
      toast(on ? "Ajouté à vos favoris" : "Retiré de vos favoris");
      return;
    }
    updateScenario((sc) => {
      if ("prio" in d) sc.weights[d.prio] = ((sc.weights[d.prio] || 0) + 1) % 3;
      if ("dom" in d) toggleIn(sc.themes, d.dom);
      if ("size" in d) toggleIn(sc.sizes, d.size);
      if ("nature" in d) sc.nature = d.nature;
      if ("ess" in d) sc.ess = !sc.ess;
      if ("region" in d) { if (!d.region) sc.regions = []; else toggleIn(sc.regions, d.region); }
      if ("role" in d) sc.role = d.role;
      if ("projet" in d) sc.projet = sc.projet === d.projet ? null : d.projet;
    });
  });
  document.addEventListener("change", (e) => {
    if (e.target.closest(".choices[data-max]")) enforceMax();
    if (e.target.id === "sc-service") updateScenario((sc) => (sc.service = e.target.value || null));
    if (e.target.id === "co-sort") { ui.sort = e.target.value; renderOutcomes(); }
  });
  document.addEventListener("input", (e) => {
    if (e.target.id !== "sc-name") return;
    current().name = e.target.value.trim() || `Scénario ${"ABC"[active]}`;
    $$(".sc-tab.is-active .sc-name").forEach((el) => (el.textContent = current().name));
    persist();
  });
  $("#wizard-form").addEventListener("submit", onSubmit);
  window.addEventListener("popstate", route);
  let resizeTimer;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => { const l = careerChart.last; if (l && l[0].isConnected && l[0].offsetParent) careerChart(...l); }, 150);
  });

  renderHome();
  route();
})();
