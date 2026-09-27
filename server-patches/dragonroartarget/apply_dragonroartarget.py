#!/usr/bin/env python3
"""apply_dragonroartarget.py <engine game/src dir> -- Linux/VPS twin of
Apply-DragonRoarTargetPatch.ps1 (same edit, same marker). Smoczy Skowyt
(SKILL_DRAGON_ROAR, 93) is SELFONLY in skill_proto, so the engine put the
caster in the victim's place and the splash was only ever around the Shaman,
while the client plays the skill at the target it was cast on - a pack at
range took the effect and no damage ("Skowyt nie zadaje dmg z odleglosci",
27 September). The client names no victim, or the Shaman itself, so the
target is the packet's victim when it is another character, or else the
character's selected target (CHARACTER::GetTarget, the one the client plays
the effect at), if the caster may strike it:
  - within 1500 the skill is computed on the target,
    whose surroundings the splash covers (ComputeSkill's FuncSplashDamage is
    centred on the victim);
  - further than that the skill is not cast at all - no mana, no cooldown,
    "Cel jest za daleko." (the operator, 27 September);
  - with no such target it is the Shaman's own surroundings, as before.
Applied once; a file without the expected code stops with an error, changing
nothing."""
import os
import re
import sys

MARK = "MT2009_PLUS_DRAGON_ROAR_TARGET_V1"
HELPER = (
    "// {mark}: Smoczy Skowyt on the target it was cast at\n"
    "// (server-patches/dragonroartarget): the packet's victim when it is not\n"
    "// the Shaman, else its selected target - one it may strike, alive, on its\n"
    "// map. Within DRAGON_ROAR_TARGET_RANGE the skill is computed on it;\n"
    "// further away the skill is refused (UseSkill).\n"
    "static const int DRAGON_ROAR_TARGET_RANGE = 1500;\n"
    "static LPCHARACTER GetDragonRoarTarget(LPCHARACTER ch, DWORD dwVnum, LPCHARACTER victim)\n"
    "{{\n"
    "\tif (dwVnum != SKILL_DRAGON_ROAR || !ch)\n"
    "\t\treturn NULL;\n"
    "\tLPCHARACTER target = (victim && victim != ch) ? victim : ch->GetTarget();\n"
    "\tif (!target || target == ch || target->IsDead() || target->GetMapIndex() != ch->GetMapIndex() ||\n"
    "\t\t\t!battle_is_attackable(ch, target))\n"
    "\t\treturn NULL;\n"
    "\treturn target;\n"
    "}}\n\n"
    "static LPCHARACTER GetSelfOnlySkillVictim(LPCHARACTER ch, DWORD dwVnum, LPCHARACTER victim)\n"
    "{{\n"
    "\tLPCHARACTER target = GetDragonRoarTarget(ch, dwVnum, victim);\n"
    "\tif (target && DISTANCE_APPROX(ch->GetX() - target->GetX(), ch->GetY() - target->GetY()) <= DRAGON_ROAR_TARGET_RANGE)\n"
    "\t\treturn target;\n"
    "\treturn ch;\n"
    "}}\n\n"
)
REFUSE = (
    "\t// {mark}: Smoczy Skowyt at a target out of its reach is not cast.\n"
    "\tif (LPCHARACTER roarTarget = GetDragonRoarTarget(this, dwVnum, pkVictim))\n"
    "\t{{\n"
    "\t\tif (DISTANCE_APPROX(GetX() - roarTarget->GetX(), GetY() - roarTarget->GetY()) > DRAGON_ROAR_TARGET_RANGE)\n"
    "\t\t{{\n"
    "\t\t\tChatPacket(CHAT_TYPE_INFO, \"Cel jest za daleko.\");\n"
    "\t\t\treturn false;\n"
    "\t\t}}\n"
    "\t}}\n\n"
)
RE_COMPUTE = re.compile(r"(\n)(int CHARACTER::ComputeSkill\(DWORD dwVnum, LPCHARACTER pkVictim, BYTE bSkillLevel\)\r?\n)")
RE_REFUSE = re.compile(r"(bool CHARACTER::UseSkill\(DWORD dwVnum, LPCHARACTER pkVictim, bool bUseGrandMaster\)\r?\n\{\r?\n(?:.*\r?\n)*?\tif \(IsPolymorphed\(\)\)\r?\n\t\treturn false;\r?\n\r?\n)")
RE_SELF1 = re.compile(r"(\tif \(IS_SET\(pkSk->dwFlag, SKILL_FLAG_SELFONLY\)\)\r?\n\t\tpkVictim = )this(;)")
RE_SELF2 = re.compile(r"(\telse if \(IS_SET\(pkSk->dwFlag, SKILL_FLAG_SELFONLY\)\)\r?\n\t\tpkVictim = )this(;)")
RE_SELF3 = re.compile(r"(\telse if \(IS_SET\(pkSk->dwFlag, SKILL_FLAG_SELFONLY\)\)\r?\n\t\tComputeSkill\(dwVnum, )this(\);)")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "char_skill.cpp")
    text = open(path, "rb").read().decode("latin-1")
    if MARK in text:
        print("dragonroartarget: already applied")
        return
    for name, rx in (("compute", RE_COMPUTE), ("refuse", RE_REFUSE), ("self1", RE_SELF1),
                     ("self2", RE_SELF2), ("self3", RE_SELF3)):
        if len(rx.findall(text)) != 1:
            sys.exit("dragonroartarget: expected code (%s) not found in %s" % (name, path))
    nl = "\r\n" if "\r\n" in text else "\n"
    helper = HELPER.format(mark=MARK).replace("\n", nl)
    refuse = REFUSE.format(mark=MARK).replace("\n", nl)
    text = RE_COMPUTE.sub(lambda m: m.group(1) + helper + m.group(2), text, count=1)
    text = RE_REFUSE.sub(lambda m: m.group(1) + refuse, text, count=1)
    pick = "GetSelfOnlySkillVictim(this, dwVnum, pkVictim)"
    text = RE_SELF1.sub(lambda m: m.group(1) + pick + m.group(2), text, count=1)
    text = RE_SELF2.sub(lambda m: m.group(1) + pick + m.group(2), text, count=1)
    # pkVictim is the one chosen just above (the Shaman or Skowyt's target).
    text = RE_SELF3.sub(lambda m: m.group(1) + "pkVictim" + m.group(2), text, count=1)
    open(path, "wb").write(text.encode("latin-1"))
    print("dragonroartarget: applied")


if __name__ == "__main__":
    main()
