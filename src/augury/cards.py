"""Rider-Waite tarot reference data for the Augury system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal


@dataclass(slots=True)
class Card:
    name: str
    number: int
    suit: str | None
    arcana: Literal["major", "minor"]
    upright_keywords: list[str]
    reversed_keywords: list[str]
    upright_meaning: str
    reversed_meaning: str
    element: str
    astrology: str
    numerology: str
    related_cards: list[str]
    educational_tip: str


MAJOR_NUMEROLOGY: Final[dict[int, str]] = {
    0: "0 / pure potential and the leap into mystery",
    1: "1 / initiative, focus, and conscious will",
    2: "2 / polarity, receptivity, and hidden knowing",
    3: "3 / creation, nurture, and embodied growth",
    4: "4 / order, authority, and stable foundations",
    5: "5 / challenge, belief, and meaningful change",
    6: "6 / union, choice, and values alignment",
    7: "7 / directed movement and disciplined victory",
    8: "8 / courage, self-mastery, and steady power",
    9: "9 / solitude, wisdom, and inner completion",
    10: "10 / turning cycles, fate, and larger patterns",
    11: "11 / truth, balance, and accountability",
    12: "12 / surrender, suspension, and altered sight",
    13: "13 / endings, transformation, and release",
    14: "14 / moderation, healing, and integration",
    15: "15 / attachment, desire, and the shadow self",
    16: "16 / breakdown, revelation, and forced change",
    17: "17 / hope, guidance, and spiritual renewal",
    18: "18 / dreams, uncertainty, and psychic tides",
    19: "19 / vitality, success, and clear illumination",
    20: "20 / awakening, reckoning, and rebirth",
    21: "21 / completion, integration, and wholeness",
}

MINOR_NUMEROLOGY: Final[dict[int, str]] = {
    1: "1 / seed, initiation, and concentrated potential",
    2: "2 / polarity, partnership, and difficult balance",
    3: "3 / growth, expression, and first expansion",
    4: "4 / structure, security, and holding form",
    5: "5 / friction, disruption, and needed change",
    6: "6 / harmony, reciprocity, and regained flow",
    7: "7 / assessment, resolve, and tested conviction",
    8: "8 / movement, repetition, and disciplined momentum",
    9: "9 / culmination, resilience, and near completion",
    10: "10 / completion, consequence, and excess before renewal",
    11: "Court / study, messages, and early embodiment",
    12: "Court / pursuit, motion, and charged direction",
    13: "Court / embodiment, nurture, and mature expression",
    14: "Court / command, mastery, and outer authority",
}

RANK_TO_NUMBER: Final[dict[str, int]] = {
    "Ace": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
    "Six": 6,
    "Seven": 7,
    "Eight": 8,
    "Nine": 9,
    "Ten": 10,
    "Page": 11,
    "Knight": 12,
    "Queen": 13,
    "King": 14,
}

RANK_ORDER: Final[list[str]] = list(RANK_TO_NUMBER)

SUIT_ELEMENTS: Final[dict[str, str]] = {
    "Wands": "Fire",
    "Cups": "Water",
    "Swords": "Air",
    "Pentacles": "Earth",
}

SUIT_DOMAINS: Final[dict[str, str]] = {
    "Wands": "creativity, courage, ambition, and life force",
    "Cups": "feelings, relationships, intuition, and spiritual openness",
    "Swords": "thought, truth, conflict, and communication",
    "Pentacles": "work, money, the body, and material security",
}

SUIT_ZODIAC: Final[dict[str, str]] = {
    "Wands": "Aries, Leo, Sagittarius",
    "Cups": "Cancer, Scorpio, Pisces",
    "Swords": "Gemini, Libra, Aquarius",
    "Pentacles": "Taurus, Virgo, Capricorn",
}

SUIT_THEME_CARDS: Final[dict[str, str]] = {
    "Wands": "The Magician",
    "Cups": "The High Priestess",
    "Swords": "Justice",
    "Pentacles": "The Empress",
}

NUMBER_LESSONS: Final[dict[str, str]] = {
    "Ace": "the raw seed of a suit before it fully takes shape",
    "Two": "polarity, reflection, and the need to choose or balance",
    "Three": "first outward growth and visible development",
    "Four": "structure, consolidation, and stabilizing the energy",
    "Five": "disruption that tests whether the foundation can hold",
    "Six": "rebalancing, relief, or harmony after strain",
    "Seven": "evaluation, resolve, and pressure on personal conviction",
    "Eight": "movement, repetition, or disciplined refinement",
    "Nine": "maturity, resilience, and nearing fulfillment",
    "Ten": "completion, saturation, and the weight of a cycle ending",
}

COURT_LESSONS: Final[dict[str, str]] = {
    "Page": "students, messages, or first attempts to embody the suit",
    "Knight": "pursuit, momentum, and active engagement with the suit",
    "Queen": "inner mastery, receptivity, and mature embodiment of the suit",
    "King": "outer mastery, direction, and responsible command of the suit",
}

COURT_ASPECTS: Final[dict[str, str]] = {
    "Page": "Earth",
    "Knight": "Fire",
    "Queen": "Water",
    "King": "Air",
}


def _major(
    *,
    number: int,
    name: str,
    upright_keywords: list[str],
    reversed_keywords: list[str],
    upright_meaning: str,
    reversed_meaning: str,
    element: str,
    astrology: str,
    related_cards: list[str],
    educational_tip: str,
) -> Card:
    return Card(
        name=name,
        number=number,
        suit=None,
        arcana="major",
        upright_keywords=upright_keywords,
        reversed_keywords=reversed_keywords,
        upright_meaning=upright_meaning,
        reversed_meaning=reversed_meaning,
        element=element,
        astrology=astrology,
        numerology=MAJOR_NUMEROLOGY[number],
        related_cards=related_cards,
        educational_tip=educational_tip,
    )


def _minor_related(suit: str, rank: str, extra_related: list[str] | None = None) -> list[str]:
    related: list[str] = []
    index = RANK_ORDER.index(rank)
    if index > 0:
        related.append(f"{RANK_ORDER[index - 1]} of {suit}")
    if index < len(RANK_ORDER) - 1:
        related.append(f"{RANK_ORDER[index + 1]} of {suit}")
    related.append(SUIT_THEME_CARDS[suit])
    for card_name in extra_related or []:
        if card_name not in related:
            related.append(card_name)
    return related


def _minor_tip(rank: str, suit: str) -> str:
    if rank in NUMBER_LESSONS:
        return (
            f"{rank}s in tarot emphasize {NUMBER_LESSONS[rank]}. "
            f"In {suit}, that lesson moves through {SUIT_DOMAINS[suit]}."
        )
    return (
        f"{rank}s usually point to {COURT_LESSONS[rank]}. "
        f"In {suit}, that role expresses itself through {SUIT_DOMAINS[suit]}."
    )


def _minor(
    *,
    rank: str,
    suit: str,
    upright_keywords: list[str],
    reversed_keywords: list[str],
    upright_meaning: str,
    reversed_meaning: str,
    astrology: str,
    extra_related: list[str] | None = None,
    educational_tip: str | None = None,
) -> Card:
    number = RANK_TO_NUMBER[rank]
    suit_element = SUIT_ELEMENTS[suit]
    if rank in COURT_ASPECTS:
        element = f"{COURT_ASPECTS[rank]} of {suit_element}"
    else:
        element = suit_element

    return Card(
        name=f"{rank} of {suit}",
        number=number,
        suit=suit,
        arcana="minor",
        upright_keywords=upright_keywords,
        reversed_keywords=reversed_keywords,
        upright_meaning=upright_meaning,
        reversed_meaning=reversed_meaning,
        element=element,
        astrology=astrology,
        numerology=MINOR_NUMEROLOGY[number],
        related_cards=_minor_related(suit, rank, extra_related),
        educational_tip=educational_tip or _minor_tip(rank, suit),
    )


MAJOR_ARCANA: Final[list[Card]] = [
    _major(
        number=0,
        name="The Fool",
        upright_keywords=["beginnings", "innocence", "spontaneity", "trust", "adventure", "faith"],
        reversed_keywords=["recklessness", "naivete", "hesitation", "poor judgment", "foolish risk", "carelessness"],
        upright_meaning=(
            "The Fool marks a threshold where life asks for openness, trust, and a willing step into the unknown. "
            "It often signals a new path, a fresh identity, or a leap that cannot be fully reasoned out in advance."
        ),
        reversed_meaning=(
            "Reversed, The Fool can show either careless impulsiveness or fear of moving at all. "
            "The invitation is still there, but it needs more awareness, grounding, and honest risk assessment."
        ),
        element="Air",
        astrology="Uranus / Air",
        related_cards=["The Magician", "The World", "Page of Wands"],
        educational_tip=(
            "Major Arcana cards describe life lessons more than passing moods. "
            "The Fool is numbered zero because it can appear at the start of any cycle, no matter where you are in life."
        ),
    ),
    _major(
        number=1,
        name="The Magician",
        upright_keywords=["manifestation", "willpower", "skill", "focus", "resourcefulness", "action"],
        reversed_keywords=["manipulation", "illusion", "scattered energy", "untapped talent", "trickery", "poor planning"],
        upright_meaning=(
            "The Magician shows the power to translate vision into action by using the tools already within reach. "
            "This card points to concentration, aligned will, and the confidence to direct energy deliberately."
        ),
        reversed_meaning=(
            "Reversed, The Magician warns that talent may be unfocused, hidden, or used dishonestly. "
            "It can indicate spin, self-deception, or the need to stop talking about potential and actually embody it."
        ),
        element="Air",
        astrology="Mercury",
        related_cards=["The Fool", "The High Priestess", "Ace of Wands"],
        educational_tip=(
            "In Rider-Waite imagery, the Magician stands before symbols of all four suits. "
            "That image teaches that manifestation is not magic alone; it is intention joined with available resources."
        ),
    ),
    _major(
        number=2,
        name="The High Priestess",
        upright_keywords=["intuition", "mystery", "inner knowing", "stillness", "receptivity", "hidden knowledge"],
        reversed_keywords=["blocked intuition", "secrets", "disconnection", "withdrawal", "confusion", "superficiality"],
        upright_meaning=(
            "The High Priestess turns attention inward and asks for trust in subtle perception rather than outer noise. "
            "She often appears when timing is not yet ripe and deeper truth is sensed before it is spoken."
        ),
        reversed_meaning=(
            "Reversed, this card can show intuition being ignored, emotional information being suppressed, or secrecy clouding judgment. "
            "The remedy is quiet honesty and a return to the signals you already feel beneath the surface."
        ),
        element="Water",
        astrology="Moon",
        related_cards=["The Magician", "The Moon", "Ace of Cups"],
        educational_tip=(
            "The pomegranates, veil, and lunar symbolism in the classic image all point to hidden layers. "
            "When this card appears, read what is unspoken as carefully as what is stated outright."
        ),
    ),
    _major(
        number=3,
        name="The Empress",
        upright_keywords=["abundance", "nurture", "creativity", "fertility", "sensuality", "growth"],
        reversed_keywords=["smothering", "stagnation", "creative block", "dependence", "neglect", "scarcity mindset"],
        upright_meaning=(
            "The Empress brings fertile, embodied growth and the ability to nourish what matters until it ripens. "
            "She can represent creativity, caregiving, pleasure, or material conditions that support flourishing."
        ),
        reversed_meaning=(
            "Reversed, The Empress can show depletion, overgiving, or a disconnect from the body's wisdom and rhythms. "
            "It may also indicate creative stagnation or nurturing that becomes controlling instead of sustaining."
        ),
        element="Earth",
        astrology="Venus",
        related_cards=["The High Priestess", "The Emperor", "Ace of Pentacles"],
        educational_tip=(
            "The Empress is not only about motherhood; she is the archetype of living systems that grow when tended well. "
            "In readings, ask what needs warmth, time, and material support rather than more force."
        ),
    ),
    _major(
        number=4,
        name="The Emperor",
        upright_keywords=["structure", "authority", "stability", "discipline", "leadership", "protection"],
        reversed_keywords=["rigidity", "domination", "control issues", "stubbornness", "misuse of power", "inflexibility"],
        upright_meaning=(
            "The Emperor establishes order, boundaries, and reliable structure so something durable can stand. "
            "He often points to leadership, strategic thinking, and the disciplined use of authority."
        ),
        reversed_meaning=(
            "Reversed, The Emperor can become hard control, brittle certainty, or power used to dominate rather than protect. "
            "It may also signal weak structure, poor boundaries, or leadership that is absent where it is needed."
        ),
        element="Fire",
        astrology="Aries",
        related_cards=["The Empress", "The Hierophant", "King of Wands"],
        educational_tip=(
            "The Emperor shows that stability is an active practice, not just a mood. "
            "When this card appears, look for the framework, rules, or responsibilities that make freedom sustainable."
        ),
    ),
    _major(
        number=5,
        name="The Hierophant",
        upright_keywords=["tradition", "teaching", "guidance", "ritual", "belief", "shared values"],
        reversed_keywords=["rebellion", "dogma", "restrictive beliefs", "empty ritual", "nonconformity", "questioning authority"],
        upright_meaning=(
            "The Hierophant connects you to a lineage of wisdom, shared practice, or trusted instruction. "
            "This card often refers to institutions, mentors, sacred learning, or the stabilizing value of tradition."
        ),
        reversed_meaning=(
            "Reversed, The Hierophant questions whether the system still serves truth or only enforces conformity. "
            "It can point to rigid doctrine, spiritual bypassing, or the need to find a more living relationship to belief."
        ),
        element="Earth",
        astrology="Taurus",
        related_cards=["The Emperor", "The Lovers", "Five of Pentacles"],
        educational_tip=(
            "This card often matters most when community, ceremony, or inherited systems shape the question. "
            "Its lesson is not blind obedience, but conscious relationship to what has been handed down."
        ),
    ),
    _major(
        number=6,
        name="The Lovers",
        upright_keywords=["union", "choice", "harmony", "alignment", "intimacy", "values"],
        reversed_keywords=["disharmony", "misalignment", "indecision", "temptation", "conflict", "imbalance"],
        upright_meaning=(
            "The Lovers speaks to meaningful union and to choices that must align with your deepest values. "
            "It can describe relationship, but just as often it marks a moment where integrity and desire need to meet."
        ),
        reversed_meaning=(
            "Reversed, this card points to disconnection, mixed signals, or choices made against one's own truth. "
            "It asks for honest examination of what is being joined, divided, or compromised."
        ),
        element="Air",
        astrology="Gemini",
        related_cards=["The Hierophant", "The Chariot", "Two of Cups"],
        educational_tip=(
            "The Lovers is as much about value alignment as romance. "
            "When it appears, read the card as a question of conscious choice before assuming it only means partnership."
        ),
    ),
    _major(
        number=7,
        name="The Chariot",
        upright_keywords=["determination", "victory", "control", "momentum", "discipline", "ambition"],
        reversed_keywords=["scattered will", "aggression", "lack of control", "delay", "directionless force", "burnout"],
        upright_meaning=(
            "The Chariot signals focused momentum and the ability to direct opposing forces toward a chosen aim. "
            "Success comes through self-command, discipline, and refusing to let conflicting impulses drive the cart."
        ),
        reversed_meaning=(
            "Reversed, The Chariot can show lost direction, forced action, or emotion taking the reins away from intention. "
            "It asks whether effort is truly coordinated or merely intense."
        ),
        element="Water",
        astrology="Cancer",
        related_cards=["The Lovers", "Strength", "Six of Wands"],
        educational_tip=(
            "In the classic image, the charioteer moves because opposing powers are held in one command. "
            "This card is about directed will, not speed for its own sake."
        ),
    ),
    _major(
        number=8,
        name="Strength",
        upright_keywords=["courage", "compassion", "resilience", "inner power", "patience", "gentle mastery"],
        reversed_keywords=["self-doubt", "weakness", "harshness", "insecurity", "anger", "depleted confidence"],
        upright_meaning=(
            "Strength teaches that the deepest power is calm, steady, and integrated rather than forceful. "
            "It points to courage, emotional regulation, and the ability to meet intensity with heart."
        ),
        reversed_meaning=(
            "Reversed, Strength can show confidence draining away or instinct being handled with shame, fear, or overcontrol. "
            "The work is to rebuild trust in yourself without slipping into aggression."
        ),
        element="Fire",
        astrology="Leo",
        related_cards=["The Chariot", "The Hermit", "Queen of Wands"],
        educational_tip=(
            "Rider-Waite places Strength at eight to emphasize balance through embodied courage. "
            "Notice that the woman does not defeat the lion; she relates to it skillfully."
        ),
    ),
    _major(
        number=9,
        name="The Hermit",
        upright_keywords=["introspection", "solitude", "wisdom", "guidance", "contemplation", "searching"],
        reversed_keywords=["isolation", "withdrawal", "loneliness", "avoidance", "misguidance", "stubborn introspection"],
        upright_meaning=(
            "The Hermit withdraws from noise so insight can ripen in silence and lived experience. "
            "This card favors reflection, patient searching, and guidance that comes from hard-won wisdom."
        ),
        reversed_meaning=(
            "Reversed, The Hermit can indicate isolation that no longer serves, avoidance disguised as spirituality, or refusal to share needed wisdom. "
            "It may be time to return from the mountain with what you have learned."
        ),
        element="Earth",
        astrology="Virgo",
        related_cards=["Strength", "Wheel of Fortune", "Eight of Cups"],
        educational_tip=(
            "The lantern matters: the Hermit usually illuminates only a few steps, not the whole road. "
            "This card often teaches that clarity arrives through patient walking, not instant certainty."
        ),
    ),
    _major(
        number=10,
        name="Wheel of Fortune",
        upright_keywords=["cycles", "fate", "turning point", "change", "opportunity", "luck"],
        reversed_keywords=["setbacks", "resistance", "bad timing", "repetition", "lack of control", "clinging"],
        upright_meaning=(
            "Wheel of Fortune marks a turning cycle where events move within a pattern larger than personal control. "
            "It can bring timely openings, reversals, or the reminder that life changes even when we try to hold it still."
        ),
        reversed_meaning=(
            "Reversed, the Wheel can feel like bad timing, repetitive lessons, or resistance to an inevitable shift. "
            "The question becomes how to move with change rather than fight the turning itself."
        ),
        element="Fire",
        astrology="Jupiter",
        related_cards=["The Hermit", "Justice", "Ten of Wands"],
        educational_tip=(
            "This card often reads more like weather than personal intention. "
            "When it appears, ask what cycle is changing and what cannot be controlled by force alone."
        ),
    ),
    _major(
        number=11,
        name="Justice",
        upright_keywords=["truth", "fairness", "accountability", "balance", "clarity", "law"],
        reversed_keywords=["injustice", "bias", "dishonesty", "avoidance", "imbalance", "unfairness"],
        upright_meaning=(
            "Justice weighs actions and consequences without sentimentality, asking for clean alignment between fact and choice. "
            "This card favors honesty, ethical clarity, and decisions grounded in what is actually true."
        ),
        reversed_meaning=(
            "Reversed, Justice can show denial, unfair treatment, or the discomfort of consequences being dodged. "
            "It may also point to self-deception where the scales are being tilted in your own story."
        ),
        element="Air",
        astrology="Libra",
        related_cards=["Wheel of Fortune", "The Hanged Man", "King of Swords"],
        educational_tip=(
            "Justice is about right relationship, not punishment for its own sake. "
            "In a spread, it often asks what the cleanest, most accountable version of truth would look like."
        ),
    ),
    _major(
        number=12,
        name="The Hanged Man",
        upright_keywords=["surrender", "pause", "perspective", "letting go", "suspension", "sacrifice"],
        reversed_keywords=["stalling", "martyrdom", "resistance", "indecision", "needless delay", "stubbornness"],
        upright_meaning=(
            "The Hanged Man suspends ordinary momentum so perception can shift and a deeper surrender can occur. "
            "This card often points to a necessary pause, a reversal of viewpoint, or a release of control."
        ),
        reversed_meaning=(
            "Reversed, the card can show being stuck without insight, sacrificing for the wrong reasons, or refusing the surrender that would free the next step. "
            "The pause becomes stagnant when it is no longer conscious."
        ),
        element="Water",
        astrology="Neptune",
        related_cards=["Justice", "Death", "Four of Swords"],
        educational_tip=(
            "The Hanged Man is one of tarot's clearest lessons in voluntary suspension. "
            "When it appears, look for the insight that only becomes visible after the usual approach is dropped."
        ),
    ),
    _major(
        number=13,
        name="Death",
        upright_keywords=["endings", "transformation", "release", "transition", "renewal", "inevitability"],
        reversed_keywords=["resistance", "stagnation", "fear of endings", "clinging", "inertia", "delayed transition"],
        upright_meaning=(
            "Death signifies a real ending that clears space for transformation, whether or not the ego welcomes it. "
            "It strips away what has completed its purpose so life can continue in a truer form."
        ),
        reversed_meaning=(
            "Reversed, Death often shows the cost of clinging to what has already changed. "
            "The transformation is still underway, but resistance makes it feel more prolonged and painful."
        ),
        element="Water",
        astrology="Scorpio",
        related_cards=["The Hanged Man", "Temperance", "Ten of Swords"],
        educational_tip=(
            "Death in tarot rarely predicts literal death; it predicts irrevocable change. "
            "Traditional readers watch this card for necessary endings, clean cuts, and deep metamorphosis."
        ),
    ),
    _major(
        number=14,
        name="Temperance",
        upright_keywords=["balance", "moderation", "healing", "integration", "patience", "harmony"],
        reversed_keywords=["excess", "imbalance", "impatience", "discord", "overindulgence", "misalignment"],
        upright_meaning=(
            "Temperance blends opposites into something workable, healing, and sustainable over time. "
            "It points to moderation, alchemy, and the patient process of integration rather than dramatic extremes."
        ),
        reversed_meaning=(
            "Reversed, Temperance shows where the mixture has gone off balance through excess, impatience, or incompatible elements. "
            "The cure is rarely more force; it is usually better proportion."
        ),
        element="Fire",
        astrology="Sagittarius",
        related_cards=["Death", "The Devil", "Two of Pentacles"],
        educational_tip=(
            "Watch how this card pours between cups: it teaches relationship between elements, not separation. "
            "In readings, it often asks for adjustment, pacing, and a calmer middle path."
        ),
    ),
    _major(
        number=15,
        name="The Devil",
        upright_keywords=["bondage", "attachment", "materialism", "temptation", "shadow", "obsession"],
        reversed_keywords=["release", "reclaiming power", "breaking chains", "detox", "awareness", "resistance to temptation"],
        upright_meaning=(
            "The Devil exposes chains made of desire, fear, shame, or false necessity. "
            "It often points to compulsive patterns, power dynamics, or material fixation that drains freedom."
        ),
        reversed_meaning=(
            "Reversed, The Devil begins the process of release and conscious disentangling from the bind. "
            "Awareness grows, even if the habit or attachment has not fully loosened yet."
        ),
        element="Earth",
        astrology="Capricorn",
        related_cards=["Temperance", "The Tower", "Five of Pentacles"],
        educational_tip=(
            "Rider-Waite's chained figures are loosely bound, which matters. "
            "This card often asks where the prison is sustained by belief, avoidance, or numbing rather than absolute necessity."
        ),
    ),
    _major(
        number=16,
        name="The Tower",
        upright_keywords=["upheaval", "revelation", "collapse", "shock", "liberation", "truth"],
        reversed_keywords=["avoided disaster", "fear of change", "lingering crisis", "denial", "internal upheaval", "delayed collapse"],
        upright_meaning=(
            "The Tower breaks structures that cannot survive the truth and does so suddenly enough to feel shocking. "
            "Though disruptive, it is often a liberation from false stability, pride, or denial."
        ),
        reversed_meaning=(
            "Reversed, The Tower can show collapse being delayed, internalized, or partially avoided without real repair. "
            "It may feel less dramatic outwardly, but the truth still demands a reckoning."
        ),
        element="Fire",
        astrology="Mars",
        related_cards=["The Devil", "The Star", "Ten of Swords"],
        educational_tip=(
            "The Tower is not random chaos in traditional tarot; it is revelation with consequences. "
            "When it appears, look for the unstable structure that has already been struck in spirit before it falls in form."
        ),
    ),
    _major(
        number=17,
        name="The Star",
        upright_keywords=["hope", "healing", "renewal", "inspiration", "serenity", "faith"],
        reversed_keywords=["discouragement", "doubt", "disconnection", "pessimism", "burnout", "fragile hope"],
        upright_meaning=(
            "The Star follows upheaval with healing, openness, and a quiet trust that life can renew itself. "
            "It offers inspiration, spiritual clarity, and the sense that guidance is available again."
        ),
        reversed_meaning=(
            "Reversed, The Star can show hope flickering low, faith being strained, or healing needing more time than expected. "
            "The light is not gone, but it may need protection and honest tending."
        ),
        element="Air",
        astrology="Aquarius",
        related_cards=["The Tower", "The Moon", "Ace of Cups"],
        educational_tip=(
            "The Star often reads softly, but it is not weak. "
            "It is the card of recovery after rupture, when trust returns one clear drop at a time."
        ),
    ),
    _major(
        number=18,
        name="The Moon",
        upright_keywords=["intuition", "dreams", "uncertainty", "illusion", "subconscious", "mystery"],
        reversed_keywords=["clarity emerging", "confusion", "fear", "deception exposed", "anxiety", "misread signals"],
        upright_meaning=(
            "The Moon moves through uncertainty, dream logic, and psychic undercurrents that are difficult to pin down. "
            "It can indicate illusion or confusion, but also deep intuition that must be read symbolically rather than literally."
        ),
        reversed_meaning=(
            "Reversed, the fog may begin to thin, though not always comfortably. "
            "Hidden fears, projections, or deception can surface so they can finally be named clearly."
        ),
        element="Water",
        astrology="Pisces",
        related_cards=["The Star", "The Sun", "Seven of Cups"],
        educational_tip=(
            "The Moon often asks for symbolic reading rather than direct statement. "
            "When it appears, pay attention to dreams, atmosphere, and what the rational mind cannot fully organize yet."
        ),
    ),
    _major(
        number=19,
        name="The Sun",
        upright_keywords=["joy", "success", "vitality", "clarity", "warmth", "confidence"],
        reversed_keywords=["temporary cloud", "low energy", "delayed success", "self-doubt", "muted joy", "burnout"],
        upright_meaning=(
            "The Sun brings visibility, warmth, and life-affirming clarity after periods of confusion or doubt. "
            "It points to success, vitality, and the uncomplicated strength that comes from being fully seen."
        ),
        reversed_meaning=(
            "Reversed, The Sun may indicate joy being temporarily muted by fatigue, worry, or delay. "
            "The positive core remains, but it may be harder to feel or express without rest and perspective."
        ),
        element="Fire",
        astrology="Sun",
        related_cards=["The Moon", "Judgement", "Six of Wands"],
        educational_tip=(
            "The Sun is one of the most straightforwardly affirmative cards in the deck. "
            "Its lesson is that truth, energy, and joy become stabilizing forces when nothing essential is hidden."
        ),
    ),
    _major(
        number=20,
        name="Judgement",
        upright_keywords=["awakening", "reckoning", "absolution", "rebirth", "calling", "renewal"],
        reversed_keywords=["self-doubt", "avoidance", "harsh self-judgment", "stagnation", "denial", "refusal of the call"],
        upright_meaning=(
            "Judgement calls the past forward so it can be answered, integrated, and redeemed in a higher form. "
            "This card often marks awakening, life review, or the unmistakable sense that a calling can no longer be postponed."
        ),
        reversed_meaning=(
            "Reversed, Judgement may show avoidance of that call, self-criticism that freezes action, or reluctance to let the old story die. "
            "The awakening is trying to happen, but it is meeting resistance."
        ),
        element="Fire",
        astrology="Pluto / Fire",
        related_cards=["The Sun", "The World", "Page of Swords"],
        educational_tip=(
            "Traditional readers often distinguish Judgement from Justice: this is not courtroom balance, but resurrection and reckoning. "
            "Look for what is being summoned back into consciousness for a final answer."
        ),
    ),
    _major(
        number=21,
        name="The World",
        upright_keywords=["completion", "integration", "fulfillment", "accomplishment", "wholeness", "travel"],
        reversed_keywords=["unfinished business", "delay", "incompletion", "stagnation", "loose ends", "lack of closure"],
        upright_meaning=(
            "The World completes the arc with integration, mastery, and the sense that a cycle has reached meaningful fulfillment. "
            "It can indicate accomplishment, belonging in a larger whole, or readiness for the next spiral of growth."
        ),
        reversed_meaning=(
            "Reversed, The World suggests loose ends, delayed closure, or a cycle that is almost complete but not fully integrated. "
            "Something still needs acknowledgment before the next chapter can begin cleanly."
        ),
        element="Earth",
        astrology="Saturn / Earth",
        related_cards=["Judgement", "The Fool", "Ten of Pentacles"],
        educational_tip=(
            "The World closes the Major Arcana while also opening the next Fool journey. "
            "Completion in tarot is rarely static; it is integration that prepares a new beginning."
        ),
    ),
]


MINOR_ARCANA: Final[list[Card]] = [
    _minor(
        rank="Ace",
        suit="Wands",
        upright_keywords=["inspiration", "spark", "creation", "potential", "drive", "courage"],
        reversed_keywords=["delays", "low energy", "false start", "hesitation", "creative block", "fading passion"],
        upright_meaning=(
            "The Ace of Wands is the raw ignition of fire: a surge of life force, inspiration, or desire that wants expression. "
            "It signals fertile beginnings, but the spark still needs commitment to become something real."
        ),
        reversed_meaning=(
            "Reversed, the spark may be delayed, diffused, or buried under fear and fatigue. "
            "The potential is present, but it requires reconnection to passion and purposeful action."
        ),
        astrology="Root of Fire / Aries, Leo, Sagittarius",
        extra_related=["The Fool"],
    ),
    _minor(
        rank="Two",
        suit="Wands",
        upright_keywords=["planning", "future vision", "personal power", "choice", "expansion", "foresight"],
        reversed_keywords=["indecision", "fear of change", "poor planning", "limited thinking", "overcontrol", "delay"],
        upright_meaning=(
            "The Two of Wands turns inspiration into strategy and asks what horizon you are willing to claim. "
            "It is the moment of vision, planning, and choosing how far your power will extend."
        ),
        reversed_meaning=(
            "Reversed, this card can show hesitation, constricted planning, or fear of stepping beyond the familiar. "
            "The world is still open, but confidence and direction are not yet fully aligned."
        ),
        astrology="Mars in Aries",
    ),
    _minor(
        rank="Three",
        suit="Wands",
        upright_keywords=["expansion", "progress", "foresight", "enterprise", "momentum", "exploration"],
        reversed_keywords=["delays", "obstacles", "frustration", "stalled growth", "lack of foresight", "scattered plans"],
        upright_meaning=(
            "The Three of Wands shows effort beginning to move beyond the starting gate into visible expansion. "
            "It favors long-range thinking, trade, exploration, and confidence that movement is underway."
        ),
        reversed_meaning=(
            "Reversed, the expected momentum meets delay, poor coordination, or an outlook that was not broad enough. "
            "Progress is possible, but timing and planning may need revision."
        ),
        astrology="Sun in Aries",
    ),
    _minor(
        rank="Four",
        suit="Wands",
        upright_keywords=["celebration", "harmony", "homecoming", "milestones", "community", "stability"],
        reversed_keywords=["tension at home", "instability", "incomplete milestone", "exclusion", "interrupted joy", "transition"],
        upright_meaning=(
            "The Four of Wands is a card of stable joy, shared celebration, and foundations strong enough to support festivity. "
            "It often points to home, ceremony, belonging, or a milestone worth marking."
        ),
        reversed_meaning=(
            "Reversed, the celebration may be interrupted by instability, exclusion, or domestic strain. "
            "The foundation is not absent, but it may need strengthening before ease can return."
        ),
        astrology="Venus in Aries",
    ),
    _minor(
        rank="Five",
        suit="Wands",
        upright_keywords=["conflict", "competition", "friction", "testing", "struggle", "rivalry"],
        reversed_keywords=["conflict avoidance", "inner tension", "resentment", "scattered effort", "de-escalation", "unresolved rivalry"],
        upright_meaning=(
            "The Five of Wands creates friction through competing drives, egos, and ambitions. "
            "Though chaotic, it can sharpen skill and reveal what you truly stand for under pressure."
        ),
        reversed_meaning=(
            "Reversed, conflict may move underground, turn inward, or dissolve without actually being resolved. "
            "The card can show either healthy de-escalation or avoidance that leaves tension intact."
        ),
        astrology="Saturn in Leo",
    ),
    _minor(
        rank="Six",
        suit="Wands",
        upright_keywords=["victory", "recognition", "confidence", "progress", "public success", "leadership"],
        reversed_keywords=["arrogance", "lack of recognition", "self-doubt", "delay", "hollow victory", "ego issues"],
        upright_meaning=(
            "The Six of Wands brings visible progress and the confidence that comes from earned recognition. "
            "It indicates success, morale, and leadership that others are willing to acknowledge."
        ),
        reversed_meaning=(
            "Reversed, this card can show praise withheld, success that feels thin, or ego needing too much validation. "
            "It may also reflect a confidence dip despite real accomplishment."
        ),
        astrology="Jupiter in Leo",
    ),
    _minor(
        rank="Seven",
        suit="Wands",
        upright_keywords=["defense", "perseverance", "conviction", "courage", "resistance", "advantage"],
        reversed_keywords=["overwhelm", "giving up", "defensiveness", "exhaustion", "vulnerability", "scattered defenses"],
        upright_meaning=(
            "The Seven of Wands asks you to hold your ground when pressure rises and opposition tests your position. "
            "It is a card of conviction, persistence, and refusing to surrender a hard-won advantage."
        ),
        reversed_meaning=(
            "Reversed, the pressure may be outstripping your energy or pushing you into brittle defensiveness. "
            "It can indicate overwhelm, poor boundaries, or the need to regroup before continuing the fight."
        ),
        astrology="Mars in Leo",
    ),
    _minor(
        rank="Eight",
        suit="Wands",
        upright_keywords=["speed", "movement", "communication", "progress", "alignment", "momentum"],
        reversed_keywords=["delays", "miscommunication", "haste", "disorder", "stalled movement", "frustration"],
        upright_meaning=(
            "The Eight of Wands accelerates events, messages, or plans so that motion becomes unmistakable. "
            "It often points to swift developments, clear signals, and energy moving in one direction."
        ),
        reversed_meaning=(
            "Reversed, the same energy splinters into misfires, crossed messages, or frustrating delay. "
            "The pace may feel wrong in either direction: too fast to manage or too blocked to flow."
        ),
        astrology="Mercury in Sagittarius",
    ),
    _minor(
        rank="Nine",
        suit="Wands",
        upright_keywords=["resilience", "persistence", "boundaries", "grit", "vigilance", "endurance"],
        reversed_keywords=["paranoia", "exhaustion", "defensiveness", "burnout", "rigidity", "weakened resolve"],
        upright_meaning=(
            "The Nine of Wands is battered endurance: tired, wary, but still standing guard over what matters. "
            "It calls for resilience, boundary protection, and one last reserve of determination."
        ),
        reversed_meaning=(
            "Reversed, the guard position may become paranoia, depletion, or stubborn refusal to rest. "
            "The card can show that courage is real, but the nervous system is nearing overload."
        ),
        astrology="Moon in Sagittarius",
    ),
    _minor(
        rank="Ten",
        suit="Wands",
        upright_keywords=["burden", "responsibility", "effort", "pressure", "obligation", "completion"],
        reversed_keywords=["collapse", "martyrdom", "release", "delegation", "burnout", "stubborn overwork"],
        upright_meaning=(
            "The Ten of Wands shows a cycle reaching completion under a heavy load of duty, ambition, or overcommitment. "
            "The work may be meaningful, but the card asks whether too much is being carried alone."
        ),
        reversed_meaning=(
            "Reversed, the burden may be breaking down, getting dropped, or finally being shared. "
            "It can indicate burnout, martyrdom, or the relief that comes from releasing what was never sustainable."
        ),
        astrology="Saturn in Sagittarius",
    ),
    _minor(
        rank="Page",
        suit="Wands",
        upright_keywords=["exploration", "enthusiasm", "messages", "discovery", "free spirit", "study"],
        reversed_keywords=["immaturity", "scattered ambition", "rashness", "setbacks", "lack of follow-through", "false starts"],
        upright_meaning=(
            "The Page of Wands is the first eager embodiment of fire, bringing curiosity, good news, and appetite for adventure. "
            "It often marks a new passion, a messenger, or the courage to try before mastery exists."
        ),
        reversed_meaning=(
            "Reversed, the Page can become all spark and no staying power, or enthusiasm may keep collapsing into distraction. "
            "The invitation is to keep the fire alive without mistaking impulse for commitment."
        ),
        astrology="Aries, Leo, Sagittarius / Earth of Fire",
    ),
    _minor(
        rank="Knight",
        suit="Wands",
        upright_keywords=["action", "adventure", "boldness", "passion", "pursuit", "movement"],
        reversed_keywords=["impulsiveness", "recklessness", "anger", "inconsistency", "burnout", "frustration"],
        upright_meaning=(
            "The Knight of Wands charges ahead with charisma, urgency, and a fierce appetite for experience. "
            "It is bold, inspiring energy that can accomplish much when it has a worthy direction."
        ),
        reversed_meaning=(
            "Reversed, the same force becomes rash, combustible, or unable to sustain itself for long. "
            "This card may show passion outrunning judgment or momentum collapsing into irritation."
        ),
        astrology="Aries, Leo, Sagittarius / Fire of Fire",
    ),
    _minor(
        rank="Queen",
        suit="Wands",
        upright_keywords=["confidence", "warmth", "courage", "magnetism", "independence", "determination"],
        reversed_keywords=["jealousy", "volatility", "insecurity", "selfishness", "domination", "theatrical anger"],
        upright_meaning=(
            "The Queen of Wands radiates steady confidence, creative heat, and the warmth that energizes others. "
            "She is independent, socially compelling, and masterful at turning desire into visible action."
        ),
        reversed_meaning=(
            "Reversed, the queen's fire can distort into jealousy, attention hunger, or anger masking insecurity. "
            "Charisma is still present, but it may be used defensively or controllingly."
        ),
        astrology="Aries, Leo, Sagittarius / Water of Fire",
    ),
    _minor(
        rank="King",
        suit="Wands",
        upright_keywords=["vision", "leadership", "inspiration", "entrepreneurship", "honor", "mastery"],
        reversed_keywords=["impulsive control", "arrogance", "intolerance", "overbearing force", "rash leadership", "ego"],
        upright_meaning=(
            "The King of Wands directs creative power with authority, conviction, and strategic boldness. "
            "He points to leadership that is visionary, dynamic, and willing to stake itself on action."
        ),
        reversed_meaning=(
            "Reversed, this king can become domineering, impatient, or intoxicated with his own certainty. "
            "He may still have vision, but it needs humility and discipline to avoid scorching the field."
        ),
        astrology="Aries, Leo, Sagittarius / Air of Fire",
    ),
    _minor(
        rank="Ace",
        suit="Cups",
        upright_keywords=["love", "compassion", "renewal", "intuition", "openness", "blessing"],
        reversed_keywords=["blocked feelings", "emptiness", "repression", "missed connection", "heartbreak", "self-protection"],
        upright_meaning=(
            "The Ace of Cups is the pure outpouring of feeling, intuition, and spiritual receptivity. "
            "It signals emotional renewal, new love, or a blessing that opens the heart to deeper connection."
        ),
        reversed_meaning=(
            "Reversed, the cup may feel blocked, guarded, or unable to receive what is being offered. "
            "The emotional current is present, but grief, fear, or numbness may be restricting its flow."
        ),
        astrology="Root of Water / Cancer, Scorpio, Pisces",
        extra_related=["The Star"],
    ),
    _minor(
        rank="Two",
        suit="Cups",
        upright_keywords=["partnership", "attraction", "union", "mutuality", "harmony", "trust"],
        reversed_keywords=["imbalance", "separation", "miscommunication", "tension", "broken trust", "disharmony"],
        upright_meaning=(
            "The Two of Cups marks mutual recognition, balanced attraction, and the meeting of equals at the heart level. "
            "It often refers to partnership, but more broadly it signals reciprocity and emotional accord."
        ),
        reversed_meaning=(
            "Reversed, the bond may be strained by misalignment, poor communication, or unequal investment. "
            "The card asks whether connection is truly mutual or merely wished for."
        ),
        astrology="Venus in Cancer",
    ),
    _minor(
        rank="Three",
        suit="Cups",
        upright_keywords=["friendship", "celebration", "community", "joy", "support", "reunion"],
        reversed_keywords=["overindulgence", "gossip", "isolation", "third-party tension", "excess", "shallow fun"],
        upright_meaning=(
            "The Three of Cups celebrates shared joy, friendship, and the emotional nourishment of community. "
            "It supports gathering, reunion, creative collaboration, and simple pleasure in good company."
        ),
        reversed_meaning=(
            "Reversed, celebration can tip into excess, gossip, or dynamics that erode trust rather than deepen it. "
            "It may also show loneliness where connection is wanted but not fully available."
        ),
        astrology="Mercury in Cancer",
    ),
    _minor(
        rank="Four",
        suit="Cups",
        upright_keywords=["contemplation", "apathy", "withdrawal", "reevaluation", "dissatisfaction", "boredom"],
        reversed_keywords=["reengagement", "awareness", "acceptance", "new perspective", "renewed interest", "movement"],
        upright_meaning=(
            "The Four of Cups turns inward through emotional fatigue, boredom, or quiet dissatisfaction. "
            "It often shows that an opportunity exists, but attention is too withdrawn to recognize its value."
        ),
        reversed_meaning=(
            "Reversed, awareness begins to return and the closed emotional posture starts to soften. "
            "The card can mark reengagement with life after a period of numbness or self-absorption."
        ),
        astrology="Moon in Cancer",
    ),
    _minor(
        rank="Five",
        suit="Cups",
        upright_keywords=["loss", "grief", "regret", "disappointment", "mourning", "sadness"],
        reversed_keywords=["acceptance", "healing", "forgiveness", "moving on", "renewal", "perspective"],
        upright_meaning=(
            "The Five of Cups mourns what has been spilled and cannot be restored exactly as it was. "
            "It is honest grief, but one that still leaves some support and possibility standing behind you."
        ),
        reversed_meaning=(
            "Reversed, the grieving process begins to open into acceptance, forgiveness, and renewed participation in life. "
            "Pain remains real, but it no longer fills the whole frame."
        ),
        astrology="Mars in Scorpio",
    ),
    _minor(
        rank="Six",
        suit="Cups",
        upright_keywords=["nostalgia", "kindness", "innocence", "reunion", "memories", "generosity"],
        reversed_keywords=["clinging to the past", "immaturity", "rose-tinted memory", "stagnation", "old wounds", "naivete"],
        upright_meaning=(
            "The Six of Cups brings sweetness from the past into the present through memory, reunion, or acts of kindness. "
            "It can indicate innocence, comfort, or healing rooted in sincere emotional exchange."
        ),
        reversed_meaning=(
            "Reversed, nostalgia may become escapism or the past may keep defining the present too strongly. "
            "The card can also reveal childish patterns that need updating rather than idealizing."
        ),
        astrology="Sun in Scorpio",
    ),
    _minor(
        rank="Seven",
        suit="Cups",
        upright_keywords=["imagination", "options", "fantasy", "temptation", "illusion", "desire"],
        reversed_keywords=["clarity", "choice", "grounded vision", "commitment", "sobering insight", "reality check"],
        upright_meaning=(
            "The Seven of Cups fills the field with alluring possibilities, not all of them practical or true. "
            "It asks for discernment so desire can become a real choice instead of endless fantasy."
        ),
        reversed_meaning=(
            "Reversed, illusion begins to clear and a decision can be made on firmer ground. "
            "The card favors reality over glamour and commitment over diffuse longing."
        ),
        astrology="Venus in Scorpio",
    ),
    _minor(
        rank="Eight",
        suit="Cups",
        upright_keywords=["withdrawal", "quest", "disappointment", "leaving behind", "soul-searching", "transition"],
        reversed_keywords=["fear of leaving", "stagnation", "aimless drifting", "avoidance", "return", "unresolved disappointment"],
        upright_meaning=(
            "The Eight of Cups walks away from what is no longer enough in order to seek deeper meaning. "
            "It is a card of voluntary departure, soul-searching, and the maturity to leave partial fulfillment behind."
        ),
        reversed_meaning=(
            "Reversed, the departure may be stalled by fear, guilt, or inability to define what would be better. "
            "It can also show returning to old ground without having resolved the original emptiness."
        ),
        astrology="Saturn in Pisces",
    ),
    _minor(
        rank="Nine",
        suit="Cups",
        upright_keywords=["contentment", "satisfaction", "pleasure", "gratitude", "wish fulfillment", "comfort"],
        reversed_keywords=["smugness", "excess", "shallow pleasure", "dissatisfaction", "indulgence", "entitlement"],
        upright_meaning=(
            "The Nine of Cups is emotional satisfaction, comfort, and appreciation for what has been achieved. "
            "It often appears as wish fulfillment, enjoyment, and a heart that feels materially and emotionally pleased."
        ),
        reversed_meaning=(
            "Reversed, pleasure may be excessive, performative, or somehow not as fulfilling as it looks. "
            "The card can ask whether desire has been satisfied deeply or only indulged superficially."
        ),
        astrology="Jupiter in Pisces",
    ),
    _minor(
        rank="Ten",
        suit="Cups",
        upright_keywords=["harmony", "family", "belonging", "peace", "fulfillment", "legacy"],
        reversed_keywords=["conflict at home", "disconnection", "broken harmony", "unrealistic ideal", "misalignment", "instability"],
        upright_meaning=(
            "The Ten of Cups represents enduring emotional harmony, belonging, and the joy of shared life. "
            "It points to family, chosen kin, and the kind of peace that extends beyond a fleeting mood."
        ),
        reversed_meaning=(
            "Reversed, the ideal of harmony may be under strain through hidden conflict, misaligned expectations, or unresolved family pain. "
            "The love may still be present, but the emotional structure needs repair."
        ),
        astrology="Mars in Pisces",
    ),
    _minor(
        rank="Page",
        suit="Cups",
        upright_keywords=["sensitivity", "intuition", "messages", "curiosity", "imagination", "tenderness"],
        reversed_keywords=["emotional immaturity", "moodiness", "blocked intuition", "escapism", "insecurity", "hypersensitivity"],
        upright_meaning=(
            "The Page of Cups brings emotional freshness, creative imagination, and surprising messages from the heart. "
            "It often signals a tender opening, an intuitive nudge, or the courage to feel something new."
        ),
        reversed_meaning=(
            "Reversed, this page can become moody, avoidant, or overwhelmed by feelings that lack structure. "
            "The sensitivity is real, but it needs steadier grounding and clearer expression."
        ),
        astrology="Cancer, Scorpio, Pisces / Earth of Water",
    ),
    _minor(
        rank="Knight",
        suit="Cups",
        upright_keywords=["romance", "charm", "invitation", "idealism", "creativity", "pursuit"],
        reversed_keywords=["moodiness", "unrealistic fantasy", "avoidance", "jealousy", "inconsistency", "manipulation"],
        upright_meaning=(
            "The Knight of Cups follows the heart with style, imagination, and sincere emotional pursuit. "
            "This card often points to invitations, romance, artistic movement, or idealism motivated by feeling."
        ),
        reversed_meaning=(
            "Reversed, the knight may drift into fantasy, emotional inconsistency, or charm used without accountability. "
            "The feeling is there, but it may not be grounded enough to trust."
        ),
        astrology="Cancer, Scorpio, Pisces / Fire of Water",
    ),
    _minor(
        rank="Queen",
        suit="Cups",
        upright_keywords=["empathy", "compassion", "intuition", "calm", "emotional depth", "nurture"],
        reversed_keywords=["emotional overwhelm", "codependency", "martyrdom", "insecurity", "withdrawal", "blurred boundaries"],
        upright_meaning=(
            "The Queen of Cups is emotionally wise, intuitive, and deeply receptive without losing her center. "
            "She listens beneath words and offers care that is gentle, profound, and spiritually alert."
        ),
        reversed_meaning=(
            "Reversed, her depth can tip into porous boundaries, self-sacrifice, or feeling swamped by what is sensed. "
            "Compassion remains, but it needs clearer containment."
        ),
        astrology="Cancer, Scorpio, Pisces / Water of Water",
    ),
    _minor(
        rank="King",
        suit="Cups",
        upright_keywords=["emotional balance", "diplomacy", "compassion", "wisdom", "steadiness", "generosity"],
        reversed_keywords=["emotional suppression", "volatility", "manipulation", "mood swings", "aloofness", "imbalance"],
        upright_meaning=(
            "The King of Cups masters feeling without deadening it, pairing compassion with stable self-command. "
            "He indicates mature emotional leadership, diplomacy, and calm under pressure."
        ),
        reversed_meaning=(
            "Reversed, the king's emotional control can become repression, volatility, or subtle manipulation. "
            "The issue is not feeling too much, but failing to relate to feeling honestly and cleanly."
        ),
        astrology="Cancer, Scorpio, Pisces / Air of Water",
    ),
    _minor(
        rank="Ace",
        suit="Swords",
        upright_keywords=["clarity", "truth", "breakthrough", "focus", "justice", "intellect"],
        reversed_keywords=["confusion", "misinformation", "clouded judgment", "harshness", "lies", "mental fog"],
        upright_meaning=(
            "The Ace of Swords cuts cleanly through confusion with truth, precision, and mental breakthrough. "
            "It marks decisive insight, a new idea, or the moment when reality becomes impossible to evade."
        ),
        reversed_meaning=(
            "Reversed, clarity is distorted by confusion, dishonesty, or a mind too clouded to make a clean judgment. "
            "The truth may still be present, but it is not yet being wielded well."
        ),
        astrology="Root of Air / Gemini, Libra, Aquarius",
        extra_related=["Justice"],
    ),
    _minor(
        rank="Two",
        suit="Swords",
        upright_keywords=["stalemate", "balance", "guardedness", "difficult choice", "denial", "truce"],
        reversed_keywords=["overwhelm", "confusion", "exposed feelings", "no peace", "stress", "indecision breaking"],
        upright_meaning=(
            "The Two of Swords holds tension in suspension while a hard choice is postponed or carefully weighed. "
            "It can show temporary balance, but also guardedness that refuses the information needed to decide."
        ),
        reversed_meaning=(
            "Reversed, the stalemate cracks and the emotional or mental strain becomes harder to contain. "
            "Clarity may break through, but often through stress rather than willing openness."
        ),
        astrology="Moon in Libra",
    ),
    _minor(
        rank="Three",
        suit="Swords",
        upright_keywords=["heartbreak", "sorrow", "separation", "truth", "grief", "pain"],
        reversed_keywords=["recovery", "release", "reconciliation", "healing", "lingering grief", "vulnerability"],
        upright_meaning=(
            "The Three of Swords is pain made clear: heartbreak, grief, or truth that pierces without softening itself. "
            "It is difficult, but it also ends denial and begins an honest reckoning with hurt."
        ),
        reversed_meaning=(
            "Reversed, the sorrow may begin to move toward healing, forgiveness, or emotional release. "
            "Even so, the card often shows pain still being processed rather than fully resolved."
        ),
        astrology="Saturn in Libra",
    ),
    _minor(
        rank="Four",
        suit="Swords",
        upright_keywords=["rest", "retreat", "recovery", "contemplation", "pause", "restoration"],
        reversed_keywords=["restlessness", "burnout", "forced pause", "insomnia", "depletion", "resistance to recovery"],
        upright_meaning=(
            "The Four of Swords calls for stillness, retreat, and active recovery after strain or conflict. "
            "It favors contemplation and rest as necessary medicine, not optional luxury."
        ),
        reversed_meaning=(
            "Reversed, rest may be resisted until the body or mind forces a stop. "
            "This card can show burnout, agitation, or difficulty accepting that healing takes time."
        ),
        astrology="Jupiter in Libra",
    ),
    _minor(
        rank="Five",
        suit="Swords",
        upright_keywords=["conflict", "betrayal", "self-interest", "defeat", "tension", "hollow victory"],
        reversed_keywords=["reconciliation", "remorse", "accountability", "lingering resentment", "lessons learned", "peacemaking"],
        upright_meaning=(
            "The Five of Swords reveals conflict where winning and losing both carry a cost. "
            "It can indicate betrayal, hostile strategy, or a situation where ego triumph leaves damage behind."
        ),
        reversed_meaning=(
            "Reversed, the card may move toward apology, accountability, or a reluctant peace. "
            "It can also show the lingering aftertaste of conflict that has ended without fully healing."
        ),
        astrology="Venus in Aquarius",
    ),
    _minor(
        rank="Six",
        suit="Swords",
        upright_keywords=["transition", "passage", "healing", "moving on", "support", "distance"],
        reversed_keywords=["stuck transition", "baggage", "reluctance to move on", "rough waters", "unresolved pain", "delay"],
        upright_meaning=(
            "The Six of Swords carries you from turbulence toward calmer conditions, even if the journey is bittersweet. "
            "It points to transition, support, and the quiet work of moving on."
        ),
        reversed_meaning=(
            "Reversed, the crossing is delayed by baggage, resistance, or conditions that do not yet feel safe enough to leave. "
            "Movement is desired, but not fully underway."
        ),
        astrology="Mercury in Aquarius",
    ),
    _minor(
        rank="Seven",
        suit="Swords",
        upright_keywords=["strategy", "stealth", "independence", "deception", "cleverness", "evasiveness"],
        reversed_keywords=["exposure", "confession", "self-deception", "accountability", "sloppy plans", "returning something"],
        upright_meaning=(
            "The Seven of Swords uses indirect tactics, secrecy, or strategic withdrawal to pursue an aim. "
            "It can represent clever independence, but also deception, evasion, or acting without transparency."
        ),
        reversed_meaning=(
            "Reversed, hidden actions are exposed or the burden of secrecy becomes too heavy to maintain. "
            "The card can point to confession, accountability, or realizing you have also been deceiving yourself."
        ),
        astrology="Moon in Aquarius",
    ),
    _minor(
        rank="Eight",
        suit="Swords",
        upright_keywords=["restriction", "fear", "entrapment", "overthinking", "helplessness", "paralysis"],
        reversed_keywords=["release", "new perspective", "self-liberation", "less fear", "empowerment", "clarity"],
        upright_meaning=(
            "The Eight of Swords is a mental prison built from fear, overidentification, and a sense of powerlessness. "
            "The constraints feel real, but the card often suggests that perception is making the walls tighter than they have to be."
        ),
        reversed_meaning=(
            "Reversed, the bindings begin to loosen as perspective changes and self-belief returns. "
            "Freedom may come gradually, but the mind is no longer consenting so fully to the cage."
        ),
        astrology="Jupiter in Gemini",
    ),
    _minor(
        rank="Nine",
        suit="Swords",
        upright_keywords=["anxiety", "worry", "guilt", "nightmares", "stress", "despair"],
        reversed_keywords=["relief", "reaching out", "perspective", "healing", "persistent worry", "shame"],
        upright_meaning=(
            "The Nine of Swords captures mental anguish, fear loops, and the way distress magnifies itself in isolation. "
            "It often points to anxiety, guilt, or grief that is most intense in the mind's private hours."
        ),
        reversed_meaning=(
            "Reversed, help may be sought, perspective may begin to return, or the worst of the spiral may be easing. "
            "Even so, the card can still show shame and worry that need compassionate attention."
        ),
        astrology="Mars in Gemini",
    ),
    _minor(
        rank="Ten",
        suit="Swords",
        upright_keywords=["ruin", "endings", "betrayal", "collapse", "exhaustion", "finality"],
        reversed_keywords=["recovery", "resilience", "survival", "lessons", "lingering pain", "rebuilding"],
        upright_meaning=(
            "The Ten of Swords is a painful ending, collapse, or point of total mental exhaustion. "
            "It is stark, but it also suggests the worst has already happened and a new dawn waits on the far edge of the scene."
        ),
        reversed_meaning=(
            "Reversed, the card begins the long arc of recovery, survival, and learning after the breakdown. "
            "The wound is not erased, but finality gives way to resilience."
        ),
        astrology="Sun in Gemini",
    ),
    _minor(
        rank="Page",
        suit="Swords",
        upright_keywords=["curiosity", "vigilance", "ideas", "communication", "candor", "alertness"],
        reversed_keywords=["gossip", "defensiveness", "haste", "scattered thoughts", "bluntness", "immature words"],
        upright_meaning=(
            "The Page of Swords is mentally quick, observant, and eager to test ideas in the open air. "
            "This card often signals study, news, sharp questions, or a youthful but genuine appetite for truth."
        ),
        reversed_meaning=(
            "Reversed, the page's sharpness can become gossip, argument for its own sake, or reactive communication. "
            "The intelligence is active, but it may lack maturity, patience, or depth."
        ),
        astrology="Gemini, Libra, Aquarius / Earth of Air",
    ),
    _minor(
        rank="Knight",
        suit="Swords",
        upright_keywords=["ambition", "speed", "directness", "intensity", "decisive action", "focus"],
        reversed_keywords=["aggression", "rash words", "impatience", "cruelty", "burnout", "poor timing"],
        upright_meaning=(
            "The Knight of Swords charges toward the objective with speed, conviction, and formidable mental force. "
            "It can indicate decisive action, fierce truth-telling, or an uncompromising pursuit of an idea."
        ),
        reversed_meaning=(
            "Reversed, that force becomes reckless, abrasive, or disconnected from consequences. "
            "The card warns that intensity without wisdom can wound just as quickly as it breaks through."
        ),
        astrology="Gemini, Libra, Aquarius / Fire of Air",
    ),
    _minor(
        rank="Queen",
        suit="Swords",
        upright_keywords=["discernment", "independence", "honesty", "boundaries", "perception", "wit"],
        reversed_keywords=["bitterness", "coldness", "cynicism", "cutting words", "isolation", "harsh judgment"],
        upright_meaning=(
            "The Queen of Swords sees clearly, names things plainly, and guards truth with intelligent boundaries. "
            "She represents mature discernment, independence, and compassion sharpened by experience."
        ),
        reversed_meaning=(
            "Reversed, the same clarity may harden into cynicism, bitterness, or verbal cruelty. "
            "The issue is not insight, but pain using insight as a weapon."
        ),
        astrology="Gemini, Libra, Aquarius / Water of Air",
    ),
    _minor(
        rank="King",
        suit="Swords",
        upright_keywords=["authority", "logic", "ethics", "strategy", "truth", "clear judgment"],
        reversed_keywords=["tyranny", "rigidity", "manipulation", "cold control", "bias", "dogmatism"],
        upright_meaning=(
            "The King of Swords governs through intellect, ethics, and principled clarity. "
            "He indicates wise judgment, strategic leadership, and decisions made from truth rather than sentimentality."
        ),
        reversed_meaning=(
            "Reversed, the king's clarity becomes severe control, dogmatism, or intelligence divorced from conscience. "
            "He may know the rules very well while using them unjustly."
        ),
        astrology="Gemini, Libra, Aquarius / Air of Air",
    ),
    _minor(
        rank="Ace",
        suit="Pentacles",
        upright_keywords=["manifestation", "prosperity", "opportunity", "stability", "seed", "resource"],
        reversed_keywords=["missed chance", "poor planning", "scarcity", "instability", "short-term thinking", "delay"],
        upright_meaning=(
            "The Ace of Pentacles offers a tangible opening: a seed of health, work, money, or material support with real growth potential. "
            "It favors grounded beginnings and opportunities that can become reliable if cultivated well."
        ),
        reversed_meaning=(
            "Reversed, the opportunity may be mishandled, delayed, or undercut by poor planning and insecurity. "
            "The seed exists, but it may not yet have the conditions needed to take root."
        ),
        astrology="Root of Earth / Taurus, Virgo, Capricorn",
        extra_related=["The Empress"],
    ),
    _minor(
        rank="Two",
        suit="Pentacles",
        upright_keywords=["adaptability", "balance", "change", "juggling", "flexibility", "flow"],
        reversed_keywords=["overwhelm", "imbalance", "disorganization", "financial strain", "dropped balls", "poor priorities"],
        upright_meaning=(
            "The Two of Pentacles manages changing practical demands through rhythm, humor, and responsive balance. "
            "It suggests juggling resources successfully, but only while movement stays flexible."
        ),
        reversed_meaning=(
            "Reversed, the juggling act becomes too much and key priorities begin to slip. "
            "This card often points to overcommitment, poor pacing, or practical strain that needs simplification."
        ),
        astrology="Jupiter in Capricorn",
    ),
    _minor(
        rank="Three",
        suit="Pentacles",
        upright_keywords=["craftsmanship", "teamwork", "skill", "planning", "collaboration", "quality"],
        reversed_keywords=["poor workmanship", "lack of teamwork", "misalignment", "mediocrity", "inexperience", "ego"],
        upright_meaning=(
            "The Three of Pentacles builds something solid through competence, planning, and collaborative effort. "
            "It honors craft, apprenticeship, and the practical value of working well with others."
        ),
        reversed_meaning=(
            "Reversed, quality suffers through ego, poor coordination, or skill that is not yet ready for the task. "
            "The structure can still be built, but the workmanship needs attention."
        ),
        astrology="Mars in Capricorn",
    ),
    _minor(
        rank="Four",
        suit="Pentacles",
        upright_keywords=["security", "control", "conservation", "stability", "boundaries", "possession"],
        reversed_keywords=["greed", "fear of loss", "stagnation", "overspending", "rigid holding", "openness"],
        upright_meaning=(
            "The Four of Pentacles protects resources, structure, and hard-won stability. "
            "At its best it shows prudent boundaries; at its tightest it reveals fear of loss and clenched control."
        ),
        reversed_meaning=(
            "Reversed, the grip may loosen in a healthy way or collapse into waste and instability. "
            "The key question is whether release is becoming generosity or simply disorganization."
        ),
        astrology="Sun in Capricorn",
    ),
    _minor(
        rank="Five",
        suit="Pentacles",
        upright_keywords=["hardship", "exclusion", "poverty", "worry", "struggle", "insecurity"],
        reversed_keywords=["recovery", "help available", "improvement", "resilience", "renewed hope", "mending"],
        upright_meaning=(
            "The Five of Pentacles experiences lack, exclusion, or practical hardship that tests faith and endurance. "
            "It can indicate illness, financial worry, or feeling shut out from the warmth you need."
        ),
        reversed_meaning=(
            "Reversed, help begins to reach the situation and recovery becomes possible. "
            "The hardship may not vanish at once, but isolation loosens and practical support becomes easier to accept."
        ),
        astrology="Mercury in Taurus",
    ),
    _minor(
        rank="Six",
        suit="Pentacles",
        upright_keywords=["generosity", "reciprocity", "charity", "fairness", "support", "exchange"],
        reversed_keywords=["strings attached", "debt", "inequality", "one-sided giving", "dependency", "unfair exchange"],
        upright_meaning=(
            "The Six of Pentacles measures the flow of resources between giver and receiver. "
            "At its best it shows generosity, fairness, and support offered in a way that restores balance."
        ),
        reversed_meaning=(
            "Reversed, the exchange becomes uneven, conditional, or entangled with debt and power. "
            "The card asks whether generosity is truly clean or quietly controlling."
        ),
        astrology="Moon in Taurus",
    ),
    _minor(
        rank="Seven",
        suit="Pentacles",
        upright_keywords=["patience", "assessment", "long-term view", "investment", "perseverance", "harvest"],
        reversed_keywords=["impatience", "poor return", "frustration", "quitting early", "wasted effort", "rethinking"],
        upright_meaning=(
            "The Seven of Pentacles pauses to assess growth, asking whether the investment is maturing as hoped. "
            "It favors patience, realistic evaluation, and trust in long processes that cannot be rushed."
        ),
        reversed_meaning=(
            "Reversed, discouragement or impatience may tempt you to abandon the work before it has ripened. "
            "It can also show poor returns that require a strategic change in method."
        ),
        astrology="Saturn in Taurus",
    ),
    _minor(
        rank="Eight",
        suit="Pentacles",
        upright_keywords=["diligence", "apprenticeship", "skill-building", "dedication", "craft", "repetition"],
        reversed_keywords=["perfectionism", "boredom", "lack of quality", "cutting corners", "drudgery", "stalled development"],
        upright_meaning=(
            "The Eight of Pentacles is devoted practice: skill refined through repetition, humility, and steady labor. "
            "It supports apprenticeship, mastery, and the quiet dignity of doing the work well."
        ),
        reversed_meaning=(
            "Reversed, the labor may become joyless, perfectionistic, or careless in quality. "
            "The card asks whether repetition is still building mastery or has turned into empty grind."
        ),
        astrology="Sun in Virgo",
    ),
    _minor(
        rank="Nine",
        suit="Pentacles",
        upright_keywords=["independence", "refinement", "abundance", "self-sufficiency", "enjoyment", "luxury"],
        reversed_keywords=["dependency", "isolation", "hollow luxury", "setbacks", "overinvestment", "superficial success"],
        upright_meaning=(
            "The Nine of Pentacles enjoys the fruits of cultivated skill, discipline, and discernment. "
            "It indicates earned comfort, independence, and the ability to appreciate what has been built."
        ),
        reversed_meaning=(
            "Reversed, independence may be more fragile than it appears or comfort may have become decorative rather than satisfying. "
            "The card can also point to setbacks that reveal hidden dependency."
        ),
        astrology="Venus in Virgo",
    ),
    _minor(
        rank="Ten",
        suit="Pentacles",
        upright_keywords=["legacy", "wealth", "family", "permanence", "inheritance", "security"],
        reversed_keywords=["instability", "family conflict", "loss", "fragile legacy", "short-term focus", "mismanagement"],
        upright_meaning=(
            "The Ten of Pentacles speaks to long-term security, legacy, and material structures that support generations. "
            "It can indicate family wealth, lasting success, or the broader system that holds a life together."
        ),
        reversed_meaning=(
            "Reversed, legacy may be under strain through conflict, mismanagement, or values that do not truly hold the structure together. "
            "The outer form of security may exist, but the roots are less stable than they seem."
        ),
        astrology="Mercury in Virgo",
    ),
    _minor(
        rank="Page",
        suit="Pentacles",
        upright_keywords=["study", "opportunity", "practicality", "diligence", "curiosity", "manifestation"],
        reversed_keywords=["procrastination", "lack of focus", "missed opportunity", "immaturity", "poor follow-through", "unrealistic plans"],
        upright_meaning=(
            "The Page of Pentacles approaches the material world with seriousness, curiosity, and willingness to learn. "
            "It often signals a practical beginning, a study path, or news related to work, money, or the body."
        ),
        reversed_meaning=(
            "Reversed, the potential is undermined by procrastination, inconsistency, or plans that are not yet grounded in reality. "
            "The path is promising, but discipline must catch up with intention."
        ),
        astrology="Taurus, Virgo, Capricorn / Earth of Earth",
    ),
    _minor(
        rank="Knight",
        suit="Pentacles",
        upright_keywords=["reliability", "patience", "duty", "persistence", "routine", "service"],
        reversed_keywords=["stagnation", "boredom", "stubbornness", "laziness", "perfectionism", "resistance to change"],
        upright_meaning=(
            "The Knight of Pentacles moves slowly, but with steadiness, integrity, and real follow-through. "
            "This card favors patience, routine, responsible labor, and progress that is built to last."
        ),
        reversed_meaning=(
            "Reversed, steadiness turns into stagnation, rigidity, or joyless overfocus on routine. "
            "The work may still be getting done, but not in a way that remains alive or adaptive."
        ),
        astrology="Taurus, Virgo, Capricorn / Fire of Earth",
    ),
    _minor(
        rank="Queen",
        suit="Pentacles",
        upright_keywords=["nurturing", "practicality", "comfort", "resourcefulness", "generosity", "grounded care"],
        reversed_keywords=["work-life imbalance", "smothering", "self-neglect", "financial stress", "materialism", "control"],
        upright_meaning=(
            "The Queen of Pentacles creates security through competence, care, and grounded stewardship of resources. "
            "She blends practical wisdom with warmth, making the material world more livable for everyone around her."
        ),
        reversed_meaning=(
            "Reversed, the queen's care can become controlling, depleted, or overly tied to material reassurance. "
            "She may be tending everything except her own underlying stability."
        ),
        astrology="Taurus, Virgo, Capricorn / Water of Earth",
    ),
    _minor(
        rank="King",
        suit="Pentacles",
        upright_keywords=["abundance", "stewardship", "discipline", "security", "leadership", "success"],
        reversed_keywords=["greed", "rigidity", "workaholism", "possessiveness", "poor judgment", "status obsession"],
        upright_meaning=(
            "The King of Pentacles masters the material realm through discipline, stewardship, and reliable leadership. "
            "He points to prosperity, practical authority, and the capacity to create enduring stability."
        ),
        reversed_meaning=(
            "Reversed, that mastery can harden into greed, status fixation, or control driven by fear of loss. "
            "Success may still exist, but it is being handled without enough wisdom or generosity."
        ),
        astrology="Taurus, Virgo, Capricorn / Air of Earth",
    ),
]


SPREADS: Final[dict[str, dict[str, str | list[str]]]] = {
    "single": {
        "name": "Single Card",
        "positions": ["focus"],
        "description": "A one-card draw for immediate guidance, a daily theme, or a simple check-in.",
    },
    "three_card": {
        "name": "Three Card",
        "positions": ["past", "present", "future"],
        "description": "A classic spread that traces momentum through time and shows how one phase flows into the next.",
    },
    "celtic_cross": {
        "name": "Celtic Cross",
        "positions": [
            "present",
            "challenge",
            "distant_past",
            "recent_past",
            "conscious_goal",
            "near_future",
            "self",
            "environment",
            "hopes_and_fears",
            "outcome",
        ],
        "description": "A traditional ten-card spread for complex situations, showing inner motives, outer forces, and likely outcome.",
    },
    "relationship": {
        "name": "Relationship",
        "positions": ["you", "other_person", "bond", "strength", "challenge", "guidance"],
        "description": "A six-card spread for relationship dynamics, mutual influence, and what the connection is asking for now.",
    },
    "career": {
        "name": "Career",
        "positions": ["current_path", "strength", "obstacle", "opportunity", "guidance", "outcome"],
        "description": "A practical spread for work, vocation, direction, and the forces shaping professional growth.",
    },
    "yes_no": {
        "name": "Yes / No",
        "positions": ["situation", "obstacle", "guidance"],
        "description": "A concise spread that favors directional clarity over a simplistic binary answer.",
    },
    "elemental": {
        "name": "Elemental Cross",
        "positions": ["fire", "water", "air", "earth"],
        "description": "A four-card spread that reads the question through drive, feeling, thought, and practical embodiment.",
    },
    "horseshoe": {
        "name": "Horseshoe",
        "positions": ["past_influences", "present_situation", "hidden_influences", "obstacles", "external_influences", "best_course_of_action", "likely_outcome"],
        "description": "A seven-card arc from past roots through hidden forces and external pressures to clear guidance and outcome.",
    },
    "shadow_work": {
        "name": "Shadow Work",
        "positions": ["the_shadow_aspect", "root_cause", "how_it_manifests", "what_to_integrate", "next_step"],
        "description": "A five-card spread for facing and integrating what has been repressed, avoided, or disowned.",
    },
    "year_ahead": {
        "name": "Year Ahead",
        "positions": [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ],
        "description": "A twelve-card calendar spread for the arc of the coming year.",
    },
    "star": {
        "name": "Star",
        "positions": [
            "present_situation",
            "what_crosses_you",
            "what_crowns_you",
            "foundation",
            "recent_past",
            "near_future",
            "your_role",
            "external_influences",
            "hopes_and_fears",
            "where_this_leads",
        ],
        "description": "A ten-card spread combining Celtic Cross structure with soul-level perspective. For complex, multi-layered questions.",
    },
    "soul_path": {
        "name": "Soul Path",
        "positions": ["where_you_came_from", "what_you_carry", "your_core_gift", "your_challenge", "your_next_step"],
        "description": "A five-card spread for identity, purpose, and the deeper arc of a person's journey.",
    },
    "new_moon_intention": {
        "name": "New Moon Intention",
        "positions": ["what_i_am_releasing", "what_i_am_calling_in", "what_supports_this", "the_action_step", "the_blessing"],
        "description": "A five-card ritual spread for new moon, new beginnings, and conscious intention-setting.",
    },
    "relationship_deep": {
        "name": "Relationship Deep",
        "positions": ["your_energy", "their_energy", "the_bond", "what_strengthens", "what_challenges", "hidden_dynamic", "guidance"],
        "description": "A seven-card spread for depth and nuance in any significant relationship — romantic, platonic, or creative.",
    },
}

ALL_CARDS: Final[list[Card]] = MAJOR_ARCANA + MINOR_ARCANA


def _normalize_card_name(name: str) -> str:
    return " ".join(name.replace("-", " ").replace("_", " ").split()).casefold()


_CARD_BY_NAME: Final[dict[str, Card]] = {}
for _card in ALL_CARDS:
    _CARD_BY_NAME[_normalize_card_name(_card.name)] = _card
    if _card.name.startswith("The "):
        _CARD_BY_NAME[_normalize_card_name(_card.name[4:])] = _card


def get_card_by_name(name: str) -> Card:
    normalized = _normalize_card_name(name)
    try:
        return _CARD_BY_NAME[normalized]
    except KeyError as exc:
        raise KeyError(f"Unknown tarot card: {name}") from exc


__all__ = [
    "Card",
    "MAJOR_ARCANA",
    "MINOR_ARCANA",
    "SPREADS",
    "ALL_CARDS",
    "get_card_by_name",
]
