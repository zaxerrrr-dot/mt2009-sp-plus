# Translation rules (Polish -> English), MT2009 server texts

Input: a file of lines `ID<TAB>Polish`. The Polish is player-facing text of a fantasy MMORPG server (NPC dialogue in the
quest window, quest titles, menu options, system chat messages, notices). The game's own escapes are written as text:
`\n` (newline), `\t`, `\\` - keep them exactly as written.

Output: a file of lines `ID<TAB>English` (UTF-8), one per input ID, same order, nothing else (no header, no comments).

Rules:
1. Keep EXACTLY, in the same order and count: printf placeholders (`%d %s %u %ld %lu %lld %.1f %02d %%` ...), tags in
   square brackets (`[ENTER]`, `[COLOR ...]`, `[DELAY ...]`, `[INSERT_IMAGE ...]` ...), and the leading / trailing
   spaces and edge punctuation of the line. Many lines (IDs starting with `F`, and many others) are pieces glued at
   runtime to numbers or names: `"Koszt: " .. n .. " Yang."` - the piece `" Yang."` must stay `" Yang."`-shaped (a leading
   space stays, a trailing space stays). Translate so that the pieces still read correctly in that order.
2. Keep the length close to the Polish (the quest window splits sentences over several lines; each line is one
   input). Do not merge or reorder lines; a sentence cut in the middle stays cut in the same place as well as English
   allows.
3. Game terms: item and monster names - use the official English from the glossary
   `/opt/metin2/git/wt-y-tr-quest/tools/i18n/handoff/glossary_en.tsv` (Polish<TAB>English<TAB>...;
   grep it, e.g. `grep -i "^Kamień Duszy" glossary_en.tsv`). Official phrasing of the stock game:
   `/opt/metin2/git/wt-y-tr-quest/linux-port/docker/game/lang/en/10_quest_stock.tsv` (Polish<TAB>English). Usual terms:
   Yang = Yang, PD / Pkt. Doś. = EXP, Smocze Monety = Dragon Coins, Smocze Znaki = Dragon Marks, Kamień Metin = Metin Stone,
   Kamień Duszy = Spirit Stone, Zwój Błogosławieństwa = Blessing Scroll, Magiczny Kamień / Kamień Magii = Magic Stone,
   lochy / loch = dungeon, Poziom Czempiona = Champion Level, Sung Ma = Sung Ma, Gaya = Gaya, Szarfa = Shoulder Sash,
   Alchemia (Smocza) = Dragon Stone Alchemy, Czempion = Champion, Biolog = Biologist, Kowal = Blacksmith,
   SZC / Szczelina = Rift (keep the abbreviation "SZC" if it stands alone), Boss Świata = World Boss, ItemShop = Item Shop.
   Proper names (NPCs, places like Yohara, Seon-Hae, Chaegirab, Jaharr, Enasir, Balathor, Sung Mahi) stay as they are.
   Polish without diacritics ("Twoj wynik") is still Polish - translate it.
4. Never write "Metin2", "Gameforge", "official server", "Ameria", "metin2alerts". If the Polish has one,
   leave that word out or use a neutral word ("the game").
5. A line that is not player text (a technical identifier, SQL, a GM command's syntax line like `/goblin gm ...`, a
   debug line full of `%u` codes, or a text already in English): output `ID<TAB>` followed by the source unchanged.
6. Natural, friendly, short English as in an MMORPG. Address the player as "you". Keep the tone (NPC speech, system
   messages). Numbers with spaces as thousands separators ("5 000 000") stay as written.

Write the output with the Write tool to the path given in your task (create it once, all lines). Then verify with a
quick script that every input ID is present exactly once and that the placeholders / [TAGS] / leading-trailing spaces
match the Polish line by line (fix any mismatch). Report only "done N lines, M kept unchanged".
