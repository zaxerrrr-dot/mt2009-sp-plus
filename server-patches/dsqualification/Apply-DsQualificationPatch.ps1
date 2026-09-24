[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# Every real player gets the Dragon Soul qualification when his affects load
# at login (server-patches/dsqualification, README.md): the alchemy inventory
# works without the level-30 quest. Same replacement and marker as
# apply_dsqualification.py (the Linux/VPS twin). A file without the expected
# code throws and nothing is written. CRLF/LF is kept.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) {
    throw "Brak pliku char_affect.cpp: $SourceFile"
}

$marker = 'MT2009_PLUS_DS_QUALIFY_ON_LOGIN_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$original = [IO.File]::ReadAllText($SourceFile, $latin1)
$hadCrlf = $original.Contains("`r`n")
$text = $original.Replace("`r`n", "`n")
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }

function L { param([string[]]$Lines) ($Lines -join "`n") + "`n" }

$old = L @("`tm_bIsLoadedAffect = true;",
           "",
           "`tComputePoints(); // @fixme156",
           "`tDragonSoul_Initialize();")
$new = L @("`tm_bIsLoadedAffect = true;",
           "",
           "`t// $marker (server-patches/dsqualification): every real",
           "`t// player is qualified for the Dragon Soul alchemy from the start, not",
           "`t// after the level-30 quest: without it a stone from a Cor Draconis",
           "`t// fell to the ground (GetEmptyDragonSoulInventory) and could not be",
           "`t// picked up. The affect is the quest's own (ds.give_qualification),",
           "`t// so the client sees the same thing; bots are left as they are.",
           "`tif (IsPC() && GetDesc() && !GetDesc()->IsBot() && NULL == FindAffect(AFFECT_DRAGON_SOUL_QUALIFIED))",
           "`t`tDragonSoul_GiveQualification();",
           "",
           "`tComputePoints(); // @fixme156",
           "`tDragonSoul_Initialize();")

if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
    throw 'Nie mozna zastosowac poprawki kwalifikacji alchemii: nie znaleziono oczekiwanego kodu w char_affect.cpp.'
}
$index = $text.IndexOf($old, [StringComparison]::Ordinal)
$text = $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length)
if ($hadCrlf) { $text = $text.Replace("`n", "`r`n") }
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
