# Lyrian Chronicles data pack (rules 0.13.2, pulled 2026-10-08)

A copy of the Lyrian Chronicles rules data, plus a small script to pull a fresh
copy whenever the rules update. It's for anyone keeping a sheet, macro set,
spreadsheet, Foundry system or tool up to date.

- **Shared by:** VerboseBard (Angel Sword: Lyrian Chronicles Character Builder).
- **Unofficial fan resource.** Not made or endorsed by Angel's Sword Studios.
- **Game content:** © Angel's Sword Studios, shared here so fan tools can stay
  current. Credit them, and check with them before any commercial use.

## What's in here

| Path | What it is |
|---|---|
| `data/0.13.2/raw/` | The official feed's responses as received (23 files). 18 are byte-for-byte; the five `*_details.json` files join the individual detail responses into one list. |
| `data/0.13.2/clean/` | Same records plus a plain-text copy of every HTML field (`descriptionText`, `requirementText`…). Names with stray trailing spaces are trimmed; the original is kept in `nameOriginal`. |
| `data/0.13.2/derived/class_progression.json` | What every class gives, in level order 1–8 (key ability, abilities, skills, heart, soul, ultimate). |
| `data/0.13.2/derived/ability_sources.json` | For each of the 958 abilities, every class + level, ancestry, race, breakthrough or key ability that grants it. |
| `data/0.13.2/extras/` | Clio's structured weapon/armor mod files (`items-mods.json`, `mod-descriptions.json`). |
| `data/0.13.2/manifest.json` | Version, time pulled, record counts, SHA-256 of every file. |
| `lyrian_pull.py` | The script that made all of the above. |
| `AI-NOTES.md` | **Give this to your AI.** How the data fits together, gotchas, safe-use rules. |
| `RULES-AND-RULINGS.md` | Rule numbers and dated rulings we've confirmed, with sources. |
| `BUGS-AND-TRICKS.md` | Things that trip people up, plus specific bugs we've spotted. |

## Counts (0.13.2)
- 185 classes, 179 key abilities, 958 abilities.
- 206 items, 89 breakthroughs, 92 keywords.
- 44 ancestries, 5 primary races.
- 84 monsters, 144 monster abilities, 163 monster actions.
- The rulebook, settings guide and patch notes.

**Change check:** compared with our full pull on 2026-09-07, no rules text
changed. Only image links differ.

## Pull a fresh copy yourself

Needs Python 3.8+ and nothing else.

```
python lyrian_pull.py --check              # what's the latest rules version?
python lyrian_pull.py                      # pull it into ./lyrian-data/<version>/
python lyrian_pull.py --extras             # also grab the weapon-mod files
python lyrian_pull.py --force              # pull again even if you already have that version
```

- A full pull is about 545 requests, 4 at a time, and takes 1–2 minutes.
- If you already have that version, it does nothing.
- If anything fails, it prints the failed addresses and leaves your previous
  copy alone.
- By default it writes to `./lyrian-data/<version>/`. The `data/` folder here
  was made with `--out data`.
- On macOS with python.org Python, run "Install Certificates.command" once if
  you get a certificate error.

## Please be gentle with their server
- Only pull again when `--check` shows a new version. The script already
  skips versions you have.
- Don't raise `--parallel` above 6, and don't run it on a timer every few
  minutes.
- The script stops itself after 10 failures in a row and honours "slow down"
  replies from the server.
- This feed is what the official website itself loads from. It's open today,
  but Angel's Sword can change it at any time.

## Using it with an AI
Give your AI `AI-NOTES.md` first, then point it at the `clean/` and `derived/`
folders. Those notes tell it which fields link to which. They also list the
traps: names with trailing spaces, ability ids that changed between versions,
the "keywords" field holding more than keywords, and so on.
