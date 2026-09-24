[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# The engine half of the alchemy balance (server-patches/dragonsoulbalance,
# README.md): the apply names dragon_soul_table.txt may use. Same
# replacements and marker as apply_dragonsoulbalance.py (the Linux/VPS twin).
# "Wartosc ataku"/"Obrona" were the percent multipliers POINT_ATT_BONUS/
# POINT_DEF_BONUS and now are the flat values an item bonus gives; the race,
# monster, critical and piercing bonuses become known names. A file without
# the expected code throws and nothing is written. CRLF/LF is kept.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) {
    throw "Brak pliku dragon_soul_table.cpp: $SourceFile"
}

$marker = 'MT2009_PLUS_DS_APPLYS_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$original = [IO.File]::ReadAllText($SourceFile, $latin1)
$hadCrlf = $original.Contains("`r`n")
$text = $original.Replace("`r`n", "`n")
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }

function L { param([string[]]$Lines) ($Lines -join "`n") + "`n" }

$blocks = @(
    @{ Name = 'atak i obrona'
       Old = L @("`t`t{ `"ATT_BONUS`",`t`t`tPOINT_ATT_BONUS },",
                 "`t`t{ `"DEF_BONUS`",`t`t`tPOINT_DEF_BONUS },",
                 "`t`t{ `"MAGIC_ATT_GRADE`",`t`tPOINT_MAGIC_ATT_GRADE },",
                 "`t`t{ `"MAGIC_DEF_GRADE`",`t`tPOINT_MAGIC_DEF_GRADE },")
       New = L @("`t`t// $marker (server-patches/dragonsoulbalance): the flat",
                 "`t`t// values an item bonus gives. POINT_ATT_BONUS/POINT_DEF_BONUS are",
                 "`t`t// percent multipliers (battle.cpp, char.cpp GetArmour...), and the",
                 "`t`t// *_GRADE points are recomputed from level and stats.",
                 "`t`t{ `"ATT_BONUS`",`t`t`tPOINT_ATT_GRADE_BONUS },",
                 "`t`t{ `"DEF_BONUS`",`t`t`tPOINT_DEF_GRADE_BONUS },",
                 "`t`t{ `"MAGIC_ATT_GRADE`",`t`tPOINT_MAGIC_ATT_GRADE_BONUS },",
                 "`t`t{ `"MAGIC_DEF_GRADE`",`t`tPOINT_MAGIC_DEF_GRADE_BONUS },") },
    @{ Name = 'bonusy na rasy'
       Old = L @("`t`t{ `"ATTBONUS_STONE`",`t`tPOINT_ATTBONUS_STONE },")
       New = L @("`t`t{ `"ATTBONUS_STONE`",`t`tPOINT_ATTBONUS_STONE },",
                 "`t`t// ${marker}: the race bonuses in place of the elemental ones,",
                 "`t`t// and the Amethyst's monster, critical and piercing bonuses.",
                 "`t`t{ `"ATTBONUS_HUMAN`",`t`tPOINT_ATTBONUS_HUMAN },",
                 "`t`t{ `"ATTBONUS_ANIMAL`",`t`tPOINT_ATTBONUS_ANIMAL },",
                 "`t`t{ `"ATTBONUS_ORC`",`t`tPOINT_ATTBONUS_ORC },",
                 "`t`t{ `"ATTBONUS_MILGYO`",`t`tPOINT_ATTBONUS_MILGYO },",
                 "`t`t{ `"ATTBONUS_UNDEAD`",`t`tPOINT_ATTBONUS_UNDEAD },",
                 "`t`t{ `"ATTBONUS_MONSTER`",`t`tPOINT_ATTBONUS_MONSTER },",
                 "`t`t{ `"CRITICAL_PCT`",`t`tPOINT_CRITICAL_PCT },",
                 "`t`t{ `"PENETRATE_PCT`",`t`tPOINT_PENETRATE_PCT },") }
)

foreach ($block in $blocks) {
    $count = ([regex]::Matches($text, [regex]::Escape($block.Old))).Count
    if ($count -ne 1) {
        throw "Nie mozna zastosowac poprawki bonusow alchemii ($($block.Name)): nie znaleziono oczekiwanego kodu w dragon_soul_table.cpp."
    }
}
foreach ($block in $blocks) {
    $index = $text.IndexOf($block.Old, [StringComparison]::Ordinal)
    $text = $text.Substring(0, $index) + $block.New + $text.Substring($index + $block.Old.Length)
}
if ($hadCrlf) { $text = $text.Replace("`n", "`r`n") }
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
