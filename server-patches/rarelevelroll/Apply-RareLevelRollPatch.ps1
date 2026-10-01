[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDirectory
)

# The 6th/7th bonus rolls its level by the panel's odds (server-patches/
# rarelevelroll, README.md). Same replacement and marker as
# apply_rarelevelroll.py (the Linux/VPS twin). A file without the expected
# code throws and nothing is written.

$ErrorActionPreference = 'Stop'
$marker = 'MT2009_PLUS_RARE_LEVEL_ROLL_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$file = Join-Path $SourceDirectory 'item_attribute.cpp'
if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Brak pliku: $file" }
$text = [IO.File]::ReadAllText($file, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$old = "`tconst TItemAttrTable& r = g_map_itemRare[avail[number(0, avail.size() - 1)]];`n`tint nAttrLevel = 5;`n"
$new = "`t// MT2009_PLUS_RARE_LEVEL_ROLL_V1 (server-patches/rarelevelroll): nothing left to add is a`n`t// refusal, and the level is rolled by the panel's odds (m2_rare_lv1..5).`n`tif (avail.empty())`n`t`treturn false;`n`tconst TItemAttrTable& r = g_map_itemRare[avail[number(0, avail.size() - 1)]];`n`tint nAttrLevel = 5;`n`t{`n`t`tstatic const int s_aiDefault[5] = { 35, 30, 20, 10, 5 };`n`t`tint aiPct[5];`n`t`tint iTotal = 0;`n`t`tfor (int i = 0; i < 5; ++i)`n`t`t{`n`t`t`tchar szFlag[16];`n`t`t`tsnprintf(szFlag, sizeof(szFlag), `"m2_rare_lv%d`", i + 1);`n`t`t`taiPct[i] = MAX(0, quest::CQuestManager::instance().GetEventFlag(szFlag));`n`t`t`tiTotal += aiPct[i];`n`t`t}`n`t`tif (iTotal <= 0)`n`t`t{`n`t`t`tfor (int i = 0; i < 5; ++i)`n`t`t`t`taiPct[i] = s_aiDefault[i];`n`t`t`tiTotal = 100;`n`t`t}`n`t`tint iRoll = number(1, iTotal);`n`t`tfor (nAttrLevel = 1; nAttrLevel < 5 && iRoll > aiPct[nAttrLevel - 1]; ++nAttrLevel)`n`t`t`tiRoll -= aiPct[nAttrLevel - 1];`n`t}`n"
if ($text.Contains("`r`n")) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
    throw 'Nie mozna zastosowac poprawki losowania poziomu 6/7: nie znaleziono oczekiwanego kodu w item_attribute.cpp.'
}
$index = $text.IndexOf($old, [StringComparison]::Ordinal)
[IO.File]::WriteAllText($file, $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length), $latin1)
return [pscustomobject]@{ Changed = $true }
