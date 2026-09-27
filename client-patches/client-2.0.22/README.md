# Klient 2.0.22: podpowiedź mikstur, pasek reputacji

Względem klienta 2.0.21 (`client-patches/client-2.0.21`):

- `root/uitooltip.py` – podpowiedź mikstur zwiększających szybkość ataku
  i ruchu nie wywala się już przy każdym najechaniu myszką (`'module' object
  has no attribute 'APPLY_ATT_SPEED'`): nasz metin2client.exe nie eksportuje
  stałych `APPLY_*`, więc używane są wartości silnika (17 i 19);
- `root/uireputation.py` – pasek nad NPC nie zgłasza błędu, gdy NPC zniknie
  z widoku między dwiema klatkami.

Pakowanie: podmienić te pliki w `root` klienta 2.0.21 i przepakować (m2pack.py).
