[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# Every costume mount's speed in the movement check (server-patches/
# mountspeed, README.md): the Magma Manni correction of
# GetAllowedMovementDistance (char_player.cpp) for every mount, widening only.
# Same replacement and marker as apply_mountspeed.py (the Linux/VPS twin). A
# file without the expected code throws and nothing is written. CRLF/LF kept.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku char_player.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_MOUNT_SPEED_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$original = [IO.File]::ReadAllText($SourceFile, $latin1)
$hadCrlf = $original.Contains("`r`n")
$text = $original.Replace("`r`n", "`n")
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }

function L { param([string[]]$Lines) ($Lines -join "`n") + "`n" }
$old = L @("`t`tif (mountVnum == 53201 || mountVnum == 53202 || mountVnum == 53203)",
           "`t`t{",
           "`t`t`tconstexpr float kCombatHorseMotionSpeed = 740.67f;",
           "`t`t`tconst float mountMotionMultiplier = ch->GetMoveMotionSpeed() / kCombatHorseMotionSpeed;",
           "",
           "`t`t`tbaseDistance = static_cast<DWORD>(baseDistance * mountMotionMultiplier);",
           "`t`t}")
$new = L @("`t`t// $marker (server-patches/mountspeed): every costume mount,",
           "`t`t// not Magma Manni alone - 98 of the 246 run faster than the combat",
           "`t`t// horse the ceiling is set for, and each was pulled back like Manni",
           "`t`t// was. Widened only: a slower mount keeps the ceiling it had.",
           "`t`tif (mountVnum != 0 && ch->GetWear(WEAR_COSTUME_MOUNT))",
           "`t`t{",
           "`t`t`tconstexpr float kCombatHorseMotionSpeed = 740.67f;",
           "`t`t`tconst float mountMotionMultiplier = ch->GetMoveMotionSpeed() / kCombatHorseMotionSpeed;",
           "",
           "`t`t`tif (mountMotionMultiplier > 1.0f)",
           "`t`t`t`tbaseDistance = static_cast<DWORD>(baseDistance * mountMotionMultiplier);",
           "`t`t}")
if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
    throw 'Nie mozna zastosowac poprawki predkosci wierzchowcow: nie znaleziono oczekiwanego kodu w char_player.cpp.'
}
$index = $text.IndexOf($old, [StringComparison]::Ordinal)
$text = $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length)
if ($hadCrlf) { $text = $text.Replace("`n", "`r`n") }
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
