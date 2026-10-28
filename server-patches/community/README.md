# Społeczność – nowe okno znajomych (28 października 2026)

Pomysł, wygląd i grafiki: paczka „Community System (Messenger Renewal)” (Autor: Best Studio,
github.com/ybeststudio). Paczka była pisana pod inny silnik (własne pakiety messengera, pola `CHARACTER`,
moduł exe `community`, inny `ui.py`), więc u nas to **własna implementacja na naszym messengerze**:
żaden istniejący pakiet się nie zmienia, **exe bez zmian** (działa na obecnym exe 3.0 i starszych),
klient rozmawia z serwerem komendami czatu – tak jak Szata Aury czy Transmutacja.

Znacznik: `MT2009_PLUS_COMMUNITY_V1`. Przełączniki silnika: `__MESSENGER_RENEWAL__`,
`__COMMUNITY_GUILD_RENEWAL__` (`CommonDefines.h`, nazwy z paczki).

## Co gracz dostaje

Jedno okno „Społeczność” (przycisk messengera na pasku i jego klawisz) zamiast starego messengera:

- **Znajomi** – trzy listy: znajomi, zablokowani, zaproszenia do znajomych (zaproszenie trafia na listę + linijka na
  czacie, zakładka mruga, i – jak w starym messengerze – wyskakuje okienko z pytaniem; odpowiedź w okienku usuwa
  wpis z listy, odpowiedź na liście zamyka okienko). Przy znajomym: stan (kolorowa
  kropka), poziom, opis pod nickiem, ikony: położenie (kanał + mapa w dymku), ulubiony (gwiazdka – ulubieni
  na górze), zaproszenie do grupy (gracz na tej samej mapie). Przyciski: dodaj, zablokuj, szept, usuń.
  Dwuklik = szept.
- **Mój stan** (rozwijana lista przy nicku): Online, Zaraz wracam (AFK), Niewidoczny – znajomi widzą mnie
  wtedy jako offline (także na starym oknie i starym kliencie). Auto Łowy same pokazują stan „Auto Łowy”.
  Wybrany stan zostaje po relogu.
- **Opis** (ołówek) – do 50 znaków, widzą go znajomi; filtr niedozwolonych słów serwera (`banword`).
- **Gildia** – członkowie z poziomem, online/offline i położeniem; szept, dodaj do znajomych, zablokuj,
  wyrzuć (z uprawnieniem), przycisk okna gildii.
- **Ustawienia** – powiadomienia na czacie (znajomy / członek gildii wchodzi do gry), prywatność
  (nie pokazuj mojego poziomu / położenia – zapisywane na serwerze), ulubieni na górze, opis pod nickiem.
- Małżonek (jeśli jest) w pasku pod nickiem; bez małżonka pasek pokazuje mój opis.

## Serwer – `edits.json` (17 zmian)

| Znacznik | Plik | Co robi |
|---|---|---|
| `(define)` | `../../common/CommonDefines.h` | `__MESSENGER_RENEWAL__`, `__COMMUNITY_GUILD_RENEWAL__` |
| `(gg header)` | `packet.h` | `HEADER_GG_COMMUNITY = 40` (wolny na wszystkich gałęziach) |
| `(gg struct)` | `packet.h` | `TPacketGGCommunity` (nick, stan, prywatność, poziom, poziom Czempiona, opis), `COMMUNITY_STATUS_MAX_LEN` 50 |
| `(gg size)` | `packet_info.cpp` | rozmiar pakietu GG |
| `(p2p)` | `input_p2p.cpp` | `MessengerManager::CommunityP2P` |
| `(declare)`, `(table)` | `cmd.cpp` | komenda `/community` |
| `(members)` | `guild.h` | `Mt2009ForEachMemberPID` – lista członków dla zakładki gildii |
| `(members)` | `messenger_manager.h` | dane i funkcje Społeczności w `MessengerManager` |
| `(login)` | `messenger_manager.cpp` | przy logowaniu: zapytanie o opis/stan gracza i jego znajomych – **przed** zapytaniem o listę (ta sama kolejka SQL), więc „niewidoczny” nie mignie znajomym jako online |
| `(logout)` | `messenger_manager.cpp` | czyści stan sesji |
| `(request)` | `messenger_manager.cpp` | przed `messenger_auth`: poziom/położenie zapraszającego dla zakładki zaproszeń |
| `(list hidden)`, `(login hidden)` | `messenger_manager.cpp` | „niewidoczny” jest na liście i przy logowaniu offline (dla każdego klienta) |
| `(list lines)`, `(login line)`, `(logout line)` | `messenger_manager.cpp` | linijka okna przy liście / wejściu / wyjściu znajomego |

