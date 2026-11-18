# Krishi Mitra — SoilGrids-powered RAG chatbot

A location-aware agricultural assistant inside CropSense AI. For every question it
combines **(1) soil properties for the user's location from ISRIC SoilGrids**,
**(2) the user's latest CropSense analysis** and **(3) passages retrieved from an
agricultural knowledge base**, then asks an LLM to answer *only* from that evidence,
in the user's language, by text and voice.

## Architecture

```
Browser (ChatWidget)                FastAPI (backend/chat.py)
  location: analysis / GPS / search ──► POST /chat/location ──► backend/soilgrids  ──► rest.isric.org (beta)
  question (text or voice)  ────────► POST /chat           ──► backend/rag/pipeline
                                                                  │ 1 retrieval queries (message + soil facts + conversation)
                                                                  │ 2 session soil data (memory.py)
                                                                  │ 3 FAISS semantic search (retriever.py)
                                                                  │ 4 prompt = soil + app analysis + excerpts K1..Kn + history
                                                                  │ 5 LLM (llm.py: Gemini | Claude | offline), structured JSON
                                                                  └ 6 citations validated, memory updated
  reply + crop cards + sources + soil card ◄──────────────────────┘
  voice reply ◄── POST /chat/tts (gTTS)
```

| Module | Responsibility |
|---|---|
| `backend/soilgrids/` | SoilGrids REST client (batching, timeouts, retry + backoff, fair-use rate limit), response validation, unit conversion, texture/pH/OC interpretation, JSON cache. **Independent of the chatbot.** |
| `backend/rag/knowledge_base/` | 11 Markdown documents: SoilGrids properties, texture & pH, Indian soil types, crop requirements (cereals/millets, pulses/oilseeds, commercial/horticulture/plantation), fertilizer management, irrigation, soil improvement, seasons, soil testing. |
| `backend/rag/ingest.py` | Load → chunk (Markdown headers + recursive splitter, LangChain) → embed (Sentence Transformers `intfloat/multilingual-e5-small`) → FAISS, persisted in `backend/rag/index/`, rebuilt automatically when documents change. |
| `backend/rag/retriever.py` | Two semantic searches (raw question + soil/conversation-enriched query), merged and filtered by similarity. |
| `backend/rag/memory.py` | Session memory: location, SoilGrids profile, analysis, last 8 turns, last crops, last sources (3 h TTL). |
| `backend/rag/prompts.py` | Grounding rules and evidence blocks. |
| `backend/rag/llm.py` | Configurable provider with one structured-output schema. |
| `backend/rag/pipeline.py` | Orchestrates one turn; offline (no-AI) evidence mode. |
| `frontend/src/chat/ChatWidget.js` | Chat UI: location bar, soil card, suggestions, crop cards, sources, voice in/out. |

## What SoilGrids does and does not provide

Fetched for 0-5, 5-15 and 15-30 cm (mean, median, 5 %/95 % quantiles, uncertainty):
`phh2o, clay, sand, silt, nitrogen (total), soc, cec, bdod, cfvo`. Values are converted
with the `d_factor` returned by the API; original units are kept.

**Not available from SoilGrids** (the chatbot says so and recommends a soil test):
available P and K, plant-available N / NPK status, micronutrients, EC/salinity/ESP,
soil moisture, and any field-specific measurement.

## Reliability

Two official ISRIC access methods are used, in this order (`SOILGRIDS_ACCESS_ORDER=wcs,rest`):

1. **WCS (maps.isric.org)** — small GeoTIFF windows (±0.02°) per property/depth/statistic (mean, Q0.05, Q0.95),
   decoded with Pillow, ~5–12 s for all 9 properties. If the exact point is unmapped (urban, water, rock), the
   nearest mapped 250 m cell inside the window is used and its distance is shown to the user and the LLM.
   Values match the REST API (pH 6.2 at the Belagavi test point) within one cell of resampling.
2. **REST API (rest.isric.org)** — beta service; it was completely unreachable for long periods during development.
   After a total failure it is skipped for 10 minutes.

For the REST path the client:

