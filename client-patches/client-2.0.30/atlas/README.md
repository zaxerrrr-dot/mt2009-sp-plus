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
