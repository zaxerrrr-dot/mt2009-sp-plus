# Potwory sprzed Yohary „jak na globalu” – `MT2009_PLUS_MOBY_GLOBAL_V1`

Decyzja właściciela z 20.10.2026: statystyki i drop potworów sprzed Yohary wg jego arkusza
`Metin2_Moby_statystyki_EXP_i_drop.xlsx` (metin2alerts, odczyt 16.10.2026). Generator:
`tools/ymoby_arkusz/gen_moby_global.py` (decyzje: `moby_global_data.py`, dane: `moby_global.json`), raport:
`/opt/metin2/cache/yohara/porownanie-moby.md`.

## Statystyki – `mariadb/playerbot/moby_global.sql` (apply.sh)
1045 zmian u 483 potworów: HP, obrażenia, EXP, poziom, obrona, STR/DEX/VIT/INT, szybkości, regeneracja, szanse efektów
(klątwa, omdlenie…), 11 odporności, flagi AI (agresja, berserk, kamienna skóra, …) i immunitety; rasa tam, gdzie jej
brakowało (Zodiak 2676–2679 – człowiek, Tu-Gui 7008–7010 – ork). UPDATE tylko kolumny, która ma jeszcze wartość
z czystego świata (world.sql) – wartość ustawiona przez operatora zostaje. Bez zmian: ranga, żywioły, kolumny, które
piszą nasze skrypty (apply.sh: Beran-Setaou, Metiny 8031–8034; maps_wz.sql: poziomy Ogrów), potwory o innej nazwie
u nas (inne potwory pod tym vnumem), NPC.
Klient: `client-patches/client-2.0.30/tools/mobyglobal/build_mobyglobal_pack.py` (te same wartości w gamedata/mob_proto).

## Drop – ten katalog (krok Dockerfile `MT2009_PLUS_MOBY_GLOBAL_V1`)
- `mob_drop_item.moby_global.remove.txt` – 199 wierszy paczki u 96 potworów, których arkusz nie wymienia, wycinane
  (`cut_rows.awk`; grupa numerowana od nowa, pusta grupa znika). Zostają: nasze grupy (MT2009_*, playerbot_*), wiersze
  dodane/zmienione przez nas, grupy specjalne (s…), przedmioty questów.
- `mob_drop_item.moby_global.txt` – 877 brakujących pozycji arkusza u 334 potworów (grupy `MT2009_mglobal_<mob>`).
  Pominięte: czego nie mamy, przedmioty questów, materiały bez zastosowania u nas, Odłamki Seon-Hae, Spróchniała
  Skrzynia. **Szanse tymczasowe** (arkusz ich nie podaje): mediana tego samego przedmiotu u naszych potworów tego
  samego rodzaju, inaczej innego rodzaju, inaczej domyślna wg rodzaju przedmiotu; zwykły potwór najwyżej v = 2 (0,5%).
