[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# A pet's magic attack % bonus (POINT_MAGIC_ATT_BONUS_PER, 131) for real
# (server-patches/magicattper, README.md): CHARACTER::PointChange had no case
# for it. Same edit and marker as apply_magicattper.py (the Linux/VPS twin);
# the line goes in with the line ending of the one it follows. A file without
# the expected code throws and nothing is written.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku char.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_MAGIC_ATT_PER_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$re = [regex]"(\t\tcase POINT_MELEE_MAGIC_ATT_BONUS_PER:(\r?\n))"
if ($re.Matches($text).Count -ne 1) {
    throw 'Nie mozna zastosowac poprawki bonusu ataku magicznego: nie znaleziono oczekiwanego kodu w char.cpp.'
}
$text = $re.Replace($text, { param($m) $m.Groups[1].Value + "`t`tcase POINT_MAGIC_ATT_BONUS_PER: // $marker" + $m.Groups[2].Value }, 1)
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
