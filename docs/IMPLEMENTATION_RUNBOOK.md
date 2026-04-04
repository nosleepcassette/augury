# Augury Depth Features Implementation Runbook

**Status:** Planning Phase  
**Created:** 2026-04-04  
**Last Updated:** 2026-04-04  
**Priority:** High - Depth enhancement is key differentiator  
**Estimated Duration:** 12 weeks (4 phases)  
**Owner:** maps · cassette.help

---

## Context

Augury currently provides basic tarot readings with shallow interpretations. The depth enhancement specification (DEPTH_ENHANCEMENT_SPEC.md) outlines a transformation to 5-layer professional-quality interpretations.

---

## Scope

This runbook covers implementation of depth features in two areas:

1. **Internal Program:** Core augury engine, CLI, data structures, interpretation layers
2. **Skill Wrapper:** Hermes agent skill (`~/.hermes/skills/augury/`) for agentic interactions

---

## Phase 1: Core Engine Foundation (Weeks 1-3)

### Priority: CRITICAL ⭐⭐⭐

**Goal:** Build the core infrastructure for multi-layer interpretation

**Deliverables:**
- New data structures for 5-layer interpretation
- Layer generation engine functions
- Elemental analysis system
- Card combination detection
- Database schema migrations

**Tasks:**

**Week 1: Data Layer**
- [ ] Create `src/augury/models/interpretation.py` with InterpretationLayer dataclass
- [ ] Create `src/augury/models/elemental.py` with ElementalAnalysis dataclass
- [ ] Add `interpretation_layers` table to database schema
- [ ] Run migrations and verify schema
- [ ] Write unit tests for data models

**Week 2: Core Functions**
- [ ] Implement `_interpret_positions()` - primary layer
- [ ] Implement `_interpret_elements()` - secondary layer
- [ ] Write tests for position and element interpretation
- [ ] Integrate with existing reading flow

**Week 3: Card Relationships**
- [ ] Implement adjacent card detection in spreads
- [ ] Build element comparison logic (fire vs water, etc)
- [ ] Implement `_interpret_relationships()` - tertiary layer
- [ ] Create card combination interpretation patterns

**Acceptance Criteria:**
- All 5 interpretation layer functions exist and return structured data
- Elemental analysis correctly identifies dominant element
- Card combinations detect adjacent cards and opposites
- All code has >90% test coverage

---

## Phase 2: Quality & Confidence (Weeks 4-6)

### Priority: HIGH ⭐⭐

**Goal:** Add confidence scoring and quality metrics

**Deliverables:**
- Confidence calculation algorithm
- Quality scoring system
- Integration layer for overall narrative
- Discord embed support for multi-layer output

**Tasks:**

**Week 4: Confidence Algorithm**
- [ ] Design confidence scoring formula (position strength, element balance, combo clarity)
- [ ] Implement `_interpret_confidence()` - cognitive layer
- [ ] Create confidence calibration dataset
- [ ] Write tests to validate confidence scores prove out

**Week 5: Quality Framework**
- [ ] Add quality metrics tracking (words per reading, layer usage)
- [ ] Implement quality validation tests
- [ ] Create interpretation quality review command for testing

**Week 6: Integration Layer**
- [ ] Implement `_interpret_overall()` - integration layer
- [ ] Build narrative synthesis from all layers
- [ ] Test integration with real readings
- [ ] Verify 500+ words per reading achieved

**Acceptance Criteria:**
- Confidence scores appear for all readings (0-100%)
- Integration layer produces coherent overall narrative
- ABC test shows quality improvement: 80 → 500+ words per reading

---

## Phase 3: Symbolism & Depth (Weeks 7-9)

### Priority: MEDIUM ⭐

**Goal:** Add symbolic depth and cultural context

**Deliverables:**
- Jungian archetype mapping
- Mythological reference database
- Numerology integration
- Temporal marker extraction

**Tasks:**

**Week 7: Archetypes & Mythology**
- [ ] Compile Jungian archetype mappings (Fool → Puer Aeternus, etc)
- [ ] Build mythological reference database (Tower → Babel, Devil → Lucifer, etc)
- [ ] Add archetype/myth fields to card definitions
- [ ] Implement archetype interpretation injection into primary layer

**Week 8: Numerology & Symbolism**
- [ ] Build numerology meanings for Major Arcana (0-21) and pips
- [ ] Add numerology interpretation sub-layer
- [ ] Integrate symbolism depth scoring
- [ ] Test interpretation quality improvement

