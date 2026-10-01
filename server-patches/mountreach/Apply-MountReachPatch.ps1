[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDirectory
)

# A rider's and a boss's reach in a normal hit (server-patches/mountreach,
# README.md). Same replacements and marker as apply_mountreach.py (the
# Linux/VPS twin). A file without the expected code throws and nothing is
# written.

$ErrorActionPreference = 'Stop'
$marker = 'MT2009_PLUS_MOUNT_REACH_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$edits = @(
    @{
        File = 'battle.cpp'
        Old = "`t`t`tif (false == victim->IsPC() && BATTLE_TYPE_MELEE == victim->GetMobBattleType())`n`t`t`t{`n`t`t`t`tmax = MAX(405, (int)(victim->GetMobAttackRange() * 1.15f));`n`t`t`t}`n"
        New = "`t`t`tif (false == victim->IsPC() && BATTLE_TYPE_MELEE == victim->GetMobBattleType())`n`t`t`t{`n`t`t`t`tmax = MAX(405, (int)(victim->GetMobAttackRange() * 1.15f));`n`t`t`t}`n`n`t`t`t// MT2009_PLUS_MOUNT_REACH_V1 (server-patches/mountreach): a rider hits from further`n`t`t`t// away (CHARACTER::Attack lets him reach 900), and a boss's body is big -`n`t`t`t// past 405 the hit was thrown away without a word.`n`t`t`tif (ch->IsRiding())`n`t`t`t`tmax = MAX(max, 600);`n`t`t`tif (false == victim->IsPC() && victim->GetMobRank() >= MOB_RANK_BOSS)`n`t`t`t`tmax += 250;`n"
    },
    @{
        File = 'char_battle.cpp'
        Old = "`tif (distance > maxRadius) {`n`t`tif (IsPC()) {`n"
        New = "`t// MT2009_PLUS_MOUNT_REACH_V1 (body): a boss's or king's body is big - a player's`n`t// reach counts from its edge (battle_melee_attack does the same).`n`tif (IsPC() && false == pkVictim->IsPC() && pkVictim->GetMobRank() >= MOB_RANK_BOSS)`n`t`tmaxRadius += 250;`n`n`tif (distance > maxRadius) {`n`t`tif (IsPC()) {`n"
    }
)
$writes = @()
foreach ($edit in $edits) {
    $file = Join-Path $SourceDirectory $edit.File
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Brak pliku: $file" }
    $text = [IO.File]::ReadAllText($file, $latin1)
    if ($text.Contains($marker)) { continue }
    $old = $edit.Old
    $new = $edit.New
    if ($text.Contains("`r`n")) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
    if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
        throw "Nie mozna zastosowac poprawki zasiegu na wierzchowcu: nie znaleziono oczekiwanego kodu w $($edit.File)."
    }
    $index = $text.IndexOf($old, [StringComparison]::Ordinal)
    $writes += @{ File = $file; Text = $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length) }
}
foreach ($w in $writes) { [IO.File]::WriteAllText($w.File, $w.Text, $latin1) }
return [pscustomobject]@{ Changed = ($writes.Count -gt 0) }
