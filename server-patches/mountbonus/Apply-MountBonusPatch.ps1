[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# A mount seal's bonuses once, not once a ride (server-patches/mountbonus,
# README.md): CMountActor::Mount (MountSystem.cpp) clears AFFECT_MOUNT_BONUS
# before it adds the seal's bonuses. Same replacement and marker as
# apply_mountbonus.py (the Linux/VPS twin). A file without the expected code
# throws and nothing is written; only the block changes, in its own line ending.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku MountSystem.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_MOUNT_BONUS_ONCE_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$old = "`tUnmount();`n`n`tm_pkOwner->AddAffect(AFFECT_MOUNT, POINT_MOUNT, m_dwVnum, AFF_NONE, lDuration, 0, true);`n"
$new = "`tUnmount();`n`t// MT2009_PLUS_MOUNT_BONUS_ONCE_V1 (server-patches/mountbonus): Unmount() above clears`n`t// the seal's bonuses only while GetMountVnum() is set, and a rider who`n`t// lost the saddle another way (death, a warp) kept them: the next Mount`n`t// added a second set, and the next a third - +30% experience a ride on`n`t// a Snow Tiger until MALL_EXPBONUS hit its cap. Cleared every time.`n`tm_pkOwner->RemoveAffect(AFFECT_MOUNT_BONUS);`n`n`tm_pkOwner->AddAffect(AFFECT_MOUNT, POINT_MOUNT, m_dwVnum, AFF_NONE, lDuration, 0, true);`n"
$done = $false
foreach ($pair in @(@($old.Replace("`n", "`r`n"), $new.Replace("`n", "`r`n")), @($old, $new))) {
    if (([regex]::Matches($text, [regex]::Escape($pair[0]))).Count -eq 1) {
        $index = $text.IndexOf($pair[0], [StringComparison]::Ordinal)
        $text = $text.Substring(0, $index) + $pair[1] + $text.Substring($index + $pair[0].Length)
        $done = $true
        break
    }
}
if (-not $done) {
    throw 'Nie mozna zastosowac poprawki bonusow wierzchowca: nie znaleziono oczekiwanego kodu w MountSystem.cpp.'
}
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
