# Augury Monetization Specification
## Enhancing Tarot Interpretation for Professional Client Use

**Author:** Wizard | **Date:** 2026-04-04 | **Version:** 1.0
**Status:** Ready for Development | **Audience:** Claude

---

## Executive Summary

Augury is moving from personal divination tool to monetized professional tarot interpretation platform. This specification outlines enhancements needed to deliver richer, deeper, more meaningful interpretations that justify paying clients.

**Current State:**
- Template-based interpretations (single sentences per card)
- Local history only
- No user profiles
- No analytics
- No premium features

**Target State:**
- Multi-layered interpretation engine
- Client profiles and reading relationships
- Premium depth levels
- Professional output formats
- Data-driven insights
- Monetization-ready features

---

## Current System Analysis

### Working Components
- ✅ 78-card Rider-Waite deck with full symbolism
- ✅ CLI commands (draw, daily, card lookup)
- ✅ Reading history storage
- ✅ JSON output for automation
- ✅ Discord formatter integration
- ✅ I Ching combined readings
- ✅ ASCII art generation for cards

### Limitations for Monetization
- Template-based outputs (low value)
- Single sentence interpretations
- No card combination analysis
- No user context tracking
- No relationship between readings
- No premium depth levels
- No professional export formats
- No client management features
- No cross-reading patterns
- No life theme identification

---

## Monetization Strategy Overview

### B2C Model (Individual Clients)
**Tier Structure:**
- **Free ($0):** Daily single card, basic spreads (3-card only)
- **Basic ($9.99/mo):** All spreads, history (30 days), standard depth
- **Professional ($24.99/mo):** PDF exports, custom spreads, deep depth
- **Premium ($49.99/mo):** Pattern analysis, partner readings, full analytics
- **Diamond ($99.99/mo):** Unlimited readings, API access, white-label exports

**Per-Reading Credits:**
- Surface: $2 (2-3 sentences)
- Standard: $5 (position analysis)
- Deep: $15 (narrative arc + patterns)
- Comprehensive: $30 (extended + action steps)

**Premium Add-ons:**
- Partner reading: +$10
- Yearly life summary: +$25
- Custom spread design: +$15
- Career guidance spread: +$20

### B2B Model (Practitioners)
- **Practitioner License: $99/mo** - All features, up to 50 clients
- **API Access: $0.10 per reading + bulk pricing**
- **White-label Platform: $500/mo + $2k setup**

---

## Core Monetization Features

### 1. Premium Interpretation Engine
**Multi-Layer Card Analysis:**
- Position meaning (where card appears)
- Arcana layer (Major vs Minor significance)
- Suit element (fire/water/air/earth)
- Number symbolism (1-21 meanings)
- Reversed state analysis
- **MUST:** Confidence scoring (0-100%) for each layer

**Card Combination Recognition:**
- Adjacent card relationships (proximity effects)
- Elemental interactions (fire + water = steam/conflict)
- Mirror patterns (cards reflecting each other)
- Numerological connections (sum of numbers)
- **MUST:** Store combination indices in database for pattern matching

**Narrative Arc Building:**
- Story arc across positions
- Tension → climax → resolution mapping
- Character development for Major Arcana
- **MUST:** Generate 200+ word narratives per position (not templates)

**Probability/Likelihood Assessments:**
- Confidence intervals on predictions (e.g., "75% likelihood within 3 months")
- Temporal markers (timing indicators from card elements)
- Alternative outcome branches

**Technical Implementation:**
```python
# New class: PremiumInterpreter
class PremiumInterpreter:
    def interpret_position(self, card: Card, position: Position) -> Interpretation:
        return {
            "text": generate_narrative(card, position),
            "confidence": calculate_confidence(card, position),
            "timelines": extract_temporal_markers(card, position),
            "archetypes": map_archetypes(card),
            "relationships": find_relationships(card, position, reading_context)
        }
```

### 2. Client Profile System
**User Account Management:**
- Email/password login
- OAuth integration (Google, Apple ID)
- Profile photos, preferences
- **MUST:** Link readings to user_id in database

**Reading History with Tagging:**
- Question categories (career, love, personal, financial)
- Life areas tagged (relationships, work, health, spirituality)
- Emotional state logging (optional, 1-10 scale)
- **MUST:** Enable cross-reading queries by tag

**Preference Tracking:**
- Favorite spreads per life area
- Preferred card decks (allows custom decks for monetization)
- Reading frequency patterns
- **MUST:** Privacy controls for what data is collected

**Relationship Context:**
- Partner profile linking (with consent)
- Family relationship tracking
- **MUST:** Ethical guidelines for relationship readings

**Database Schema:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE,
    subscription_tier TEXT,  -- 'free', 'basic', 'pro', 'premium', 'diamond'
    created_at TIMESTAMP,
    preferences JSONB
);

