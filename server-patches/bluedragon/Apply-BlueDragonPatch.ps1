[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDir
)

# The Blue Dragon lair (server-patches/bluedragon, README.md): the edits of
# edits.json, each with its own marker (MT2009_PLUS_BLUE_DRAGON_V1 ...) - the
# same file apply_bluedragon.py (the Linux/VPS twin) reads. An edit already
# there is skipped; one whose code is not found exactly once throws before a
# file is written. A file keeps its own line endings: an edit goes in with
# CRLF where the file's matching code has CRLF, with LF otherwise.

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
        $texts[$e.file] = $raw
        $originals[$e.file] = $raw
    }
}
function Get-Count([string]$text, [string]$part) {
    $n = 0
    $at = $text.IndexOf($part, [StringComparison]::Ordinal)
    while ($at -ge 0) {
        $n++
        $at = $text.IndexOf($part, $at + 1, [StringComparison]::Ordinal)
    }
    return $n
}
$applied = 0
foreach ($e in $edits) {
    $text = $texts[$e.file]
    if ($text.Contains($e.marker)) { continue }
    $old = $e.old
    $new = $e.new
    $oldCrlf = $old.Replace("`n", "`r`n")
    if ((Get-Count $text $oldCrlf) -eq 1) {
        $old = $oldCrlf
        $new = $new.Replace("`n", "`r`n")
    }
    if ((Get-Count $text $old) -ne 1) {
        throw "Nie mozna zastosowac poprawki $($e.marker): nie znaleziono oczekiwanego kodu w $($e.file)."
    }
    $first = $text.IndexOf($old, [StringComparison]::Ordinal)
    $texts[$e.file] = $text.Substring(0, $first) + $new + $text.Substring($first + $old.Length)
    $applied++
}
foreach ($name in @($texts.Keys)) {
    if ($texts[$name] -ne $originals[$name]) {
        [IO.File]::WriteAllText((Join-Path $SourceDir $name), $texts[$name], $latin1)
    }
}
return [pscustomobject]@{ Changed = ($applied -gt 0); Applied = $applied }
