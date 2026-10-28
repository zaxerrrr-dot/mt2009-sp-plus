[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDir
)

# The TEST auto hunt (server-patches/autohunttest, MT2009_PLUS_AUTOHUNT_TEST_V1; the owner, 28 October 2026):
# /autohunt_test answers root's uiautohunt_test.py (Alt+H) whether the exe's own hunt may run - event flags
# autohunt_test_off (off for everybody) and autohunt_test_ticket (only with an Auto Lowy ticket); cmd.cpp, cmd_general.cpp.
# Anchors on autohuntnorevenge's /autohunt_stop - apply after it. The edits of edits.json, each with its own marker - the
# same file apply_autohunttest.py (the Linux/VPS twin) reads. An edit already there is skipped; one whose code is not
# found exactly once throws before a file is written.

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
