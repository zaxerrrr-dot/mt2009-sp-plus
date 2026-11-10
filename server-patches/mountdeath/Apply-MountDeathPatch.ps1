[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# MT2009_PLUS_MOUNT_DEATH_KEEP_SEAL_V2 (server-patches/mountdeath, README.md): death only takes the rider off the
# mount seal's mount - the seal stays in its slot (the costume set bonus stays) and its mount comes out again at the
# revive. -SourceFile is char_battle.cpp (CHARACTER::Dead); char.cpp next to it gets the revive part
# (CHARACTER::ReviveInvisible). V1 (MT2009_PLUS_MOUNT_DEATH_UNEQUIP_V1, the seal into the bag at death) is taken out of
# an already patched char_battle.cpp. Same replacements and markers as apply_mountdeath.py (the Linux/VPS twin). Both
# files are checked before either is written; a file without the expected code throws and nothing is written.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku char_battle.cpp: $SourceFile" }
$charFile = Join-Path (Split-Path -Parent $SourceFile) 'char.cpp'
if (-not (Test-Path -LiteralPath $charFile -PathType Leaf)) { throw "Brak pliku char.cpp: $charFile" }
$marker = 'MT2009_PLUS_MOUNT_DEATH_KEEP_SEAL_V2'
$markerV1 = 'MT2009_PLUS_MOUNT_DEATH_UNEQUIP_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$battle = [IO.File]::ReadAllText($SourceFile, $latin1)
$char = [IO.File]::ReadAllText($charFile, $latin1)
if ($battle.Contains($marker) -and $char.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }

function Replace-Once([string]$text, [string]$old, [string]$new, [string]$what) {
    if ($text.Contains("`r`n")) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
    if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
        throw "Nie mozna zastosowac poprawki pieczeci wierzchowca po smierci: nie znaleziono oczekiwanego kodu ($what)."
    }
    $index = $text.IndexOf($old, [StringComparison]::Ordinal)
    return $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length)
}