**Week 9: Temporal Markers**
- [ ] Implement temporal phrase extraction ("2-4 weeks", "next moon cycle")
- [ ] Build timing interpretation layer
- [ ] Add confidence weighting to temporal predictions
- [ ] Verify temporal accuracy with retrospective test

**Acceptance Criteria:**
- Archetype references appear in relevant readings
- Numerology adds meaningful depth (not just filler)
- Temporal markers correctly identify timing phrases
- Readings feel "deeper" and more culturally grounded

---

## Phase 4: Output & UX (Weeks 10-12)

### Priority: MEDIUM ⭐

**Goal:** Rich formatted output and alternative perspectives

**Deliverables:**
- Rich TTY/Discord output formatting
- Alternative perspective generation
- A/B testing framework for interpretations
- User feedback collection system

**Tasks:**

**Week 10: Rich Formatting**
- [ ] Implement Rich-based multi-layer output formatting
- [ ] Add Discord embed support with field structure
- [ ] Create formatting test suite for visual rendering
- [ ] Integrate with existing Discord bot

**Week 11: Alternative Perspectives**
- [ ] Build life area classifier (career, relationship, spiritual, etc)
- [ ] Implement alternative perspective generation (2-3 perspectives per reading)
- [ ] Add perspective tooltip/hover in output
- [ ] Test with real users for usefulness

**Week 12: Polish & Feedback**
- [ ] Add interpretation feedback collection (!good, !bad commands)
- [ ] Build A/B testing framework for interpretation variants
- [ ] Run qualitative user study on interpretation quality
- [ ] Refine based on feedback

**Acceptance Criteria:**
- Discord embeds show all 5 layers cleanly
- Alternative perspectives appear meaningful and distinct
- User feedback collection working
- NPS score shows improvement for interpretation quality

---

## Skill Wrapper Implementation (Hermes)

**Priority:** HIGH ⭐⭐

**Location:** `~/.hermes/skills/augury/` (new)

**Goal:** Enable agentic interactions with Augury

**Features:**
- Agent can query readings
- Agent can request specific layer depth
- Agent can extract interpretations for reports
- Agent can batch process readings

**Implementation Order:**

**Week 2-3: Basic Wrapper**
- [ ] Create augury skill directory and SKILL.md
- [ ] Implement `augury_read_wrapper()` calling augury CLI
- [ ] Add layer selection parameter (e.g., `--layers primary,cognitive`)
- [ ] Parse JSON output from augury

**Week 5-6: Advanced Features**
- [ ] Implement batch reading processing
- [ ] Add interpretation extraction for reports
- [ ] Build confidence score filtering
- [ ] Add quality metrics tracking

**Week 9-10: Integration**
- [ ] Integrate with agent workflows (Claude, Codex, Opencode)
- [ ] Add to agent preloaded_skills lists
- [ ] Create example agentic workflows
- [ ] Document agent-augury interaction patterns

---

## Technical Architecture

### Database Changes

**New Tables:**
```sql
reading_layers - stores each interpretation layer
card_combinations - stores detected card relationships
elemental_analyses - stores element distribution per reading
reading_quality - stores quality metrics
interpretation_feedback - stores user feedback
```

### New Files

**Models:**
- `src/augury/models/interpretation.py`
- `src/augury/models/elemental.py`
- `src/augury/models/quality.py`

**Engine:**
- `src/augury/engine/depth.py` - core layer generation
- `src/augury/engine/combinations.py` - card relationships
- `src/augury/engine/confidence.py` - confidence scoring

**CLI:**
- `src/augury/cli/depth.py` - depth commands
- Updates to `src/augury/cli/main.py` for layer flags

**Herms Skill:**
- `~/.hermes/skills/auguary/SKILL.md`
- `~/.hermes/skills/auguary/wrapper.py`

---

## Quality Metrics

**Baseline (Current State):**
- Avg words per reading: ~80
- Layers per reading: 1 (basic)
- Card combinations: 0
- Confidence score: N/A
- User satisfaction: Unknown

**Target (Phase 4 Complete):**
- Avg words per reading: 500+
- Layers per reading: 5 (all layers)
- Card combinations: 2-3 per reading
- Confidence score: 0-100% range
- User satisfaction: 4+ NPS

**Measurement:**
- Weekly quality audit of 10 random readings
- Compare layer usage (which layers used most/least)
- Track confidence score distribution
- A/B test variants for unclear interpretations

---

## Risk Management

**Risks & Mitigations:**

1. **Complexity Overload**
   - *Risk:* Users find 5 layers overwhelming
   - *Mitigation:* Default to 2-3 layers, allow `--full-depth` flag for power users

