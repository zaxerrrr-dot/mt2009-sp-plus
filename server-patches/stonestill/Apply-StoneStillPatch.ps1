[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDirectory
)

# A Metin stone never walks (server-patches/stonestill, README.md): Goto
# refuses a stone (char.cpp) and a stone in the battle state goes back to idle
# (char_state.cpp). Same replacements and marker as apply_stonestill.py (the
# Linux/VPS twin). A file without the expected code throws and nothing is
# written to it.

$ErrorActionPreference = 'Stop'
$marker = 'MT2009_PLUS_STONE_STILL_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$edits = @(
    'char.cpp', "bool CHARACTER::Goto(long x, long y)`n{`n`tif (GetX() == x && GetY() == y)`n`t`treturn false;`n", "bool CHARACTER::Goto(long x, long y)`n{`n`t// MT2009_PLUS_STONE_STILL_V1 (server-patches/stonestill): a Metin stone`n`t// never walks. One that was sent here went into the move state and from`n`t// it into the battle state it has no AI for (`"Stone must not use battle`n`t// state`", hundreds a minute). Refused, and said once a stone with who it`n`t// was fighting and who synced it, to find the caller.`n`tif (IsStone())`n`t{`n`t`tstatic DWORD s_dwStoneGotoLogged = 0;`n`t`tif (s_dwStoneGotoLogged != GetVID())`n`t`t{`n`t`t`ts_dwStoneGotoLogged = GetVID();`n`t`t`tsys_err(`"stone goto refused (name %s vnum %u map %ld pos %ld,%ld to %ld,%ld victim %s sync_owner %s)`",`n`t`t`t`t`tGetName(), GetRaceNum(), GetMapIndex(), GetX(), GetY(), x, y,`n`t`t`t`t`tGetVictim() ? GetVictim()->GetName() : `"-`", m_pkChrSyncOwner ? m_pkChrSyncOwner->GetName() : `"-`");`n`t`t}`n`t`treturn false;`n`t}`n`n`tif (GetX() == x && GetY() == y)`n`t`treturn false;`n",
    'char_state.cpp', "`tif (IsStone())`n`t{`n`t`tsys_err(`"Stone must not use battle state (name %s)`", GetName());`n`t`treturn;`n`t}`n", "`tif (IsStone())`n`t{`n`t`t// MT2009_PLUS_STONE_STILL_V1: back to the stone's own idle state, once,`n`t`t// instead of this line every pass for as long as the stone stood.`n`t`tsys_err(`"Stone must not use battle state (name %s), back to idle`", GetName());`n`t`tGotoState(m_stateIdle);`n`t`tm_dwStateDuration = 1;`n`t`treturn;`n`t}`n"
)
$changed = $false
for ($i = 0; $i -lt $edits.Count; $i += 3) {
    $file = Join-Path $SourceDirectory $edits[$i]
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Brak pliku: $file" }
    $text = [IO.File]::ReadAllText($file, $latin1)
    if ($text.Contains($marker)) { continue }
    $old = $edits[$i + 1]; $new = $edits[$i + 2]
    if ($text.Contains("`r`n")) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
    if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
        throw "Nie mozna zastosowac poprawki nieruchomych kamieni Metin: nie znaleziono oczekiwanego kodu w $($edits[$i])."
    }
    $index = $text.IndexOf($old, [StringComparison]::Ordinal)
    $text = $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length)
    [IO.File]::WriteAllText($file, $text, $latin1)
    $changed = $true
}
return [pscustomobject]@{ Changed = $changed }