- fetches 3 properties per request and splits a failing batch into single properties;
- uses a 25 s per-request timeout, 2 retries with exponential backoff + jitter, and a 60 s overall budget;
- limits itself to 5 requests/minute (ISRIC fair use);
- validates every response (layers, `d_factor`);
- caches successful profiles for 30 days (partial 1 h, no-data 1 day) in `backend/data/soilgrids_cache.json`;
- returns status `ok`, `partial` (lists missing properties), `no_data` (urban/water pixel) or `unavailable`.
  With `unavailable` **no soil values exist in the profile**, so nothing can be fabricated; the chatbot says
  soil data could not be retrieved and answers generally.

The retrieval layer is a plain function (`fetch_json`) so another official access method
(e.g. WCS / GeoTIFF download) can replace the REST transport without touching the rest.

## Setup

```bash
# from the project root, inside the virtual environment
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
cp .env.example backend/.env        # then edit backend/.env
python -m backend.rag.ingest        # optional: build the vector index now (first run downloads ~470 MB model)
uvicorn backend.main:app --reload --port 8000
cd frontend && npm start
```

### Choosing the LLM (`backend/.env`)

| Setting | Cost | Notes |
|---|---|---|
| `GEMINI_API_KEY=...` (default when set) | Free tier | Key from https://aistudio.google.com/apikey. Rate-limited; free-tier data may be used by Google. Set `GEMINI_MODEL` if the default alias changes. |
| `ANTHROPIC_API_KEY=...` | Paid | Claude Opus 5.5 with server-side refusal fallback. |
| neither (`offline`) | Free | No generation: shows the soil summary and retrieved excerpts (English). |

Restart the backend after editing `.env`.

## API

| Endpoint | Body | Returns |
|---|---|---|
| `POST /chat/location` | `{session_id, location:{lat,lon,name}, refresh}` | soil summary |
| `POST /chat` | `{session_id, message, ui_language, context?, location?, refresh_soil?}` | `reply, language, crops[], sources[], soil, provider, retrieved[]` |
| `POST /chat/reset` | `{session_id}` | clears memory |
| `GET /chat/status` | – | provider, index readiness |
| `POST /chat/tts` | `{text, language}` | MP3 |

## Testing

```bash
python -m pytest tests/test_rag_chatbot.py -v          # 21 offline tests (no network, no API key)
python -m pytest tests/test_rag_chatbot.py -v -m live  # + real SoilGrids call
```

The offline suite runs the whole pipeline on a SoilGrids-format fixture
(`tests/fixtures/soilgrids_sample.json`; pH and clay 0-5 cm are real values for Belagavi,
the rest illustrative) with a stubbed LLM, and checks:

- unit conversion, uncertainty, texture class, unavailable-parameter list;
- batching, partial failures, outages (no values, nothing cached), no-data points, cache and refresh;
- retrieval relevance in English, Hindi and Kannada;
- that the prompt sent to the LLM contains both the soil data and the retrieved excerpts;
- multi-turn memory (follow-ups keep soil context; location change refreshes soil);
- that unavailable soil produces no numeric values, district NPK is labelled as reference data, invalid citations are dropped.

### Manual checks in the app

1. Open the chatbot → *Use my location* or *Search place* → soil card appears (or a clear unavailable/no-data message).
2. Ask: "Which crops can I grow here?" → crop cards with reasons and sources.
3. Follow up: "Why did you recommend this crop?", "What fertilizer should I use?", "Can I grow tomatoes?" (no location prompt again).
4. Ask "What is my soil potassium?" → it must say SoilGrids does not provide it and suggest a soil test.

## Limitations

- SoilGrids values are 250 m model predictions with sometimes wide uncertainty; a soil test is better.
- The knowledge base is general guidance compiled from widely published Indian/FAO sources; extend it by
  adding Markdown files to `backend/rag/knowledge_base/` (the index rebuilds automatically).
- Session memory is in-process (lost on backend restart); use Redis or a database for multi-server deployments.
- Odia voice output depends on a browser voice; voice input needs Chrome or Edge.
