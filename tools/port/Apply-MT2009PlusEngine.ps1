[CmdletBinding()]
param(
    # The full mt2009 server folder (VERSION, linux-port\docker\game\src\server).
    [Parameter(Mandatory = $true)][string]$ServerRoot
)

# MT2009 Plus engine changes, applied the way Tieru's port/playerbotify.py
# applies his: ONCE, on the developer's full server folder, while a release
# is prepared. The patched engine files (listed in
# launcher\server-update-files.mod.txt) then travel in the update zip, and a
# player's start-server.ps1 or a VPS's update.sh never edits an engine file.
# Every step is idempotent: a second run changes nothing. A step whose
# expected code is missing throws.
#
# Auto Lowy need nothing here: the engine files of the package already carry
# Tieru's do_autohunt_target/do_autohunt_loot (Auto Lowy 2.0), which answer
# the MT2009 Plus client's window too.
#
#   shop search        ikarus_shop_manager.cpp   (MT2009_PLUS_SHOP_SEARCH_ITEM_V1)
#   bot rare drop      item_manager.cpp          (MT2009_PLUS_BOT_RARE_DROP_V1..V3)
#   Death Ruler wings  item_manager.cpp, char_item.cpp (no 85101/85104 drop)
#   alchemy bonuses    dragon_soul_table.cpp     (MT2009_PLUS_DS_APPLYS_V1)
#   alchemy for all    char_affect.cpp           (MT2009_PLUS_DS_QUALIFY_ON_LOGIN_V1)
#
# tools\New-M2UpdatePackage.ps1 refuses a server package without these marks.

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$root = [IO.Path]::GetFullPath($ServerRoot)
$enginePath = Join-Path $root 'linux-port/docker/ENGINE'
if (-not (Test-Path -LiteralPath $enginePath -PathType Leaf) -or
    ([IO.File]::ReadAllText($enginePath)).Trim() -ieq 'r40250') {
    throw "To nie jest folder serwera mt2009 (brak linux-port\docker\ENGINE): $root"
}
$syncedFiles = 0

$engineGameSource = Join-Path $root 'linux-port/docker/game/src/server/game/src'

