[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDirectory
)

# Metin drops and the command flood guard (server-patches/metindrops,
# README.md): a Metin drops the sash at 15 percent and Cor Draconis at 20,
# and the client's own polls no longer eat a player's commands. Same
# replacements and marker as apply_metindrops.py (the Linux/VPS twin). Needs
# botsashdrop and raretoggle first. A file without the expected code throws
# and nothing is written.

$ErrorActionPreference = 'Stop'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$edits = @(
    'item_manager.cpp',
    "`t`tconst int szarfaChance = 80;`n",
    "`t`t// MT2009_PLUS_METIN_DROPS_V1 (server-patches/metindrops): a Metin 15%, a boss 80%.`n`t`tconst int szarfaChance = pkChr->IsStone() ? 15 : 80;`n",
    'item_manager.cpp',
    "`t`t`tcorChance = 50;`n`t`t`tcorKind = `"stone`";`n",
    "`t`t`t// MT2009_PLUS_METIN_DROPS_V1 (server-patches/metindrops): a Metin 20% (it was 50).`n`t`t`tcorChance = 20;`n`t`t`tcorKind = `"stone`";`n",
    'cmd.cpp',
    "`tif (ch && !PulseManager::Instance().IncreaseCount(ch->GetPlayerID(), ePulse::CommandRequest, std::chrono::milliseconds(500), 5))`n",
    "`t// MT2009_PLUS_METIN_DROPS_V1 (server-patches/metindrops): the client's own polls do not`n`t// count, and a player has 10 commands a half second (it was 5).`n`tstatic const char* const s_apszUnthrottled[] = { `"autohunt_target`", `"autohunt_loot`", `"gmpanel_check_gm`", `"kalendarz`", `"ingame_event`", NULL };`n`tbool bUnthrottled = false;`n`tfor (int i = 0; s_apszUnthrottled[i] && !bUnthrottled; ++i)`n`t{`n`t`tconst size_t n = strlen(s_apszUnthrottled[i]);`n`t`tbUnthrottled = !strncmp(argument, s_apszUnthrottled[i], n) && (argument[n] == ' ' || argument[n] == '\0');`n`t}`n`tif (ch && !bUnthrottled && !PulseManager::Instance().IncreaseCount(ch->GetPlayerID(), ePulse::CommandRequest, std::chrono::milliseconds(500), 10))`n"
)
$texts = @{}
for ($i = 0; $i -lt $edits.Count; $i += 3) {
    $file = Join-Path $SourceDirectory $edits[$i]
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Brak pliku: $file" }
    if (-not $texts.ContainsKey($file)) { $texts[$file] = [IO.File]::ReadAllText($file, $latin1) }
}
for ($i = 0; $i -lt $edits.Count; $i += 3) {
    $file = Join-Path $SourceDirectory $edits[$i]
    $text = $texts[$file]
    $old = $edits[$i + 1]; $new = $edits[$i + 2]
    $lines = $new.Split("`n")
    if ($text.Contains($lines[0]) -and $text.Contains($lines[1])) { continue }
    if ($text.Contains("`r`n")) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
    if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
        throw "Nie mozna zastosowac poprawki dropu z metinow i limitu komend: nie znaleziono oczekiwanego kodu w $($edits[$i])."
    }
    $index = $text.IndexOf($old, [StringComparison]::Ordinal)
    $texts[$file] = $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length)
}
$changed = $false
foreach ($file in @($texts.Keys)) {
    if ($texts[$file] -ne [IO.File]::ReadAllText($file, $latin1)) {
        [IO.File]::WriteAllText($file, $texts[$file], $latin1)
        $changed = $true
    }
}
return [pscustomobject]@{ Changed = $changed }
