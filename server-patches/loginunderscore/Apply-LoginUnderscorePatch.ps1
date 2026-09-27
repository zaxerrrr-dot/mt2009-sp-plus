[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# A login may carry an underscore (server-patches/loginunderscore, README.md):
# every bot's account is playerbot_NNN, and a bot taken over from the advanced
# panel ("Przejmij bota") was refused as "wrong login" before its password was
# read. Same edit and marker as apply_loginunderscore.py (the Linux/VPS twin).
# A file without the expected code throws and nothing is written.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku input_auth.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_LOGIN_UNDERSCORE_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$nl = if ($text.Contains("`r`n")) { "`r`n" } else { "`n" }
$old = (@(
    "`t`tif (isdigit(*tmp) || isalpha(*tmp))",
    "`t`t`tcontinue;",
    "",
    "#ifdef ENABLE_ACCOUNT_W_SPECIALCHARS"
) -join $nl) + $nl
$new = (@(
    "`t`tif (isdigit(*tmp) || isalpha(*tmp))",
    "`t`t`tcontinue;",
    "",
    "`t`t// MT2009_PLUS_LOGIN_UNDERSCORE_V1 (server-patches/loginunderscore): a",
    "`t`t// bot's account is playerbot_NNN, and the advanced panel hands it to a",
    "`t`t// person for a while (`"Przejmij bota`").",
    "`t`tif (*tmp == '_')",
    "`t`t`tcontinue;",
    "",
    "#ifdef ENABLE_ACCOUNT_W_SPECIALCHARS"
) -join $nl) + $nl
$first = $text.IndexOf($old, [StringComparison]::Ordinal)
if ($first -lt 0 -or $text.IndexOf($old, $first + 1, [StringComparison]::Ordinal) -ge 0) {
    throw 'Nie mozna zastosowac poprawki loginu: nie znaleziono oczekiwanego kodu w input_auth.cpp.'
}
$text = $text.Substring(0, $first) + $new + $text.Substring($first + $old.Length)
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
