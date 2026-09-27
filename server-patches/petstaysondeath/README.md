# Pet zostaje po śmierci (petstaysondeath)

`CPetActor::Update` (`PetSystem.cpp`) odwoływał peta w chwili śmierci
właściciela. Teraz pet czeka przy ciele i po wskrzeszeniu znowu idzie za
właścicielem („po zginięciu pet jest odwoływany, ma zostawać”, 27 września
2026). Pet znika jak dotąd, gdy sam zginie albo gdy jego przedmiot zmieni
właściciela lub zniknie.

- `Apply-PetStaysOnDeathPatch.ps1` – Windows (instalator silnika,
  `tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_petstaysondeath.py` – ta sama zmiana dla Linuksa/VPS;
- znacznik: `MT2009_PLUS_PET_STAYS_ON_DEATH_V1`.
