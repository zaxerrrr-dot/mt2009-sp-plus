[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# Level range of the Cor Draconis and sash drops (server-patches/rarelevel,
# README.md): nothing from a Metin or boss more than 15 levels below the
# killer (item_manager.cpp, ITEM_MANAGER::CreateDropItem). Same replacements
# and marker as apply_rarelevel.py (the Linux/VPS twin). A file without the
# expected code throws and nothing is written; only the two blocks change,
# in the file's own line ending.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku item_manager.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_RARE_LEVEL_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$crlf = $text.Contains("`r`n")
$pairs = @(
    @("`tif (pkKiller &&`n`t`tpkKiller->IsPC() &&`n`t`tpkKiller->GetDesc())`n`t{`n`t`tint corChance = 0;`n", "`t// MT2009_PLUS_RARE_LEVEL_V1 (server-patches/rarelevel): no Cor Draconis from a`n`t// Metin or boss more than 15 levels below the killer (a level 90 at a level`n`t// 5 stone); a stronger one drops with no limit.`n`tif (pkKiller &&`n`t`tpkKiller->IsPC() &&`n`t`tpkKiller->GetDesc() &&`n`t`tpkKiller->GetLevel() <= pkChr->GetLevel() + 15)`n`t{`n`t`tint corChance = 0;`n"),
    @("`t`tpkKiller->GetDesc() &&`n`t`tpkChr->GetMobRank() >= MOB_RANK_BOSS)`n`t{`n", "`t`tpkKiller->GetDesc() &&`n`t`tpkChr->GetMobRank() >= MOB_RANK_BOSS &&`n`t`t// MT2009_PLUS_RARE_LEVEL_V1: the sash, too, only within 15 levels below.`n`t`tpkKiller->GetLevel() <= pkChr->GetLevel() + 15)`n`t{`n")
)
foreach ($pair in $pairs) {
    $old = $pair[0]; $new = $pair[1]
    if ($crlf) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
    if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
        throw 'Nie mozna zastosowac poprawki poziomu dropu Cor Draconis i szarf: nie znaleziono oczekiwanego kodu w item_manager.cpp.'
    }
    $index = $text.IndexOf($old, [StringComparison]::Ordinal)
    $text = $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length)
}
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
