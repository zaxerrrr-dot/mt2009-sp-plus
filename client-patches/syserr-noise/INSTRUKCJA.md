# Zadanie dla agenta klienta: dwa błędy zaśmiecające syserr.txt

Oba zgłoszone z `syserr.txt` gracza (klient 2.0.10, serwer 2.4.0). Nie
wyrzucają z gry, ale w kilkanaście minut robią z `syserr.txt` kilka MB.

## 1. `'module' object has no attribute 'APPLY_ATT_SPEED'`

Przy najechaniu myszką na miksturę wzmacniającą w ekwipunku (np. zieloną
27101–27103 albo fioletową 27104–27106) podpowiedź się wywraca, a dopóki kursor
jest nad przedmiotem, każda klatka dopisuje traceback:

```
uiInventory.py, line 1568, in OverInItem
uiInventory.py, line 1786, in ShowToolTip
uiToolTip.py,   line 603,  in SetInventoryItem
uiToolTip.py,   line 1376, in AddItemData
uiToolTip.py,   line 1866, in __AppendAbilityPotionInformation
AttributeError: 'module' object has no attribute 'APPLY_ATT_SPEED'
```

`metin2client.exe` nie eksportuje w module `item` stałej `APPLY_ATT_SPEED`.
Poprawka w `root/uiToolTip.py`, w `__AppendAbilityPotionInformation` (ok. linii
1866): każde `item.APPLY_ATT_SPEED` zastąp stałą z zapasem, np. na początku
funkcji:

```python
APPLY_ATT_SPEED = getattr(item, "APPLY_ATT_SPEED", 7)   # 7 = szybkość ataku (EApplyTypes)
```

i używaj `APPLY_ATT_SPEED`. Sprawdź w tej funkcji pozostałe `item.APPLY_*`
tak samo (`getattr` z numerem z `EApplyTypes`: MOV_SPEED 8, MAX_HP 1, MAX_SP 2).
Test: najedź na zieloną i fioletową miksturę – podpowiedź pokazuje bonus,
w `syserr.txt` nic nie przybywa.

## 2. `Unknown Server Command PlayerBotStatus / PlayerBotTitle`

Serwer wysyła botom napisy nad głową komendami czatu (`CHAT_TYPE_COMMAND`):

```
PlayerBotStatus <vid> <tekst PL hex> <tekst EN hex>
PlayerBotTitle <vid> <numer tytułu>
```

Teksty są w hex (cp1250), np. `476f6e696520447a696b692050696573` = „Gonie Dziki Pies”.
Klient 2.0.10 ich nie zna, więc każdą (kilka na sekundę) zapisuje jako
„Unknown Server Command”. W `root/game.py`, w słowniku komend serwera
(`self.serverCommander` / `__ServerCommand_Build`), zarejestruj oba:

- najprościej: puste funkcje (`lambda *args: None`), żeby log był czysty;
- lepiej (jeśli jest czas): pokaż status nad botem – odkoduj hex
  (`binascii.unhexlify`), wybierz tekst wg języka klienta i ustaw go pod
  nazwą postaci o danym `vid` (jak tytuł/rangę); `PlayerBotTitle` to numer
  tytułu bota do wyświetlenia obok nicku.

Test: zaloguj się przy botach – w `syserr.txt` nie ma „Unknown Server Command”.

Obie zmiany wchodzą do następnej, pełnej (kumulatywnej) paczki klienta.
