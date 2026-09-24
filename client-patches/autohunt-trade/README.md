# Auto Łowy oraz handel Cor Draconis i szarfami

Ten katalog przechowuje klientową część zmiany rozwijanej na gałęzi
`claude/vibrant-meitner-o2s0a2`.

## Zawartość

- `root/uiautohunt.py` — kompletne okno Auto Łowów, konfiguracja osobna dla
  postaci, walka, umiejętności, mikstury, przedmioty czasowe, wstawanie i
  filtrowane podnoszenie łupu.
- `game.py.patch` — rejestruje system w pętli klienta, przypisuje okno do
  klawisza **K** i odbiera odpowiedzi `AutoHuntTarget` / `AutoHuntLoot`.
- `ItemManager.cpp.patch` — usuwa klientowe blokady `GIVE` i `MYSHOP`
  wyłącznie z Cor Draconis i wszystkich szarf. Pozostałe zabezpieczenia,
  w tym zakaz wyrzucania i dropu po śmierci, pozostają bez zmian.
- `uiInventory-crashfix.patch` — usuwa trzy tymczasowe logi szarfy razem z
  otaczającymi je warunkami. Pozostawienie pustych `if` powodowało crash przy
  przejściu z wyboru postaci do gry.

Serwerowa część Auto Łowów jest w
`linux-port/overlays/playerbot/serverfiles/player_autohunt_commands.inc`.
`start-server.ps1` wstawia ją do źródła silnika i rejestruje obie komendy
przed kompilacją. Ten sam skrypt usuwa 85101 z puli Metinów/bossów oraz 85104
z puli szkatułek.

Zmiana flag w bazie jest wykonywana idempotentnie przy starcie przez
`linux-port/docker/mariadb/playerbot/apply.sh`.

## Test

1. Zaloguj postać i naciśnij **K**.
2. Włącz walkę, skille, mikstury oraz wybrane rodzaje łupu.
3. Sprawdź powrót do punktu startowego, wstawanie po śmierci i zmianę mapy.
4. Przekaż Cor Draconis oraz szarfę przez handel bezpośredni.
5. Wystaw oba przedmioty w sklepie zwykłym i offline.
6. Zabij serię Metinów/bossów i otwórz właściwe szkatułki — rodzina
   Death Ruler 85101–85104 nie może już wypaść.
