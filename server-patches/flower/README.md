# Dzieci Kwiaty (Flower Event Owsapa) – `MT2009_PLUS_FLOWER_V1`

Event Owsapa v6.2.6 (`flower_event.cpp`, `uiflowerevent.py`) na naszym menedżerze eventów
(`server-patches/eventmanager`). Logika jest w nakładce
`linux-port/overlays/playerbot/src/game/src/playerbot_flower.h` (dołączonej do
`playerbot_manager.cpp` zaraz po `playerbot_ingame_events.h`); tu są tylko zmiany plików
silnika, opisane w `edits.json`:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_FLOWER_V1 (cg header)` | `packet.h` | `HEADER_CG_FLOWER_EVENT = 187` |
| `MT2009_PLUS_FLOWER_V1 (gc header)` | `packet.h` | `HEADER_GC_FLOWER_EVENT = 187` |
| `MT2009_PLUS_FLOWER_V1 (packet)` | `packet.h` | enumy Owsapa (`SHOOT_*`, `FLOWER_EVENT_CHAT_TYPE_*`, podnagłówki) i pakiety `TPacketGCFlowerEvent` (32 B), `TPacketCGFlowerEvent` (4 B) |
| `MT2009_PLUS_FLOWER_V1 (size)` | `packet_info.cpp` | rozmiar pakietu CG 187 |
| `MT2009_PLUS_FLOWER_V1 (input)` | `input_main.cpp` | `case HEADER_CG_FLOWER_EVENT` → `FlowerEventPacket` z nakładki |
| `MT2009_PLUS_FLOWER_V1 (kill)` | `item_manager.cpp` | koniec `CreateQuestDropItem` → `FlowerEventOnKill` (nasiona) |
| `MT2009_PLUS_FLOWER_V1 (use)` | `char_item.cpp` | `USE_AFFECT` z `value0 = 570` → `FlowerEventUseItem` (kwiaty) |

- `Apply-FlowerPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, po eventmanager,
  bo kotwiczy na jego liniach w `packet.h`);
- `apply_flower.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json`.

## Pakiety (układ Owsapa, `#pragma pack(1)`)

```
CG 187, 4 B:  BYTE bHeader; BYTE bSubHeader; BYTE bShootType; BYTE bExchangeKey;
              bSubHeader 0 = INFO_ALL (prośba o liczniki), 1 = EXCHANGE
              bShootType 0 nasiona, 1..5 chryzantema, konwalia, narcyz, lilia, słonecznik
              bExchangeKey 0..3 = ×1, ×10, ×50, ×100
GC 187, 32 B: BYTE bHeader; BYTE bSubHeader; BYTE bChatType; BYTE bShootType; int aiShootCount[7];
              bSubHeader 0 = INFO_ALL (aiShootCount[0..5]), 1 = GET_INFO (komunikat bChatType,
              przy bShootType < 6 także aiShootCount[bShootType]), 2 = UPDATE_INFO (jeden licznik)
```

Exe (osobny agent, `client-patches/exe`) robi to, co Owsap: `net.SendFlowerEventRequestInfo()`,
`net.SendFlowerEventExchange(type, key)`, stałe `net.FLOWER_EVENT_SUBHEADER_GC_*`,
`player.SHOOT_*`, `player.FLOWER_EVENT_*`, `player.Set/GetFlowerEventEnable`, a pakiet GC woła
`FlowerEventProcess(type, data)` okna gry: INFO_ALL `(0, (6 liczb))`, GET_INFO `(1, chatType)`
albo `(1, (shootType, count))`, UPDATE_INFO `(2, (shootType, count))`. Serwer wysyła GC 187
tylko klientowi, którego exe w tej sesji wysłało CG 187 (stary exe zamknąłby się na nieznanym
nagłówku); stary exe dostaje o nasionach linię na czacie.

## Jak działa

- **Kiedy**: event `flower` menedżera – rodzaj harmonogramu `flower` z paneli albo flaga
  `e_flower_drop` ustawiona przez GM. Po końcu z harmonogramu 7 dni okna nagród
  (`e_flower_reward`, nowy wiersz `s_defs` w `playerbot_ingame_events.h`): nasiona już nie
  wypadają, ale to, co zostało, można wymienić i (domyślnie) używać kwiatów.
- **Nasiona**: zabity potwór (nie gracz) daje nasiono z szansą `seed_chance` setnych procenta
  (100 = 1 % przy równym poziomie, skalowane jak drop: różnica poziomów, premium, rękawice).
  Licznik, nie przedmiot: flaga `flower_event.envelope`. Boty nic nie dostają.
- **Wymiana** (okno klienta): nasiona → losowe latorośle (flagi `flower_event.chrysanthemum`,
  `.may_bell`, `.daffodil`, `.lily`, `.sunflower`); 10 latorośli jednego kwiatu → nagroda.
- **Kwiaty 25121–25125**: jeden bonus naraz (affect 570); ten sam kwiat – poziom wyżej
  (15 %), inny – zamiana (30 %), brak – nowy (50 %); nieudana próba też zużywa kwiat.

## Co zmienia administrator (bez budowania)

- **Ustawienia i nagrody za kwiaty**: panel klasyczny → „🌸 Dzieci Kwiaty” (`/flower`), plik
  `/opt/m2spool/flower_event.tsv` (rdzeń czyta go co 5 s, bez restartu):
  `seed_chance`, `min_level`, `seeds_per_shoot`, `shoots_per_reward`, `add_rate`,
  `change_rate`, `upgrade_rate`, `max_level`, `counter_max`, `use_after_event`,
  `reward <1-5> <vnum> <ilość>` (domyślnie pudełka 83023–83027 po 1).
- **Zawartość pudełek 83023–83027**: grupy `special_item_group`
  (`linux-port/docker/game/special_item_group.flower.txt`), edycja w panelu Sebana →
  „Szkatułki” (pudełka są na górze listy), działa po restarcie rdzeni.
- **Wartości bonusów kwiatów**: wiersze `world.item_proto` 25121–25125 (`value2` poziom 1,
  `value3` czas, `value4` na poziom).

## Poprawione błędy Owsapa

1. Typ latorośli i klucz ilości od klienta są sprawdzane (u Owsapa indeksy poza tablicą).
2. Nasiona są zabierane tylko za latorośle, które gracz dostał (Owsap brał je przy pełnych
   licznikach, a test „wszystko pełne” nigdy nie był prawdziwy).
3. Jedna aktualizacja licznika na wymianę (Owsap wysyłał dwie).
4. Licznik zmienia się przed wydaniem nagrody i dopiero po sprawdzeniu miejsca (brak
   podwójnego odbioru i utraty nagrody); 1 s przerwy między wymianami na serwerze; wymiana
   zablokowana przy otwartym handlu, sklepie, magazynie i kostce.
5. Liczniki zostają między eventami (jak u Owsapa) – nic, co gracz zebrał, nie przepada.

Test GM: `/setqf flower_event.envelope 100` (i pozostałe flagi), `/ingame_event gm`.
