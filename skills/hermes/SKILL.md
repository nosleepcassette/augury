---
name: Augury Tarot
description: Tarot reading engine with a local Rider-Waite deck.
---

# Augury Tarot

Use this skill for local tarot readings and card reference work.

## CLI

`augury` on `PATH`

If `augury` is not yet on `PATH`, install stable launchers with:

```bash
python3 -m augury configure --no-input --install-launchers
```

That installs `augury` and `augury-discord` into `/usr/local/bin` by default, or
`~/.local/bin` as a fallback when `/usr/local/bin` is not writable.

## Capabilities

- single card draw: `augury read --spread single`
- three-card spread: `augury read --spread three-card`
- celtic cross: `augury read --spread celtic-cross`
- daily card: `augury daily`
- card lookup: `augury card "The Fool"`
- reading history: `augury history --limit 25`
- path inspection: `augury paths --json`

## Notes

- Uses a local 78-card Rider-Waite deck.
- Interpretations are template-based.
- No external API calls are needed.
- Reading history is stored under the Augury user data directory reported by `augury paths`.
- When showing a reading, include each card's ASCII art with the interpretation instead of only naming the card.
- Reading payloads and saved history include the card art, so preserve it when quoting or logging a draw.