Logika: `linux-port/overlays/playerbot/src/game/src/playerbot_community.cpp` (bez definicji się nie
kompiluje do niczego). Kolejność: **ostatnia** (po `kupon100`) w `yohara-deploy.sh` i w
`tools/port/Apply-MT2009PlusEngine.ps1` (już dopisane).

### Komendy

- klient → serwer: `/community hello` (okno jest – od teraz linijki poniżej), `state <0|1|4>`,
  `auto <0|1>`, `status [tekst]` (puste = usuń), `privacy <8|16|24>`, `guild`, `party <nick>`;
- serwer → klient: `community_my <stan> <prywatność> [opis]`,
  `community_friend <nick> <stan> <poziom> <poz. Czempiona> <kanał> <mapa> [opis]`,
  `community_guild <pid>:<kanał>:<mapa> ...` (po 20), `community_request <nick> <poziom> <poz. Czemp.> <kanał> <mapa>`.

Serwer bez łatki nie odpowiada na `hello` – okno działa wtedy jak messenger (bez stanów, poziomów, opisów).
Klient bez nowego roota nigdy nie wysyła `hello` i nic nowego nie dostaje.

### Między rdzeniami

Rdzeń gracza wysyła `HEADER_GG_COMMUNITY` przy logowaniu i przy każdej zmianie (stan, opis, prywatność,
poziom z chwili logowania). Kanał i mapa gracza z innego rdzenia są z logowania P2P (`CCI`). Ograniczenia:
poziom znajomego na innym rdzeniu odświeża się przy jego relogu / teleporcie; „zaproś do grupy” tylko na tej
samej mapie (jak w paczce – gracz w zasięgu).

### Boty

Boty są graczami silnika z deskryptorem, który gubi pakiety. Nic nie jest do nich wysyłane
(`CommunityIsClient`: deskryptor i `!IsBot()` przy każdej linijce i komendzie), nigdy nie wysyłają
`/community`. Bot jako znajomy wygląda jak każdy znajomy (online, poziom, mapa). Zaproszenie do bota
idzie dalej przez `server-patches/botfriends` (bot odpowiada od razu; linijka `community_request` trafia
tylko do gracza z oknem).

## Baza – `linux-port/docker/mariadb/playerbot/community.sql`

`player.status_message VARCHAR(50)` i `player.community_flags TINYINT` (bity 0–2 wybrany stan, 8 ukryj
poziom, 16 ukryj położenie) + te same kolumny w `player_deleted` (ta sama kolejność – `INSERT ... SELECT *`).
`ADD COLUMN IF NOT EXISTS`, krok w `apply.sh`, plik w `launcher/server-update-files.mod.txt`. Bez kolumn
lista znajomych działa jak dotąd (jej zapytanie ich nie używa) – brakuje tylko dodatków okna.

## Klient

- `client-patches/client-2.0.30/root/uicommunity.py` (nowy) – okno w kodzie (bez pliku uiscript), na naszym
  `ui.py`; teksty po polsku w module (CP1250). Przejmuje uchwyt messengera z exe i przekazuje każde
  wywołanie staremu oknu `uimessenger` (zostaje bez zmian – inne okna z niego korzystają). Ustawienia
  klienta i ulubieni: `spolecznosc.cfg`.
- `interfacemodule.py` – tworzenie / niszczenie okna, przycisk i klawisz messengera otwierają Społeczność
  (gdy okno się nie utworzy – stare okno, jak dotąd).
- `game.py` – cztery linijki serwera, zaproszenie do znajomych do okna, updatable (`hello`, Auto Łowy),
  wywołania małżeństwa.
- Grafiki: `client-patches/client-2.0.30/community/d_` (71 plików GF 26.1.11 z paczki, `.sub` z CRLF;
  `community_config_subtopic_title_bg.sub` wskazuje na nasz `windows_yohara.dds`) → nowa paczka
  `community_ui` (`tools/community/build_community_packs.py`, sprawdzenie `verify_community.py`).

## Pliki

- `edits.json` – zmiany (plik, znacznik, stary i nowy kod);
- `Apply-CommunityPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_community.py` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie raz, przerywa
całość, zanim cokolwiek zostanie zapisane.