# The item finder normally searches a complete category. This tracked,
# idempotent source transformation lets a player click one icon and search
# offline shops and playerbot stalls for exactly that vnum/socket0 pair.
$shopSearchApply = Join-Path $repo 'server-patches/offlineshopsearch/Apply-ShopSearchPatch.ps1'
$shopManagerSource = Join-Path $engineGameSource 'ikarus_shop_manager.cpp'
if ((Test-Path -LiteralPath $shopSearchApply -PathType Leaf) -and
    (Test-Path -LiteralPath $shopManagerSource -PathType Leaf)) {
    $shopSearchResult = & $shopSearchApply -SourceFile $shopManagerSource
    if ($shopSearchResult.Changed) {
        $syncedFiles++
        Write-Host 'Enabled exact-item offline shop search.' -ForegroundColor DarkGray
    }
}
# Bots get the Cor Draconis and sash drop of Metin stones and bosses
# (server-patches/botraredrop): the engine gave both to a real player's
# kill only, so a bot never had one to list. A bot's own drop goes straight
# into its bag; the ground pickup of a Cor Draconis stays player-only.
$botRareDropApply = Join-Path $repo 'server-patches/botraredrop/Apply-BotRareDropPatch.ps1'
$itemManagerSource = Join-Path $engineGameSource 'item_manager.cpp'
if ((Test-Path -LiteralPath $botRareDropApply -PathType Leaf) -and
    (Test-Path -LiteralPath $itemManagerSource -PathType Leaf)) {
    $botRareDropResult = & $botRareDropApply -SourceFile $itemManagerSource
    if ($botRareDropResult.Changed) {
        $syncedFiles++
        Write-Host 'Enabled the Cor Draconis and sash drop for bots.' -ForegroundColor DarkGray
    }
}
# The alchemy balance (server-patches/dragonsoulbalance): the apply names
# the MT2009 Plus dragon_soul_table.txt uses (race, monster, critical and
# piercing bonuses), and "Wartosc ataku"/"Obrona" as the flat values an item
# bonus gives instead of percent multipliers. The table itself is replaced at
# image build (game/Dockerfile, dragon_soul_applys.mt2009plus.txt).
$dsBalanceApply = Join-Path $repo 'server-patches/dragonsoulbalance/Apply-DragonSoulBalancePatch.ps1'
$dsTableSource = Join-Path $engineGameSource 'dragon_soul_table.cpp'
if ((Test-Path -LiteralPath $dsBalanceApply -PathType Leaf) -and
    (Test-Path -LiteralPath $dsTableSource -PathType Leaf)) {
    $dsBalanceResult = & $dsBalanceApply -SourceFile $dsTableSource
    if ($dsBalanceResult.Changed) {
        $syncedFiles++
        Write-Host 'Enabled the MT2009 Plus alchemy bonuses.' -ForegroundColor DarkGray
    }
}
# The Dragon Soul alchemy without the level-30 quest
# (server-patches/dsqualification): every real player is qualified when his
# affects load, so a Cor Draconis opens and its stone goes into the alchemy
# inventory instead of onto the ground.
$dsQualifyApply = Join-Path $repo 'server-patches/dsqualification/Apply-DsQualificationPatch.ps1'
$charAffectSource = Join-Path $engineGameSource 'char_affect.cpp'
if ((Test-Path -LiteralPath $dsQualifyApply -PathType Leaf) -and
    (Test-Path -LiteralPath $charAffectSource -PathType Leaf)) {
    $dsQualifyResult = & $dsQualifyApply -SourceFile $charAffectSource
    if ($dsQualifyResult.Changed) {
        $syncedFiles++
        Write-Host 'Enabled the Dragon Soul alchemy for every player.' -ForegroundColor DarkGray
    }
}
# Death Ruler wings (85101..85104) use broken assets in this client.
# Older MT2009 Plus sources added grade 1 to the Metin/boss pool and grade
# 4 to the chest pool in two compact arrays.  Remove the family from both
# arrays when it is present; installations that never had it are a no-op.
foreach ($dropSourceName in @('item_manager.cpp', 'char_item.cpp')) {
    $dropSource = Join-Path $engineGameSource $dropSourceName
    if (-not (Test-Path -LiteralPath $dropSource -PathType Leaf)) { continue }
    $dropText = Get-Content -LiteralPath $dropSource -Raw
    $dropBefore = $dropText
    foreach ($pair in @(@('s_aSzarfaTier1', '85101'), @('s_aSzarfaTier4', '85104'))) {
        $arrayName = $pair[0]
        $badVnum = $pair[1]
        $arrayPattern = '(?s)(' + [regex]::Escape($arrayName) +
            '[ \t]*\[[^\]]*\][ \t]*=[ \t]*\{)(.*?)(\};)'
        $dropText = [regex]::Replace($dropText, $arrayPattern, {
            param($match)
            $body = $match.Groups[2].Value
            $body = [regex]::Replace($body,
                '(?<![0-9])' + $badVnum + '(?![0-9])[ \t]*,?', '')
            $body = $body -replace ',[ \t]*,', ','
            $body = $body -replace ',[ \t]*$', ''
            $match.Groups[1].Value + $body + $match.Groups[3].Value
        })
        # The old code hard-coded the last index as 5.  Once the broken
        # sixth entry is gone that would read past the array, so derive it
        # from the array that is actually compiled.
        $pickPattern = [regex]::Escape($arrayName) +
            '\[number\([ \t]*0[ \t]*,[ \t]*[0-9]+[ \t]*\)\]'
        $pickExpression = $arrayName + '[number(0, _countof(' +
            $arrayName + ') - 1)]'
        $dropText = [regex]::Replace($dropText, $pickPattern, $pickExpression)
    }
    if ($dropText -ne $dropBefore) {
        [IO.File]::WriteAllText($dropSource, $dropText)
        $syncedFiles++
        Write-Host "Removed broken Death Ruler sash drops from $dropSourceName." -ForegroundColor DarkGray
    }
}

Write-Host "MT2009 Plus engine: $syncedFiles file(s) changed."
