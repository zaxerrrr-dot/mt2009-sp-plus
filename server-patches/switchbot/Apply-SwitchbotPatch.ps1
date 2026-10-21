[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDir
)

# Bonus Switcher - Ameria Project's switchbot (server-patches/switchbot, README.md,
# MT2009_PLUS_SWITCHBOT_V1): the entries of edits.json - the same file apply_switchbot.py
# (the Linux/VPS twin) reads. An edit already there (its marker) is skipped; a "revert"
# takes out a line of the old bonus switcher (MT2009_PLUS_BONUS_SWITCH_V1) when it is
# there and does nothing when it is not. An edit whose code is not found exactly once
# throws before a file is written. Edits common/length.h too (../../common from
# game/src). Anchors on the extra inventory's lines, so after ekwipunek.

$ErrorActionPreference = 'Stop'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$edits = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'edits.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$texts = @{}
$crlf = @{}
foreach ($e in $edits) {
    if (-not $texts.ContainsKey($e.file)) {
        $path = Join-Path $SourceDir $e.file
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Brak pliku $($e.file): $path" }
        $raw = [IO.File]::ReadAllText($path, $latin1)
        $crlf[$e.file] = $raw.Contains("`r`n")
        $texts[$e.file] = $raw.Replace("`r`n", "`n")
    }
}
$applied = 0
$reverted = 0
foreach ($e in $edits) {
    $text = $texts[$e.file]
    $first = $text.IndexOf($e.old, [StringComparison]::Ordinal)
    $again = ($first -ge 0) -and ($text.IndexOf($e.old, $first + 1, [StringComparison]::Ordinal) -ge 0)
    if ($e.revert) {
        if ($first -lt 0) { continue }
        if ($again) { throw "Nie mozna cofnac $($e.marker): kod jest kilka razy w $($e.file)." }
        $texts[$e.file] = $text.Substring(0, $first) + $e.new + $text.Substring($first + $e.old.Length)
        $reverted++
        continue
    }
    if ($text.Contains($e.marker)) { continue }
    if ($first -lt 0 -or $again) {
        throw "Nie mozna zastosowac poprawki $($e.marker): nie znaleziono oczekiwanego kodu w $($e.file)."
    }
    $texts[$e.file] = $text.Substring(0, $first) + $e.new + $text.Substring($first + $e.old.Length)
    $applied++
}
foreach ($name in @($texts.Keys)) {
    $text = $texts[$name]
    if ($crlf[$name]) { $text = $text.Replace("`n", "`r`n") }
    $path = Join-Path $SourceDir $name
    if ([IO.File]::ReadAllText($path, $latin1) -ne $text) { [IO.File]::WriteAllText($path, $text, $latin1) }
}
return [pscustomobject]@{ Changed = (($applied + $reverted) -gt 0); Applied = $applied; Reverted = $reverted }
