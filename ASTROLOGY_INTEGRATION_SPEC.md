# Augury Astrology Integration Spec

## Goal

Integrate the local Astrolog bridge into Augury in two layers:

1. A full astrology wrapper mode so Augury can serve tarot and astrology from one CLI/TUI surface.
2. An astrology-aware tarot mode that uses natal and transit context to enrich readings without collapsing tarot into deterministic astrology.

## Shared Backend

Augury should not speak raw Astrolog flags. Reuse the Hermes bridge as the system of record:

- Backend binary: `/Users/maps/dev/astrolog/astrolog`
- Shared wrapper: `~/.hermes/skills/divination/astrolog/scripts/astrolog_bridge.py`
- Shared natal profile: `~/.hermes/astrolog/profile.json`
- Shared chart file: `~/.hermes/astrolog/natal.as`

If Augury needs tighter packaging later, factor the wrapper into a small standalone Python package that both Hermes and Augury import.

## Integration Modes

### 1. Wrapper Mode

Expose astrology directly through Augury commands:

```bash
augury astro profile set ...
augury astro profile show
augury astro natal
augury astro moment
augury astro transits
augury astro forecast --month 2026-04
```

This gives the user one divination shell while keeping tarot and astrology implementations separate internally.

### 2. Reading-Enrichment Mode

Allow tarot readings to incorporate astrology context:

```bash
augury read --spread three-card --with-astrology
augury read --spread celtic-cross --with-astrology --date 2026-04-15 --time 09:00
augury daily --with-astrology
```

Astrology should be additive, not replacing the tarot draw.

## Data Flow

### Wrapper Mode

1. Augury shells out to the Astrolog bridge with `--json`.
2. Augury renders the factual chart/transit data in its own formatter.
3. Optional narrative mode can synthesize across the astrology output afterward.

### Reading-Enrichment Mode

1. Draw tarot cards normally.
2. Query the astrology bridge for:
   - natal summary
   - current or requested transits
   - optional month forecast if the spread is timing-oriented
3. Build a combined payload:
   - `reading`
   - `drawn_cards`
   - `astrology.natal`
   - `astrology.transits`
   - `astrology.moment`
4. Render the reading with explicit section boundaries so the user can see what came from tarot and what came from astrology.

## Recommended Output Shape

```json
{
  "reading": {...},
  "drawn_cards": [...],
  "astrology": {
    "profile": {...},
    "natal": {...},
    "moment": {...},
    "transits": {...}
  }
}
```

This keeps Discord, TUI, and JSON automation aligned.

## TUI Opportunities

- Add an `Astrology` tab beside cards, spreads, and history.
- Let the user view:
  - saved natal chart
  - current sky
  - top transits now
  - month forecast
- In a reading detail view, add an `Astrology Context` panel that summarizes:
  - top 3 transits
  - dominant element/modality in the current sky
  - timing windows from the forecast

## Interpretation Strategy

Tarot should stay primary. Astrology context should answer:

- What background pressure or timing is active now?
- What natal themes amplify or complicate the draw?
- Are upcoming transits supportive, tense, clarifying, or destabilizing?

Keep these layers explicit:

1. Tarot symbolism and card positions
2. Natal predisposition
3. Current or future transit timing
4. Augury's synthesis

## MVP

1. Add `augury astro ...` wrapper commands that proxy the bridge.
2. Add `--with-astrology` to `read` and `daily`.
3. Store astrology payloads in reading history.
4. Render astrology blocks in CLI and Discord output.

## Phase Two

1. Add an astrology pane to the full-screen TUI.
2. Add cached summaries so repeated daily readings do not rerun the same astrology calls unnecessarily.
3. Add a prompt-style narrative mode that blends tarot and astrology into one larger analysis block while preserving the raw sections.

## Risks

- Birth-time ambiguity will contaminate house-based interpretation.
- Transit ranking in Astrolog is anchored to the saved natal chart's zone/location unless a separate event chart is computed.
- The combined output can become too dense. UI and formatter boundaries matter.

## Recommendation

Implement wrapper mode first. Once the shared astrology payload is stable, add tarot enrichment as a thin composition layer instead of duplicating astrology logic inside Augury.
