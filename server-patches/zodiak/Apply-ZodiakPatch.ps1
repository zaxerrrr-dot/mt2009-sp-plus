[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDir
)

# Swiatynia Zodiaku (server-patches/zodiak, README.md, "Autor: Digi Rasta",
# nowy-system 0.35.0, MT2009_PLUS_ZODIAC_V1): the 64 hooks of edits.json, each with
# its own marker - the same file apply_zodiak.py (the Linux/VPS twin) reads. The
# work is the overlay's playerbot_zodiac_*. The define ENABLE_12ZI (CommonDefines.h)
# is the last edit, and nothing is written unless every edit's code is found once,
# so the define never comes without its hooks. Last in Apply-MT2009PlusEngine.ps1:
# the hooks anchor on lines the other patches leave. An edit already there is
# skipped; one whose code is not found exactly once throws before a file is written.

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
foreach ($e in $edits) {
    $text = $texts[$e.file]
    if ($text.Contains($e.marker)) { continue }
    $first = $text.IndexOf($e.old, [StringComparison]::Ordinal)
    if ($first -lt 0 -or $text.IndexOf($e.old, $first + 1, [StringComparison]::Ordinal) -ge 0) {
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
return [pscustomobject]@{ Changed = ($applied -gt 0); Applied = $applied }
