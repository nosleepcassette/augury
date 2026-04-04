# Augury Depth Enhancement Specification
## Making Tarot Interpretations Actually Good

**Goal:** Transform Augury from template-based surface readings to rich, multi-layered, professional-quality interpretations.

---

## Problem: Current System is Too Shallow

**Current output:**
"The Fool means new beginnings"

**Needed output:**
"Position 1 (Current): The Fool here represents a new beginning emerging now. 
This is a Fire card in a Water-heavy spread, suggesting this new beginning is emotionally charged.
The Fool is adjacent to the Magician, creating tension: new start meets existing skill.
Overall: You're starting something new but your skills need to catch up. Confidence: 78%. Alternative: If this is about career vs relationship, these cards suggest..."

---

## Solution: 5-Layer Interpretation

Each reading generates interpretation through 5 layers:

**Layer 1 - Primary:** What the card means in its position
**Layer 2 - Secondary:** Elemental analysis (fire/water/air/earth balance)
**Layer 3 - Tertiary:** How cards relate to each other (combos, tension, harmony)
**Layer 4 - Cognitive:** How confident are we in this interpretation
**Layer 5 - Integration:** Overall narrative synthesizing all layers

---

## Implementation (Clean Code)

```python
# New data structures
@dataclass
class InterpretationLayer:
 layer: str # primary|secondary|tertiary|cognitive|integration
 interpretation: str
 confidence: float

@dataclass 
class ElementalAnalysis:
 fire: List[DrawnCard]
 water: List[DrawnCard]
 air: List[DrawnCard]
 earth: List[DrawnCard]
 dominant: str
 interpretation: str

# Core function (add to engine.py)
def generate_premium_interpretation(reading):
 return {
 'primary': _interpret_positions(reading),
 'secondary': _interpret_elements(reading),
 'tertiary': _interpret_relationships(reading),
 'cognitive': _interpret_confidence(reading),
 'integration': _interpret_overall(reading)
 }

# Card combinations - HIGH PRIORITY
def _interpret_relationships(reading):
 "When cards appear together, actually analyze them"
 for card1, card2 in adjacent_pairs(reading):
 if same_element(card1, card2):
 return f"{card1.element}+ {card2.element} = harmony strengthens"
 if opposing_elements(card1, card2):
 return f"{card1.element} vs {card2.element} = creates tension"
```

---

## Key Features to Build

### 1. Multi-Layer Output (MUST HAVE)
Every reading shows 5 distinct interpretation layers

### 2. Card Combinations (MUST HAVE)
When two cards appear together, analyze relationship.
Examples:
- Fool + Magician (both fire) = intensified fire energy
- Fool (fire) + Moon (water) = passion vs intuition, internal conflict
- Reversed + Upright = blocked vs flowing

### 3. Elemental Analysis (MUST HAVE)
Count and interpret Fire/Water/Air/Earth distribution
"This reading shows 4 Water cards (emotion focus) and 2 Fire (action focus)"

### 4. Card Symbolism Depth (MEDIUM)
Beyond basic meanings:
- Jungian archetypes (Fool = Puer Aeternus)
- Mythological references (Tower = Babel myth)
- Numerology (7 = introspection, 21 = completion)
- Cultural contexts

### 5. Temporal Markers (MEDIUM)
Extract timing: "This energy manifests in 2-4 weeks"

### 6. Confidence Scoring (MEDIUM)
Calculate confidence: "Confidence: 78%"

### 7. Alternative Perspectives (MEDIUM)
Generate 2-3 ways this could be interpreted based on life area:
"Career alternative: ..., Relationship alternative: ..."

---

## Output Format (Rich)

```
═══════════════════════════════════════
‖ Reading: Celtic Cross
╰─────────────────────────────────────

🎴 Position 1 - Current
├─ The Fool (Upright)
│
│ Primary: new beginning now
│
│ Secondary: Fire in Water-heavy = emotionally charged start
│
│ Tertiary: adjacent to Magician = tension (new vs skill)
│
│ Cognitive: Confidence 78%
│
[Positions 2-10 follow similar format]

╭─────────────────────────────────────
│ Integration: Overall narrative
╰─────────────────────────────────────

Alternative perspectives:
• Career: new role with skill gap
• Relationship: fresh start with challenges

Confidence: 78%
═══════════════════════════════════════
```

---

## Implementation Order

**Phase 1 (Weeks 1-3): Core Engine**
- Build layer generation
- Add element analysis
- Card combination detection

**Phase 2 (Weeks 4-6): Quality** 
- Add confidence scoring
- Add integration layer
- Build overall narrative

**Phase 3 (Weeks 7-9): Symbolism**
- Jungian archetypes
- Mythological references
- Temporal markers

**Phase 4 (Weeks 10-12): Output**
- Discord embeds
- Rich formatting
- Alternative perspectives

---

## Database Schema

```sql
CREATE TABLE reading_layers (
 id UUID PRIMARY KEY,
 reading_id UUID REFERENCES readings(id),
 layer_type TEXT, -- primary|secondary|tertiary|cognitive|integration
 interpretation TEXT NOT NULL,
 confidence DECIMAL(3,2)
);

CREATE TABLE card_combinations (
 id UUID PRIMARY KEY,
 reading_id UUID,
 cards TEXT[], -- ["fool", "magician"]
 relationship_type TEXT,
 interpretation TEXT
);
```

---

## Testing

**Quality Goals:**
- Words per reading: 80 → 500+
- Interpretation layers: 1 → 5
- Card combinations: 0 → 2-3 per reading
- Alternative perspectives: 0 → 2+ per reading
- Elemental/suit analysis: YES (detailed)
- Confidence scoring: YES (0-100%)

---

## File Location

**Location:** `~/dev/augury/docs/DEPTH_ENHANCEMENT_SPEC.md`
**Created:** 2026-04-04
**Size:** ~8KB (readable by you)

**Summary:** Make interpretations actually good by analyzing cards together, not separately.

---

## I Ching Integration Spec

**Goal:** Add full I Ching application as first-class sibling to tarot.

**Key Features:**
- Native inside Augury CLI/TUI
- Standalone `iching` launcher
- Three-coin casting method with yarrow-stalk probabilities
- Daily hexagrams by calendar date
- Command pattern: `augury iching cast --method coins --query "..."`

---

## Astrology Integration Spec

**Goal:** Integrate Astrolog bridge into Augury

**Two Modes:**
1. Wrapper mode: `augury astro natal`, `augury astro transits`
2. Reading-enrichment: `augury read --with-astrology` (adds context without replacing tarot)

**Shared Backend:**
- Uses existing Hermes Astrolog bridge at `/Users/maps/dev/astrolog/astrolog`
- Shared natal profile: `~/.hermes/astrolog/profile.json`

---

*Clean spec successfully written - this time to correct location in augury repo*
