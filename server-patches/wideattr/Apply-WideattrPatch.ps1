[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDir
)

# Dwubajtowy typ bonusu (server-patches/wideattr, README.md, MT2009_PLUS_WIDE_ATTR_V1; the owner,
# 3 November 2026): the edits of edits.json - the same file apply_wideattr.py (the Linux/VPS twin)
# reads. Applied LAST, after every other patch. An edit whose new code is already there is skipped;
# one whose old code is not found exactly once throws before a file is written.

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
    if ($text.Contains($e.new)) { continue }
    # a later patch (bonusy67c) puts its points between the new lines: applied when the old code is gone and each new line stands, in order
    if (-not $text.Contains($e.old)) {
        $pos = 0; $all = $true
        foreach ($line in ($e.new -split "`n")) {
            if (-not $line.Trim()) { continue }
            $code = ($line -split '//', 2)[0].TrimEnd()
            if ($code.Trim()) { $line = $code }  # a trailing comment may be renumbered (POINT_WIDE_END after bonusy67c)
            $i = $text.IndexOf($line, $pos, [StringComparison]::Ordinal)
            if ($i -lt 0) { $all = $false; break }
            $pos = $i + $line.Length
        }
        if ($all) { continue }
    }
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
