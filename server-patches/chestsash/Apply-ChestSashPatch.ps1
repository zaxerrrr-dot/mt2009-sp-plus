[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDirectory
)

# The unique sash from a box opened with its key: the bosses' chests only, not
# the Gold and Silver Caskets (server-patches/chestsash, README.md). Same
# replacement and marker as apply_chestsash.py (the Linux/VPS twin). A file
# without the expected code throws and nothing is written.

$ErrorActionPreference = 'Stop'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$mark = 'MT2009_PLUS_CHEST_SASH_BOSS_ONLY_V1'
$file = Join-Path $SourceDirectory 'char_item.cpp'
if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Brak pliku: $file" }
$text = [IO.File]::ReadAllText($file, $latin1)
if ($text.Contains($mark)) { return [pscustomobject]@{ Changed = $false } }
$old = "`t`t`t`t`t`tif (GetDesc() &&`n`t`t`t`t`t`t`t`tquest::CQuestManager::instance().GetEventFlag(`"m2_sash_off`") == 0)`n"
$new = "`t`t`t`t`t`t// MT2009_PLUS_CHEST_SASH_BOSS_ONLY_V1 (server-patches/chestsash): not from the Gold and`n`t`t`t`t`t`t// Silver Caskets (50006, 50007, 50012, 50013), only the bosses' chests.`n`t`t`t`t`t`tif (GetDesc() && dwBoxVnum != 50006 && dwBoxVnum != 50007 &&`n`t`t`t`t`t`t`t`tdwBoxVnum != 50012 && dwBoxVnum != 50013 &&`n`t`t`t`t`t`t`t`tquest::CQuestManager::instance().GetEventFlag(`"m2_sash_off`") == 0)`n"
if ($text.Contains("`r`n")) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
    throw "Nie mozna zastosowac poprawki szarf ze szkatulek: nie znaleziono oczekiwanego kodu w char_item.cpp."
}
$index = $text.IndexOf($old, [StringComparison]::Ordinal)
$text = $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length)
[IO.File]::WriteAllText($file, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
