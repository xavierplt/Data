# Idées de graphes — Données IESF 2025 non exploitées

Le dashboard actuel utilise **30 colonnes sur 667** disponibles dans le questionnaire 2025.
Ce fichier recense les graphes à forte valeur ajoutée issus des colonnes restantes.

---

## 1. Satisfaction au travail — 16 dimensions (cols 553–570)

La colonne `satisfaction` actuellement utilisée est une **note globale unique**.
Le questionnaire contient 16 sous-dimensions individuelles.

| Graphe | Colonnes | Type de visualisation |
|---|---|---|
| Radar des 16 dimensions de satisfaction | 553–570 | Radar / Spider chart |
| Heatmap satisfaction × secteur | 553–570 + 101 | Heatmap |
| Dimensions les moins bien notées | 553–570 | Bar horizontal |
| Satisfaction par genre × dimension | 553–570 + 60 | Bar groupé |

**Dimensions disponibles :**
- Sécurité de l'emploi
- Intérêt des tâches / contenu du travail
- Perspectives de carrière
- Ambiance au travail
- Niveau de stress
- Charge de travail
- Autonomie
- Facilité d'exercice des responsabilités
- Sens / valeur du travail
- Rémunération et compléments
- Équilibre vie professionnelle / personnelle
- Développement des compétences
- Organisation générale de l'entreprise
- Style de management
- Reconnaissance par la hiérarchie
- Reconnaissance par les pairs

---

## 2. Mobilité & Intentions de départ (cols 168–176, 573–575)

| Graphe | Colonnes | Type de visualisation |
|---|---|---|
| Nature des derniers changements professionnels | 173 | Bar horizontal |
| Raison principale du dernier changement | 174 | Bar horizontal |
| Intention de changer d'employeur × satisfaction globale | 573 + 551 | Bar groupé ou scatter |
| Mode de découverte de l'emploi actuel | 159 | Bar horizontal |
| Satisfaction de la dernière mobilité | 172 | Bar ou camembert |
| Intention de changer d'employeur × tranche d'âge | 573 + 59 | Heatmap ou bar groupé |

---

## 3. Rémunération complémentaire (cols 218–227)

| Graphe | Colonnes | Type de visualisation |
|---|---|---|
| Distribution du % variable contractuel | 218 | Histogramme |
| Bénéficiaires de l'intéressement & participation par taille d'entreprise | 219, 220, 221 | Bar groupé |
| Montant brut de l'intéressement — distribution | 220 | Histogramme |
| Évolution salariale envisagée pour 2025 (hausse / stable / baisse) | 225, 226 | Camembert + bar |
| Rémunération totale estimée (fixe + variable + intéressement) | 211, 217, 220 | Box plot par secteur |

---

## 4. Intelligence Artificielle — usage détaillé (cols 490–529)

### 4a. Usages

| Graphe | Colonnes | Type de visualisation |
|---|---|---|
| Pour quoi utilise-t-on l'IA ? (automatiser, innover, vérifier…) | 491–496 | Bar horizontal multi-réponses |
| Domaines d'application de l'IA | 515–522 | Bar horizontal multi-réponses |
| Domaines d'application de l'IA × secteur | 515–522 + 101 | Heatmap |

### 4b. Préoccupations & Formation

| Graphe | Colonnes | Type de visualisation |
|---|---|---|
| Préoccupations liées à l'IA (éthique, sécurité, emploi…) | 498–505 | Bar horizontal multi-réponses |
| Formation à l'IA par l'entreprise × taille d'entreprise | 507 + 99 | Bar groupé |
| Formation à l'IA par l'entreprise × secteur | 507 + 101 | Bar groupé |
| Changements anticipés liés à l'IA (rôles, charge de travail…) | 508–514 | Bar horizontal multi-réponses |

### 4c. Télétravail — analyse du gap

