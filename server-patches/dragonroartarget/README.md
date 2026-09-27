# Smoczy Skowyt na cel (dragonroartarget)

Smoczy Skowyt (umiejętność szamana 93, `SKILL_DRAGON_ROAR`) ma w `skill_proto`
flagę `SELFONLY`, więc silnik zawsze podmieniał cel na samego szamana i obszar
obrażeń był tylko wokół niego. Klient rysuje umiejętność przy celu, na który
została rzucona, więc stado na dystans dostawało efekt, ale nie obrażenia
(„Skowyt nie zadaje dmg z odległości”, 27 września 2026).

Łatka w `char_skill.cpp`. Klient nie podaje celu Skowytu (albo podaje samego
szamana), więc celem jest zaznaczona postać (`CHARACTER::GetTarget`, przy
niej klient rysuje efekt) – żywa, na tej samej mapie, taka, którą szaman
może zaatakować:

- w zasięgu 1500 umiejętność liczy się na celu, a obszar obrażeń obejmuje
  jego otoczenie (`FuncSplashDamage` w `ComputeSkill` jest liczony wokół
  ofiary);
- dalej umiejętność w ogóle się nie rzuca: bez many i bez odnowienia,
  komunikat „Cel jest za daleko.”;
- bez takiego celu działa jak dotąd, wokół szamana.

- `Apply-DragonRoarTargetPatch.ps1` – Windows (instalator silnika,
  `tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_dragonroartarget.py` – ta sama zmiana dla Linuksa/VPS;
- znacznik: `MT2009_PLUS_DRAGON_ROAR_TARGET_V1`.
