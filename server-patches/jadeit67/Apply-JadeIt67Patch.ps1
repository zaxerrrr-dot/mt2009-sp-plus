[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDir
)

# Jade jewellery takes the 6th/7th bonus (server-patches/jadeit67, README.md, MT2009_PLUS_JADE_BONUS67_V1): the edits
# of edits.json, each with its own marker - the same file apply_jadeit67.py (the Linux/VPS twin) reads. An edit
# already there is skipped; otherwise the first of its "olds" found exactly once is replaced; none found throws before
# a file is written.

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
    $done = $false
    foreach ($old in @($e.olds)) {
        $first = $text.IndexOf($old, [StringComparison]::Ordinal)
        if ($first -lt 0 -or $text.IndexOf($old, $first + 1, [StringComparison]::Ordinal) -ge 0) { continue }
        $texts[$e.file] = $text.Substring(0, $first) + $e.new + $text.Substring($first + $old.Length)
        $done = $true
        break
    }
    if (-not $done) {
        throw "Nie mozna zastosowac poprawki $($e.marker): nie znaleziono oczekiwanego kodu w $($e.file)."
    }
    $applied++
}
foreach ($name in @($texts.Keys)) {
    $text = $texts[$name]
    if ($crlf[$name]) { $text = $text.Replace("`n", "`r`n") }
    $path = Join-Path $SourceDir $name
    if ([IO.File]::ReadAllText($path, $latin1) -ne $text) { [IO.File]::WriteAllText($path, $text, $latin1) }
}
return [pscustomobject]@{ Changed = ($applied -gt 0); Applied = $applied }
