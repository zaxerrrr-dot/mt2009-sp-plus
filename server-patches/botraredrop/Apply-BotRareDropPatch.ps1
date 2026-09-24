[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# Bots get the Cor Draconis and sash drop of Metin stones and bosses
# (server-patches/botraredrop, README.md). Same replacements and marker as
# apply_botraredrop.py (the Linux/VPS twin). Idempotent: a file that already
# carries the marker is left alone; a file without the expected code throws
# and nothing is written. CRLF/LF is kept as it was.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) {
    throw "Brak pliku item_manager.cpp: $SourceFile"
}

$marker = 'MT2009_PLUS_BOT_RARE_DROP_V1'
$original = [IO.File]::ReadAllText($SourceFile)
$hadCrlf = $original.Contains("`r`n")
$text = $original.Replace("`r`n", "`n")

if ($text.Contains($marker)) {
    return [pscustomobject]@{ Changed = $false }
}

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

foreach ($block in $blocks) {
    $count = ([regex]::Matches($text, [regex]::Escape($block.Old))).Count
    if ($count -ne 1) {
        throw "Nie można zastosować poprawki dropu dla botów ($($block.Name)): nie znaleziono oczekiwanego kodu w item_manager.cpp."
    }
}
foreach ($block in $blocks) {
    $index = $text.IndexOf($block.Old)
    $text = $text.Substring(0, $index) + $block.New + $text.Substring($index + $block.Old.Length)
}
if ($hadCrlf) { $text = $text.Replace("`n", "`r`n") }
[IO.File]::WriteAllText($SourceFile, $text)
return [pscustomobject]@{ Changed = $true }
