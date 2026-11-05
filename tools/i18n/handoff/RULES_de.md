# Translation rules (Polish -> German), MT2009 server texts

Input: a file of lines `ID<TAB>Polish<TAB>English`. The Polish is the source: player-facing text of a fantasy MMORPG
server (NPC dialogue in the quest window, quest titles, menu options, system chat messages, notices). The English is a
reviewed translation of the same line - use it to understand the Polish, but translate the meaning of the Polish.
Escapes are written as text: `\n` (newline), `\t`, `\\` - keep them exactly as written.

Output: a file of lines `ID<TAB>translation` (UTF-8), one per input ID, same order, nothing else.

Rules:
1. Keep EXACTLY, in the same order and count: printf placeholders (`%d %s %u %ld %lu %lld %.1f %02d %%` ...), tags in
   square brackets written in capitals (`[ENTER]`, `[COLOR ...]`, `[DELAY ...]`, `[INSERT_IMAGE ...]` ...), and the
   leading / trailing spaces of the line. Many lines (IDs starting with `F`, and others) are pieces glued at runtime to
   numbers or names: `"Koszt: " .. n .. " Yang."` - the piece `" Yang."` keeps its leading space and shape. Translate so
   that the pieces still read correctly in that order.
2. Keep the length close to the Polish (the quest window splits sentences over several lines; each line is one input).
   Do not merge or reorder lines; a sentence cut in the middle stays cut in the same place as well as the language
   allows.
3. Game terms: item and monster names - use the official names from the glossary
   `/opt/metin2/git/wt-y-tr-quest/tools/i18n/handoff/glossary_de.tsv`
   (Polish<TAB>English<TAB>German<TAB>kind; grep it by the Polish or the English name). The official phrasing of the
   stock game in this language: `/opt/metin2/git/wt-y-tr-quest/linux-port/docker/game/lang/de/10_quest_stock.tsv`
   (Polish<TAB>German) - grep it for a term (e.g. Yang, EXP, Dragon Coins, Metin Stone, Spirit Stone, Blessing Scroll,
   dungeon, Biologist, Blacksmith) to use the game's usual word in this language. Proper names (NPCs, places like
   Yohara, Seon-Hae, Chaegirab, Jaharr, Enasir, Balathor, Sung Mahi) stay as they are.
4. Never write "Metin2", "Gameforge", "official server", "Ameria", "metin2alerts".
5. Every character must exist in the client's code page cp1252 (the check below tests it). Use plain ASCII
   punctuation (straight quotes, "-"); for Romanian use ş ţ (cedilla), not ș ț.
6. A line that is not player text (a technical identifier, a GM command's syntax line, a debug line full of `%u` codes)
   or a proper name that stays the same: output `ID<TAB>` followed by the Polish unchanged.
7. Natural, friendly, short German as in an MMORPG; address the player informally as the game in this language does
   (look at the stock file). Keep the tone. Numbers with spaces as thousands separators stay as written.

Write the output with the Write tool to the path given in your task (if you write it in several pieces, write
separate files and join them with `cat` into the output path). Then run
`python3 /opt/metin2/git/wt-y-tr-quest/tools/i18n/handoff/check_tr2.py <input> <output> cp1252`
and fix every problem it lists until it reports 0 problems. Report only "done N lines".
