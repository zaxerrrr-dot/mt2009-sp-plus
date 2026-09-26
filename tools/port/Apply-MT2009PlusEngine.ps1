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
#   alchemy deck cmd   cmd.cpp, cmd_gm.cpp       (MT2009_PLUS_DS_PLAYER_CMD_V1)
#   pet magic att %    char.cpp                  (MT2009_PLUS_MAGIC_ATT_PER_V1)
#   mount speed        char_player.cpp           (MT2009_PLUS_MOUNT_SPEED_V1)
#   bot rare share     char_battle.cpp           (MT2009_PLUS_BOT_RARE_SHARE_V1)
#   mount off at death char_battle.cpp           (MT2009_PLUS_MOUNT_DEATH_UNEQUIP_V1)
#   saddlebags on a mount char.cpp               (MT2009_PLUS_SADDLEBAG_MOUNT_V1)
#   stones stand still char.cpp, char_state.cpp  (MT2009_PLUS_STONE_STILL_V1)
#   mount bonus once   MountSystem.cpp           (MT2009_PLUS_MOUNT_BONUS_ONCE_V1)
#   permanent seals    MountSystem.cpp           (MT2009_PLUS_MOUNT_PERMANENT_V1)
#   rare drop levels   item_manager.cpp          (MT2009_PLUS_RARE_LEVEL_V1)
#   drop preview min   item_manager.cpp          (MT2009_PLUS_DROP_PREVIEW_MIN_V1)
#   rare switches      item_manager.cpp, char_item.cpp (MT2009_PLUS_RARE_TOGGLE_V1)
#   speedhack slack    input_main.cpp            (MT2009_PLUS_SPEEDHACK_CLOCK_V1)
#   Cor stacking       char_item.cpp             (IsStackableCorDraconisVnum)
#   Cor pickup stacks  char_item.cpp             (MT2009_PLUS_COR_AUTOSTACK_V1)
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
# Cor Draconis and sashes only from a Metin or boss at most 15 levels below
# the killer (server-patches/rarelevel); after botraredrop, same blocks.
$rareLevelApply = Join-Path $repo 'server-patches/rarelevel/Apply-RareLevelPatch.ps1'
if ((Test-Path -LiteralPath $rareLevelApply -PathType Leaf) -and
    (Test-Path -LiteralPath $itemManagerSource -PathType Leaf)) {
    $rareLevelResult = & $rareLevelApply -SourceFile $itemManagerSource
    if ($rareLevelResult.Changed) {
        $syncedFiles++
        Write-Host 'Cor Draconis and sash drops within 15 levels below the killer.' -ForegroundColor DarkGray
    }
}
# The drop preview lists an item only at 1 in 10 000 kills or better
# (server-patches/droppreview); the drop itself is unchanged.
$dropPreviewApply = Join-Path $repo 'server-patches/droppreview/Apply-DropPreviewPatch.ps1'
if ((Test-Path -LiteralPath $dropPreviewApply -PathType Leaf) -and
    (Test-Path -LiteralPath $itemManagerSource -PathType Leaf)) {
    $dropPreviewResult = & $dropPreviewApply -SourceFile $itemManagerSource
    if ($dropPreviewResult.Changed) {
        $syncedFiles++
        Write-Host 'Drop preview without items under 1 in 10 000 kills.' -ForegroundColor DarkGray
    }
}
# The world's switches for the Cor Draconis and the sashes (event flags
# m2_alchemy_off / m2_sash_off, server-patches/raretoggle); after rarelevel,
# whose lines it extends.
$rareToggleApply = Join-Path $repo 'server-patches/raretoggle/Apply-RareTogglePatch.ps1'
if ((Test-Path -LiteralPath $rareToggleApply -PathType Leaf) -and
    (Test-Path -LiteralPath $engineGameSource -PathType Container)) {
    $rareToggleResult = & $rareToggleApply -SourceDirectory $engineGameSource
    if ($rareToggleResult.Changed) {
        $syncedFiles++
        Write-Host 'Cor Draconis and sash drops follow the world switches.' -ForegroundColor DarkGray
    }
}
# A mount seal comes off into the bag at death (server-patches/mountdeath).
$mountDeathApply = Join-Path $repo 'server-patches/mountdeath/Apply-MountDeathPatch.ps1'
$charBattleSource = Join-Path $engineGameSource 'char_battle.cpp'
if ((Test-Path -LiteralPath $mountDeathApply -PathType Leaf) -and
    (Test-Path -LiteralPath $charBattleSource -PathType Leaf)) {
    $mountDeathResult = & $mountDeathApply -SourceFile $charBattleSource
    if ($mountDeathResult.Changed) {
        $syncedFiles++
        Write-Host 'Mount seal off into the bag at death.' -ForegroundColor DarkGray
    }
}
# The horse saddlebags open on a mount seal too (server-patches/saddlebagmount).
$saddlebagMountApply = Join-Path $repo 'server-patches/saddlebagmount/Apply-SaddlebagMountPatch.ps1'
$charSource = Join-Path $engineGameSource 'char.cpp'
if ((Test-Path -LiteralPath $saddlebagMountApply -PathType Leaf) -and
    (Test-Path -LiteralPath $charSource -PathType Leaf)) {
    $saddlebagMountResult = & $saddlebagMountApply -SourceFile $charSource
    if ($saddlebagMountResult.Changed) {
        $syncedFiles++
        Write-Host 'Horse saddlebags open on a mount seal too.' -ForegroundColor DarkGray
    }
}
# A Metin stone never walks (server-patches/stonestill).
$stoneStillApply = Join-Path $repo 'server-patches/stonestill/Apply-StoneStillPatch.ps1'
if ((Test-Path -LiteralPath $stoneStillApply -PathType Leaf) -and
    (Test-Path -LiteralPath $engineGameSource -PathType Container)) {
    $stoneStillResult = & $stoneStillApply -SourceDirectory $engineGameSource
    if ($stoneStillResult.Changed) {
        $syncedFiles++
        Write-Host 'Metin stones stand still.' -ForegroundColor DarkGray
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
# The alchemy deck for players (server-patches/dscommand): the client's
# "/dragon_soul activate" was a GM_IMPLEMENTOR command, so a player got
# "Ta komenda nie istnieje"; its testing aids stay a GM's.
$dsCommandApply = Join-Path $repo 'server-patches/dscommand/Apply-DsCommandPatch.ps1'
if ((Test-Path -LiteralPath $dsCommandApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cmd.cpp') -PathType Leaf)) {
    $dsCommandResult = & $dsCommandApply -SourceDir $engineGameSource
    if ($dsCommandResult.Changed) {
        $syncedFiles++
        Write-Host 'Enabled the alchemy deck command for players.' -ForegroundColor DarkGray
    }
}
# A pet's magic attack % (server-patches/magicattper): PointChange had no
# case for POINT_MAGIC_ATT_BONUS_PER, so the bonus never applied.
$magicAttApply = Join-Path $repo 'server-patches/magicattper/Apply-MagicAttPerPatch.ps1'
$charSource = Join-Path $engineGameSource 'char.cpp'
if ((Test-Path -LiteralPath $magicAttApply -PathType Leaf) -and
    (Test-Path -LiteralPath $charSource -PathType Leaf)) {
    $magicAttResult = & $magicAttApply -SourceFile $charSource
    if ($magicAttResult.Changed) {
        $syncedFiles++
        Write-Host 'Enabled the pets'' magic attack bonus.' -ForegroundColor DarkGray
    }
}
# Every costume mount's speed in the movement check (server-patches/
# mountspeed): the Magma Manni correction for all of them, widening only.
$mountSpeedApply = Join-Path $repo 'server-patches/mountspeed/Apply-MountSpeedPatch.ps1'
$charPlayerSource = Join-Path $engineGameSource 'char_player.cpp'
if ((Test-Path -LiteralPath $mountSpeedApply -PathType Leaf) -and
    (Test-Path -LiteralPath $charPlayerSource -PathType Leaf)) {
    $mountSpeedResult = & $mountSpeedApply -SourceFile $charPlayerSource
    if ($mountSpeedResult.Changed) {
        $syncedFiles++
        Write-Host 'Enabled the speed correction for every costume mount.' -ForegroundColor DarkGray
    }
}
# A Cor Draconis or a sash a many-item drop hands to a bot goes into its bag
# (server-patches/botrareshare), not onto the ground under its name.
$rareShareApply = Join-Path $repo 'server-patches/botrareshare/Apply-BotRareSharePatch.ps1'
$charBattleSource = Join-Path $engineGameSource 'char_battle.cpp'
if ((Test-Path -LiteralPath $rareShareApply -PathType Leaf) -and
    (Test-Path -LiteralPath $charBattleSource -PathType Leaf)) {
    $rareShareResult = & $rareShareApply -SourceFile $charBattleSource
    if ($rareShareResult.Changed) {
        $syncedFiles++
        Write-Host 'Enabled the bots'' share of Cor Draconis and sashes.' -ForegroundColor DarkGray
    }
}
# A mount seal's bonuses once, not once a ride (server-patches/mountbonus).
$mountBonusApply = Join-Path $repo 'server-patches/mountbonus/Apply-MountBonusPatch.ps1'
$mountSystemSource = Join-Path $engineGameSource 'MountSystem.cpp'
if ((Test-Path -LiteralPath $mountBonusApply -PathType Leaf) -and
    (Test-Path -LiteralPath $mountSystemSource -PathType Leaf)) {
    $mountBonusResult = & $mountBonusApply -SourceFile $mountSystemSource
    if ($mountBonusResult.Changed) {
        $syncedFiles++
        Write-Host 'Mount seal bonuses counted once a ride.' -ForegroundColor DarkGray
    }
}
# Mount seals without a time limit ride with no end (server-patches/mountpermanent).
$mountPermanentApply = Join-Path $repo 'server-patches/mountpermanent/Apply-MountPermanentPatch.ps1'
if ((Test-Path -LiteralPath $mountPermanentApply -PathType Leaf) -and
    (Test-Path -LiteralPath $mountSystemSource -PathType Leaf)) {
    $mountPermanentResult = & $mountPermanentApply -SourceFile $mountSystemSource
    if ($mountPermanentResult.Changed) {
        $syncedFiles++
        Write-Host 'Mount seals without a time limit are permanent.' -ForegroundColor DarkGray
    }
}
# 5 s of slack in the speedhack move check for Docker/WSL2 clocks stepped back
# a few seconds at a time (server-patches/speedhackclock).
$speedHackClockApply = Join-Path $repo 'server-patches/speedhackclock/Apply-SpeedHackClockPatch.ps1'
$inputMainSource = Join-Path $engineGameSource 'input_main.cpp'
if ((Test-Path -LiteralPath $speedHackClockApply -PathType Leaf) -and
    (Test-Path -LiteralPath $inputMainSource -PathType Leaf)) {
    $speedHackClockResult = & $speedHackClockApply -SourceFile $inputMainSource
    if ($speedHackClockResult.Changed) {
        $syncedFiles++
        Write-Host 'Speedhack check tolerant of stepped clocks.' -ForegroundColor DarkGray
    }
}
# Cor Draconis boxes stack in MoveItem despite ANTI_STACK in the proto
# (server-patches/corstack; Codex's change from the test server).
$corStackApply = Join-Path $repo 'server-patches/corstack/Apply-CorStackPatch.ps1'
$charItemSource = Join-Path $engineGameSource 'char_item.cpp'
if ((Test-Path -LiteralPath $corStackApply -PathType Leaf) -and
    (Test-Path -LiteralPath $charItemSource -PathType Leaf)) {
    $corStackResult = & $corStackApply -SourceFile $charItemSource
    if ($corStackResult.Changed) {
        $syncedFiles++
        Write-Host 'Cor Draconis boxes stack.' -ForegroundColor DarkGray
    }
}
# And join the bag's stack when picked up or given (server-patches/corautostack,
# after corstack, whose helper it uses).
$corAutoStackApply = Join-Path $repo 'server-patches/corautostack/Apply-CorAutoStackPatch.ps1'
if ((Test-Path -LiteralPath $corAutoStackApply -PathType Leaf) -and
    (Test-Path -LiteralPath $charItemSource -PathType Leaf)) {
    $corAutoStackResult = & $corAutoStackApply -SourceFile $charItemSource
    if ($corAutoStackResult.Changed) {
        $syncedFiles++
        Write-Host 'A Cor Draconis picked up joins the stack in the bag.' -ForegroundColor DarkGray
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