| Graphe | Colonnes | Type de visualisation |
|---|---|---|
| Jours de télétravail réels vs idéaux (par tranche d'âge) | 230 vs 231 | Bar groupé |
| Gap jours réels / idéaux par secteur | 230 vs 231 + 101 | Heatmap |
| Employeur favorise-t-il le télétravail ? | 233 | Camembert |

---

## 5. Rôles & Responsabilités (cols 123–131)

| Graphe | Colonnes | Type de visualisation |
|---|---|---|
| Répartition chef de projet / expert technique / manager | 130, 131 | Camembert ou bar |
| Taille des équipes encadrées — distribution | 123 | Histogramme |
| Responsabilités à l'international × secteur | 128 + 101 | Bar groupé |
| Membre d'un Codir/Comex × genre × âge | 125 + 60 + 59 | Heatmap (plafond de verre) |
| Reconnaissance de l'expertise × secteur | 136 + 101 | Bar groupé |
| Salaire médian par rôle (chef de projet / expert / manager) | 130, 131 + 666 | Bar horizontal |

---

## 6. Attractivité employeur & Engagement (cols 576–598)

| Graphe | Colonnes | Type de visualisation |
|---|---|---|
| Top critères pour choisir un employeur | 576–594 | Bar horizontal pondéré |
| Critères par génération (< 30 ans vs 50+ ans) | 576–594 + 59 | Bar groupé par âge |
| Critères par genre | 576–594 + 60 | Bar groupé |
| Sentiment envers l'employeur (confiance / attachement / enthousiasme) | 596, 597, 598 | Radar ou bar groupé |
| Employeur idéal × secteur actuel | 595 + 101 | Bar groupé |

---

## 7. International (cols 384–402)

| Graphe | Colonnes | Type de visualisation |
|---|---|---|
| Envie de travailler à l'international × tranche d'âge | 399 + 59 | Bar groupé |
| Raisons de refus d'une offre internationale | 402 | Bar horizontal |
| Temps cumulé passé à l'international | 384 | Histogramme |
| Qualité de vie / rémunération / opportunités à l'international vs France | 389, 390, 391 | Bar groupé |

---

## 8. Formation initiale & Parcours (cols 47, 141–145)

| Graphe | Colonnes | Type de visualisation |
|---|---|---|
| Spécialité initiale vs domaine fonctionnel actuel | 142 + 97 | Sankey / heatmap (reconversion disciplinaire) |
| Impact d'une césure sur le salaire médian | 47 + 666 | Bar comparatif |
| Bac d'origine (général / technologique / autre) | 141 | Camembert |
| Bac d'origine × diplôme obtenu × salaire | 141 + 2 + 666 | Heatmap |
| Changement de spécialité au cours de la carrière × salaire | 143 + 666 | Bar comparatif |

---

## 9. Bénévolat & Engagement citoyen (cols 403–406)

| Graphe | Colonnes | Type de visualisation |
|---|---|---|
| Taux d'activité bénévole × genre × âge | 403 + 60 + 59 | Bar groupé |
| Domaines de bénévolat | 406 | Bar horizontal multi-réponses |
| Heures mensuelles de bénévolat — distribution | 405 | Histogramme |

---

## 10. Responsabilité & Transition environnementale (cols 443–484)

| Graphe | Colonnes | Type de visualisation |
|---|---|---|
| Perception des grandes contraintes (écologique, géopolitique, sociétale, digitale) | 443–454 | Bar groupé ou radar |
| Actions environnementales mises en œuvre par l'entreprise | 477 | Bar multi-réponses |
| Ingénieurs souhaitant changer de statut pour l'écologie | 484 | Camembert |

---

## Priorités recommandées

| # | Graphe | Raison |
|---|---|---|
| 1 | **Radar 16 dimensions de satisfaction** | Données très riches, inexploitées, très visuelles |
| 2 | **Critères de l'employeur idéal × génération** | Fort intérêt RH, sujet d'actualité |
| 3 | **Usages détaillés de l'IA + préoccupations** | Données inédites sur un sujet clé 2025 |
| 4 | **Gap jours télétravail réels vs idéaux** | Frustration mesurable, simple à implémenter |
| 5 | **Plafond de verre — Codir/Comex × genre × âge** | Impact fort, données directes |
| 6 | **Évolution salariale envisagée 2025** | Signal avancé sur l'année en cours |
| 7 | **Sankey spécialité initiale → domaine fonctionnel** | Parcours atypiques, reconversion |
