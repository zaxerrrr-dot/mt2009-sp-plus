# strefy – strefy ataku na ziemi lochów (Głębie Północnego Wiatru, Świątynia Węży)

`MT2009_PLUS_DUNGEON_ZONE_V1` (14.10.2026, decyzja właściciela: „Śmiertelny Chłód ma działać w STREFACH na ziemi.
Kolce i atak z powierzchni mają działać jak w grze wg wiki – mogą zabić”).

Dotąd silnik nie umiał z questa zadać obrażeń w obszarze, więc quest `ymaps3_glebie` trafiał Chłodem wszystkich naraz,
a kolce i atak z powierzchni działały jako „stoisz 3 s w miejscu = trafienie, nigdy do zera PŻ”. Ta łatka dodaje dwie
funkcje lua lochu (`questlua_dungeon.cpp`):

```lua
d.zone_attack(x, y, promień, proc, stała, opóźnienie_ms, efekt_ostrzeżenia [, efekt_trafienia [, powtórz_ms [, znacznik [, życie_ms]]]])
d.zone_hurt(pid, proc, stała)
```

- `x, y, promień` – komórki mapy lochu (jak `d.spawn_mob`). Na miejscu staje niewidzialny znacznik **3975**
  (NPC bez nazwy i bez kliknięcia, w kliencie model „warp” – bez siatki i bez kolizji); widzą go wszyscy w zasięgu,
  a na nim rysuje się `efekt_ostrzeżenia` (plik .mse klienta).
- Po `opóźnienie_ms` każdy **żywy gracz lochu w kręgu** traci `proc`% maks. PŻ + `stała` – prawdziwe obrażenia
  (`CHARACTER::Damage`, `DAMAGE_TYPE_SYSTEM`): liczba obrażeń nad głową, a przy zerze PŻ zwykła śmierć
  (`Dead` – okno odrodzenia, questy `die` lochu, np. limit ożywień Świątyni). Obrażenia zawsze z wydarzenia
  silnika, nigdy w trakcie questa (śmierć uruchamia własne questy).
- `efekt_trafienia` (albo `""`) – gra na znaczniku, gdy ktoś oberwał.
- `powtórz_ms` > 0 – strefa zostaje i uderza znowu co tyle ms (najmniej 500) do `życie_ms` (0 = do końca lochu);
  co 15 s dostaje nowy znacznik, żeby jej efekt zobaczył też ktoś, kto przyszedł z daleka albo wrócił do gry.
- `znacznik` – każde trafienie dodaje 1 do flagi lochu `<znacznik><id postaci>` (quest liczy z niej np. osłabienie).
- `d.zone_hurt` – te same prawdziwe obrażenia jednemu graczowi lochu (tyk osłabienia), też z wydarzenia.

Lekkie dla 32-bitowego rdzenia: jedno wydarzenie na strefę, przy uderzeniu przegląd tylko graczy lochu (≤ 8).
Bez wiersza 3975 w `mob_proto` strefy działają bez efektów (sam znacznik się nie pojawia).

## Użycie (wg wiki PL/TR, efekty z klienta GF 26.1.11)

| loch | mechanika | wywołanie |
|---|---|---|
| Głębie Płn. Wiatru | lodowe kolce co 15 s pod każdym żywym graczem: 50% maks. PŻ, kręgi się sumują | promień 3, 1800 ms, `whitedragon_ground_ice.mse` (czerwony krąg, lód po 1,76 s) |
| Głębie Płn. Wiatru | Śmiertelny Chłód (12 razy, co 100 s, +20 s za każde zniszczone jajo): stały biały krąg pod losowym żywym graczem; po 3 s każdy, kto w nim stoi lub wejdzie (co 2 s), traci 15 000 (słaby) / 20 000 (silny) PŻ i dostaje osłabienie; gdy nikt nie żyje – Chłód czeka | promień 5, 3000 ms, powtórz 2000 ms, znacznik `zc`, `whitedragon_circle_ice.mse` + `whitedragon_boss2_s1_blow.mse` |
| Głębie Płn. Wiatru | osłabienie: co 10 s 5% / 7% maks. PŻ za każdy stos (do 5 / 7), znika po śmierci | `d.zone_hurt` |
| Świątynia Węży | atak z powierzchni co 20 s pod losowym żywym graczem: 20% maks. PŻ, czasem spowolnienie | promień 3, 1800 ms, znacznik `za`, `snake_circle_snake.mse` (krąg, wąż po 1,75 s) |

Źródła: wiki TR „Alastor (Kolay)” / „Alastor (Zor)” (Ölümcül Soğuk: „Kalıcı bembeyaz dairesel alan”, 15 000 /
20 000 PŻ, osłabienie 5% / 7% co 10 s do 5 / 7 razy; kolce co 15 s, 50% PŻ, „Dikenli Alan hasarları birikebilir”),
wiki PL i TR „Świątynia Węży” / „Yılan Tapınağı” (co 20 s, 20% maks. PŻ, debuff z pewną szansą). Rozmiary kręgów
i opóźnienia – z plików efektów (cząsteczka 625 = krąg ~3 m, lód/wąż w 1,76 s; biały krąg 970 = ~5 m).

## Pliki

- Silnik: `questlua_dungeon.cpp` (lista `launcher/server-update-files.mod.txt`).
- Questy: `linux-port/docker/game/quest/ymaps3_glebie.quest`, `swiatynia_wezy.quest`; nazwy `d.zone_attack`,
  `d.zone_hurt` dopisane do `quest_functions` w Dockerfile.
- Znacznik 3975: `tools/yohara_maps3/ymaps3_data.py` (`ZONE_MARKS`, `NPCLIST_ADD`) → `yohara_maps3.sql`,
  `ymaps3_mobs.json` (klient: mob_proto + npclist „warp”).
- Efekty w kliencie: `client-patches/client-2.0.30/tools/ymaps3/stage_ymaps3.py` (`ZONE_EFFECTS` → paczka
  `ymaps3_mobs`), sprawdza je `verify_ymaps3.py`.

Linux/VPS: `python3 apply_strefy.py <game/src>`; Windows: `Apply-StrefyPatch.ps1 -SourceDir <game/src>` (wołane przez
`tools/port/Apply-MT2009PlusEngine.ps1`).
