[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDir
)

# System Zwierzat Domowych (server-patches/pety, README.md, MT2009_PLUS_GROWTH_PET_V1; the owner, 4 November 2026):
# files/ installed next to game/src (overwritten when they differ), then the edits of edits.json, each with its own
# marker - the same files apply_pety.py (the Linux/VPS twin) reads. An edit already there is skipped; one whose code is
# not found exactly once throws before a file is written.

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
$root = [IO.Path]::GetFullPath((Join-Path $SourceDir '..\..'))
$files = Join-Path $PSScriptRoot 'files'
foreach ($f in Get-ChildItem -LiteralPath $files -Recurse -File) {
    $rel = $f.FullName.Substring($files.Length + 1)
    $dst = Join-Path $root $rel
    if (-not (Test-Path -LiteralPath (Split-Path $dst -Parent) -PathType Container)) { throw "Brak katalogu dla $rel w $root" }
    if (-not (Test-Path -LiteralPath $dst) -or ([IO.File]::ReadAllBytes($dst) -join ',') -ne ([IO.File]::ReadAllBytes($f.FullName) -join ',')) {
        Copy-Item -LiteralPath $f.FullName -Destination $dst -Force
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
