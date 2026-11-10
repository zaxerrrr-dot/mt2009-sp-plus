# Wytwarzanie wielu sztuk naraz (MT2009_PLUS_CUBE_BATCH_V1)

Discord, 9 November 2026: "nie przerabia sokow wody po 200 szt. Loga (wylogowuje / rozlacza)".

## The cause

The juices and waters are cube recipes (locale cube.txt; Yu-Hwan 20017, Huahn-So 20022, Rybak 9009 / Baek-Go 20018 for
the juices): Kwiat Brzoskwini 50721 -> Sok z Kwiatu Brzoskwini 50801, Sok + Bez 50725 -> Woda Sim 50813 / Woda Dok 50814,
100 Sok z Kwiatu Kaki / Korzenia Gango + Grzyb Tue 50726 -> 100 Woda Bo / Young 50815 / 50816.

The crafting window (client root/uicuberenewal.py, MT2009_PLUS_CUBE_RENEWAL_V1) made N attempts by sending
"/cube make" N times in the same frame - 200 for a full stack. On the server:

- `interpret_command` (cmd.cpp, ENABLE_ANTI_CMD_FLOOD) lets 10 commands through per 500 ms and drops the rest, so a
  200 click made 5-14 attempts (the cube log of a live server: 6-7 rows per click, 1 November);
- `CInputMain::Analyze` (input_main.cpp) closes the connection at 300 packets in one second - the 200 makes plus the
  window's "/cube del" / "/cube add" / "/cube pick" and a second click (the player clicks again, as few were made):
  hack_log `FLOOD_HEADER_3` (HEADER_CG_CHAT) in the very seconds of those cube rows.

## The fix

- `cmd_general.cpp` do_cube: "/cube make <n>" (a number) calls `Cube_make_batch(ch, n)`; "/cube make" (one attempt)
  and "/cube make <word>" (the old loop until the first failure) stay.
- `cube.cpp` `Cube_make_batch` (1-200 attempts):
  - a plain recipe (one reward, no set_value / copy_attr / fail_keep, Yang >= 0, chance > 0): n is cut to what the
    window's materials, the Yang and the Gaya pay for; the n rolls are made (the chance-raising item's bonus on as many
    attempts as it has pieces, one piece each, as `Cube_make_window`), the materials taken at once (one update per
    stack), the Yang and Gaya at once, the results given as full stacks of 200 (a blend item - its value rolled per
    item - or an unstackable one attempt by attempt); two cube log rows (the successes with their total, the failures)
    and one `CubeBatch <ok> <tried> <vnum> <count>` back;
  - any other recipe: `Cube_make_window` n times in this one command, stopping when an attempt took nothing (a set /
    copied / kept piece: once), then `CubeBatch`.
  - nothing payable: one `Cube_make_window` for its own refusal text, `CubeBatch 0 0 ...`.
- Client (root/uicuberenewal.py, game.py): one "/cube make <n>" for a batch, `OnCubeBatch` ends it ("Udane proby:
  ok z n"); an older server (no CubeBatch) still ends by the timeout.

Overflow: results that do not fit the bag go where `AutoGiveItem` puts them (the ground, the owner's) - as before.

Developer: `python3 gen_edits.py <game/src>` writes edits.json and checks each anchor is there once.
Linux: `python3 apply_cubebatch.py <game/src>`; Windows: `Apply-CubeBatchPatch.ps1` (tools/port/Apply-MT2009PlusEngine.ps1,
last). The Linux deploy list needs "cubebatch".
