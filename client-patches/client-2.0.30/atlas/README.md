# Podgląd mapy (M): Groty Wygnańców i Groty Pająków

Pod klawiszem M obie Groty Wygnańców mają mapę, a mapy obu Grot Pająków pokazują tylko
przejścia, którymi da się chodzić.

Pliki pochodzą z projektu upstream, z którego wolno nam brać pliki klienta (klient 2.0.70,
wydanie serwera 2.2.61, paczka `root`), bajt w bajt. Nazwy map są takie same jak w naszym
`gamedata/atlasinfo.txt` (`season2/metin2_map_skipia_dungeon_01`,
`metin2_map_skipia_dungeon_02`, `metin2_map_spiderdungeon`, `metin2_map_spiderdungeon_02`).
Exe szuka najpierw `<mapa>/atlas.sub`, potem `d:/ymir work/ui/atlas/<mapa>/atlas.sub`;
`.sub` w wersji 1.0 wskazuje obraz względem `d:/ymir work/ui/`.

Układ: `d_/` = `d:/`, reszta ścieżki to nazwa wpisu. Wszystkie wpisy idą do paczki `root`
(tak jak u upstream) i są **nowe** – w naszych paczkach nie ma żadnego atlasu tych map.
Katalog celowo nie leży w `root/`, bo build roota bierze ścieżki z `root/` dosłownie
(bez zamiany `d_/` na `d:/`). Upstream trzyma te wpisy z typem 2.

| Paczka | Wpis | Status | Rozmiar | Obraz |
|---|---|---|---|---|
| root | `d:/ymir work/ui/atlas/season2/metin2_map_skipia_dungeon_01/atlas.sub` | nowy | 129 | – |
| root | `d:/ymir work/ui/atlas/season2/metin2_map_skipia_dungeon_01/atlas.tga` | nowy | 337202 | 510×510 |
| root | `d:/ymir work/ui/atlas/metin2_map_skipia_dungeon_02/atlas.sub` | nowy | 121 | – |
| root | `d:/ymir work/ui/atlas/metin2_map_skipia_dungeon_02/atlas.tga` | nowy | 77891 | 510×510 |
| root | `d:/ymir work/ui/atlas/metin2_map_spiderdungeon/atlas.sub` | nowy | 117 | – |
| root | `d:/ymir work/ui/atlas/metin2_map_spiderdungeon/atlas.tga` | nowy | 65845 | 384×384 |
| root | `d:/ymir work/ui/atlas/metin2_map_spiderdungeon_02/atlas.sub` | nowy | 120 | – |
| root | `d:/ymir work/ui/atlas/metin2_map_spiderdungeon_02/atlas.tga` | nowy | 98923 | 512×512 |

Obrazy: TGA 32 bit z RLE (typ 10), w pełni nieprzezroczyste. `.sub` mają CRLF.

## Inne obrazy `d:/` paczki `root`

Ten katalog (`atlas/d_/`) budowa paczki `root` przechodzi w całości, więc trafiają tu też inne nowe
obrazy z `d:/`, nie tylko atlasy.

| Paczka | Wpis | Status | Rozmiar | Obraz | Po co |
|---|---|---|---|---|---|
| root | `d:/ymir work/ui/pattern/gauge_green.tga` | nowy | 556 | 16×8 | zielony pasek życia otrutego celu (`uitarget.py`, MT2009_PLUS_TARGET_POISON_GAUGE_V1) |
| root | `d:/ymir work/ui/gemshop_001.dds` | nowy | 44800 | 140×236 DXT5 (tło 3×3, ikona Gaya, przycisk odświeżania) | okno Sklepu Gaya (`uiygaya.py`, MT2009_PLUS_GAYA_SHOP_WINDOW_V1) – plik GF 26.1.11 bajt w bajt |
| root | `d:/ymir work/ui/gemshop/gemshop_backimg.sub` | nowy | 92 | – | okno Sklepu Gaya (`uiygaya.py`, MT2009_PLUS_GAYA_SHOP_WINDOW_V1) – plik GF 26.1.11 bajt w bajt |
| root | `d:/ymir work/ui/gemshop/gemshop_gemicon.sub` | nowy | 96 | – | okno Sklepu Gaya (`uiygaya.py`, MT2009_PLUS_GAYA_SHOP_WINDOW_V1) – plik GF 26.1.11 bajt w bajt |
| root | `d:/ymir work/ui/gemshop/gemshop_refreshbutton_up.sub` | nowy | 94 | – | okno Sklepu Gaya (`uiygaya.py`, MT2009_PLUS_GAYA_SHOP_WINDOW_V1) – plik GF 26.1.11 bajt w bajt |
| root | `d:/ymir work/ui/gemshop/gemshop_refreshbutton_over.sub` | nowy | 94 | – | okno Sklepu Gaya (`uiygaya.py`, MT2009_PLUS_GAYA_SHOP_WINDOW_V1) – plik GF 26.1.11 bajt w bajt |
| root | `d:/ymir work/ui/gemshop/gemshop_refreshbutton_down.sub` | nowy | 95 | – | okno Sklepu Gaya (`uiygaya.py`, MT2009_PLUS_GAYA_SHOP_WINDOW_V1) – plik GF 26.1.11 bajt w bajt |

