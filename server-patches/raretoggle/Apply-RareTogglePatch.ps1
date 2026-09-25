[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDirectory
)

# The world's switches for the rare goods (server-patches/raretoggle,
# README.md): event flag m2_alchemy_off stops the Cor Draconis from Metins and
# bosses (item_manager.cpp), m2_sash_off the sash from bosses (item_manager.cpp)
# and from boss chests (char_item.cpp). Same replacements and marker as
# apply_raretoggle.py (the Linux/VPS twin). Applied after rarelevel. A file
# without the expected code throws and nothing is written.

$ErrorActionPreference = 'Stop'
$marker = 'MT2009_PLUS_RARE_TOGGLE_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$files = @(
    [pscustomobject]@{ Name = 'item_manager.cpp'; Pairs = [string[]]@(
        "`t`tpkKiller->GetLevel() <= pkChr->GetLevel() + 15)`n`t{`n`t`tint corChance = 0;`n", "`t`tpkKiller->GetLevel() <= pkChr->GetLevel() + 15 &&`n`t`t// MT2009_PLUS_RARE_TOGGLE_V1 (server-patches/raretoggle): no Cor Draconis`n`t`t// while the world has the alchemy switched off (M2_ALCHEMY=0, the panel).`n`t`tquest::CQuestManager::instance().GetEventFlag(`"m2_alchemy_off`") == 0)`n`t{`n`t`tint corChance = 0;`n",
        "`t`t// MT2009_PLUS_RARE_LEVEL_V1: the sash, too, only within 15 levels below.`n`t`tpkKiller->GetLevel() <= pkChr->GetLevel() + 15)`n", "`t`t// MT2009_PLUS_RARE_LEVEL_V1: the sash, too, only within 15 levels below.`n`t`tpkKiller->GetLevel() <= pkChr->GetLevel() + 15 &&`n`t`t// MT2009_PLUS_RARE_TOGGLE_V1: no sash while the world has them switched off.`n`t`tquest::CQuestManager::instance().GetEventFlag(`"m2_sash_off`") == 0)`n"
    ) },
    [pscustomobject]@{ Name = 'char_item.cpp'; Pairs = [string[]]@(
        "`t`t`t`t`t`tif (GetDesc() && !GetDesc()->IsBot())`n`t`t`t`t`t`t{`n`t`t`t`t`t`t`t// 85104 (Death Ruler Wings +3)", "`t`t`t`t`t`t// MT2009_PLUS_RARE_TOGGLE_V1 (server-patches/raretoggle): no sash from a`n`t`t`t`t`t`t// boss chest while the world has them switched off (M2_SASHES=0).`n`t`t`t`t`t`tif (GetDesc() && !GetDesc()->IsBot() &&`n`t`t`t`t`t`t`t`tquest::CQuestManager::instance().GetEventFlag(`"m2_sash_off`") == 0)`n`t`t`t`t`t`t{`n`t`t`t`t`t`t`t// 85104 (Death Ruler Wings +3)"
    ) }
)
$pending = @()
foreach ($file in $files) {
    $path = Join-Path $SourceDirectory $file.Name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Brak pliku $($file.Name): $path" }
    $text = [IO.File]::ReadAllText($path, $latin1)
    if ($text.Contains($marker)) { continue }
    $crlf = $text.Contains("`r`n")
    for ($i = 0; $i -lt $file.Pairs.Count; $i += 2) {
        $old = $file.Pairs[$i]; $new = $file.Pairs[$i + 1]
        if ($crlf) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
        if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
            throw "Nie mozna zastosowac przelacznikow alchemii i szarf: nie znaleziono oczekiwanego kodu w $($file.Name)."
        }
        $index = $text.IndexOf($old, [StringComparison]::Ordinal)
        $text = $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length)
    }
    $pending += [pscustomobject]@{ Path = $path; Text = $text }
}
foreach ($p in $pending) { [IO.File]::WriteAllText($p.Path, $p.Text, $latin1) }
return [pscustomobject]@{ Changed = ($pending.Count -gt 0) }
