[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# The Dragon Stone equip trace for players only (server-patches/dstraceplayers,
# README.md): CHARACTER::EquipItem (char_item.cpp). Same replacement and marker
# as apply_dstraceplayers.py (the Linux/VPS twin). A file without the expected
# code throws and nothing is written.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku char_item.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_DS_TRACE_PLAYERS_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$old = "`tconst bool bDSTrace = (item->GetType() == ITEM_DS || item->GetType() == ITEM_SPECIAL_DS);`n"
$new = "`t// MT2009_PLUS_DS_TRACE_PLAYERS_V1 (server-patches/dstraceplayers): the Dragon`n`t// Stone equip trace is for players; bots wear stones all day (playerbot_alchemy.h)`n`t// and eight syserr lines a stone buried everything else.`n`tconst bool bDSTrace = (item->GetType() == ITEM_DS || item->GetType() == ITEM_SPECIAL_DS) &&`n`t`t!(GetDesc() && GetDesc()->IsBot());`n"
if ($text.Contains("`r`n")) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
    throw 'Nie mozna zastosowac poprawki logowania kamieni alchemii: nie znaleziono oczekiwanego kodu w char_item.cpp.'
}
$index = $text.IndexOf($old, [StringComparison]::Ordinal)
$text = $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length)
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
