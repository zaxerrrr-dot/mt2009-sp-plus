[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# Drop preview threshold (server-patches/droppreview, README.md): the /mob_drop
# list (item_manager.cpp, ITEM_MANAGER::GetPossibleMobDropItems) shows an item
# rolled against iRandRange only at 1 in 10 000 kills or better. The drop
# itself is unchanged. Same replacements and marker as apply_droppreview.py
# (the Linux/VPS twin). A file without the expected code throws and nothing is
# written; only the preview's lines change, in the file's own line ending.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku item_manager.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_DROP_PREVIEW_MIN_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$crlf = $text.Contains("`r`n")
$pairs = @(
    @("`t`tout_complete = false;`n`t`treturn;`n`t}`n`n`tint iLevel = pkKiller->GetLevel();`n`tBYTE bRank = pkChr->GetMobRank();`n", "`t`tout_complete = false;`n`t`treturn;`n`t}`n`n`t// MT2009_PLUS_DROP_PREVIEW_MIN_V1 (server-patches/droppreview): an item`n`t// rolled against iRandRange is listed only at 1 in 10 000 kills or better,`n`t// not at 1 in 4 000 000 - the common drop goes by the killer's level, and a`n`t// level-35 player saw +2 weapons on a level-1 dog. The drop is unchanged.`n`tconst int iPreviewMinPercent = MAX(1, iRandRange / 10000);`n`n`tint iLevel = pkKiller->GetLevel();`n`tBYTE bRank = pkChr->GetMobRank();`n"),
    @("`t`t`tint iPercent = (info.m_iPercent * iDeltaPercent) / 100;`n`t`t`tif (iPercent < 1)`n", "`t`t`tint iPercent = (info.m_iPercent * iDeltaPercent) / 100;`n`t`t`tif (iPercent < iPreviewMinPercent)`n"),
    @("`t`t`t`tint iPercent = (info.dwPct * iDeltaPercent) / 100;`n`t`t`t`tif (iPercent < 1)`n", "`t`t`t`tint iPercent = (info.dwPct * iDeltaPercent) / 100;`n`t`t`t`tif (iPercent < iPreviewMinPercent)`n"),
    @("`t`t`t`t`tint iPercent = (vec[i].dwPct * iDeltaPercent) / 100;`n`t`t`t`t`tif (iPercent >= 1)`n", "`t`t`t`t`tint iPercent = (vec[i].dwPct * iDeltaPercent) / 100;`n`t`t`t`t`tif (iPercent >= iPreviewMinPercent)`n"),
    @("`t`t`tint iPercent = (it->second * iDeltaPercent) / 100;`n`t`t`tif (iPercent >= 1)`n`t`t`t`tout_vnums.insert(pkChr->GetMobDropItemVnum());`n", "`t`t`tint iPercent = (it->second * iDeltaPercent) / 100;`n`t`t`tif (iPercent >= iPreviewMinPercent)`n`t`t`t`tout_vnums.insert(pkChr->GetMobDropItemVnum());`n")
)
foreach ($pair in $pairs) {
    $old = $pair[0]; $new = $pair[1]
    if ($crlf) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
    if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
        throw 'Nie mozna zastosowac poprawki podgladu dropu: nie znaleziono oczekiwanego kodu w item_manager.cpp.'
    }
    $index = $text.IndexOf($old, [StringComparison]::Ordinal)
    $text = $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length)
}
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
