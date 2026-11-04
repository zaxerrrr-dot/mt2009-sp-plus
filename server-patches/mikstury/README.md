# Mikstury bez limitu (MT2009_PLUS_MIKSTURY_V1)

The owner, 4 November 2026 (cache/yohara/decyzje-lowienie-mikstury.md, M1 / M6; the research
cache/yohara/mikstury-analiza.md §C / §5):

- different bonuses always run together - no group caps, no cross-family blocks;
- the same bonus (affect type + point) from the same kind of item is refreshed, or replaced by an equal or
  stronger one; a weaker one is refused ("Silniejszy efekt tego rodzaju już działa.");
- the same value still running at least as long as the new one would is refused too ("Ten efekt już działa i
  potrwa dłużej niż nowy.") - the item would be spent for nothing.

The (type, point) identity stays unique: the server and the client's affect bar key an affect by it, so two copies
of one bonus never add up (one Czerwona Rosa at a time; the second refreshes or upgrades). The same bonus from
*different* families (Woda Dok 516 + Czerwona Rosa 531 + Dłoń Krytyka 510 + a herbal potion 352) are separate
records and all run.

## The engine (this patch: edits.json, applied last - after skillcolor)

`MiksturyMayRefresh(ch, type, point, value, duration)` (char_affect.cpp) is the rule; `CHARACTER::UseItemEx`
(char_item.cpp) asks it on every buff path and then adds with override + per point (`IsCube`):

| tag | path | before | now |
|---|---|---|---|
| juice | `ITEM_USE` 50801-50820 `USE_ABILITY_UP` (juices, waters) | "already activated" whatever the value | refresh / upgrade |
| water | Woda Sim / Dok (`USE_AFFECT`, 516) | "already activated", appended | refresh / upgrade, override |
| speed mov / att | generic `USE_ABILITY_UP` speed potions | a +10 overwrote a +60 | a weaker one refused |
| stats | generic `USE_ABILITY_UP` ST/DX/HT/IQ/cast/att/def (sushi) | one `AFFECT_STR` record for every stat (Sushi z Łososia took Sushi z Suma off) | one record per stat; `POINT_RESIST_MAGIC` added |
| use affect | generic `USE_AFFECT` (ItemShop potions, Dłoń Krytyka ...) | the same (type, point) refused; refused when a herbal BOOST potion gave the point | refresh / upgrade; the BOOST cross-block gone |
| blend | `ITEM_BLEND` (dews 50821-50826, elixirs 50830-50853) | the same point refused; **every** dew / elixir refused while Woda Mong ran | refresh / upgrade (a golden elixir replaces a normal one); the Woda Mong block gone |

Developer: `python3 gen_edits.py <game/src>` writes edits.json and checks each anchor is there once.
Linux: `python3 apply_mikstury.py <game/src>`; Windows: `Apply-MiksturyPatch.ps1` (tools/port/Apply-MT2009PlusEngine.ps1).

## Outside the engine

- The herbal potions and the grilled fish (item type 36) go through the quest library `potion_system.lua`:
  game/quest/m2_mikstury_limity.lua replaces `potion_system.use_potion` (Dockerfile `MT2009_PLUS_MIKSTURY_V1`) -
  no group caps (BOOST 5 / OFFENSIVE 3 / DEFENSIVE 2 / FOOD 2 gone), no block by an ItemShop speed potion, the same
  refresh / upgrade rule, and the fish exceptions (decision 9): the EXP fish (Słodka Ryba 27879 < Złoty Karaś 27883
  < Rak Niebieski 27887) never run together - a better one switches the previous off, a weaker one is refused while a
  better runs; Złoty Karaś and Krab Królewski (27886) exclude each other. Baek-Go's recipe potions lose their group
  cap the same way; their crafting is untouched.
- The bots: playerbot_duel.h (the BOOST and Woda Mong conditions gone) and playerbot_herbalism.h (one herbal potion
  per (group, point), not per group).
- The client: root/uiautohunt.py `ItemAffectPresent` (the same two blocks gone; the juices / waters' 516 and the
  type-36 potions' 350+group affects recognised, so autohunt drinks a buff only when it is gone).