$v1Old = "`t`t`tUpdatePacket();`n`t`t}`n`n`t}`n#endif`n`n`tif (!pkKiller && m_dwKillerPID)`n"
$v1New = "`t`t`tUpdatePacket();`n`t`t}`n`n`t}`n#endif`n`n`t// MT2009_PLUS_MOUNT_DEATH_UNEQUIP_V1 (server-patches/mountdeath): a player's`n`t// mount seal comes off into the bag at death - left in its slot it could`n`t// not be ridden again until taken off and put back on. A full bag keeps`n`t// it where it is. A bot puts it back on from the bag (WearPlayerBotBoughtLook).`n`tif (IsPC())`n`t{`n`t`t// Moved as UnequipItem moves it, without CanUnequipNow: the killing`n`t`t// blow stuns first (Stun), and a stunned character may unequip nothing.`n`t`tLPITEM mountSeal = GetWear(WEAR_COSTUME_MOUNT);`n`t`tconst int sealCell = mountSeal ? GetEmptyInventoryEx(mountSeal) : -1;`n`t`tif (mountSeal && sealCell >= 0)`n`t`t{`n`t`t`tmountSeal->RemoveFromCharacter();`n`t`t`tmountSeal->AddToCharacter(this, TItemPos(mountSeal->GetWindowInventoryEx(), sealCell));`n`t`t}`n`t}`n`n`tif (!pkKiller && m_dwKillerPID)`n"
$deadOld = "`t`telse if (GetMountVnum())`n`t`t{`n`t`t`tRemoveAffect(AFFECT_MOUNT_BONUS);`n`t`t`tm_dwMountVnum = 0;`n`t`t`tUnEquipSpecialRideUniqueItem();`n`n`t`t`tUpdatePacket();`n`t`t}`n"
$deadNew = "`t`telse if (GetMountVnum())`n`t`t{`n`t`t`t// MT2009_PLUS_MOUNT_DEATH_KEEP_SEAL_V2 (server-patches/mountdeath): death only`n`t`t`t// takes the rider off. The mount seal stays worn - taken off, it took the`n`t`t`t// costume set bonus with it - and after the revive its mount is called`n`t`t`t// again (ReviveInvisible -> CheckMount); Ctrl+G rides it. AFFECT_MOUNT goes`n`t`t`t// with the bonus, as in CMountActor::Unmount. An old unique ride item`n`t`t`t// (UNIQUE1/2) still comes off as before.`n`t`t`tRemoveAffect(AFFECT_MOUNT);`n`t`t`tRemoveAffect(AFFECT_MOUNT_BONUS);`n`t`t`tm_dwMountVnum = 0;`n`t`t`tLPITEM rideUnique1 = GetWear(WEAR_UNIQUE1);`n`t`t`tLPITEM rideUnique2 = GetWear(WEAR_UNIQUE2);`n`t`t`tif ((rideUnique1 && rideUnique1->GetSpecialGroup() == UNIQUE_GROUP_SPECIAL_RIDE) ||`n`t`t`t`t(rideUnique2 && rideUnique2->GetSpecialGroup() == UNIQUE_GROUP_SPECIAL_RIDE))`n`t`t`t`tUnEquipSpecialRideUniqueItem();`n`n`t`t`tUpdatePacket();`n`t`t}`n"
$reviveOld = "void CHARACTER::ReviveInvisible(int iDur)`n{`n`tAddAffect(AFFECT_REVIVE_INVISIBLE, POINT_NONE, 0, AFF_REVIVE_INVISIBLE, iDur, 0, true);`n}`n"
$reviveNew = "void CHARACTER::ReviveInvisible(int iDur)`n{`n`tAddAffect(AFFECT_REVIVE_INVISIBLE, POINT_NONE, 0, AFF_REVIVE_INVISIBLE, iDur, 0, true);`n#ifdef ENABLE_MOUNT_COSTUME_SYSTEM`n`t// MT2009_PLUS_MOUNT_DEATH_KEEP_SEAL_V2 (revive), server-patches/mountdeath: the seal`n`t// stayed worn through the death, its mount went away with the dying rider`n`t// (CMountActor::Update) - it comes out again as at the login (input_login.cpp,`n`t// CheckMount: only when none is out). Not at the login itself (its phase is`n`t// not PHASE_GAME yet, the login calls CheckMount later), not before a warp`n`t// (the town restart: the next login calls it), not while riding, not on the`n`t// OX map (113) or an arena - the login's own rules.`n`tif (IsPC() && !IsDead() && !GetMountVnum() && !IsHorseRiding() && GetWear(WEAR_COSTUME_MOUNT) &&`n`t`tGetDesc() && GetDesc()->IsPhase(PHASE_GAME) && !IsWarping() && GetMapIndex() != 113 &&`n`t`t!CArenaManager::instance().IsArenaMap(GetMapIndex()))`n`t`tCheckMount();`n#endif`n}`n"

$newBattle = $battle
$newChar = $char
if (-not $newBattle.Contains($marker)) {
    if ($newBattle.Contains($markerV1)) { $newBattle = Replace-Once $newBattle $v1New $v1Old 'V1, char_battle.cpp' }
    $newBattle = Replace-Once $newBattle $deadOld $deadNew 'CHARACTER::Dead, char_battle.cpp'
}
if (-not $newChar.Contains($marker)) {
    $newChar = Replace-Once $newChar $reviveOld $reviveNew 'CHARACTER::ReviveInvisible, char.cpp'
}
if ($newBattle -ne $battle) { [IO.File]::WriteAllText($SourceFile, $newBattle, $latin1) }
if ($newChar -ne $char) { [IO.File]::WriteAllText($charFile, $newChar, $latin1) }
return [pscustomobject]@{ Changed = $true }