2. **Confidence Miscalibration**
   - *Risk:* System is overconfident or underconfident
   - *Mitigation:* Retrospective validation every 2 weeks, adjust scoring formula

3. **Performance Degradation**
   - *Risk:* Layer generation makes readings slower
   - *Mitigation:* Batch processing, caching common patterns, optimize queries

4. **User Confusion**
   - *Risk:* New format breaks existing scripts/workflows
   - *Mitigation:* Maintain backward compatibility, add version flags, clear migration path

**Rollback Plan:**
- Keep old interpretation path accessible via `--legacy` flag
- Database migrations are reversible
- Version 1.x maintains old behavior

---

## Success Criteria

**Phase 1 Complete When:**
- All 5 layer functions exist and pass tests
- Elemental analysis runs without errors
- CI passes with >90% coverage
- Code review approved

**Phase 2 Complete When:**
- Confidence scores appear in all readings
- Integration synthesis reads coherently
- Quality metrics show improvement from 80 → 500+ words

**Phase 3 Complete When:**
- Archetype/mythology references appear in readings
- Numerology adds meaningful depth
- Temporal markers extract timing correctly

**Phase 4 Complete When:**
- Discord embeds display multi-layer output cleanly
- Alternative perspectives appear (2-3 per reading)
- User feedback collection is deployed
- NPS score improvement measured

**Project Complete When:**
- Skill wrapper is in Hermes preloaded_skills (Cassette & Wizard)
- Augury depth features launched in production
- User satisfaction data shows improvement
- Documentation is complete and accessible

---

## Dependencies & Blockers

**External Dependencies:**
- [ ] Database migration approval (maps)
- [ ] Discord bot webhook configuration (if needed)
- [ ] Test environment setup for integration testing

**Internal Blockers:**
- Card element data must be complete (check: /Users/maps/dev/augury/src/augury/data/)
- Astrolog integration requires Astrolog binary available
- I Ching requires yarrow-probability coin method implementation

---

## Timeline & Milestones

**Week 3 Milestone:** Phase 1 Complete - Core engine running
**Week 6 Milestone:** Phase 2 Complete - Confidence and quality
**Week 9 Milestone:** Phase 3 Complete - Symbolism and depth
**Week 12 Milestone:** Phase 4 Complete - UX and polish
**Week 13:** Production launch & skill wrapper deployment

---

## Documentation Checklist

- [x] DEPTH_ENHANCEMENT_SPEC.md created
- [ ] ICHING_INTEGRATION_SPEC.md (create separate spec)
- [ ] ASTROLOGY_INTEGRATION_SPEC.md (create separate spec)
- [ ] Implementation runbook (IN PROGRESS - this document)
- [ ] Developer setup guide
- [ ] API documentation
- [ ] User guide for interpretation layers
- [ ] Agent usage examples
- [ ] Quality metrics dashboard

---

## Resource Allocation

**Estimated Effort:**
- Core engine: ~80 hours (weeks 1-9)
- Discord/TUI improvements: ~20 hours (week 10-12)
- Skill wrapper: ~16 hours (weeks 2-10)
- Testing & QA: ~20 hours (ongoing)
- Documentation: ~12 hours (ongoing)

**Total:** ~148 hours (approx 6 weeks at standard pace or 12 weeks with other projects)

**Skills Needed:**
- Python dataclasses and type hints
- Database migrations (Alembic/SQLAlchemy)
- Rich text formatting
- Discord API/embeds
- Hermes skill development
- YAML configuration
- Git workflow
- Testing (pytest)

---

## Next Steps

**Immediate Actions:**
1. **Authorization required** - Review runbook and approve scope
2. Create ICHING_INTEGRATION_SPEC.md (priority: medium)
3. Create ASTROLOGY_INTEGRATION_SPEC.md (priority: medium)
4. Set up development branch for depth features
5. Begin Phase 1 implementation

**Awaiting:**
- Feedback on priority ordering
- Authorization to proceed with Phase 1
- Confirmation of resource allocation
- Decision on skill wrapper timeline

---

## Questions for Review

**For maps:**
1. Priority confirmation: Does the 4-phase ordering make sense? Should anything be reordered?
2. Feature cut: Any layers or features you'd cut to ship faster?
3. Skill wrapper: Same timeline or decouple?
4. Quality metrics: Any specific thresholds you care about most?
5. Astrology/I Ching: Should those specs be separate priorities from depth?

---

**Document Status:** DRAFT - Ready for review and authorization before implementation begins.

---

*Runbook created: 2026-04-04*  
*Location: ~/dev/augury/docs/IMPLEMENTATION_RUNBOOK.md*