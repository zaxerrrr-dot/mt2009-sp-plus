[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# Bots get the Cor Draconis and sash drop of Metin stones and bosses
# (server-patches/botraredrop, README.md). Same replacements and markers as
# apply_botraredrop.py (the Linux/VPS twin). Two steps, each applied once:
# V1 lets a bot's kill roll both (into its bag), V2 gives bots their own
# chances (Cor 5%, sash 3%). A file without the expected code throws and
# nothing is written. CRLF/LF is kept as it was.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) {
    throw "Brak pliku item_manager.cpp: $SourceFile"
}

$marker = 'MT2009_PLUS_BOT_RARE_DROP_V1'
$markerV2 = 'MT2009_PLUS_BOT_RARE_DROP_V2'
# A bot's own chance, percent (operator, 24 Sep 2026); players keep theirs
# (Cor Draconis: stone 50, boss 80; sash: boss 80).
$botCorChance = 5
$botSashChance = 3
$original = [IO.File]::ReadAllText($SourceFile)
$hadCrlf = $original.Contains("`r`n")
$text = $original.Replace("`r`n", "`n")

function L { param([string[]]$Lines) ($Lines -join "`n") + "`n" }

$blocks = @(
    @{ Name = 'warunek dropu Cor Draconis'
       Old = L @("`tif (pkKiller &&",
                 "`t`tpkKiller->IsPC() &&",
                 "`t`tpkKiller->GetDesc() &&",
                 "`t`t!pkKiller->GetDesc()->IsBot())",
                 "`t{",
                 "`t`tint corChance = 0;")
       New = L @("`t// $marker (server-patches/botraredrop): a bot's kill rolls the",
                 "`t// Cor Draconis like a player's; the bot lists it on its counter.",
                 "`tif (pkKiller &&",
                 "`t`tpkKiller->IsPC() &&",
                 "`t`tpkKiller->GetDesc())",
                 "`t{",
                 "`t`tint corChance = 0;") },
    @{ Name = 'Cor Draconis do plecaka bota'
       Old = L @("`t`t`t`tif (cor)",
                 "`t`t`t`t`tvec_item.push_back(cor);")
       New = L @("`t`t`t`t// A bot's own Cor Draconis goes straight into its bag: a bot may",
                 "`t`t`t`t// not pick one up off the ground (char_item.cpp, PickupItem).",
                 "`t`t`t`tif (cor)",
                 "`t`t`t`t{",
                 "`t`t`t`t`tif (pkKiller->GetDesc()->IsBot())",
                 "`t`t`t`t`t`tpkKiller->AutoGiveItem(cor);",
                 "`t`t`t`t`telse",
                 "`t`t`t`t`t`tvec_item.push_back(cor);",
                 "`t`t`t`t}") },
    @{ Name = 'warunek dropu szarfy'
       Old = L @("`tif (pkKiller &&",
                 "`t`tpkKiller->IsPC() &&",
                 "`t`tpkKiller->GetDesc() &&",
                 "`t`t!pkKiller->GetDesc()->IsBot() &&",
                 "`t`tpkChr->GetMobRank() >= MOB_RANK_BOSS)")
       New = L @("`t// ${marker}: a bot's boss kill rolls the sash too.",
                 "`tif (pkKiller &&",
                 "`t`tpkKiller->IsPC() &&",
                 "`t`tpkKiller->GetDesc() &&",
                 "`t`tpkChr->GetMobRank() >= MOB_RANK_BOSS)") },
    @{ Name = 'szarfa do plecaka bota'
       Old = L @("`t`t`tif (szarfa)",
                 "`t`t`t`tvec_item.push_back(szarfa);")
       New = L @("`t`t`tif (szarfa)",
                 "`t`t`t{",
                 "`t`t`t`tif (pkKiller->GetDesc()->IsBot())",
                 "`t`t`t`t`tpkKiller->AutoGiveItem(szarfa);",
                 "`t`t`t`telse",
                 "`t`t`t`t`tvec_item.push_back(szarfa);",
                 "`t`t`t}") }
)

# V2: the bots' own chances, on top of V1.
$blocksV2 = @(
    @{ Name = 'szansa Cor Draconis dla bota'
       Old = L @("`t`tif (corChance > 0)",
                 "`t`t{",
                 "`t`t`tint roll = number(1, 100);")
       New = L @("`t`t// ${markerV2}: a bot's kill rolls at a bot's own chance.",
                 "`t`tif (corChance > 0 && pkKiller->GetDesc()->IsBot())",
                 "`t`t`tcorChance = $botCorChance;",
                 "",
                 "`t`tif (corChance > 0)",
                 "`t`t{",
                 "`t`t`tint roll = number(1, 100);") },
    @{ Name = 'szansa szarfy dla bota'
       Old = L @("`t`tconst int szarfaChance = 80;")
       New = L @("`t`t// ${markerV2}: a bot's own chance; a player keeps 80.",
                 "`t`tconst int szarfaChance = pkKiller->GetDesc()->IsBot() ? $botSashChance : 80;") }
)

$changed = $false
foreach ($step in @(@{ Marker = $marker; Blocks = $blocks }, @{ Marker = $markerV2; Blocks = $blocksV2 })) {
    if ($text.Contains($step.Marker)) { continue }
    foreach ($block in $step.Blocks) {
        $count = ([regex]::Matches($text, [regex]::Escape($block.Old))).Count
        if ($count -ne 1) {
            throw "Nie można zastosować poprawki dropu dla botów ($($block.Name)): nie znaleziono oczekiwanego kodu w item_manager.cpp."
        }
    }
    foreach ($block in $step.Blocks) {
        $index = $text.IndexOf($block.Old, [StringComparison]::Ordinal)
        $text = $text.Substring(0, $index) + $block.New + $text.Substring($index + $block.Old.Length)
    }
    $changed = $true
}
if (-not $changed) { return [pscustomobject]@{ Changed = $false } }
if ($hadCrlf) { $text = $text.Replace("`n", "`r`n") }
[IO.File]::WriteAllText($SourceFile, $text)
return [pscustomobject]@{ Changed = $true }
