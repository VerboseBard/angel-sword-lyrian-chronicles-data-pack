# AI notes: using the Lyrian Chronicles data

Paste this file to your AI before asking it to work with the data. The counts,
links and gotchas here were checked against the 0.13.2 data on 2026-10-08.
Statements about older versions come from earlier pulls.

## Ground rules for the AI
1. **Rules come from the data and the rulebook text, never from memory.** Quote
   the field you used. If two sources disagree, say so; don't pick one silently.
2. **Key everything on `indexId`.** It's a UUID that stays the same across
   rules versions. Don't store `id` (a database id that changes every version).
   Slugs like `trueAbilityId` / `classId` are readable but can change: in 0.13.2
   Warning Shot's slug went from `warning_shot` to `warning-shot`, while its
   `indexId` stayed `38d587b1-7ed6-4c69-a0a1-a543e49b08d9`.
3. **Keep the last good copy.** On a new version, pull into a new folder and
   compare by `indexId` (added / removed / changed fields) before replacing
   anything.
4. **Be gentle with the server.** Check `version/latest` first and pull only
   when it changes. Make no more than 6 requests at a time, with a timeout and
   retries. `lyrian_pull.py` already does this.

## Where the data comes from
Base: `https://clio-proxy.angelssword.com/api/ttrpg`. This is the feed the
official site loads from; it is open, with no key.

| Request | Returns |
|---|---|
| `version/latest` | `{versionNumber, versionId, name}`; 0.13.2 on 2026-10-08 |
| `version/list` | All 38 published versions |
| `{v}/classes`, `key-abilities`, `true-abilities`, `items`, `breakthroughs`, `keywords`, `primary-races`, `ancestries`, `monsters`, `monsters-abilities`, `monsters-abilities-lists`, `monsters-active-actions`, `monsters-active-actions-lists` | Full lists |
| `{v}/rulebook`, `settings-guide`, `patch-notes` | `{id, content}` with the whole text as one HTML blob |
| `{v}/class/{classId}`, `item/{itemId}`, `monster/{monsterId}`, `primary-race/{primaryRaceId}`, `ancestry/{ancestryId}` | One detail record. Lists are summaries, so **use the detail records**. |

Extras on the official Clio builder (not the feed):
`https://clio.angelssword.com/characterbuilder/data/items-mods.json` and
`mod-descriptions.json`.

**Format change in 0.13.2:** text fields now arrive as **plain HTML**. Older
versions sent them **base64-encoded**. A reader that only decodes base64
silently loses every description. In `clean/`, each HTML field has a
plain-text twin ending in `Text`.

## How the files link together

