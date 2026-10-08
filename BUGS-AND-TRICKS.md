# Bugs we've spotted and tricks that help

## Getting data (spreadsheet, Roll20 and tool makers)
- **"It works sometimes, then hangs":** don't fire hundreds of requests at
  once. Use a few at a time (4–6), a 30-second timeout and 3 retries with a
  short wait. That's how `lyrian_pull.py` got ~545 requests with zero
  failures on 2026-10-08.
- **"The site doesn't serve the data anymore":** the pages load their data
  in the browser from `https://clio-proxy.angelssword.com/api/ttrpg`. Reading the HTML
  page gets you an empty shell; read the feed instead (see `AI-NOTES.md`).
- **Descriptions went blank after 0.13.2:** text fields switched from base64 to
  plain HTML. Check for `<` before trying to base64-decode.
- **Class-tier / class lookups break on a few classes:** `"Flash Star Blade
  Style "`, `"Magitechnician "` and `"Onmyoji "` (and key ability `"Five
  Harmonies "`) have a trailing space. Trim names before matching, or better,
  match on `indexId`.
- **Abilities added at the wrong level:** the same ability can sit at different
  levels in different classes (Lunge: Lancer 2 / Fencer 4; Battle Cast:
  Archsage 2 / Battle Mage 4). The level comes from the class's slot. Store
  (class, level) pairs; `derived/class_progression.json` has them.
- **Weapon mods crammed into one cell:** Clio's `items-mods.json` (in
  `extras/`) lists the mods for the 107 moddable items, with tier (A/B/C/F,
  F = Frame) and point cost.
  - Price = mod points × 25 Clim.
  - Polarity mods (entries with `pt`/`pc`) also need `pc` units of the named
    material.
  - Per-item limits: see `RULES-AND-RULINGS.md`.
- **Know when to update:** compare `version/latest` with the version you
  have. 0.13.2 was already current on 2026-09-07 and still is. No rules text
  changed between then and 2026-10-08, only image links.

## Roll20 "Lyrian Chronicles" sheet: possible causes for reported bugs
We spotted these by reading the public sheet code (Roll20's community repo,
`LyrianChronicles/LyrianChronicles.html`, as of 2026-10-08). They're leads to
check, not confirmed fixes.

1. **Old macros stick until you remove and re-add the ability.**
   - **What we saw:** the default macro (`ability_default_roll`, from
     `abilityMacroMap`) is only set when an ability is picked in
     `ability_select`, and autofill skips abilities that already exist.
   - **Idea:** keep a sheet-version attribute. On `sheet:opened`, if the
     version changed, loop `repeating_abilities` and re-apply the current
     macro and description to every row whose `ability_select` is a known key
     (skip `custom`). Everyone's sheets refresh once, automatically.
2. **Requirements missing on auto-filled abilities.** The autofill writes
   `repeating_abilities_<id>_ability_reequirements` (double "e"), while the
   pick handler and the rest of the sheet use `ability_requirements`.
3. **Mount section / Trample not using mount power.**
   - **What we saw:** the `change:repeating_mounts` handler checks
     `mount_type === "current-mount"`, but `mount_type` doesn't appear to be
     in the attributes it reads. So the "current mount" copy (including
     `current_mount_power`) may never be filled.
   - **Confirmed in the sheet source:** the Mount Type box is
     `<input type="number" name="attr_mount_type">`. That's why it only
     accepts digits, "e" and ".", and why "current-mount" can never be typed
     into it, so the comparison can never match.
   - Also, the "Current Mount Focus" box is bound to
     `attr_current_mount_power`.
4. **Using the clicked weapon instead of the main weapon.** The sheet's own
   weapon-row roll already reads the clicked row's stats (`clicked:repeating_weapons`).
   The gap appears to be in ability macros, which read `main_weapon_*` (about
   410 references in `abilityMacroMap`).

**Workaround players already use:** if an ability's text or macro looks old,
delete the ability and add it again.

## Importing characters into Roll20 today
- GitHub user EliLeeVT published a copy of the Lyrian Chronicles sheet with
  **import boxes**:
  `github.com/EliLeeVT/lyrian-chronicles-clio-import-roll20-character-sheet`.
  - The player side reads Clio's `"format": "angelssword-character"` file.
  - The NPC side reads Clio's monster tool.
  - It installs as a Roll20 Custom sheet.
- Character files in that format come from the official Clio builder and from
  VerboseBard's builder (`.aschar.json` export).

## Saved characters going stale (for anyone building a sheet or app)
If you copy an ability's text into the character when it's added, it goes stale
on the next rules update. Store the `indexId` plus any player edits. Re-read
everything else from the current data whenever the data version changes.

## Smaller confirmed facts
- **Precise Attack's Pinpoint:** ignore Guard equal to your Focus; Guard can't
  go below 0 (rulebook).
- **Criticals:** a natural 20 that hits deals max damage plus half-pierce. A
  target taking the Block action can't be crit (rulebook).
- **Heavy damage:** `2*(powers)+damage` and `(2*(powers)+damage)` are
  identical.