CREATE TABLE readings (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    query TEXT,
    tags TEXT[],  -- ['career', 'relationship', 'decision']
    spread_name TEXT,
    depth_level TEXT,  -- 'surface', 'standard', 'deep', 'comprehensive'
    created_at TIMESTAMP,
    interpretation JSONB
);
```

### 3. Reading Relationships & Patterns
**Comparative Analysis Across Time:**
- Week-over-week card strength tracking
- Month-over-month theme evolution
- Suit/element balance trends
- Reversed card frequency patterns
- **MUST:** Graph visualizations for premium tier

**Theme Identification:**
- Life area focus tracking (career appears in 60% of readings = pattern)
- Repeating symbols across readings
- Archetype emergence (e.g., "you're in a Tower phase")
- **MUST:** Alert users to patterns ("3rd work-related reading this month")

**Pattern Matching Across Life Areas:**
- Career vs Relationship reading comparison
- Personal growth trajectory
- Challenge/solution cycle identification
- **MUST:** Probability calculations for pattern continuation

**I Ching Narrative Tracking:**
- Hexagram sequence evolution (changing lines over time)
- Primary/secondary hexagram relationships
- Line change frequency analysis

**Database Schema:**
```sql
CREATE TABLE reading_patterns (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    pattern_type TEXT,  -- 'career_focus', 'relationship_recurrence', 'tower_phase'
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    confidence DECIMAL(3,2),  -- 0.00 to 1.00
    description TEXT
);
```

### 4. Premium Spread Designer
**Professional Spread Templates:**
- Relationship dynamics spread (7 positions: past, present, future, obstacle, advice, outcome, lesson)
- Career decision spread (6 positions: current state, hidden factors, visible opportunities, challenge, advice, potential outcome)
- Lost item recovery spread (5 positions: last seen, current location, obstacles, help needed, retrieval method)
- New vs. familiar choices spread (4 positions: old path, new path, what's common, advice)

**Custom Spread Designer:**
- Drag-and-drop position editor
- Position meaning editor
- Spread preview functionality
- Test readings for new spreads
- Share to community marketplace (revenue split: creator 70%, platform 30%)

**Visual Editor:**
- Position arrangement (triangle, cross, circle, custom)
- Position labeling
- Spread thumbnail generation

### 5. Professional Output Formats
**Branded PDF Exports:**
- PDF with embedded fonts (Adobe Fonts licensing for professional typography)
- Card positions with full-page card images (high-res scans)
- Page-per-card detail (card image full page, interpretation on facing page)
- **MUST:** Watermarking with practitioner branding

**Formatted Email Reports:**
- HTML email template (responsive design)
- Card thumbnail grid + interpretations
- Pattern highlights section
- Recommended follow-up actions

**Printable Summaries:**
- Two-page summary (overview on page 1, card details on page 2)
- One-page condensed (for desk reference)
- One-page per card (for card-of-the-day)

**Audio Narration:**
- Text-to-speech generation (ElevenLabs API integration for realistic voice)
- MP3 download per reading
- Tiered voices (standard, premium, celebrity-licensed)

**Multi-page Detailed Reports:**
- Table of contents
- Executive summary
- Position-by-position deep dive
- Pattern analysis section
- Appendix with card database references

### 6. Export & Sharing Capabilities
**Data Exports:**
- JSON export for API consumers
- CSV for spreadsheet analysis (suit counts, position frequencies)
- LaTeX for typesetting publications
- **MUST:** Spec compliance (OpenAI function format for AI interoperability)

**White-Label Embeddables:**
- iframe widget for websites
- WordPress plugin
- Squarespace/OAuth integrations (if applicable)
- React/Vue components for SPAs

**Sharing Features:**
- Expiring links (24h for free tier, unlimited for paid)
- Password-protected readings (premium)
- Revoke access functionality
- View analytics (premium: see who opened)

### 7. Client Dashboard Portal
**Reading History Timeline:**
- Chronological scroll
- Filter by date, spread type, life area
- Star/favorite system
- Search by query text

**Analytics Dashboard:**
- Card frequency heatmap
- Element balance pie chart
- Reading frequency graph
- Pattern timeline

**Subscription Management:**
- Upgrade/downgrade
- Payment method management
- Usage stats (how many readings remaining)
- Cancel/pause subscription

### 8. Advanced Analytics for Clients
**Suit & Element Tracking:**
- Fire/water/air/earth balance over time
- Major Arcana concentration
- Court card frequency (personality indicators)
- Suit strength per quarter

**Prediction Accuracy:**
- User can rate readings 1-10 on accuracy
- Learning system adjusts interpretation weights
- Confidence scoring refinement
- **MUST:** Privacy-preserving (aggregated only)

**Goal Tracking:**
- User states goals
- Reading alignment with goals
- Progress markers
- **MUST:** Encrypted storage for sensitive goals

### 9. API & Integration Features
**REST API Endpoints:**
```
POST /api/v1/readings - Create reading
GET  /api/v1/readings/{id} - Get reading
GET  /api/v1/users/{id}/readings - User history
GET  /api/v1/patterns - User patterns
```

**Authentication:**
- API keys per user
- Rate limiting (100/month free, 1000/month pro, unlimited enterprise)
- OAuth 2.0 for third-party integrations

**Third-Party Integrations:**
- Calendar sync (Google Calendar) - schedule reading follow-ups (take note: calendar replaces iCalendar)
- Zapier (connect to 5000+ apps)
- Webflow/Shopify embed
- CRM integrations (HubSpot, Salesforce)
- Notion database sync (if applicable)

### 10. Client Tiering System
**Feature Matrix:**
```
Feature                Free   Basic  Pro    Premium Diamond
├─ Daily single card   ✓      ✓      ✓      ✓       ✓
├─ 3-card spread         ✓      ✓      ✓      ✓       ✓
├─ Celtic cross          ✗      ✓      ✓      ✓       ✓
├─ Custom spreads        ✗      ✗      ✓      ✓       ✓
├─ PDF exports           ✗      ✗      ✓      ✓       ✓
├─ Pattern analysis      ✗      ✗      ✗      ✓       ✓
├─ Partner readings      ✗      ✗      ✗      ✓       ✓
├─ API access            ✗      ✗      ✗      ✗       ✓
└─ White-label           ✗      ✗      ✗      ✗       ✓
```

**Database Enforcement:**
```sql
CREATE FUNCTION check_reading_limit(user_id UUID) RETURNS BOOLEAN AS $$
DECLARE
    tier TEXT;
    reading_count INTEGER;
