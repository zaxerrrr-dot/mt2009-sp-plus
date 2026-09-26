[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDirectory
)

# Bots roll sashes like players (server-patches/botsashdrop, README.md): the
# boss kill at 80% (it was 3%, botraredrop V2) and the boss chest's unique,
# into the bag or nowhere when it is full. Same replacements and marker as
# apply_botsashdrop.py (the Linux/VPS twin). Needs botraredrop first. A file
# without the expected code throws and nothing is written.

$ErrorActionPreference = 'Stop'
$marker = 'MT2009_PLUS_BOT_SASH_DROP_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$edits = @(
    'item_manager.cpp',
    "`t`t// MT2009_PLUS_BOT_RARE_DROP_V2: a bot's own chance; a player keeps 80.`n`t`tconst int szarfaChance = pkKiller->GetDesc()->IsBot() ? 3 : 80;`n",
    "`t`t// $marker (server-patches/botsashdrop): a bot rolls at a`n`t`t// player's chance (it was 3, MT2009_PLUS_BOT_RARE_DROP_V2).`n`t`tconst int szarfaChance = 80;`n",
    'char_item.cpp',
    "`t`t`t`t`t`tif (GetDesc() && !GetDesc()->IsBot() &&`n",
    "`t`t`t`t`t`t// $marker (server-patches/botsashdrop): a bot's chest too.`n`t`t`t`t`t`tif (GetDesc() &&`n",
    'char_item.cpp',
    "`t`t`t`t`t`t`t`tif (szarfa)`n`t`t`t`t`t`t`t`t`tAutoGiveItem(szarfa, true);`n",
    "`t`t`t`t`t`t`t`t// ${marker}: a bot's full bag gets nothing, never the ground.`n`t`t`t`t`t`t`t`tif (szarfa && GetDesc()->IsBot() && GetEmptyInventoryEx(szarfa) == -1)`n`t`t`t`t`t`t`t`t`tM2_DESTROY_ITEM(szarfa);`n`t`t`t`t`t`t`t`telse if (szarfa)`n`t`t`t`t`t`t`t`t`tAutoGiveItem(szarfa, true);`n"
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
    if ($text.Contains($new.Split("`n")[0])) { continue }
    if ($text.Contains("`r`n")) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
    if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
        throw "Nie mozna zastosowac poprawki dropu szarf dla botow: nie znaleziono oczekiwanego kodu w $($edits[$i])."
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
