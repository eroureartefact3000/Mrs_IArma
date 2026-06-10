# Mrs IArma — Documentation technique

> Outil IA de prédiction "Ce projet pub va-t-il gagner un Cannes Lions ?"
> Projet Artefact 3000 · Lead tech : Etienne Roure
> Dernière mise à jour : 2026-06-10
>
> Branding runtime (frontend) : **« Mrs Airma · The Cannes Oracle »** (anglais, ton oraculaire).
> Toute sortie destinée à l'utilisateur (verdict, présages, synthèse, axes) est en anglais. Cette documentation reste en français car elle s'adresse à l'équipe interne.

## Sommaire

1. [Contexte & objectif](#1-contexte--objectif)
2. [Approche méthodologique](#2-approche-méthodologique)
3. [Architecture du système](#3-architecture-du-système)
4. [Setup pour un nouveau contributeur](#4-setup-pour-un-nouveau-contributeur)
5. [Pipeline détaillé phase par phase](#5-pipeline-détaillé-phase-par-phase)
6. [Décisions clés et corrections DA](#6-décisions-clés-et-corrections-da)
7. [Structure des fichiers](#7-structure-des-fichiers)
8. [Commandes utiles](#8-commandes-utiles)
9. [État d'avancement & roadmap](#9-état-davancement--roadmap)
10. [Annexes](#10-annexes)

---

## 1. Contexte & objectif

### Le besoin

Une directrice artistique d'Artefact 3000 souhaite un outil ludique de prédiction pour les **Cannes Lions** — l'équivalent des Oscars de la publicité. Chaque année, des milliers d'agences soumettent des projets. Nous voulons permettre aux créatifs d'uploader une **"board"** (digital presentation image — un one-pager qui résume une campagne) et obtenir une **prédiction du tier** que leur projet pourrait gagner (Grand Prix / Gold / Silver / Bronze / pas de médaille).

### La proposition de valeur

- **Pour l'agence** : outil marketing visible à l'international, démonstration de notre maîtrise de l'IA générative.
- **Pour les créatifs du monde entier** : feedback structuré et instantané sur la "Cannes-ability" de leur travail, avec des références concrètes (gagnants des années précédentes les plus similaires).

### Le périmètre couvert

- **30 catégories** Cannes Lions 2026 activées de bout en bout (criteria + RAG index + rationales) :
  Outdoor · Print & Publishing · Audio & Radio · Film · PR · Direct · Media · Social & Influencer · Creative B2B · Creative Data · Design · Industry Craft · Digital Craft · Film Craft · Brand Experience & Activation · Creative Commerce · Creative Business Transformation · Innovation · Luxury · Entertainment · Entertainment Lions for Sport · Entertainment for Gaming · Entertainment for Music · Health & Wellness · Pharma · Sustainable Development Goals · Glass (The Lion for Change) · Creative Strategy · Creative Effectiveness · Titanium.
- **Base RAG** : 1466 boards extraites, 604 gagnantes (avec rationales générées) servant de références.
- **Calibration formelle** sur Outdoor (n=10, ~80% binaire) et PR (n=20, ~75% binaire). Les 28 autres catégories ont été testées end-to-end (smoke tests) mais n'ont pas fait l'objet d'une calibration formelle sur held-out.
- **Méthodologie validée** par la directrice artistique sur Outdoor (mai 2026), généralisée aux autres catégories via des briefs MECE par catégorie (`agent_briefs/categories/{SLUG}.md`).

---

## 2. Approche méthodologique

### Pourquoi pas un classifieur supervisé classique

On a 53 boards gagnantes + 65 shortlist + 2 losers en Outdoor 2024. Dataset trop petit pour entraîner un classifieur supervisé, et surtout très peu de "négatifs" propres. Le jugement Cannes est de plus très qualitatif (idée, stratégie, exécution, impact) — il se modélise mal en pure tâche de classification.

### La méthode retenue : **LLM-as-a-Judge + RAG**

```
                                  ┌──────────────────────────────────┐
                                  │ Base de gagnantes Outdoor 2024   │
                                  │ (117 boards extraites + scorées) │
                                  └────────────────┬─────────────────┘
                                                   │
                                          embeddings Voyage AI
                                                   │
                                                   ▼
  ┌────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
  │ Nouveau    │───▶│ Extraction   │───▶│ Recherche       │───▶│ LLM-juge     │
  │ board      │    │ structurée   │    │ vectorielle     │    │ Claude Opus  │
  │ (upload)   │    │ (Claude VLM) │    │ → top-5 proches │    │ → tier + raison│
  └────────────┘    └──────────────┘    └─────────────────┘    └──────────────┘
```

**Trois piliers :**

1. **Extraction structurée** — On parse chaque board (image haute résolution) en un schéma JSON (`extracted` + `inferred` + `visual`) qui capture l'idée, la stratégie, l'exécution, les résultats.

2. **Why-it-won rétrospectif** — Pour chaque gagnante de notre base, on génère une **rationale jury simulée** (per axe : Idea / Strategy / Execution / Impact) avec un score chiffré. C'est la "fiche jury" qui servira de référence.

3. **Retrieval-Augmented Generation (RAG)** — Au moment de l'évaluation d'un nouveau board, on retrouve les 5 gagnantes les plus similaires conceptuellement (via embeddings Voyage). Le LLM-juge Claude les utilise comme **calibration concrète** pour scorer le nouveau board.

### Les 4 axes d'évaluation (Outdoor)

Pondération issue de l'entry kit Cannes Lions 2026, adaptée à notre framework :

| Axe | Poids | Question |
|---|---|---|
| **Idea** | 35% | L'idée est-elle vraiment originale et mémorable ? |
| **Strategy** (le WHY) | 10% | (1) Qui est la marque + cohérence avec sa mission ? (2) Insights & contexte data-backed ? |
| **Execution** (le HOW) | 30% | Les moyens et médias sont-ils pertinents vs objectif et cible ? Orchestration ? |
| **Impact** | 25% | Résultats mesurables : business, comportemental, culturel ? |

Mapping tier → score (du brief initial) :
- Grand Prix : 90-100
- Gold : 80-100
- Silver : 65-80
- Bronze : 50-65
- Shortlist / Loser : pas de bande officielle (sont labels de données, pas catégorie Cannes)

---

## 3. Architecture du système

### Stack technique

| Composant | Choix | Pourquoi |
|---|---|---|
| Language | Python 3.11+ | Standard ML/data |
| Package manager | `uv` | Install rapide, lockfile reproductible |
| LLM (extraction + jugement) | **Claude Opus 4.7** | Meilleure compréhension multi-modale + raisonnement |
| Image processing | Pillow + pillow-avif-plugin | Support format mixte (jpg/png/webp/avif), resize sous limite API |
| Schema validation | Pydantic v2 | Type-safe, validation native |
| Embeddings (RAG) | **Voyage-3-large** (1024-dim) | Partenaire Anthropic, free tier généreux |
| Stockage vecteurs | numpy `.npy` + `.jsonl` | ~120 vecteurs = pas besoin de DB |
| Doc finale (review DA) | Word .docx (via python-docx) | Conversion auto Google Docs, commentaires inline |

### Coût opérationnel (par run complet)

| Étape | Boards | Coût estimé | Durée |
|---|---|---|---|
| Pré-classification (si dataset non trié) | ~358 | ~$8 | ~6 min |
| Extraction v3 (2-pass) | 120 | ~$35 | ~9 min |
| Génération why-it-won | 120 | ~$25 | ~10 min |
| Build index vectoriel | 120 | ~$0.01 | ~30 sec |
| **Total Phase 1 complète** | | **~$70** | **~30 min** |

Une fois la base RAG construite, **chaque évaluation utilisateur coûte ~$0.50** (extraction du board upload + recherche + 1 appel juge).

---

## 4. Setup pour un nouveau contributeur

### Pré-requis

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) : `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Clés API : Anthropic + Voyage AI (free tiers couvrent largement notre usage)

### Installation

```bash
git clone <repo>
cd Mrs_IArma
uv sync                        # installe toutes les deps dans .venv
cp .env.example .env           # puis édite .env avec tes clés
```

### `.env` requis

```bash
ANTHROPIC_API_KEY=sk-ant-...   # https://console.anthropic.com/settings/keys
VOYAGE_API_KEY=pa-...          # https://www.voyageai.com (free tier 50M tok/mois)
```

### Lancement rapide pour comprendre

```bash
# Lance le pipeline sur 5 boards déjà eyeballées (smoke test, ~$1)
uv run python test_5_boards.py

# Inspecte la sortie
cat data/test_5_boards.json | jq '.[0]'
```

---

## 5. Pipeline détaillé phase par phase

### Phase 1.1 — Extraction (`extract_2024_outdoor.py`)

**Input** : 120 boards dans `2024/OUTDOOR/{GRAND PRIX, GOLD, SILVER, BRONZE, SHORTLIST}/` + 2 losers Outdoor dans `2024/loser/`.

**Process — 2-pass VLM avec Claude Opus** :

1. **Pass 1 (strict)** : extrait uniquement les infos **explicitement visibles** sur la board. Tous les champs peuvent être `null` si non présents. Pas d'invention.
2. **Pass 2 (inferred)** : remplit les champs manquants par inférence + génère systématiquement `one_liner`, `creative_mechanisms`, `qualitative_summary` et le bloc `visual`.

**Output** : `data/outdoor_2024_extractions.jsonl` — 1 record par board avec le schéma v3 (voir [Annexe A](#a-schéma-v3-dextraction)).

**Robustesse** :
- Resize automatique des images > 3.5 MB (limite Voyage API base64)
- Détection du format réel via Pillow (les `.jpg` peuvent en fait être des WebP renommés)
- Retry sur JSON parse error (3 tentatives max)
- Resumable : skip les records déjà traités

### Phase 1.2 — Why-it-won (`generate_outdoor_why_won.py`)

**Input** : `outdoor_2024_extractions.jsonl`

**Process** : pour chaque board, un appel Claude Opus avec :
- L'extraction v3 (texte uniquement, pas l'image)
- Les critères Outdoor (`OUTDOOR_CRITERIA` dans `pipeline/outdoor_criteria.py`)
- Le tier connu (ground truth)
- Le **prompt rationale** (`pipeline/rationale.py`) qui force :
  - Strict separation Strategy = WHY / Execution = HOW
  - Score discrimination (pas d'ancrage forcé sur la bande de tier)
  - **5 patterns de rigueur DA** ([§6](#6-décisions-clés-et-corrections-da))

**Output** : `data/outdoor_2024_with_rationale.jsonl` — chaque record enrichi de `why_it_won` (4 axes × {score, rationale} + weighted_score + verdict + tier_consistency).

### Phase 1.3 — Review humaine DA

**Input** : `outdoor_2024_with_rationale.jsonl`

**Process** : `build_review_doc.py` génère un Word `.docx` avec une page par board (image + scores + verdict + rationale axe par axe + placeholder feedback).

```bash
uv run python scripts/build_review_doc.py \
  --input data/outdoor_2024_with_rationale.jsonl \
  --output data/outdoor_2024_review_v2.docx \
  --title "Mrs IArma · Outdoor 2024 Review"
```

**Workflow DA** :
1. Le `.docx` est uploadé sur Google Drive
2. Right-click → Ouvrir avec → Google Docs (conversion auto)
3. Partage avec la DA en mode **Commentateur**
4. Elle commente inline les boards (Insert > Comment)
5. On itère : corrections → re-run rationale → re-génération doc

### Phase 1.4 — Indexation vectorielle (terminée 2026-05-29)

**Input** : `outdoor_2024_with_rationale.jsonl`

**Process** :
1. `pipeline/search_doc.py` construit pour chaque board un **search document** condensé : `one_liner + creative_mechanisms + idea + insight`. On omet brand/campaign/metrics (bruit pour la recherche conceptuelle).
2. `build_outdoor_index.py` embedde tous les search documents via Voyage-3-large.
3. Sauvegarde : `data/outdoor_index.npy` (matrice 120 × 1024 float32) + `data/outdoor_index_meta.jsonl` (id → record).

**API search** (`pipeline/search.py`) :

```python
from pipeline.search import search

hits = search("ambient billboard that becomes a product", k=5)
# Returns top-5 boards par cosine similarity, avec score + full_record
```

Filtres optionnels : `tier_filter={"Grand Prix", "Gold"}` pour ne chercher que les gagnantes médaillées.

**Notes free-tier Voyage** : sans payment method, l'API limite à **3 RPM + 10K TPM**. Notre code (`pipeline/embeddings.py`) gère ça via :
- batch_size par défaut 32 (≈ 4.8K tokens, sous la limite)
- throttle 22s entre batches (au-dessus de 1 req / 20 s)
- retry-on-rate-limit (`_with_rate_limit_retry`) avec backoff progressif
Ajouter un payment method sur le dashboard Voyage (les 200M tokens free restent) débloque les limites normales et rend tout instantané.

**Résultats du smoke test** (7 queries, voir `test_search.py`) :

| Query | Top hit | Score | Verdict |
|---|---|---|---|
| object-as-medium ambient | Privacy Shades / BÄSTIS / Privacy Swap | 0.60-0.63 | ✅ Tous des "objet-devient-billboard" |
| purpose-driven pet adoption | Adoptable (Pedigree GP) | 0.636 | ✅ Le bon GP en #1 |
| competitor wordplay ambush | Et le Buuuuuud / Aldidas / Whopper Island | 0.59-0.65 | ✅ Mécanique captée |
| environment-responsive billboard | Megh Santoor (pluie) / Magnum (soleil) | 0.57-0.61 | ✅ |
| public-space viral prank | Marina Prieto / F***ing Car / Cruise Heist | 0.54-0.57 | ✅ |
| paid-to-remove-its-logo | Clean Sponsorship Gold + Silver | 0.58 | ✅ Exact match en #1-2 |
| out-of-distribution (quantum) | Megh Santoor | 0.29 | ✅ Scores < 0.30 confirment OOD |

**Lecture** : sur les queries pertinentes, scores ~0.55-0.65 ; sur l'OOD, scores plafonnent à ~0.29. L'écart est franc, donc le RAG saura discriminer entre "boards similaires" et "rien dans la base".

### Phase 2 — Moteur d'évaluation (terminée 2026-05-29)

Pipeline end-to-end pour évaluer un board NOUVEAU (jamais vu par le système). Implémenté dans :

- `pipeline/judge.py` — LLM-Judge multi-pass avec image + RAG context. 3 passes parallèles, scores moyennés, narrative prise du pass le plus proche du centroïde
- `pipeline/malus.py` — détection holding (Publicis/Havas/Omnicom) + compute_malus (esthétique -10%, client -20%, réseau -20%)
- `pipeline/evaluate.py` — orchestrateur `evaluate_board(image, metadata) → BoardEvaluation`
- `evaluate_board.py` (root) — CLI

**Flow** :
```
1. Extract v3 (Claude Opus, 2-pass)      ~17s, ~$0.40
2. RAG retrieval (Voyage top-5)          <1s, négligeable
3. Multi-pass judge 3× parallèle         ~26s, ~$1.50 (3 × $0.50)
4. Malus + tier prediction (déterministe) <1s, gratuit
                                          ─────────────────
                                          ~45s, ~$1.90 par évaluation
```

**Mapping score → tier** (du brief) :
- ≥ 90 : Grand Prix
- ≥ 80 : Gold
- ≥ 65 : Silver
- ≥ 50 : Bronze
- < 50 : No Medal

**Malus** (cumulatifs additifs, multiplicateur final = `1.0 - somme`) :
- `aesthetic_penalty` -10% si `visual.craft_quality == "low"`
- `client_penalty` -20% si l'utilisateur indique que le client n'est PAS connu à l'international
- `network_penalty` -20% si l'agence n'est PAS détectée comme appartenant à Publicis, Havas ou Omnicom (3 holdings explicites du brief — non négociable, voir [`pipeline/malus.py`](pipeline/malus.py))

**Smoke test — KitKat Phone Break 2025 GP Outdoor (board hors-index)** :
- Base score LLM : 70.4 (Silver band)
- Malus : ×0.80 (VML Prague pas dans Publicis/Havas/Omnicom → -20%)
- Score final : 56.3 → **Bronze prédit**
- Tier réel : **Grand Prix**

L'écart Bronze ↔ GP s'explique par 3 facteurs :
1. Le board KitKat est connu pour être très visuel et léger en data (le jury Cannes avait le case film, nous avons juste la board)
2. Les 5 references RAG retrouvées sont toutes des Silver/Bronze "object-as-medium" — le juge calibre contre elles
3. Le malus -20% sur VML (WPP, hors 3-holdings du brief) est sévère par construction

C'est un comportement honnête et défendable de l'outil : il pénalise l'absence de preuve d'impact et reflète strictement les contraintes du brief. Une amélioration future pourrait être de demander à l'utilisateur de fournir le case film en supplément de la board pour avoir une analyse plus complète.

**Schéma de sortie** :

```python
class BoardEvaluation:
    user_metadata: UserMetadata          # campaign, agency, client, client_internationally_known
    analysis: BoardAnalysis              # v3 extraction + why-it-might-win (4 axes scorés)
    base_weighted_score: float           # avant malus
    final_weighted_score: float          # après malus
    predicted_tier: PredictedTier        # Grand Prix / Gold / Silver / Bronze / No Medal
    references: list[Reference]          # top-5 RAG avec similarity_score
    malus: dict                          # MalusBreakdown serialized
    pass_scores: list[dict]              # raw scores des 3 passes
```

**Usage CLI** :
```bash
uv run python scripts/evaluate_board.py \
  --image path/to/board.jpg \
  --campaign "Phone Break" \
  --agency "VML Prague" \
  --client "KitKat" \
  --client-international \
  --passes 3 \
  --k 5 \
  --output data/eval_result.json
```

### Phase 3 — Calibration (terminée 2026-05-29)

Test set de 10 boards évalué en bout-en-bout pour mesurer l'écart prédiction/réalité.

**Composition du test set** :
- 2 Losers Outdoor (déjà dans l'index → `exclude_ids` self-match)
- 5 hold-out 2024 (GP + Gold + Silver + Bronze + Shortlist, avec `exclude_ids`)
- 3 fresh 2025 (Paris 2024 Opening GP / Heinz Gold / BK Bundles Silver)

**Résultats** (v2, après extension malus à 6 holdings + prompt renforcé) :

| Métrique | Valeur | Lecture |
|---|---|---|
| Exact match | 3/10 (30%) | Le LLM-judge ne distingue pas cleanly les tiers médaillés entre eux |
| Within ±1 tier | 6/10 (60%) | Indication directionnelle fiable mais imparfaite |
| Délta max | -3 (Paris 2024 GP → Bronze) | Cas extrême : jury Cannes indulgent malgré faiblesse native-to-category |
| Délta moyen | -0.4 | Léger biais conservateur du juge (logique vu RIGOUR strict) |

**Distribution observée par tier réel** (base scores LLM, avant malus) :

```
Grand Prix  → [57.4, 84.0]   (très large, 27 pts de spread)
Gold        → [74.2, 83.7]
Silver      → [76.4, 82.8]
Bronze      → 79.8
Shortlist   → 75.6
Loser       → [67.4, 70.4]   (clean separation vs autres tiers)
```

**Insight clé** : seuls les **Losers** se distinguent cleanly (sous 70). Pour les médailles (Gold / Silver / Bronze), les distributions se chevauchent et le LLM ne peut pas trancher. Les thresholds initiaux du brief (GP≥90, Gold≥80, Silver≥65, Bronze≥50) restent les meilleurs après test de 4 alternatives — toute recalibration empire l'accuracy.

**Changements V1 → V2 appliqués** :

1. **Extension malus à 6 holdings** (`pipeline/malus.py`) — ajout de WPP, IPG, Dentsu aux 3 originaux du brief. La règle d'origine excluait des winners légitimes (W+K, McCann, Ogilvy, VML…).

2. **Prompt judge renforcé** (`pipeline/judge.py`) — deux nouvelles sections :
   - **Calibration anchors 0-100** : indique au modèle d'utiliser activement la full range, pas juste 70-85.
   - **Native-to-category check** : hard-cap Idea ≤ 60 et Execution ≤ 50 si le board est un live event / Twitch stunt / film campaign déguisé en Outdoor. Détecte les Losers (KitKat Break Chair, IKEA First Steps) ET les GP atypiques (Paris 2024 — où le jury était indulgent).

**Limite intrinsèque** : le LLM-judge donne une **indication directionnelle** mais ne peut pas être un oracle exact. C'est OK pour le positionnement "outil ludique de prédiction" du brief. La restitution UI (Phase 4) devra communiquer la confiance honnêtement et mettre en avant les références similaires pour que l'utilisateur juge par lui-même.

**Archives** :
- `data/calibration_results_v1.jsonl` — résultats V1 (3 holdings, prompt initial)
- `data/calibration_results_v2.jsonl` — V2 (6 holdings + prompt renforcé)
- `data/calibration_results_v3_pairwise.jsonl` — V3 (pairwise + probabilités, JSON instable)
- `data/calibration_results_v3_tooluse.jsonl` — V3.1 (tool_use JSON forcé)
- `data/calibration_results.jsonl` — V4 courant (5 winners + 2 non-winners RAG)

### Phase 3.5 — Pivot binaire (2026-06-01)

**Constat** : malgré les 3 itérations Phase 3, l'accuracy tier-exact plafonnait à 20-30% et within-±1 à 50-60%. Discussion utilisateur : *« C'est déjà bien si on peut déterminer que ça gagne ou non, partons là dessus dans un premier temps. »*

**Pivot produit** : on remplace la prédiction de tier exact par une **prédiction binaire MEDAL / NO MEDAL** + une note de synthèse courte + 3 pistes d'amélioration actionnables. Le tier exact (argmax probabilités) reste calculé en interne mais n'est plus exposé à l'utilisateur.

**Changements techniques** :

1. **`tool_use` API d'Anthropic** (`pipeline/judge.py`) — le LLM-judge utilise désormais un outil avec JSON Schema strict. Élimine les JSON parse errors qui plombaient 2/10 cas en v3.

2. **Output utilisateur épuré** (`MedalPrediction` dans `pipeline/schema.py`) :
   - `will_medal: bool` — réponse binaire
   - `medal_probability: float` — P(medal) après malus, entre 0 et 1
   - `confidence: "high" | "medium" | "low"` — fonction de la distance au threshold
   - `synthesis: str` — 1-2 phrases punchy (max ~40 mots)
   - `improvement_tips: list[str]` — exactement 3 actions concrètes, priorisées par impact

3. **RAG enrichi 5 + 2** (`pipeline/evaluate.py`) — le judge reçoit désormais :
   - 5 winners (GP/Gold/Silver/Bronze) — calibrent la borne supérieure ("à quoi ressemble un gagnant")
   - **2 non-winners (Shortlist/Loser)** — calibrent la borne inférieure ("à quoi ressemble du travail qui ne gagne pas")

4. **Threshold par défaut** : `P(medal) >= 0.65` (vs 0.50 initial), trouvé empiriquement via threshold sweep sur les 10 cas.

**Résultats mesurés (10 cas test)** :

| Métrique | v3 (winners only) | v4 (5 winners + 2 non-winners) | Δ |
|---|---|---|---|
| **Binary medal/no medal** | 7/10 (70%) | **8/10 (80%)** | **+10 pts** |
| Within ±1 tier (debug) | 5/10 (50%) | 7/10 (70%) | +20 pts |
| Exact tier (debug) | 2/10 (20%) | 3/10 (30%) | +10 pts |
| P(No Medal) sur Losers | 0.23 | **0.33** | +0.10 |
| P(No Medal) sur Medals | 0.13 | 0.18 | (acceptable) |
| **Gap (séparation)** | +0.10 | **+0.16** | +60% |
| Brier score | 0.85 | **0.79** | mieux calibré |

**Les 2 erreurs restantes** :
- KitKat Break Chair (Loser) → P(no medal) = 23% → prédit Bronze. Board très bien craftée, le modèle reste optimiste.
- Paris 2024 Opening (GP) → P(no medal) = 40% → prédit No Medal. Le judge dit "pas natif Outdoor" (techniquement vrai), mais le jury Cannes a fermé les yeux.

**Lecture** : avec 80% binaire on s'approche de la cible 85% sans toucher à l'architecture. Pour gratter les 5 derniers points il faudrait probablement enrichir le signal d'entrée (case film) ou ajouter une couche ML supervisée — chantiers significatifs.

> **Limites de calibration system-wide** : la même méthodologie a été poussée sur PR (80% → ~75% binaire sur n=20) et Print & Publishing (~60% binaire sur n=10). Le palier observé n'est pas un bug ; c'est une limite intrinsèque du LLM-judge qui compresse les scores pondérés dans la bande 65-85 et discrimine mal à l'intérieur. Détails et bornes documentés dans `data_internal/SYSTEM_CALIBRATION_NOTES.md`, `data_internal/PR_CALIBRATION_NOTES.md`, `data_internal/PRINT_CALIBRATION_NOTES.md`.

#### Piste différée : couche ML supervisée au-dessus du LLM-judge

Documenté ici pour reprise future. Décision 2026-06-01 : **on accepte ~75-80% binaire** sur les catégories formellement calibrées et on enchaîne sur le front-end. Cette piste sera reprise si la précision devient insuffisante en production.

**Principe** : un petit modèle classique (Random Forest binaire visé) prend en entrée les ~25-30 features produites par le LLM-judge (axis_scores, tier_probabilities, malus, RAG metadata, features visuelles) et prédit `is_medal` (0/1) en apprenant le biais systématique du LLM.

**Données disponibles** : 120 boards Outdoor 2024 déjà labelisées (2 GP + 9 Gold + 15 Silver + 27 Bronze = 53 medals VS 65 Shortlist + 2 Loser = 67 non-medals). Dataset équilibré, idéal pour un classifier binaire.

**Effort estimé** :
- Collection des features (~$220 API + ~3h runtime, exclude self-ID pour éviter data leakage)
- Entraînement (gratuit, 2-3h dev)
- Intégration dans `pipeline/evaluate.py` (2-3h)
- Validation sur les 10 cas test (~$20 API)
- **Total : ~$240 et ~2 jours**

**Gain attendu** : 80% → 85-90% binary accuracy + meilleure calibration des probabilités affichables.

**À mettre en œuvre quand** : si le retour utilisateur montre que la précision actuelle n'est pas suffisante, OU si on veut afficher P(medal) comme un vrai pourcentage de confiance (besoin de probabilités calibrées).

---

## 6. Décisions clés et corrections DA

### Itération 1 (mai 2026) — méthodologie initiale sur PR 2025

**Test sur 65 boards PR Cannes 2025.** Premiers résultats raisonnables mais 2 problèmes pointés par la DA après review du document `.docx` :

1. **Confusion Strategy vs Execution** — le prompt mélangeait WHY (mission + insight) et HOW (orchestration + médias).
2. **Scores trop resserrés intra-tier** — tous les Bronze entre 60-73, difficile de distinguer.

### Itération 2 (mai 2026) — corrections + pivot Outdoor 2024

**Pivot dataset** : passage de PR 2025 (organisé par tier mixé) à Outdoor 2024 (organisé par catégorie ET tier, + losers disponibles).

**Corrections du prompt rationale** (`pipeline/rationale.py`) :

| Avant | Après (validé DA) |
|---|---|
| Strategy = "earned-media thinking, audience, channels…" | Strategy = WHY UNIQUEMENT : (1) qui est la marque + idée-mission, (2) insight veracity. **Pas d'orchestration**. |
| Execution = "PR techniques vague" | Execution = HOW UNIQUEMENT : orchestration des phases + media-target fit + amplification. **Pas de brand mission**. |
| Ancrage strict sur bande de tier | "Judge absolute craft, two same-tier boards may differ by 10-15 points" |

### Itération 3 (29 mai 2026) — patterns de rigueur

Après review du doc Outdoor par la DA, elle identifie **5 patterns récurrents** où notre modèle manquait de rigueur de jury professionnel :

| Pattern | Exemple | Correction prompt |
|---|---|---|
| **Pourcentages sans base** | Pedigree "50% of featured dogs" — 50% de combien ? Marina Prieto "+39,285%" = +3000 followers réels. | Le rationale doit demander "X% of what?" et pénaliser si la base manque. |
| **Sources non vérifiées** | F***ing Car "303M impressions, CNN Brasil" — la DA a cherché, pas d'article CNN. | Traiter les claims press comme "entrant-reported, unaudited". |
| **Business outcome manquant** | F***ing Car promeut une saison Netflix mais n'affiche pas le viewership lift. | Identifier l'objectif business réel et pénaliser son absence. |
| **Superlatifs vagues** | "Exceptional craft" → DA : "exceptionnel uniquement en cela qu'il utilise l'IA pour transformer photos amateures". | Justifier immédiatement tout superlatif avec une observation concrète et spécifique. |
| **Nuances culturelles** | "Et le Buuuud" = jeu de mots **Québec-francophone**, pas pan-canadien. | Capter et nommer le scope culturel précis. |

**Effet mesuré sur l'itération v2** :
- Loser mean : 47.5 → **41.3** (-6.2 pts, plus aligné avec un vrai loser)
- Marina Prieto Gold Impact : 92 → 84 (-8 pts, refléte le scepticisme sur % sans base)
- Le modèle a même **fait l'arithmétique de la DA** : "39,285% of 28 followers ≈ 11,000"

### Itération 4 (29 mai 2026) — passage Phase 1.4

DA validée sur la qualité globale. On enchaîne sur l'indexation vectorielle pour le RAG.

---

## 7. Structure des fichiers

```
Mrs_IArma/
├── DOCUMENTATION.md                ← ce fichier
├── pyproject.toml                  ← deps Python
├── .env                            ← clés API (jamais committé)
├── .env.example                    ← template
├── .gitignore
│
├── 2024/                           ← dataset 2024, par catégorie/tier
│   ├── OUTDOOR/
│   │   ├── GRAND PRIX/             (2 boards)
│   │   ├── GOLD/                   (9 boards)
│   │   ├── SILVER/                 (15 boards)
│   │   ├── BRONZE/                 (27 boards)
│   │   └── SHORTLIST/              (65 boards)
│   ├── PR/                         (115 boards)
│   ├── PRINT&PUBLISHING/, FILM/, DESIGN/, … (30 catégories Cannes Lions 2026, toutes activées)
│   └── loser/                      (4 boards perdantes manuelle)
│
├── 2025/                           ← dataset 2025, par tier mixé (utilisé pour PR v1)
│   ├── Grand Prix/                 (23 boards)
│   ├── Gold/                       (78 boards)
│   ├── Silver/                     (117 boards)
│   └── Bronze/                     (140 boards)
│
├── pipeline/                       ← code de prod
│   ├── __init__.py
│   ├── schema.py                   ← Pydantic models (Extracted, Inferred, Visual, WhyItWon, BoardAnalysis)
│   ├── images.py                   ← Loader image/PDF avec resize + détection format (PDF natif via Claude document block)
│   ├── client.py                   ← Wrapper Anthropic SDK + helper build_media_block (image/document)
│   ├── classifier.py               ← Pré-classification famille Cannes (utilisé si dataset non trié)
│   ├── extractor.py                ← Extraction 2-pass + impact_strength + flag_for_review
│   ├── rationale.py                ← Générateur why-it-won (DA mental model + RIGOUR)
│   ├── category_registry.py        ← Registre central des 30 catégories (criteria + index lazy-loaded)
│   ├── {slug}_criteria.py          ← 30 modules de critères (un par catégorie), poids d'axes spécifiques
│   ├── search_doc.py               ← Construction du search document par board
│   ├── embeddings.py               ← Wrapper Voyage AI
│   └── search.py                   ← API de recherche vectorielle
│
├── data/                           ← outputs (gitignored)
│   ├── outdoor_2024_extractions.jsonl
│   ├── outdoor_2024_with_rationale.jsonl
│   ├── outdoor_2024_with_rationale_v1.jsonl  (archive itération précédente)
│   ├── outdoor_2024_review_v2.docx           (livrable pour la DA)
│   ├── outdoor_index.npy                     (matrice embeddings, Phase 1.4)
│   ├── outdoor_index_meta.jsonl              (metadata index)
│   ├── categories.jsonl                      (pré-classification 358 boards 2025)
│   ├── pr_extractions.jsonl                  (PR 2025 v1)
│   └── pr_with_rationale.jsonl               (PR 2025 v1 avec rationale)
│
├── scripts/                        ← runners (déplacés à la Phase 4 chantier 2)
│   ├── evaluate_board.py           (CLI évaluation single board)
│   ├── test_5_boards.py            (smoke test sur 5 boards eyeballées)
│   ├── classify_all.py             (pré-classification dataset 2025)
│   ├── extract_all_pr.py           (extraction PR 2025 — itération 1)
│   ├── generate_why_won.py         (rationale PR 2025 — itération 1)
│   ├── extract_2024_outdoor.py     (extraction Outdoor 2024)
│   ├── generate_outdoor_why_won.py (rationale Outdoor 2024)
│   ├── build_review_doc.py         (génération docx pour DA)
│   ├── build_outdoor_index.py      (Phase 1.4 — build embeddings)
│   ├── analyze_calibration.py      (analyse résultats calibration)
│   ├── run_calibration.py          (Phase 3 calibration runner)
│   └── test_search.py              (smoke test retrieval)
│
├── api/                            ← service FastAPI de référence
│   ├── main.py, routes.py, config.py, middleware.py
│   └── tests/
│
├── mini_frontend/                  ← UI de test (vanilla HTML/JS)
│   ├── index.html, style.css, app.js
│
├── tests/                          ← pytest smoke tests
│   ├── test_pipeline_smoke.py
│   └── test_api_smoke.py
│
├── data_internal/                  ← dev artefacts (gitignored)
│   └── calibration_results*.jsonl, eval_*.json, etc.
│
├── Dockerfile, docker-compose.yml  ← deployment
├── INTEGRATION.md                  ← guide pour intégrateurs front/back
└── README.md                       ← entrée du repo
```

---

## 8. Commandes utiles

```bash
# Pipeline complet Outdoor 2024 (à lancer dans l'ordre)
uv run python scripts/extract_2024_outdoor.py --workers 4         # ~9 min, ~$35
uv run python scripts/generate_outdoor_why_won.py --workers 4     # ~10 min, ~$25
uv run python scripts/build_outdoor_index.py                      # ~30 sec, ~$0.01
uv run python scripts/test_search.py                              # ~5 sec, gratuit

# Génération doc pour DA review
uv run python scripts/build_review_doc.py \
  --input data/outdoor_2024_with_rationale.jsonl \
  --output data/outdoor_2024_review.docx \
  --title "Mrs IArma · Outdoor Review"

# Resume / inspection
uv run python scripts/extract_2024_outdoor.py --summary           # stats sans relancer
uv run python scripts/generate_outdoor_why_won.py --summary       # stats sur les rationales
uv run python scripts/classify_all.py --summary-only              # distribution catégories

# Smoke test sur 5 boards seulement (avant scale)
uv run python scripts/extract_2024_outdoor.py --limit 5 --workers 4
```

---

## 9. État d'avancement & roadmap

### ✅ Terminé

- [x] Méthodologie LLM-judge + RAG définie
- [x] Schéma v3 d'extraction validé
- [x] Pipeline extraction + rationale + doc de review
- [x] Itération 1 sur PR 2025 (65 boards)
- [x] Itération 2 sur Outdoor 2024 (120 boards) avec corrections DA Strategy/Execution + score discrimination
- [x] Itération 3 avec 5 patterns de rigueur DA (validée par la DA)
- [x] **Phase 1.4 — Indexation vectorielle Voyage AI** : index `data/outdoor_index.npy` (120 × 1024 float32) construit, retrieval validé sur 7 queries
- [x] **Phase 2 — Moteur d'évaluation** : extract → RAG → multi-pass judge → malus → tier prédit. ~$0.90, ~45s par évaluation. Testé sur KitKat Phone Break 2025 GP.
- [x] **Phase 3 — Calibration** sur 10 boards (2 losers + 5 hold-out 2024 + 3 fresh 2025). Extension malus à 6 holdings (Publicis/Havas/Omnicom + WPP/IPG/Dentsu). Prompt judge renforcé avec calibration anchors 0-100 + native-to-category check.
- [x] **Phase 3.5 — Pivot binaire (medal vs no medal)** : refactor judge.py vers `tool_use` API (élimine JSON parse errors), output `MedalPrediction` (will_medal + P(medal) + confidence + synthesis 1-2 phrases). RAG enrichi 5 winners + 2 non-winners pour casser le biais "tout est medal". **Binary accuracy : 60% → 80%** (threshold 0.65). Gap P(No Medal) entre losers et medals : +0.16 (vs +0.08 avant).
- [x] **Phase 4 — Chantier 1 : couche présentation Mme Airma** : nouveau `TierPrediction` comme primary output (tier + score % + confidence + verdict oraculaire + 4 axes + 3 présages structurés + synthèse diagnostique). `MedalPrediction` conservé pour usage interne. Synthèse reformulée en **post-mortem diagnostique** (boards déjà soumises au jury 2026 → tips d'amélioration retirés, ton observationnel uniquement). Pondération Outdoor alignée sur entry kit (35/10/30/25).
- [x] **Phase 4.5 — Bascule langue de sortie : français → anglais oraculaire** : tous les outputs runtime (tier_label, axes labels, mystic_verdict, presages, synthesis) passés en anglais sous la marque "Mrs Airma · The Cannes Oracle". Em dashes (—) explicitement bannis du prompt synthèse (rendu trop « IA »). Renommage des champs `*_fr` → version sans suffixe (`AxisScoreFr` → `AxisScore`, etc.).
- [x] **Phase 5 — Extension à 30 catégories** : généralisation de la méthodologie Outdoor à 29 autres catégories Cannes Lions 2026. Pour chaque catégorie : (1) brief MECE auto-suffisant (`agent_briefs/categories/{SLUG}.md`), (2) module `{slug}_criteria.py` avec pondération d'axes spécifique au métier, (3) extraction des boards source via subagents Claude Code (subscription, $0 API), (4) génération des rationales why-it-won, (5) RAG index `{slug}_index.npy` + meta. Registre central dans `pipeline/category_registry.py` qui lazy-load les indexes. Calibration formelle limitée à Outdoor et PR ; les 28 autres catégories sont smoke-tested.
- [x] **Phase 5.5 — PDF natif** : support des PDF (cases studies multi-pages) via le content block `document` de l'API Claude. Magic header `%PDF-` détecté dans `pipeline/images.py`, helper `build_media_block()` dans `pipeline/client.py` aiguille vers `image` ou `document`. Pas de conversion préalable.
- [x] **Phase 6 — Frontend de référence** : React 18 + TypeScript + Vite 5 + Tailwind 3, design system « Mrs Airma · The Cannes Oracle » (SunRays motif, dropdown custom, 5-step wizard, mocks Playwright pour itération visuelle). Branding et copy en anglais, sans em dashes.

### ⏳ À venir
- [ ] **Dockerfile multi-stage** (build frontend → serve via FastAPI ou via Firebase Hosting + Cloud Run).
- [ ] **Mise à jour du dropdown frontend** pour exposer les 30 catégories.
- [ ] **Calibration formelle** étendue à d'autres catégories (priorité : Film, Design, Social, Innovation) si retour DA le demande.
- [ ] **Couche ML supervisée** au-dessus du LLM-judge (cf. § Phase 3.5) — différée tant que ~75-80% binaire suffit.

---

## 10. Annexes

### A. Schéma v3 d'extraction

Tous les champs sont définis dans `pipeline/schema.py` comme Pydantic models.

```jsonc
{
  "id": "adoptable-pedigree-colenso-bbdo-auckland",
  "tier": "Grand Prix",                        // ou Gold/Silver/Bronze/Shortlist/Loser
  "category": "Outdoor",
  "category_confidence": "high",
  "category_reasoning": "Sourced from 2024/OUTDOOR folder...",
  "file_path": "2024/OUTDOOR/GRAND PRIX/Adoptable - Pedigree...",

  "extracted": {                                // ce qui est EXPLICITEMENT visible
    "campaign": "Adoptable",
    "brand": "Pedigree",
    "agencies": [],                             // souvent vide (dans le filename, pas la board)
    "tagline": "...",
    "context": "...",                           // ou null
    "insight": "...",                           // ou null
    "idea": "...",                              // ou null
    "execution": ["...", "..."],                // bullets channels/mechanics
    "metrics": ["6x site visits", "50% adopted"],
    "press_coverage": ["Adweek", "...quote..."]
  },

  "inferred": {                                 // ce que le modèle infère depuis le visuel
    "context": null,                            // si extracted déjà rempli → null ici
    "insight": null,
    "idea": null,
    "one_liner": "Every Pedigree ad dog is a real shelter dog.",
    "creative_mechanisms": ["object-as-medium", "..."],
    "qualitative_summary": "..."                // résumé d'impact en 1-2 phrases
  },

  "visual": {
    "style_description": "...",
    "craft_quality": "high",                    // high|medium|low
    "dominant_colors": ["yellow", "white", "black"]
  },

  "impact_strength": "strong",                  // strong|moderate|qualitative_only|none
  "review_flag": false,
  "review_reasons": [],

  "why_it_won": {                               // ajouté par Phase 1.2
    "idea":      {"score": 95, "rationale": "..."},
    "strategy":  {"score": 92, "rationale": "..."},
    "execution": {"score": 93, "rationale": "..."},
    "impact":    {"score": 88, "rationale": "..."},
    "weighted_score": 92.3,
    "verdict": "Grand Prix because it doesn't just advertise adoption — it rebuilds the brand's entire media buy into an adoption product...",
    "tier_consistency": "expected"              // expected|below|above|n/a
  }
}
```

### B. Critères Outdoor (entry kit Cannes Lions 2026)

Source : `CL26_ENTRY_KIT_1.1.1_.pdf` page 16 — "The main criteria considered during judging will be the idea, the execution and the impact."

Notre adaptation 4-axes (cf. [`pipeline/outdoor_criteria.py`](pipeline/outdoor_criteria.py)) :

| Axe | Poids | Définition |
|---|---|---|
| Idea | 35% | Originalité + mémorabilité, native-to-outdoor |
| Strategy | 10% | (1) Qui est la marque + cohérence ; (2) Insights data-backed. PAS l'orchestration. |
| Execution | 30% | Craft + placement + orchestration + amplification + media-target fit. PAS la mission. |
| Impact | 25% | Reach, business, behaviour change, cultural footprint |

### C. Glossaire

- **Board** = digital presentation image, one-pager de 7063×5008 px qui résume une campagne Cannes. Document principal soumis au jury.
- **Tier** = niveau de prix (Grand Prix > Gold > Silver > Bronze). Shortlist = passé le premier screening jury sans médailler. Loser = pas passé le screening.
- **VLM** = Vision Language Model. Claude Opus 4.7 est un VLM (lit images + texte).
- **RAG** = Retrieval-Augmented Generation. Pattern : on récupère des références similaires dans une base avant de demander au LLM de juger.
- **Search document** = texte condensé par board, utilisé pour l'embedding et la recherche. Notre choix : `one_liner + mechanisms + idea + insight`.
- **Embedding** = vecteur 1024-dim qui représente sémantiquement un texte. Deux textes similaires → vecteurs proches.
- **Cosine similarity** = produit scalaire entre vecteurs unitaires, mesure la proximité sémantique (0-1).
- **Why-it-won** = analyse rétrospective qu'on génère pour chaque gagnante : pourquoi a-t-elle gagné ce tier précis, axe par axe.
- **Mental model DA** = Strategy = WHY (mission + insight), Execution = HOW (orchestration + média). Correction apportée en mai 2026.
- **Rigour patterns DA** = 5 vérifications de rigueur ajoutées au prompt après review DA (% sans base, sources non vérifiées, business outcome manquant, superlatifs, nuances culturelles).
