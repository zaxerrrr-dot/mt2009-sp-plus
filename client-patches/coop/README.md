# COOP w kliencie MT2009 Plus

Ta poprawka jest kandydatem do klienta 2.0.9. Nie jest jeszcze wskazana przez
`update-manifest-mt2009.json` i nie wolno jej publikować przed testem operatora.

## Zawartość

- `client-serverinfo-coop.patch` dodaje do `root/serverinfo.py` opcjonalny drugi
  świat czytany z `coop.cfg`. Localhost pozostaje zawsze pierwszym serwerem.
- `Dolacz.ps1` dekoduje kod `M2COOP1`, sprawdza JSON, host, porty i liczbę
  kanałów, a następnie zapisuje `coop.cfg` jako ASCII z zakończeniami CRLF.
- `Dolacz.bat` uruchamia skrypt w Windows PowerShell 5.1.

`Dolacz.ps1` musi pozostać zapisany jako UTF-8 z BOM. Oba skrypty należy
umieścić obok `metin2client.exe`.

## Budowanie

Patch stosuje się do rozpakowanego `root` klienta 2.0.8 po poprawce
`client-patches/serverlist-localhost`. Zmiany z `client-patches/coffee-links`
dotyczą innych plików i muszą wejść do tej samej paczki klienta.

Po zastosowaniu patcha trzeba przepakować `root.data` i `root.index`. Paczka
aktualizacyjna zawiera:

```
pack/root.data
pack/root.index
Dolacz.bat
Dolacz.ps1
```

Nie należy dodawać `coop.cfg` do paczki. Tworzy go launcher albo `Dolacz.ps1`
na komputerze gracza.

## Zachowanie i walidacja

Brak pliku, błędna linia, duplikat klucza, niepoprawny host, port spoza zakresu
1-65535, więcej niż dwa kanały albo przepełnienie portu CH2 powodują pominięcie
wpisu COOP. Cały odczyt jest osłonięty `try/except`, więc uszkodzony plik nie
blokuje startu klienta.

Testowy wpis VPS:

```
name=Swiat testowy
host=179.61.251.72
auth=11000
channel=13000
channels=2
```

Przykładowy kod użyty w teście `Dolacz.ps1` (login i hasło są fikcyjne):

```
M2COOP1:eyJ2IjoxLCJuYW1lIjoixZp3aWF0IEtvd2Fsc2tpZWdvIiwiaG9zdCI6IjE3OS42MS4yNTEuNzIiLCJhdXRoIjoxMTAwMCwiY2hhbm5lbCI6MTMwMDAsImNoYW5uZWxzIjoyLCJsb2dpbiI6Imtvd2Fsc2tpIiwicGFzc3dvcmQiOiJ0YWpuZTEyMyIsInZwbiI6InRhaWxzY2FsZSJ9
```

## Wynik audytu przełączania rdzeni

W źródle klienta `UserInterface/PythonNetworkStreamPhaseGame.cpp`, w funkcji
`CPythonNetworkStream::RecvWarpPacket()`, klient wywołuje:

```
CNetworkStream::PingPort(kWarpPacket.lAddr, kWarpPacket.wPort);
CNetworkStream::Connect((DWORD)kWarpPacket.lAddr, kWarpPacket.wPort);
```

Klient łączy się więc z adresem i portem przesłanym przez serwer w
`TPacketGCWarp`, a nie z hostem zapisanym wcześniej przy logowaniu. Podczas
hostowania COOP launcher/serwer musi ustawić dostępny dla znajomego `PROXY_IP`
dla wszystkich rdzeni map.
