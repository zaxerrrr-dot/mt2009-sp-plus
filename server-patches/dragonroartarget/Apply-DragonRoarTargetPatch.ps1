[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# Smoczy Skowyt (SKILL_DRAGON_ROAR, 93) on the target it was cast at
# (server-patches/dragonroartarget, README.md): skill_proto makes it SELFONLY,
# so the splash was only ever around the Shaman while the client plays it at
# the target. Same edit and marker as apply_dragonroartarget.py (the
# Linux/VPS twin). A file without the expected code throws and nothing is
# written.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku char_skill.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_DRAGON_ROAR_TARGET_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$reCompute = [regex]'(\n)(int CHARACTER::ComputeSkill\(DWORD dwVnum, LPCHARACTER pkVictim, BYTE bSkillLevel\)\r?\n)'
$reSelf1 = [regex]'(\tif \(IS_SET\(pkSk->dwFlag, SKILL_FLAG_SELFONLY\))(\)\r?\n\t\tpkVictim = this;)'
$reSelf2 = [regex]'(\telse if \(IS_SET\(pkSk->dwFlag, SKILL_FLAG_SELFONLY\))(\)\r?\n\t\tpkVictim = this;)'
$reSelf3 = [regex]'(\telse if \(IS_SET\(pkSk->dwFlag, SKILL_FLAG_SELFONLY\)\)\r?\n\t\tComputeSkill\(dwVnum, )this(\);)'
foreach ($re in @($reCompute, $reSelf1, $reSelf2, $reSelf3)) {
    if ($re.Matches($text).Count -ne 1) {
        throw 'Nie mozna zastosowac poprawki Smoczego Skowytu: nie znaleziono oczekiwanego kodu w char_skill.cpp.'
    }
}
$nl = if ($text.Contains("`r`n")) { "`r`n" } else { "`n" }
$helper = @(
    "// ${marker}: Smoczy Skowyt on the target it was cast at",
    '// (server-patches/dragonroartarget).',
    'static bool IsDragonRoarAtTarget(LPCHARACTER ch, DWORD dwVnum, LPCHARACTER victim)',
    '{',
    "`treturn dwVnum == SKILL_DRAGON_ROAR && ch && victim && victim != ch && !victim->IsDead() &&",
    "`t`tvictim->GetMapIndex() == ch->GetMapIndex() &&",
    "`t`tDISTANCE_APPROX(ch->GetX() - victim->GetX(), ch->GetY() - victim->GetY()) <= 1500;",
    '}',
    '',
    ''
) -join $nl
$cond = ' && !IsDragonRoarAtTarget(this, dwVnum, pkVictim)'
$text = $reCompute.Replace($text, { param($m) $m.Groups[1].Value + $helper + $m.Groups[2].Value }, 1)
$text = $reSelf1.Replace($text, { param($m) $m.Groups[1].Value + $cond + $m.Groups[2].Value }, 1)
$text = $reSelf2.Replace($text, { param($m) $m.Groups[1].Value + $cond + $m.Groups[2].Value }, 1)
$text = $reSelf3.Replace($text, { param($m) $m.Groups[1].Value + 'IsDragonRoarAtTarget(this, dwVnum, pkVictim) ? pkVictim : this' + $m.Groups[2].Value }, 1)
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