| From | Field | Points to |
|---|---|---|
| `class_details` | `keyAbility` | `key_abilities.indexId` |
| `class_details` | `ability1`, `ability2`, `ability3`, `ultimateAbility` | `true_abilities.indexId` |
| `key_abilities` | `associatedAbility` | `true_abilities.indexId` (null or `""` when there isn't one) |
| `ancestry_details` | `trait1`–`trait3` | `true_abilities.indexId` (all 122 resolve) |
| `ancestry_details` | `primaryRace` | primary race **name** (a string, not an id) |
| `primary_race_details` | `ability1`, `ability2` | `true_abilities.indexId` |
| `primary_race_details` | `wi`, `lir`, `d`, `ar`, `lu`, `ni`, `un`, `vi`, `none` | choice objects `{text, ability}`; `ability` → `true_abilities.indexId`. Only Demon has them filled in 0.13.2 (nine house options); the other four races have empty objects. |
| `breakthroughs` | `ability` | `true_abilities.indexId` (only 5 breakthroughs use it) |
| `monster_details` | `abilities` | `monster_ability_lists.indexId` → `ability1`–`ability6` → `monster_abilities.indexId` |
| `monster_details` | `activeActions` | `monster_active_action_lists.indexId` → `action1`–`action6` → `monster_active_actions.indexId` |
| `true_abilities` | `keywords` | comma-separated **names**. See the gotcha below. |
| `extras/items-mods.json` | key = item slug (e.g. `bow--two-handed-`) | list of mods `{n: name, t: tier A/B/C/F (F = Frame, only on armor and accessories), p: crafting points, s: "s" item-specific / "u" universal}`. 832 of the 2,881 entries also have `pt` (a polarity material, e.g. Salachar) and `pc` (units of it needed, e.g. 4000). |

### Class levels: slot order gives the level
Every class has a key ability plus 7 purchasable steps; the rulebook calls
them "7 levels of normal abilities". The fields don't contain numbers. Levels
1–8 are the order the official builder sells them in, and the numbering the
community uses (Lunge: Lancer 2, Fencer 4):

| Level | Field | Kind |
|---|---|---|
| 1 | `keyAbility` | key ability; unlocking the class |
| 2 | `ability1` | ability |
| 3 | `skills` | text |
| 4 | `ability2` | ability |
| 5 | `heart` | text |
| 6 | `ability3` | ability |
| 7 | `soul` | text |
| 8 | `ultimateAbility` | ability |

`derived/class_progression.json` has this already laid out.

**The same ability can be a different level in different classes:**
- Lunge = Lancer level 2 but Fencer level 4.
- Battle Cast = Archsage level 2 but Battle Mage level 4.

These are the only two abilities in 0.13.2 that differ by class, but never
store a single "level" on an ability. Store (class, level) pairs; see
`derived/ability_sources.json`.

## Gotchas (all real, all in 0.13.2)
- **Trailing spaces in names:** classes `"Flash Star Blade Style "`,
  `"Magitechnician "`, `"Onmyoji "`, and key ability `"Five Harmonies "`.
  Exact-match lookups fail. Trim before comparing. `clean/` trims them and
  keeps `nameOriginal`.
- **`keywords` holds more than keywords.** Besides real keyword names, it holds
  tags with no keyword record: elements (Arcane, Earth, Frost, Wind, Dark…),
  `Healing`, `Encounter Start`, `Shield`, `Aura`, `Poison`, `Mind Affecting`,
  and a `-` placeholder (38 times). Fire is the one element that does have a
  keyword record. Treat unknown entries as tags, not errors. Separators are
  inconsistent (`Spell,Celestial` and `Spell, Celestial`), so trim each part.
- **Numbers are strings, and some aren't numbers:**
  - `tier: "2"`;
  - monster `evasion: "7 / 20"`, `initiative: "+1"`, `movementSpeed: "20ft"`;
  - monster `lightAttack: "+2 Accuracy, 2d4+3"`;
  - item `cost: "Original Weapon + 3000"`, `burden: "Original Weapon"`.

  Parse defensively, and keep the original text.
- **11 abilities aren't linked by id from any class, race, ancestry,
  breakthrough or key ability:** Anathema, Astral Projection, Corpse Domination,
  Elemental Mastery: Frost, Emergency Shield, Empower Mana Shield, Freerunner,
  Good Fortune, Hydromancer, Lightning Rod, Pixie Flight. Only two are granted
  by another ability's text: Hydromancer by Blue Soul, and Elemental Mastery:
  Frost by Chilling Cold. For the other nine we found no source anywhere in
  the 0.13.2 data. They may be unused, granted some other way, or gaps in the
  official data. Search the text before calling one orphaned.
- **Weapon mods aren't structured in the feed.** On weapon items they sit inside
  the description text ("A mods: … B mods: …"), plus four "Universal … Mods"
  items. Use `extras/items-mods.json` for a structured version.
- **The rulebook is one big HTML string.** Split on `<h2>`/`<h3>` headings if you
  need sections.

## Keeping saved characters current (lesson from the Roll20 sheet)
If a sheet copies an ability's text or macro into the character when it's
added, that copy goes stale after every rules update. Players then have to
remove and re-add the ability to refresh it. Better:
- store only the reference (`indexId`) plus the player's own overrides;
- on load or version change, re-read name, description, costs and macro from
  the current data, unless the player customised that entry.

## Checking your work
- Counts in 0.13.2:
  - classes 185, key abilities 179, abilities 958;
  - items 206, breakthroughs 89, keywords 92;
  - ancestries 44, primary races 5;
  - monsters 84, monster abilities 144, monster actions 163.
- Every `class_details` slot resolves (0 broken links); all ancestry traits,
  breakthrough abilities and key-ability links resolve.
- `manifest.json` lists SHA-256 for every file. If your copy's hashes match,
  you have exactly what we pulled.
