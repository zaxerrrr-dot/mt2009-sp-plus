[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# 5 s of slack in the speedhack move check (server-patches/speedhackclock,
# README.md): CInputMain::Move (input_main.cpp) disconnected every player of
# a PC whose Docker/WSL2 clock is stepped back a few seconds at a time. Same
# replacement and marker as apply_speedhackclock.py (the Linux/VPS twin). A
# file without the expected code throws and nothing is written; only the line
# changes, in its own line ending.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku input_main.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_SPEEDHACK_CLOCK_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$old = "`t`t`telse if (iDelta < -(iServerDelta / 50))`n"
$new = "`t`t`t// MT2009_PLUS_SPEEDHACK_CLOCK_V1 (server-patches/speedhackclock): 5 s of slack.`n`t`t`t// A Docker/WSL2 clock that runs fast and is stepped back 2-3 s at a time put`n`t`t`t// a player's moves 'in the future' and the 2% margin disconnected him every`n`t`t`t// half minute (SPEEDHACK: DETECTED! ... delta -1500). A real speedhack runs`n`t`t`t// ahead by far more than 5 s.`n`t`t`telse if (iDelta < -(iServerDelta / 50) - 5000)`n"
$done = $false
foreach ($pair in @(@($old.Replace("`n", "`r`n"), $new.Replace("`n", "`r`n")), @($old, $new))) {
    if (([regex]::Matches($text, [regex]::Escape($pair[0]))).Count -eq 1) {
        $index = $text.IndexOf($pair[0], [StringComparison]::Ordinal)
        $text = $text.Substring(0, $index) + $pair[1] + $text.Substring($index + $pair[0].Length)
        $done = $true
        break
    }
}
if (-not $done) {
    throw 'Nie mozna zastosowac poprawki kontroli speedhacka: nie znaleziono oczekiwanego kodu w input_main.cpp.'
}
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
