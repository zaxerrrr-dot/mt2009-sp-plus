[CmdletBinding()]
param(
    # The engine's game/src directory (cmd.cpp and cmd_gm.cpp).
    [Parameter(Mandatory = $true)][string]$SourceDir
)

# The alchemy deck for players (server-patches/dscommand, README.md): the
# client activates it with "/dragon_soul activate <deck>", which was a
# GM_IMPLEMENTOR command, so a player got "Ta komenda nie istnieje". Same
# replacements and marker as apply_dscommand.py (the Linux/VPS twin). Each
# file is edited in place (cmd.cpp mixes CRLF and LF lines). A file without
# the expected code throws and nothing is written.

$ErrorActionPreference = 'Stop'
$marker = 'MT2009_PLUS_DS_PLAYER_CMD_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$cmdPath = Join-Path $SourceDir 'cmd.cpp'
$gmPath = Join-Path $SourceDir 'cmd_gm.cpp'
foreach ($p in @($cmdPath, $gmPath)) {
    if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw "Brak pliku: $p" }
}
$cmd = [IO.File]::ReadAllText($cmdPath, $latin1)
$gm = [IO.File]::ReadAllText($gmPath, $latin1)
if ($cmd.Contains($marker) -and $gm.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }

function Fix-Eol { param([string]$Text, [string]$S) if ($Text.Contains("`r`n")) { $S.Replace("`n", "`r`n") } else { $S } }

$cmdRe = '(\{ "dragon_soul",[^\r\n]*?)GM_IMPLEMENTOR \},'
$guard = "`t`t`tif (ch->GetGMLevel() < GM_IMPLEMENTOR) // ${marker}: a GM's testing aid`n`t`t`t`tbreak;`n"
$gmOld = @(
    ("`t`t`t// reach NPC 20001 (operator's explicit request, 17 September 2026).`n" +
     "`t`t`tch->DragonSoul_RefineWindow_Open(NULL);`n"),
    "`tcase 'c':`n`t`t{`n`t`t`tch->DragonSoul_RefineWindow_ChangeAttr_Open(NULL);`n")
$gmNew = @(
    ("`t`t`t// reach NPC 20001 (operator's explicit request, 17 September 2026).`n" +
     $guard + "`t`t`tch->DragonSoul_RefineWindow_Open(NULL);`n"),
    ("`tcase 'c':`n`t`t{`n" + $guard + "`t`t`tch->DragonSoul_RefineWindow_ChangeAttr_Open(NULL);`n"))

if (-not $cmd.Contains($marker) -and ([regex]::Matches($cmd, $cmdRe)).Count -ne 1) {
    throw 'Nie mozna zastosowac poprawki komendy alchemii: nie znaleziono oczekiwanego kodu w cmd.cpp.'
}
if (-not $gm.Contains($marker)) {
    foreach ($old in $gmOld) {
        if (([regex]::Matches($gm, [regex]::Escape((Fix-Eol $gm $old)))).Count -ne 1) {
            throw 'Nie mozna zastosowac poprawki komendy alchemii: nie znaleziono oczekiwanego kodu w cmd_gm.cpp.'
        }
    }
}
if (-not $cmd.Contains($marker)) {
    $cmd = ([regex]$cmdRe).Replace($cmd, '${1}GM_PLAYER }, // ' + $marker + ': the client activates the deck with it', 1)
    [IO.File]::WriteAllText($cmdPath, $cmd, $latin1)
}
if (-not $gm.Contains($marker)) {
    for ($i = 0; $i -lt $gmOld.Count; $i++) {
        $o = Fix-Eol $gm $gmOld[$i]; $n = Fix-Eol $gm $gmNew[$i]
        $idx = $gm.IndexOf($o, [StringComparison]::Ordinal)
        $gm = $gm.Substring(0, $idx) + $n + $gm.Substring($idx + $o.Length)
    }
    [IO.File]::WriteAllText($gmPath, $gm, $latin1)
}
return [pscustomobject]@{ Changed = $true }
