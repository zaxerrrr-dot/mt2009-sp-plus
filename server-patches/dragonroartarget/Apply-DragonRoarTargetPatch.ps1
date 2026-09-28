[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# Smoczy Skowyt (SKILL_DRAGON_ROAR, 93) on the target it was cast at
# (server-patches/dragonroartarget, README.md): skill_proto makes it SELFONLY,
# so the splash was only ever around the Shaman while the client plays it at
# the target. Within 1800 of its target (Flying Talisman's reach) the skill is computed there, further
# away it is refused. Same edit and marker as apply_dragonroartarget.py (the
# Linux/VPS twin). A file without the expected code throws and nothing is
# written.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku char_skill.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_DRAGON_ROAR_TARGET_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$reCompute = [regex]'(\n)(int CHARACTER::ComputeSkill\(DWORD dwVnum, LPCHARACTER pkVictim, BYTE bSkillLevel\)\r?\n)'
$reRefuse = [regex]'(bool CHARACTER::UseSkill\(DWORD dwVnum, LPCHARACTER pkVictim, bool bUseGrandMaster\)\r?\n\{\r?\n(?:.*\r?\n)*?\tif \(IsPolymorphed\(\)\)\r?\n\t\treturn false;\r?\n\r?\n)'
$reSelf1 = [regex]'(\tif \(IS_SET\(pkSk->dwFlag, SKILL_FLAG_SELFONLY\)\)\r?\n\t\tpkVictim = )this(;)'
$reSelf2 = [regex]'(\telse if \(IS_SET\(pkSk->dwFlag, SKILL_FLAG_SELFONLY\)\)\r?\n\t\tpkVictim = )this(;)'
$reSelf3 = [regex]'(\telse if \(IS_SET\(pkSk->dwFlag, SKILL_FLAG_SELFONLY\)\)\r?\n\t\tComputeSkill\(dwVnum, )this(\);)'
foreach ($re in @($reCompute, $reRefuse, $reSelf1, $reSelf2, $reSelf3)) {
    if ($re.Matches($text).Count -ne 1) {
        throw 'Nie mozna zastosowac poprawki Smoczego Skowytu: nie znaleziono oczekiwanego kodu w char_skill.cpp.'
    }
}
$nl = if ($text.Contains("`r`n")) { "`r`n" } else { "`n" }
$helper = (@(
    "// MT2009_PLUS_DRAGON_ROAR_TARGET_V1: Smoczy Skowyt on the target it was cast at",
    "// (server-patches/dragonroartarget): the packet's victim when it is not",
    "// the Shaman, else its selected target - one it may strike, alive, on its",
    "// map. Within DRAGON_ROAR_TARGET_RANGE the skill is computed on it;",
    "// further away the skill is refused (UseSkill).",
    "static const int DRAGON_ROAR_TARGET_RANGE = 1800;",
    "static LPCHARACTER GetDragonRoarTarget(LPCHARACTER ch, DWORD dwVnum, LPCHARACTER victim)",
    "{",
    "`tif (dwVnum != SKILL_DRAGON_ROAR || !ch)",
    "`t`treturn NULL;",
    "`tLPCHARACTER target = (victim && victim != ch) ? victim : ch->GetTarget();",
    "`tif (!target || target == ch || target->IsDead() || target->GetMapIndex() != ch->GetMapIndex() ||",
    "`t`t`t!battle_is_attackable(ch, target))",
    "`t`treturn NULL;",
    "`treturn target;",
    "}",
    "",
    "static LPCHARACTER GetSelfOnlySkillVictim(LPCHARACTER ch, DWORD dwVnum, LPCHARACTER victim)",
    "{",
    "`tLPCHARACTER target = GetDragonRoarTarget(ch, dwVnum, victim);",
    "`tif (target && DISTANCE_APPROX(ch->GetX() - target->GetX(), ch->GetY() - target->GetY()) <= DRAGON_ROAR_TARGET_RANGE)",
    "`t`treturn target;",
    "`treturn ch;",
    "}",
    ""
) -join $nl) + $nl
$refuse = (@(
    "`t// MT2009_PLUS_DRAGON_ROAR_TARGET_V1: Smoczy Skowyt at a target out of its reach is not cast.",
    "`tif (LPCHARACTER roarTarget = GetDragonRoarTarget(this, dwVnum, pkVictim))",
    "`t{",
    "`t`tif (DISTANCE_APPROX(GetX() - roarTarget->GetX(), GetY() - roarTarget->GetY()) > DRAGON_ROAR_TARGET_RANGE)",
    "`t`t{",
    "`t`t`tChatPacket(CHAT_TYPE_INFO, `"Cel jest za daleko.`");",
    "`t`t`treturn false;",
    "`t`t}",
    "`t}",
    ""
) -join $nl) + $nl
$pick = 'GetSelfOnlySkillVictim(this, dwVnum, pkVictim)'
$text = $reCompute.Replace($text, { param($m) $m.Groups[1].Value + $helper + $m.Groups[2].Value }, 1)
$text = $reRefuse.Replace($text, { param($m) $m.Groups[1].Value + $refuse }, 1)
$text = $reSelf1.Replace($text, { param($m) $m.Groups[1].Value + $pick + $m.Groups[2].Value }, 1)
$text = $reSelf2.Replace($text, { param($m) $m.Groups[1].Value + $pick + $m.Groups[2].Value }, 1)
$text = $reSelf3.Replace($text, { param($m) $m.Groups[1].Value + 'pkVictim' + $m.Groups[2].Value }, 1)
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
