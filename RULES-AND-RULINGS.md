# Rules and rulings we've confirmed

Unofficial fan notes, not made or endorsed by Angel's Sword Studios. Each
line says where it came from. Rulebook = the 0.13.2 rulebook text in
`data/0.13.2/clean/rulebook.json` (`contentText`). Official builder rulings
came from Angel's Sword's own Clio character builder in July 2026 (rules
0.13.1); recheck them after big updates.

## Character creation (rulebook)
- **Stats:**
  - main array (5, 4, 4, 3) across Power / Focus / Agility / Toughness;
  - sub array (5, 4, 3, 2, 1) across Fitness / Cunning / Reason / Awareness / Presence.
- **Derived stats:**
  - Spirit Core = total EXP spent (starts 0).
  - HP = 20 + (Toughness × 10). Mana = 6 + Power. RP = 2 + Agility.
  - Guard = equipment value + Toughness. Guard takes 1 off each point of
    damage but can't reduce an attack below 1. Block or a similar action
    can, and resistance or damage reduction applies afterward and can bring
    it to 0.
  - Initiative = Agility. Evasion = 7 + Agility. Potency = 11 + Focus.
  - Save bonus = Toughness. Speed = 20.
- **Breakthroughs:** 300 EXP that can only be spent on breakthroughs. This
  EXP is not added to Spirit Core, and anything unspent after character
  creation is removed.
- **Classes:**
  - start with 1000 class EXP + 3 Interlude Points;
  - a new class costs 1 IP + 100 EXP per tier;
  - each class has 7 more abilities at 100 EXP each, bought in order.
- **Class levels** (data, not prose): 1 key ability, 2 ability, 3 skills,
  4 ability, 5 heart, 6 ability, 7 soul, 8 ultimate. See `AI-NOTES.md`.

## Attacks (rulebook)
- **Light Attack:** 1 AP, 2d4 + Power.
- **Heavy Attack:** 2 AP, 4d6 + (2 × Power), or 5d6 + (2 × Power) with a
  two-handed melee weapon making a melee attack.
- **Precise Attack:** 2 AP, 2d4 + Power, Focus doubled for accuracy, with
  **Pinpoint** (ignore the target's Guard equal to your Focus; Guard can't go
  below 0).
- **Critical hit:** a natural 20 that hits deals maximum damage and gains
  half-pierce. A target taking the Block action can't be critically hit.
- **Order of operations (math note, not from the rulebook):** `2*(power + weapon power + extra power) + extra
  damage` gives the same number with or without outer parentheses. It's all
  addition.

## Official builder rulings (from Clio's builder code, July 2026)
- **Humans:** +100 class EXP (1,100 total). Part of it can go to creation
  breakthroughs; the builder tracks how much was spent.
- **Skill cap:** 15 for every skill at creation, including artisan and
  gathering. The old artisan cap of 10 was wrong. The rulebook adds 5 at
  Skybound tier (5k Spirit Core) and removes the cap at 10k. Expertise cap is also 15; artisan expertise is
  effectively 14, since 1 point converts to 2 (ruling 2026-07-18).
- **Artisan skills:** Alchemy, Blacksmith, Farming, Carpentry, Armorsmithing,
  Artificer, Culinary.
- **Gathering skills:** Mining, Herbalism, Foraging, Fishing, Hunting, Logging.
- **Specialized weapon groups:** Pistol, Shotgun, Sniper Rifle, Saboteur
  Thread Daggers, Lance, Whip, Chainsaw, Channeling Weapons.
  - Gauntlets are **not** a selectable specialized proficiency; they come with
    Unarmed (2026-07-20).
  - Chainsaw was added (2026-07-20); it's not in the 0.13.2 rulebook's list
    yet.
  - Artifices are attachments, not weapons.
- **Skilled Flier** needs an ancestry trait literally named "Flight" (Harpy,
  Tengu, Pixie) or the Racial Flight breakthrough. A Sylph's Fly ability does
  **not** count (2026-07-16).
- **Leftover Interlude Points at creation:** Job (+300 Clim), Train (+25 EXP)
  or Other (GM decides).
- **Transmuter:** at most 2 disciplines (one from Transmuter, one from
  Alkahest) (2026-07-18).
- **Fixed racial expertise,** pre-granted and free:
  - Anubis: Insight (Discern Lies) +5.
  - Cu Sith: Perception (Smell) +5.
  - Mothfolk: Perception (Vibration Sense) +10.

## Designer answers (questions sent by VerboseBard, answered 2026-07-22)
1. **How many items can you carry?** Burden is the limit, plus obvious
   exclusivities (e.g. not two cloaks).
2. **Do bonuses from the same source stack?** No. A shield's block bonus
   applies once however many shields you hold.
3. **Two-handed versions:** proficiency in a weapon group covers both its
   one-handed and two-handed versions.
4. **Quick-access items:** burden is the only limit.
5. **Changing armor in combat:** no rule allows it by default. Exceptions:
   Armiger, and Mage Armor (Battle Mage).
6. **Mods:** mods are added **when the item is crafted**. They're part of
   the item, not attached later. **Mirane:** you can't buy modded armor at
   character creation. The official builder goes further and offers no mods
   at all for Mirane starting gear.

## Weapon and armor mods (official mod rules + rulebook)
- **Per item (official builder rule; not stated in the rulebook):**
  - max one A mod and one B mod;
  - one Frame mod, which only armor and accessories have;
  - one material.

  The 0.13.2 rulebook says armor takes 1 modification unless stated, which
  disagrees with this for armor. Recheck with the designers.
- **C mods (artifices):** limited by the material's C slots: 1 normally,
  2–5 with special artifice parts.
- **Alloy mods** need the matching alloy in the item.
- **Armor:** one modification unless stated. Armor mods are added only when
  the armor is made; Armor Plates are the exception (rulebook).
- **Artifice attachments** (Blaster, Buster, Silencer…): one slot on regularly
  crafted weapons. Artifice weapons and unique weapons such as Astra Relics
  generally have none (rulebook).
- **Value of a modded item:**
  - base cost + 25 Clim per crafting point of each mod + materials (rulebook);
  - for modded alchemy, the mod's value is divided by 3.
- **Mirane:** the designers said modded armor can't be bought at character
  creation. The official builder goes further and offers no mods on starting
  gear at all. Items bought after the game begins can have mods (official
  builder).

## Mirane, as said publicly in the community channel
- Starting Clim is 4,000 in Mirane vs 3,000 in a normal game (Florentino).
- IP resets weekly in Mirane, and you may use an IP for the week you join
  (Florentino).