BEGIN
    SELECT subscription_tier INTO tier FROM users WHERE id = user_id;
    SELECT COUNT(*) INTO reading_count FROM readings 
    WHERE user_id = user_id AND created_at >= DATE_TRUNC('month', NOW());
    
    RETURN CASE tier
        WHEN 'diamond' THEN TRUE -- Unlimited
        WHEN 'premium' THEN reading_count < 50
        WHEN 'pro' THEN reading_count < 20
        WHEN 'basic' THEN reading_count < 5
        ELSE FALSE -- Free: no readings
    END;
END;
$$ LANGUAGE plpgsql;
```

### 11. Reading Depth Levels
**Surface Level: $2**
- 2-3 sentence interpretation per card
- Basic position meaning
- Quick summary of reading
- **For:** Daily draws, quick questions, freemium

**Standard Level: $5**
- Position-by-position analysis (3-4 sentences each)
- Suit/element balance summary
- Reading synthesis (2-3 paragraphs)
- **For:** One-time questions, standard consultations

**Deep Level: $15**
- Full narrative arc (10+ sentences per card)
- Card combination recognition
- Pattern analysis
- Theme exploration
- Confidence scoring for predictions
- **For:** Important life decisions, monthly readings

**Comprehensive Level: $30**
- Everything from Deep level
- **Plus:**
    - Action steps with timelines (steps 1-3 with 1-month, 3-month, 6-month frames)
    - Alternative outcome branches
    - Follow-up spread recommendations
    - Quarterly re-read suggestion
- **For:** Yearly planning, major life crossroads

**Delivery Format per Level:**
- Surface: Text only
- Standard: Text with ASCII art
- Deep: Text with full card images
- Comprehensive: PDF with images + audio narration

### 12. Symbolism & Archetype Engine
**Jungian Archetype Mapping:**
- Major Arcana → Jungian archetypes
    - The Fool → Puer Aeternus
    - The High Priestess → Anima
    - The Emperor → Father Archetype
    - The Magician → Trickster/Psychopomp

**Elemental Impact Analysis:**
- Fire cards: Career/passion indicators
- Water cards: Emotion/family emphasis
- Air cards: Communication/thought themes
- Earth cards: Finance/physical matters

**Number Symbolism Depth:**
- Beyond 0-21 (include numerological system breakdown)
- Repeating number significance
- Life path correlations

**Seasonal/Timing Correlations:**
- Suit timing: Wands (action phase), Pentacles (manifestation phase)
- Arcana timing: Cups (spring emotions), Swords (conflict periods)
- **MUST:** Offer "likely timeline for manifestation: 2-4 weeks" etc.

### 13. Question Refinement System
**Query Clarification:**
- "You're asking about career. Is this about:
    - a. Job transition
    - b. Promotion opportunity
    - c. Skill development
    - d. Starting a business
    e. Work/life balance?"

**Life Area Identification:**
- Card choice reveals life area focus
- Not "What should I know?" → "What about [career] do you want to explore?"

**Goal vs Obstacle Distinction:**
- "Is this reading to identify obstacles or clarify goals?"
- Affects interpretation focus (challenge focus vs outcome focus)

**Frequency Recommendations:**
- Daily: Single card
- Weekly: 3-card spread
- Monthly: Celtic cross
- Quarterly: Custom overview spread
- Yearly: Comprehensive deep reading

### 14. Monetization Features for Operators
**Analytics Dashboard:**
- Revenue per reading type
- Lifetime client value
- Subscription churn rate
- Reading abandonment rate
- Premium feature usage

**Operational Metrics:**
- Average reading time per depth level
- Client engagement trends
- Premium feature adoption rate
- Month-over-month growth

**Marketing Insights:**
- Most popular spreads per tier
- Client lifetime value by acquisition channel
- Seasonal reading trends (holidays = peaks)
- Retention by life area questioned

### 15. Collaborative Features
**Multiple Practitioner Support:**
- Agency/practice accounts
- Shared client access (with consent)
- Reading notes (practitioner can add private/assistant notes)
- Supervised readings (mentor reviews apprentice)

**Second Opinion Requests:**
- Client can request second practitioner review
- Original practitioner notified
- Comparative interpretations provided

---

## Monetization Implementation Strategy

**Phase 1: Premium Engine (Weeks 1-4)**
- Build deep interpretation engine
- Implement multi-layer card analysis
- Create narrative generation system
- **Goal:** Professional-quality interpretations

**Phase 2: Client System (Weeks 5-8)**
- User authentication
- Reading history with tagging
- API endpoints
- **Goal:** User account infrastructure

**Phase 3: Database & Analytics (Weeks 9-12)**
- PostgreSQL integration
- Pattern recognition system
- Analytics dashboard
- **Goal:** Data-driven insights

**Phase 4: Premium Features (Weeks 13-16)**
- PDF generation
- Custom spread designer
- Audio narration
- **Goal:** Professional outputs

**Phase 5: Monetization Layer (Weeks 17-20)**
- Subscription management
- Tier enforcement
- Stripe integration
- **Goal:** Ready for client billing

---

## Technical Architecture Requirements

**Backend:**
- Python 3.10+
- PostgreSQL 14+
- Redis (for caching premium interpretations)
- FastAPI for API layer
- Alembic for migrations

**Frontend:**
- React or Vue for dashboard
- Chart.js for visualizations

**Infrastructure:**
- Docker containers
- Stripe API integration
- Cloud storage (S3) for PDFs/audio

---

## Pricing Validation

**Market Research Shows:**
- Other tarot apps: $4.99-9.99/mo
- Professional tarot platforms: $29.99-79.99/mo
- White-label solutions: $299-$999/mo

**Our Competitive Advantage:**
- I Ching + Tarot combined (unique)
- Pattern analysis (unique)
- Multi-system integration (unique)

**Recommended Pricing:**
- After validation: $24.99/mo for "Professional" tier (matches market)
- Premium at $49.99/mo (pattern analysis premium)
- Pricing tests: A/B test $19.99 vs $29.99 for Pro

---

## First Client Deliverables

**For Initial Client (current):**
1. Custom spread for their specific niche
2. Branded PDF reports with their branding
3. Priority support (email/Discord)
4. API access for their integration needs
5. Quarterly business reviews (QBRs) on usage & insights

**Revenue from First Client:**
- One-time customization: $500
- Monthly license: $99/mo
- Reading credits: prepaid block ($100 for 20 readings)
- Expected LTV (12 month): $1,500-2,000

---

## Go-to-Market Plan

**Pilot Phase (Month 1):**
- Deploy for first client
- Gather feedback
- Refine tiering

**Beta Launch (Month 2):**
- Invite 10 beta testers (give 1 month free)
- Get testimonials/case studies
- Finalize pricing

**Public Launch (Month 3):**
- Product Hunt launch
- Indie Hackers posting
- Tutorials for practitioners

**Scale (Month 4+):**
- SEO for "professional tarot platform"
- Content marketing (tarot business tips)
- Practitioner outreach

---

## Success Metrics

**KPIs to Track:**
- MRR (Monthly Recurring Revenue)
- Conversion rate (free → paid)
- Average revenue per user (ARPU)
- Client churn rate (<5% target)
- Reading completion rate (abandonment <10%)
- Premium feature adoption (>30% of paying users)
- Client satisfaction (NPS >50)

**Overall Monetization Goal:**
- $1,000 MRR by Month 3
- $5,000 MRR by Month 6
- $10,000 MRR by Month 12
- 90+ paying clients by end of Year 1

---

*Specification created for Augury professional monetization*
*Documented to guide first client development and scale*
*Ready for Claude implementation*

**Next Steps:**
1. Review spec with client
2. Prioritize Phase 1 features
3. Assign development tasks
4. Begin Premium Engine build
5. Set up Stripe account
6. Deploy beta to client
