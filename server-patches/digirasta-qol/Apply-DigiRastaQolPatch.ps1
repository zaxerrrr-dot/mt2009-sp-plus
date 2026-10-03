[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDir
)

# Digi Rasta's server conveniences (server-patches/digirasta-qol, README.md,
# "Autor: Digi Rasta", MT2009_PLUS_DIGI_SERVER_QOL_V1): the edits of
# edits.json, each with its own marker - the same file apply_digirasta_qol.py
# (the Linux/VPS twin) reads. An edit already there is skipped; one whose code
# is not found exactly once throws before a file is written. Some engine files
# mix CRLF and LF lines, so an edit is looked for as written (LF) and then with
# CRLF line ends, and goes in with the line ends it was found with.

$ErrorActionPreference = 'Stop'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$edits = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'edits.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$texts = @{}
$originals = @{}
foreach ($e in $edits) {
    if (-not $texts.ContainsKey($e.file)) {
        $path = Join-Path $SourceDir $e.file
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Brak pliku $($e.file): $path" }
        $raw = [IO.File]::ReadAllText($path, $latin1)
        $originals[$e.file] = $raw
        $texts[$e.file] = $raw
    }
}
function Find-Once([string]$text, [string]$what) {
    $first = $text.IndexOf($what, [StringComparison]::Ordinal)
    if ($first -lt 0) { return -1 }
    if ($text.IndexOf($what, $first + 1, [StringComparison]::Ordinal) -ge 0) { return -1 }
    return $first
}
$applied = 0
foreach ($e in $edits) {
    $text = $texts[$e.file]
    if ($text.Contains($e.marker)) { continue }
    $old = [string]$e.old
    $new = [string]$e.new
    $first = Find-Once $text $old
    if ($first -lt 0) {
        $old = $old.Replace("`n", "`r`n")
        $new = $new.Replace("`n", "`r`n")
        $first = Find-Once $text $old
    }
    if ($first -lt 0) {
        throw "Nie mozna zastosowac poprawki $($e.marker): nie znaleziono oczekiwanego kodu w $($e.file)."
    }
    $texts[$e.file] = $text.Substring(0, $first) + $new + $text.Substring($first + $old.Length)
    $applied++
}
foreach ($name in @($texts.Keys)) {
    if ($texts[$name] -ne $originals[$name]) {
        [IO.File]::WriteAllText((Join-Path $SourceDir $name), $texts[$name], $latin1)
    }
}
return [pscustomobject]@{ Changed = ($applied -gt 0); Applied = $applied }
