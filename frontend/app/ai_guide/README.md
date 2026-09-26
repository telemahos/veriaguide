# AI Travel Guide (`/ai-guide`)

Wizard (dates, party, interests, budget, wishes, review) that retrieves matching WordPress listings and asks one OpenRouter model for a day-by-day itinerary. Also served under `/el/ai-guide` and `/de/ai-guide`. Off by default: every route returns 404 while the flag is off.

## Environment

| Variable | Default | Notes |
| --- | --- | --- |
| `AI_GUIDE_ENABLED` | `false` | `true` mounts the pages and shows the footer link |
| `OPENROUTER_API_KEY` | – | Required for generation; without it users see the retry page |
| `AI_GUIDE_MODEL` / `OPENROUTER_MODEL` | `google/gemini-2.5-flash` | First one set wins |
| `AI_GUIDE_MAX_VENUES` | `25` | Venues sent to the model (capped at 40) |
| `AI_GUIDE_MAX_TOKENS` | `2500` | Completion token cap |
| `AI_GUIDE_TIMEOUT` | `45` | Seconds per OpenRouter call (one retry) |
| `AI_GUIDE_RATE_LIMIT` | `5` | Generations per IP per hour |
| `AI_GUIDE_TTL_DAYS` | `14` | Itinerary lifetime |

Staging: set `AI_GUIDE_ENABLED=true` and `OPENROUTER_API_KEY`, restart.

## Storage

Redis (the existing `REDIS_URL` pool), no MySQL schema:

- `aiguide:sess:<id>`: wizard state, 2 h, referenced by the httponly `vg_aiguide` cookie
- `aiguide:it:<id>`: itinerary, venues and answers, `AI_GUIDE_TTL_DAYS`
- `aiguide:rate:<ip>`: hourly generation counter

If Redis is unreachable the process falls back to in-memory storage.

## Rules

Tours are never fetched or sent to the model. Model output is validated and any venue id not in the retrieved list is dropped. Map, email and PDF export are follow-ups; printing uses print CSS.