`gauge_green.tga` (pomysł: Kiciamol) ma ten sam format co `gauge_red.tga` z paczki bazowej (TGA 32 bit bez RLE,
typ 2). Klient bez tego pliku zostawia czerwony pasek (`app.IsExistFile`).

### Druga runda exe Yohary (`MT2009_PLUS_YOHARA_EXE2_V1`)

Wszystko nowe (własne nazwy / własny katalog – żaden wpis nie zastępuje pliku paczek bazowych):

| Paczka | Wpis | Rozmiar | Skąd | Po co |
|---|---|---|---|---|
| root | `d:/ymir work/ui/game/taskbar/mt2009_conqueror_exp_point.tga` | 1462 | `taskbar.tga` GF 26.1.11, wycinek 493,107–512,126 (`new_exp_gauge_point.sub` GF), TGA 32 bit typ 2 | niebieska kula exp Czempiona (`uitaskbar.py`) |
| root | `d:/ymir work/ui/skill/common/affect/mt2009_sungma_{buff,str_debuff,hp_debuff,move_debuff,immune_debuff,control_debuff}.sub` | ~90 | `.sub` GF (`sungma_all`, `sungma_*_debuff`, `hit_bonus`) z obrazem `skill9_common.dds` (paczka `yskill9` = `newskillcommon.dds` GF) | ikony Sung Ma na pasku afektów (`sungmastate.py`; bez `skill9_common.dds` – ikony okna postaci) |
| root | `d:/ymir work/effect/etc/conqueror_exp/ga_piece_orange_small.msf`, `ga_piece_orange2.mse`, `ga_center_small_orange.mse`, `ga_piece_orange.dds`, `ga_center_small_yellow.dds`, `ga_chips copy.dds` | 32 KB | GF 26.1.11 `effect/etc/gathering/` (bajt w bajt; nazwy w środku względne) | efekt exp Czempiona `FLY_CONQUEROR_EXP` (exe `PythonPlayerSettingsModule.cpp`) |

### Okno postaci w układzie 3.0 (`MT2009_PLUS_CHAMPION_WINDOW_V1`)

Zakładka Status jak w kliencie globalnym (`root/uiscript/characterwindow.py`, `root/uicharacter.py`). Wszystko nowe,
własne nazwy (`mt2009_` / `_yohara`), żaden wpis nie zastępuje pliku paczek bazowych:

| Paczka | Wpis | Skąd | Po co |
|---|---|---|---|
| root | `d:/ymir work/ui/tabchar_yohara.tga` | `tabchar.tga` GF 26.1.11 bajt w bajt (253×148, TGA 32 bit typ 2) | pasek zakładek z ikonami |
| root | `d:/ymir work/ui/game/windows/mt2009_char_tab_01..04.sub` | `.sub` GF `char_tab_0x`, obraz `tabchar_yohara.tga` | 4 stany paska zakładek |
| root | `d:/ymir work/ui/game/windows/mt2009_{level_exp_info,base_info_bar,status_extent_bar,char_info_status_img,char_info_status_plus_img,char_info_status_value_img}.sub` | `.sub` GF, obraz `windows_yohara.dds` (= GF `windows.dds`) | ramka Lv / EXP, pasek z wolnymi punktami („+” i liczba), linia nad dolnym blokiem |
| root | `d:/ymir work/ui/game/windows/mt2009_char_info_{con,int,str,dex,hp,sp,att,def,movespeed,attspeed,magspeed,magatt,magdef,hitpct}.sub` | `.sub` GF, obraz `windows_yohara.dds` | ikony statystyk (`hitpct` = Precyzja) |
| root | `d:/ymir work/ui/game/windows/mt2009_passive_expanded_button_01..03.sub` | `.sub` GF, obraz `windows_yohara.dds` | trzeci przycisk rzędu (u nas „Bonusy”) |

### Okno umiejętności w układzie 3.0 (`MT2009_PLUS_SKILL_WINDOW_V1`)

Zakładka Umiejętności jak w kliencie globalnym (`root/uiscript/characterwindow.py` „Skill_Page”, `root/uicharacter.py`,
`root/riposty.py`): pięć rzędów po trzy stopnie (M → G → P) ze strzałkami – umiejętności 1–6, riposta (pole 7), dopalacz
(pole 8), 9. umiejętność (pole 9); umiejętności pomocnicze 6 × 3 pod paskiem z ikoną; wolne punkty jako „+ [n]”. Nowe
wpisy (własne nazwy, obraz `windows_yohara.dds` = GF `windows.dds`, który już jest w paczce):

| Paczka | Wpis | Skąd | Po co |
|---|---|---|---|
| root | `d:/ymir work/ui/game/windows/mt2009_skill_board.sub` | `.sub` GF `skill_board` (0,0–227,152) | tło 4 rzędów umiejętności ze strzałkami |
| root | `d:/ymir work/ui/game/windows/mt2009_skill_board_expanded.sub` | `.sub` GF `skill_board_expanded` (8,442–235,484) | 5. rząd (9. umiejętność) |
| root | `d:/ymir work/ui/game/windows/mt2009_support_skill_bar_icon.sub` | `.sub` GF `support_skill_bar_icon` (496,513–512,528) | ikona paska umiejętności pomocniczych |
