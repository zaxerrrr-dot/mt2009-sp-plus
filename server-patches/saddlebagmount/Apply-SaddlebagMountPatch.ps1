[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# Horse saddlebags on a mount seal too (server-patches/saddlebagmount,
# README.md): CHARACTER::CanUseHorseInventory (char.cpp) opened the fifth bag
# page only with the horse out or ridden. Same replacement and marker as
# apply_saddlebagmount.py (the Linux/VPS twin). A file without the expected
# code throws and nothing is written.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku char.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_SADDLEBAG_MOUNT_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$old = "`treturn GetHorseLevel() > 0 && (GetHorse() || IsHorseRiding());`n"
$new = "`t// MT2009_PLUS_SADDLEBAG_MOUNT_V1 (server-patches/saddlebagmount): the`n`t// saddlebags open on a mount seal too (IsRiding: the horse or a mount).`n`treturn GetHorseLevel() > 0 && (GetHorse() || IsRiding());`n"
if ($text.Contains("`r`n")) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
    throw 'Nie mozna zastosowac poprawki jukow na wierzchowcu: nie znaleziono oczekiwanego kodu w char.cpp.'
}
$index = $text.IndexOf($old, [StringComparison]::Ordinal)
$text = $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length)
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
