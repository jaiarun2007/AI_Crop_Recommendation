# Grand Finale Pitch Strategy (curated)

> Curation note: this file summarizes the *architecture and pitch-structure* content from the
> team's internal presentation-prep notes. It deliberately omits hyper-specific institutional
> claims from that source document (individual names, register numbers, funding figures, MoU
> partner names, lab equipment pricing) that could not be cross-verified against the team's other
> project documents and should not be presented to judges without independent confirmation.

## Production-Grade Microservices Tech Stack (as proposed)

| Microservice | Core Tech | Input Data | Target Outcome |
|---|---|---|---|
| auth | FastAPI, JWT, OAuth2 | Credentials | Identity verification, access tokens |
| user | FastAPI, PostgreSQL | Farmer profiles | Regional demographic management |
| farm | GeoDjango, PostgreSQL | Geospatial plot boundaries | GIS mapping of plots/soil profiles |
| crop-recommendation | Scikit-learn, FastAPI | NPK, pH, rainfall, temperature | Multi-class crop classification |
| cv/disease | PyTorch, KServe, TorchServe | Leaf images | YOLO-based lesion detection + remedies |
| yield | TensorFlow Serving, Triton | Multi-temporal agri data | Regression yield mapping |
| irrigation | Python, RESTful API | Weather + soil moisture | Execution charts, water volumes |
| fertilizer | FastAPI, NumPy | Soil Health Card metrics | Soil balance, dosing matrices |
| weather-intel | Python, OpenWeather API | Satellite/meteorology streams | Flood/drought/heatwave alerts |
| RAG assistant | Hugging Face, FastAPI | Vector-embedded agri policies | Natural-language farmer Q&A |

Serving runtimes: KServe/TorchServe for image models, Triton for tensor ops with dynamic
batching, TensorFlow Serving for regression graphs. Scaling via Kubernetes HPA on
CPU/memory/custom latency metrics.

## Alignment with Judging Criteria (general strategy, not institution-specific claims)

**Innovation & Technical Depth** — lead with the shift from a monolithic single-process
prototype to a decoupled microservices architecture with dedicated model-serving engines, and
the inclusion of a RAG-based multilingual assistant as a step beyond a typical chat interface.

**Social Impact & Scalability** — connect each service back to a concrete farmer pain point
(wrong crop choice, late disease detection, over-application of inputs), and describe how a
cloud-native design scales from a single-node prototype toward serving many farmers.

**Feasibility & Sustainability** — speak to whatever institutional backing, partnerships, and
commercialization pathway are *actually verified and current* at pitch time — do not repeat
unverified specifics from draft materials.

**Presentation & Clarity** — prioritize architectural specificity over buzzwords within the
strict 5-minute format.

## Suggested 5-Minute Pitch Structure

1. **0:00-1:00 — Problem Definition & Agricultural Bottlenecks.** Introduce the team; state the
   three core problems targeted (incorrect crop selection, delayed disease detection, excessive
   chemical application); contrast with the platform's unified approach.
2. **1:00-2:00 — Technological Evolution & Architecture Overview.** Briefly trace how the
   project moved from an early prototype to the current production-oriented architecture.
3. **2:00-4:00 — Production-Grade System Architecture / Live Demo.** Show the architecture
   diagram and/or a live demo of the working services (crop recommendation, disease screening,
   yield prediction, weather alerts, fertilizer/irrigation advice).
4. **4:00-5:00 — Feasibility & Roadmap.** Cover realistic next steps, current institutional
   support, and path to deployment/commercialization — using only verified facts.
5. **5:00-7:00 — Jury Q&A.**

## Risk Mitigation for the Live Demo
Bring a secondary backup (USB drive and/or cloud link) in case of connectivity issues during the
live demonstration, and pre-load media assets ahead of the presentation slot.
