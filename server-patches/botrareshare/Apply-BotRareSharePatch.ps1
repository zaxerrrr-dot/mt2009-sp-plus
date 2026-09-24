[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# A bot's share of a many-item drop (server-patches/botrareshare, README.md):
# a Cor Draconis or a sash that CHARACTER::Reward (char_battle.cpp) hands to a
# bot goes into its bag instead of lying on the ground under its name. Same
# replacement and marker as apply_botrareshare.py (the Linux/VPS twin). A file
# without the expected code throws and nothing is written; only the block
# changes, in its own line ending.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku char_battle.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_BOT_RARE_SHARE_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$old = "`t`t`t`t`tif (it == v.end())`n`t`t`t`t`t`tit = v.begin();`n`n#ifdef ENABLE_DICE_SYSTEM`n`t`t`t`t`tif (ch->GetParty())`n"
$new = "`t`t`t`t`tif (it == v.end())`n`t`t`t`t`t`tit = v.begin();`n`n`t`t`t`t`t// MT2009_PLUS_BOT_RARE_SHARE_V1 (server-patches/botrareshare): a Cor Draconis or`n`t`t`t`t`t// a sash whose share of a many-item drop falls to a bot goes into`n`t`t`t`t`t// its bag, as a bot's own kill's does (item_manager.cpp,`n`t`t`t`t`t// MT2009_PLUS_BOT_RARE_DROP_V3): on the ground, owned by a bot that`n`t`t`t`t`t// may not pick a Cor up (char_item.cpp, PickupItem), it lay there`n`t`t`t`t`t// out of every player's reach until the ownership ran out.`n`t`t`t`t`tif (ch->GetDesc() && ch->GetDesc()->IsBot() && (item->GetVnum() == 50255`n#ifdef ENABLE_ACCE_COSTUME_SYSTEM`n`t`t`t`t`t`t`t|| (item->GetType() == ITEM_COSTUME && item->GetSubType() == COSTUME_ACCE)`n#endif`n`t`t`t`t`t`t`t))`n`t`t`t`t`t{`n`t`t`t`t`t`titem->RemoveFromGround();`n`t`t`t`t`t`tsys_log(0, `"[DS_COR_DROP] share to bag: bot pid=%u name=%s vnum=%u id=%u room=%d`",`n`t`t`t`t`t`t`t`tch->GetPlayerID(), ch->GetName(), item->GetVnum(), item->GetID(),`n`t`t`t`t`t`t`t`tch->GetEmptyInventoryEx(item) != -1 ? 1 : 0);`n`t`t`t`t`t`tif (ch->GetEmptyInventoryEx(item) != -1)`n`t`t`t`t`t`t`tch->AutoGiveItem(item);`n`t`t`t`t`t`telse`n`t`t`t`t`t`t`tM2_DESTROY_ITEM(item);`n`t`t`t`t`t`tcontinue;`n`t`t`t`t`t}`n`n#ifdef ENABLE_DICE_SYSTEM`n`t`t`t`t`tif (ch->GetParty())`n"
# Edited in place, in the line ending the block has: the file mixes CRLF and
# LF lines, and nothing else in it may change.
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
    throw 'Nie mozna zastosowac poprawki podzialu dropu dla botow: nie znaleziono oczekiwanego kodu w char_battle.cpp.'
}
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
