[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# A player's mount seal off into the bag at death (server-patches/mountdeath,
# README.md): left in its slot it could not be ridden again until taken off
# and put back on (char_battle.cpp, CHARACTER::Dead). Same replacement and
# marker as apply_mountdeath.py (the Linux/VPS twin). A file without the
# expected code throws and nothing is written.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku char_battle.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_MOUNT_DEATH_UNEQUIP_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$old = "`t`t`tUpdatePacket();`n`t`t}`n`n`t}`n#endif`n`n`tif (!pkKiller && m_dwKillerPID)`n"
$new = "`t`t`tUpdatePacket();`n`t`t}`n`n`t}`n#endif`n`n`t// MT2009_PLUS_MOUNT_DEATH_UNEQUIP_V1 (server-patches/mountdeath): a player's`n`t// mount seal comes off into the bag at death - left in its slot it could`n`t// not be ridden again until taken off and put back on. A full bag keeps`n`t// it where it is. A bot puts it back on from the bag (WearPlayerBotBoughtLook).`n`tif (IsPC())`n`t{`n`t`t// Moved as UnequipItem moves it, without CanUnequipNow: the killing`n`t`t// blow stuns first (Stun), and a stunned character may unequip nothing.`n`t`tLPITEM mountSeal = GetWear(WEAR_COSTUME_MOUNT);`n`t`tconst int sealCell = mountSeal ? GetEmptyInventoryEx(mountSeal) : -1;`n`t`tif (mountSeal && sealCell >= 0)`n`t`t{`n`t`t`tmountSeal->RemoveFromCharacter();`n`t`t`tmountSeal->AddToCharacter(this, TItemPos(mountSeal->GetWindowInventoryEx(), sealCell));`n`t`t}`n`t}`n`n`tif (!pkKiller && m_dwKillerPID)`n"
if ($text.Contains("`r`n")) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
    throw 'Nie mozna zastosowac poprawki pieczeci wierzchowca po smierci: nie znaleziono oczekiwanego kodu w char_battle.cpp.'
}
$index = $text.IndexOf($old, [StringComparison]::Ordinal)
$text = $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length)
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
