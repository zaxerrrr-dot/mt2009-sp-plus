#!/usr/bin/env python3
"""apply_dragonroartarget.py <engine game/src dir> -- Linux/VPS twin of
Apply-DragonRoarTargetPatch.ps1 (same edit, same marker). Smoczy Skowyt
(SKILL_DRAGON_ROAR, 93) is SELFONLY in skill_proto, so the engine put the
caster in the victim's place and the splash was only ever around the Shaman,
while the client plays the skill at the target it was cast on - a pack at
range took the effect and no damage ("Skowyt nie zadaje dmg z odleglosci",
27 September). With a living target of the caster's map within 1500 the
skill is computed on the target, whose surroundings the splash covers
(ComputeSkill's FuncSplashDamage is centred on the victim); without one it
is the Shaman's own surroundings, as before. Applied once; a file without
the expected code stops with an error, changing nothing."""
import os
import re
import sys

MARK = "MT2009_PLUS_DRAGON_ROAR_TARGET_V1"
HELPER = (
    "// {mark}: Smoczy Skowyt on the target it was cast at\n"
    "// (server-patches/dragonroartarget).\n"
    "static bool IsDragonRoarAtTarget(LPCHARACTER ch, DWORD dwVnum, LPCHARACTER victim)\n"
    "{{\n"
    "\treturn dwVnum == SKILL_DRAGON_ROAR && ch && victim && victim != ch && !victim->IsDead() &&\n"
    "\t\tvictim->GetMapIndex() == ch->GetMapIndex() &&\n"
    "\t\tDISTANCE_APPROX(ch->GetX() - victim->GetX(), ch->GetY() - victim->GetY()) <= 1500;\n"
    "}}\n\n"
)
RE_COMPUTE = re.compile(r"(\n)(int CHARACTER::ComputeSkill\(DWORD dwVnum, LPCHARACTER pkVictim, BYTE bSkillLevel\)\r?\n)")
RE_SELF1 = re.compile(r"(\tif \(IS_SET\(pkSk->dwFlag, SKILL_FLAG_SELFONLY\))(\)\r?\n\t\tpkVictim = this;)")
RE_SELF2 = re.compile(r"(\telse if \(IS_SET\(pkSk->dwFlag, SKILL_FLAG_SELFONLY\))(\)\r?\n\t\tpkVictim = this;)")
RE_SELF3 = re.compile(r"(\telse if \(IS_SET\(pkSk->dwFlag, SKILL_FLAG_SELFONLY\)\)\r?\n\t\tComputeSkill\(dwVnum, )this(\);)")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "char_skill.cpp")
    text = open(path, "rb").read().decode("latin-1")
    if MARK in text:
        print("dragonroartarget: already applied")
        return
    for name, rx in (("compute", RE_COMPUTE), ("self1", RE_SELF1), ("self2", RE_SELF2), ("self3", RE_SELF3)):
        if len(rx.findall(text)) != 1:
            sys.exit("dragonroartarget: expected code (%s) not found in %s" % (name, path))
    nl = "\r\n" if "\r\n" in text else "\n"
    helper = HELPER.format(mark=MARK).replace("\n", nl)
    text = RE_COMPUTE.sub(lambda m: m.group(1) + helper + m.group(2), text, count=1)
    cond = " && !IsDragonRoarAtTarget(this, dwVnum, pkVictim)"
    text = RE_SELF1.sub(lambda m: m.group(1) + cond + m.group(2), text, count=1)
    text = RE_SELF2.sub(lambda m: m.group(1) + cond + m.group(2), text, count=1)
    text = RE_SELF3.sub(lambda m: m.group(1) + "IsDragonRoarAtTarget(this, dwVnum, pkVictim) ? pkVictim : this" + m.group(2), text, count=1)
    open(path, "wb").write(text.encode("latin-1"))
    print("dragonroartarget: applied")


if __name__ == "__main__":
    main()
