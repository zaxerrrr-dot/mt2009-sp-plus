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
#   bot sash drop      item_manager.cpp, char_item.cpp (MT2009_PLUS_BOT_SASH_DROP_V1)
#   mount bonus once   MountSystem.cpp           (MT2009_PLUS_MOUNT_BONUS_ONCE_V1)
#   permanent seals    MountSystem.cpp           (MT2009_PLUS_MOUNT_PERMANENT_V1)
#   rare drop levels   item_manager.cpp          (MT2009_PLUS_RARE_LEVEL_V1)
#   drop preview min   item_manager.cpp          (MT2009_PLUS_DROP_PREVIEW_MIN_V1)
#   rare switches      item_manager.cpp, char_item.cpp (MT2009_PLUS_RARE_TOGGLE_V1)
#   speedhack slack    input_main.cpp            (MT2009_PLUS_SPEEDHACK_CLOCK_V1)
#   Cor stacking       char_item.cpp             (IsStackableCorDraconisVnum)
#   Cor pickup stacks  char_item.cpp             (MT2009_PLUS_COR_AUTOSTACK_V1)
#   DS trace players   char_item.cpp             (MT2009_PLUS_DS_TRACE_PLAYERS_V1)
#   event manager      packet.h, cmd.cpp, cmd_general.cpp (MT2009_PLUS_EVENT_MANAGER_V1)
#   Seon-Hae 6/7 bonus cmd.cpp, cmd_general.cpp, item_manager.cpp (MT2009_PLUS_SEONHAE_V1)
#   Rumi (Okey)        packet.h, packet_info.cpp, input_main.cpp, char.cpp, char_item.cpp,
#                      item_manager.cpp, questlua_game.cpp (MT2009_PLUS_RUMI_V1)
#   Yut Nori           packet.h, packet_info.cpp, input_main.cpp, char_item.cpp,
#                      item_manager.cpp (MT2009_PLUS_YUTNORI_V1)
#   Digi Rasta's systems char_item.cpp, char_battle.cpp, char_horse.cpp
#                      (MT2009_PLUS_AWAKENING_V1, MT2009_PLUS_SOULSTONE9_V1,
#                      MT2009_PLUS_HORSE30_V1; server-patches/digirasta)
#   Kolczan (quiver)   char_battle.cpp           (MT2009_PLUS_QUIVER_V1; server-patches/quiver)
#   mount quick swap   cmd_general.cpp, char_item.cpp, MountSystem.cpp
#                      (MT2009_PLUS_MOUNT_QUICKSWAP_V1, MT2009_PLUS_MOUNT_CRASH_FIX_V1;
#                      server-patches/mountquickswap)
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
# Smoczy Skowyt on its target (server-patches/dragonroartarget): SELFONLY
# put the splash round the Shaman while the client plays it at the target.
$roarApply = Join-Path $repo 'server-patches/dragonroartarget/Apply-DragonRoarTargetPatch.ps1'
$skillSource = Join-Path $engineGameSource 'char_skill.cpp'
if ((Test-Path -LiteralPath $roarApply -PathType Leaf) -and
    (Test-Path -LiteralPath $skillSource -PathType Leaf)) {
    $roarResult = & $roarApply -SourceFile $skillSource
    if ($roarResult.Changed) {
        $syncedFiles++
        Write-Host 'Smoczy Skowyt now hits round its target.' -ForegroundColor DarkGray
    }
}
# The companion picks up its owner's Cor Draconis (server-patches/corpartypickup):
# the blanket "no Cor for a bot" refused the party branch that hands it over.
$corPartyApply = Join-Path $repo 'server-patches/corpartypickup/Apply-CorPartyPickupPatch.ps1'
$itemSource = Join-Path $engineGameSource 'char_item.cpp'
if ((Test-Path -LiteralPath $corPartyApply -PathType Leaf) -and
    (Test-Path -LiteralPath $itemSource -PathType Leaf)) {
    $corPartyResult = & $corPartyApply -SourceFile $itemSource
    if ($corPartyResult.Changed) {
        $syncedFiles++
        Write-Host 'The companion now picks up its owner''s Cor Draconis.' -ForegroundColor DarkGray
    }
}
# The pet stays when its owner dies (server-patches/petstaysondeath).
$petStayApply = Join-Path $repo 'server-patches/petstaysondeath/Apply-PetStaysOnDeathPatch.ps1'
$petSource = Join-Path $engineGameSource 'PetSystem.cpp'
if ((Test-Path -LiteralPath $petStayApply -PathType Leaf) -and
    (Test-Path -LiteralPath $petSource -PathType Leaf)) {
    $petStayResult = & $petStayApply -SourceFile $petSource
    if ($petStayResult.Changed) {
        $syncedFiles++
        Write-Host 'The pet now stays when its owner dies.' -ForegroundColor DarkGray
    }
}
# A login may carry an underscore, the bots' playerbot_NNN taken over from the
# advanced panel (server-patches/loginunderscore).
$loginUnderscoreApply = Join-Path $repo 'server-patches/loginunderscore/Apply-LoginUnderscorePatch.ps1'
$authSource = Join-Path $engineGameSource 'input_auth.cpp'
if ((Test-Path -LiteralPath $loginUnderscoreApply -PathType Leaf) -and
    (Test-Path -LiteralPath $authSource -PathType Leaf)) {
    $loginUnderscoreResult = & $loginUnderscoreApply -SourceFile $authSource
    if ($loginUnderscoreResult.Changed) {
        $syncedFiles++
        Write-Host 'Logins may now carry an underscore (bot takeover).' -ForegroundColor DarkGray
    }
}
# The players' conveniences of 28 September (server-patches/playerqol): the
# garbage bin by the batch, the pickup filter of the Z key and the loot pets,
# the merge-only arrange, the search's MT2009 Plus category and the horse
# skills on a costume mount.
$playerQolApply = Join-Path $repo 'server-patches/playerqol/Apply-PlayerQolPatch.ps1'
if ((Test-Path -LiteralPath $playerQolApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cmd_general.cpp') -PathType Leaf)) {
    $playerQolResult = & $playerQolApply -SourceDir $engineGameSource
    if ($playerQolResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} player convenience edit(s).' -f $playerQolResult.Applied) -ForegroundColor DarkGray
    }
}
# The Dom Towarowy's part of a stack and its search with Polish capitals
# (server-patches/shopsearch2): game core, db core and common/tables.h; after
# playerqol, whose lock lines in ClientManagerIkarusShop.cpp it anchors on.
$shopSearch2Apply = Join-Path $repo 'server-patches/shopsearch2/Apply-ShopSearch2Patch.ps1'
if ((Test-Path -LiteralPath $shopSearch2Apply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'ikarus_shop_manager.cpp') -PathType Leaf)) {
    $shopSearch2Result = & $shopSearch2Apply -SourceDir $engineGameSource
    if ($shopSearch2Result.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Dom Towarowy edit(s).' -f $shopSearch2Result.Applied) -ForegroundColor DarkGray
    }
}
# The Blue Dragon lair (server-patches/bluedragon, MT2009_PLUS_BLUE_DRAGON_V1):
# Beran-Setaou in an instance of map 208 takes no damage while one of his four
# stones stands, and each dragon keeps its own skill cooldowns.
$blueDragonApply = Join-Path $repo 'server-patches/bluedragon/Apply-BlueDragonPatch.ps1'
if ((Test-Path -LiteralPath $blueDragonApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'BlueDragon.cpp') -PathType Leaf)) {
    $blueDragonResult = & $blueDragonApply -SourceDir $engineGameSource
    if ($blueDragonResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Blue Dragon lair edit(s).' -f $blueDragonResult.Applied) -ForegroundColor DarkGray
    }
}
# The in-game event manager (server-patches/eventmanager): the event list's
# packet HEADER_GC_INGAME_EVENT (183) in packet.h and "/ingame_event" in
# cmd.cpp / cmd_general.cpp (playerbot_ingame_events.h); after playerqol,
# whose goblin lines it anchors on.
$eventManagerApply = Join-Path $repo 'server-patches/eventmanager/Apply-EventManagerPatch.ps1'
if ((Test-Path -LiteralPath $eventManagerApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'packet.h') -PathType Leaf)) {
    $eventManagerResult = & $eventManagerApply -SourceDir $engineGameSource
    if ($eventManagerResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} event manager edit(s).' -f $eventManagerResult.Applied) -ForegroundColor DarkGray
    }
}
# Seon-Hae's 6th/7th bonus (server-patches/seonhae): "/seonhae" in cmd.cpp /
# cmd_general.cpp and the shard/additive drop in item_manager.cpp
# (playerbot_seonhae.h); after playerqol, whose goblin lines it anchors on.
$seonHaeApply = Join-Path $repo 'server-patches/seonhae/Apply-SeonHaePatch.ps1'
if ((Test-Path -LiteralPath $seonHaeApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cmd.cpp') -PathType Leaf)) {
    $seonHaeResult = & $seonHaeApply -SourceDir $engineGameSource
    if ($seonHaeResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Seon-Hae edit(s).' -f $seonHaeResult.Applied) -ForegroundColor DarkGray
    }
}
# The Flower Event "Dzieci Kwiaty" (server-patches/flower): packets 187 in
# packet.h / packet_info.cpp / input_main.cpp, the seeds on a kill in
# item_manager.cpp and the flowers in char_item.cpp (playerbot_flower.h);
# after eventmanager, whose packet.h lines it anchors on.
$flowerApply = Join-Path $repo 'server-patches/flower/Apply-FlowerPatch.ps1'
if ((Test-Path -LiteralPath $flowerApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'packet.h') -PathType Leaf)) {
    $flowerResult = & $flowerApply -SourceDir $engineGameSource
    if ($flowerResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Flower Event edit(s).' -f $flowerResult.Applied) -ForegroundColor DarkGray
    }
}
# Owsap's Rumi (Okey card game) (server-patches/rumi, MT2009_PLUS_RUMI_V1):
# CG/GC 181 in packet.h / packet_info.cpp / input_main.cpp, the logout
# settlement in char.cpp, the card items in char_item.cpp, the per-kill card in
# item_manager.cpp and the table's quest functions in questlua_game.cpp
# (playerbot_rumi.h); after the event manager, whose packet.h lines it anchors on.
$rumiApply = Join-Path $repo 'server-patches/rumi/Apply-RumiPatch.ps1'
if ((Test-Path -LiteralPath $rumiApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'packet.h') -PathType Leaf)) {
    $rumiResult = & $rumiApply -SourceDir $engineGameSource
    if ($rumiResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Rumi edit(s).' -f $rumiResult.Applied) -ForegroundColor DarkGray
    }
}
# Catch the King (server-patches/catchking, MT2009_PLUS_CATCH_KING_V1): packets
# CG 226 / GC 238 in packet.h and packet_info.cpp, their case in input_main.cpp,
# the King Card share of a kill (item_manager.cpp), a game left mid-way
# (char.cpp) and the quest functions (questlua_game.cpp) - playerbot_catchking.h;
# after the event manager, whose packet.h lines it anchors on.
$catchKingApply = Join-Path $repo 'server-patches/catchking/Apply-CatchKingPatch.ps1'
if ((Test-Path -LiteralPath $catchKingApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'packet.h') -PathType Leaf)) {
    $catchKingResult = & $catchKingApply -SourceDir $engineGameSource
    if ($catchKingResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Catch the King edit(s).' -f $catchKingResult.Applied) -ForegroundColor DarkGray
    }
}
# Yut Nori (server-patches/yutnori): Owsap's packets 182, their dispatch, the
# Birch Branch and the board's use and the kill's roll for a branch
# (playerbot_yutnori.h); after the event manager, whose packet lines it
# anchors on.
$yutnoriApply = Join-Path $repo 'server-patches/yutnori/Apply-YutnoriPatch.ps1'
if ((Test-Path -LiteralPath $yutnoriApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'packet.h') -PathType Leaf)) {
    $yutnoriResult = & $yutnoriApply -SourceDir $engineGameSource
    if ($yutnoriResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Yut Nori edit(s).' -f $yutnoriResult.Applied) -ForegroundColor DarkGray
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
# The Dragon Stone equip trace for players only (server-patches/dstraceplayers).
$dsTraceApply = Join-Path $repo 'server-patches/dstraceplayers/Apply-DsTracePlayersPatch.ps1'
if ((Test-Path -LiteralPath $dsTraceApply -PathType Leaf) -and
    (Test-Path -LiteralPath $charItemSource -PathType Leaf)) {
    $dsTraceResult = & $dsTraceApply -SourceFile $charItemSource
    if ($dsTraceResult.Changed) {
        $syncedFiles++
        Write-Host 'Dragon Stone equip trace for players only.' -ForegroundColor DarkGray
    }
}
# Bots roll sashes like players (server-patches/botsashdrop): the boss kill
# at 80% and the boss chest's unique; after botraredrop, rarelevel and
# raretoggle, which shape the same blocks.
$botSashDropApply = Join-Path $repo 'server-patches/botsashdrop/Apply-BotSashDropPatch.ps1'
if ((Test-Path -LiteralPath $botSashDropApply -PathType Leaf) -and
    (Test-Path -LiteralPath $engineGameSource -PathType Container)) {
    $botSashDropResult = & $botSashDropApply -SourceDirectory $engineGameSource
    if ($botSashDropResult.Changed) {
        $syncedFiles++
        Write-Host 'Bots roll sashes like players.' -ForegroundColor DarkGray
    }
}
# Metin drops and the command flood guard (server-patches/metindrops): a
# Metin's sash at 15% and its Cor Draconis at 20%, and the client's own polls
# no longer eat a player's commands; after botsashdrop and raretoggle.
$metinDropsApply = Join-Path $repo 'server-patches/metindrops/Apply-MetinDropsPatch.ps1'
if ((Test-Path -LiteralPath $metinDropsApply -PathType Leaf) -and
    (Test-Path -LiteralPath $engineGameSource -PathType Container)) {
    $metinDropsResult = & $metinDropsApply -SourceDirectory $engineGameSource
    if ($metinDropsResult.Changed) {
        $syncedFiles++
        Write-Host 'Metin drops and the command limit.' -ForegroundColor DarkGray
    }
}
# Per-mob Cor Draconis / sash rules (server-patches/raremobrules): no Cor and no
# sash from the Wukong Metins and the Phoenix nor from the library's Metin, WuKong
# 5 Cor at 15% and a sash at 15%, and the library's Metin's own drop group;
# after metindrops.
$rareMobRulesApply = Join-Path $repo 'server-patches/raremobrules/Apply-RareMobRulesPatch.ps1'
if ((Test-Path -LiteralPath $rareMobRulesApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item_manager.cpp') -PathType Leaf)) {
    $rareMobRulesResult = & $rareMobRulesApply -SourceDir $engineGameSource
    if ($rareMobRulesResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} per-mob rare drop edit(s).' -f $rareMobRulesResult.Applied) -ForegroundColor DarkGray
    }
}
# The 6th/7th bonus rolls its level lv1-lv5 by the panel's odds
# (server-patches/rarelevelroll; m2_rare_lv1..5, default 35/30/20/10/5).
$rareLevelRollApply = Join-Path $repo 'server-patches/rarelevelroll/Apply-RareLevelRollPatch.ps1'
if ((Test-Path -LiteralPath $rareLevelRollApply -PathType Leaf) -and
    (Test-Path -LiteralPath $engineGameSource -PathType Container)) {
    $rareLevelRollResult = & $rareLevelRollApply -SourceDirectory $engineGameSource
    if ($rareLevelRollResult.Changed) {
        $syncedFiles++
        Write-Host 'The 6th/7th bonus level by the panel odds.' -ForegroundColor DarkGray
    }
}
# A rider's reach in a normal hit and a boss's body (server-patches/mountreach):
# battle_melee_attack no longer drops a rider's hit past 405, and a boss adds 250
# to a player's reach (Razador's hits on a mount, 1 October).
$mountReachApply = Join-Path $repo 'server-patches/mountreach/Apply-MountReachPatch.ps1'
if ((Test-Path -LiteralPath $mountReachApply -PathType Leaf) -and
    (Test-Path -LiteralPath $engineGameSource -PathType Container)) {
    $mountReachResult = & $mountReachApply -SourceDirectory $engineGameSource
    if ($mountReachResult.Changed) {
        $syncedFiles++
        Write-Host 'Reach on a mount and at a boss.' -ForegroundColor DarkGray
    }
}
# The health of monsters, bosses and Metin stones (server-patches/mobhp): a
# percent of max_hp from the event flag m2_mob_hp, at a spawn and live for
# every one standing (Frelik's proposal; .env M2_MONSTER_HP, the panel's card).
$mobHpApply = Join-Path $repo 'server-patches/mobhp/Apply-MobHpPatch.ps1'
if ((Test-Path -LiteralPath $mobHpApply -PathType Leaf) -and
    (Test-Path -LiteralPath $engineGameSource -PathType Container)) {
    $mobHpResult = & $mobHpApply -SourceDirectory $engineGameSource
    if ($mobHpResult.Changed) {
        $syncedFiles++
        Write-Host 'Monster health from the world settings.' -ForegroundColor DarkGray
    }
}
# The wait between two Soul Stones follows the difficulty, at most 12 hours
# (server-patches/soulstonewait; the bots' side is in the overlay).
$soulStoneWaitApply = Join-Path $repo 'server-patches/soulstonewait/Apply-SoulStoneWaitPatch.ps1'
if ((Test-Path -LiteralPath $soulStoneWaitApply -PathType Leaf) -and
    (Test-Path -LiteralPath $engineGameSource -PathType Container)) {
    $soulStoneWaitResult = & $soulStoneWaitApply -SourceDirectory $engineGameSource
    if ($soulStoneWaitResult.Changed) {
        $syncedFiles++
        Write-Host 'Soul Stone wait by the difficulty.' -ForegroundColor DarkGray
    }
}
# The unique sash from a box opened with its key: the bosses' chests only, not
# the Gold and Silver Caskets (server-patches/chestsash).
$chestSashApply = Join-Path $repo 'server-patches/chestsash/Apply-ChestSashPatch.ps1'
if ((Test-Path -LiteralPath $chestSashApply -PathType Leaf) -and
    (Test-Path -LiteralPath $engineGameSource -PathType Container)) {
    $chestSashResult = & $chestSashApply -SourceDirectory $engineGameSource
    if ($chestSashResult.Changed) {
        $syncedFiles++
        Write-Host 'No unique sash from the Gold and Silver Caskets.' -ForegroundColor DarkGray
    }
}
# Engine fixes of 1 October (server-patches/enginefixes): a chat command or a
# whisper before the game phase is passed over whole (channel change with the
# Companion's window open), the map list's bound checked before the write, and
# the minibosses in Auto Lowy's "Bossy".
$engineFixesApply = Join-Path $repo 'server-patches/enginefixes/Apply-EngineFixesPatch.ps1'
if ((Test-Path -LiteralPath $engineFixesApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'input.cpp') -PathType Leaf)) {
    $engineFixesResult = & $engineFixesApply -SourceDir $engineGameSource
    if ($engineFixesResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} engine fix edit(s).' -f $engineFixesResult.Applied) -ForegroundColor DarkGray
    }
}
# Lua stack room (server-patches/luastack): get_special_item_group and two
# other quest functions that push many values ask Lua for the room first
# (a group longer than 10 lines wrote past the coroutine's stack - Catch the
# King's Golden Loot crashed the core).
$luaStackApply = Join-Path $repo 'server-patches/luastack/Apply-LuaStackPatch.ps1'
if ((Test-Path -LiteralPath $luaStackApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'questlua_global.cpp') -PathType Leaf)) {
    $luaStackResult = & $luaStackApply -SourceDir $engineGameSource
    if ($luaStackResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Lua stack edit(s).' -f $luaStackResult.Applied) -ForegroundColor DarkGray
    }
}
# A dungeon's own monster health (server-patches/dungeonhp): d.count_players()
# and d.mob_hp_percent(vnum, percent) - the Biblioteka Wiedzy's Metins at 55%
# and its Baroness by the players inside (the owner, 2 October); V2: a raised
# monster heals as many points a tick as before the rescale (char.cpp).
$dungeonHpApply = Join-Path $repo 'server-patches/dungeonhp/Apply-DungeonHpPatch.ps1'
if ((Test-Path -LiteralPath $dungeonHpApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'questlua_dungeon.cpp') -PathType Leaf)) {
    $dungeonHpResult = & $dungeonHpApply -SourceDirectory $engineGameSource
    if ($dungeonHpResult.Changed) {
        $syncedFiles++
        Write-Host 'Dungeon monster health from the quests.' -ForegroundColor DarkGray
    }
}
# Guild war kills (server-patches/guildwarkills): a field war's score is its
# kills, one a kill, not the victim's level - the bots end a war with a bot
# guild on a side at WAR_KILLS (playerbot_guild_war.h).
$guildWarKillsApply = Join-Path $repo 'server-patches/guildwarkills/Apply-GuildWarKillsPatch.ps1'
if ((Test-Path -LiteralPath $guildWarKillsApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'guild_manager.cpp') -PathType Leaf)) {
    $guildWarKillsResult = & $guildWarKillsApply -SourceDir $engineGameSource
    if ($guildWarKillsResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} guild war kills edit(s).' -f $guildWarKillsResult.Applied) -ForegroundColor DarkGray
    }
}
# The System Legend (server-patches/legends): a bot of a tier strikes harder
# against people and monsters, gains more experience, and its deaths and
# kills count for the Legends (playerbot_legends.h).
$legendsApply = Join-Path $repo 'server-patches/legends/Apply-LegendsPatch.ps1'
if ((Test-Path -LiteralPath $legendsApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'battle.cpp') -PathType Leaf)) {
    $legendsResult = & $legendsApply -SourceDir $engineGameSource
    if ($legendsResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} System Legend edit(s).' -f $legendsResult.Applied) -ForegroundColor DarkGray
    }
}
# Digi Rasta's systems (server-patches/digirasta, "Autor: Digi Rasta"): the
# Ritual of Awakening and the awakened weapons that never burn, the soul
# stones refined to +9, the awakening stone from the bosses and the Black
# Steed of the horse's level 30 (playerbot_awakening.h, quest konie).
$digiRastaApply = Join-Path $repo 'server-patches/digirasta/Apply-DigiRastaPatch.ps1'
if ((Test-Path -LiteralPath $digiRastaApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_horse.cpp') -PathType Leaf)) {
    $digiRastaResult = & $digiRastaApply -SourceDir $engineGameSource
    if ($digiRastaResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Digi Rasta system edit(s).' -f $digiRastaResult.Applied) -ForegroundColor DarkGray
    }
}
# Digi Rasta's client conveniences, server side (server-patches/digirasta-client,
# MT2009_PLUS_DIGI_CLIENT_QOL_V1, "Autor: Digi Rasta"): a real player's pick-up
# (item or yang) sends "PickupSound <vnum>" and the client plays a sound by the
# item's kind (game.py, digiqol.py).
$digiRastaClientApply = Join-Path $repo 'server-patches/digirasta-client/Apply-DigiRastaClientPatch.ps1'
if ((Test-Path -LiteralPath $digiRastaClientApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_item.cpp') -PathType Leaf)) {
    $digiRastaClientResult = & $digiRastaClientApply -SourceDir $engineGameSource
    if ($digiRastaClientResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Digi Rasta client convenience edit(s).' -f $digiRastaClientResult.Applied) -ForegroundColor DarkGray
    }
}
# Entity snapshot check (server-patches/entitysnapshot): ForEachAround's
# snapshot skips characters destroyed while it is walked (a splash skill's
# kill ran d.purge_area and the next blow landed on a freed monster - the
# Arezzo dungeons' core crash).
$entitySnapshotApply = Join-Path $repo 'server-patches/entitysnapshot/Apply-EntitySnapshotPatch.ps1'
if ((Test-Path -LiteralPath $entitySnapshotApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'sectree.cpp') -PathType Leaf)) {
    $entitySnapshotResult = & $entitySnapshotApply -SourceDir $engineGameSource
    if ($entitySnapshotResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} entity snapshot edit(s).' -f $entitySnapshotResult.Applied) -ForegroundColor DarkGray
    }
}
# Safebox "Tylko scal stosy" (server-patches/safeboxmerge): "/safebox_arrange
# merge" pours the safebox's stacks together and moves nothing else
# (playerbot_arrange::MergeSafeboxStacks).
$safeboxMergeApply = Join-Path $repo 'server-patches/safeboxmerge/Apply-SafeboxMergePatch.ps1'
if ((Test-Path -LiteralPath $safeboxMergeApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cmd_general.cpp') -PathType Leaf)) {
    $safeboxMergeResult = & $safeboxMergeApply -SourceDir $engineGameSource
    if ($safeboxMergeResult.Changed) {
        $syncedFiles++
        Write-Host 'The safebox merges its stacks without sorting.' -ForegroundColor DarkGray
    }
}
# Inventory sort lock (server-patches/sortlock): "/inventory_arrange" reads
# "keep=<hex>", the cells locked with Alt + left click, and leaves those
# items where they stand (playerbot_arrange::InventoryArrangeCommand); after
# playerqol, whose "merge" lines it anchors on.
$sortLockApply = Join-Path $repo 'server-patches/sortlock/Apply-SortLockPatch.ps1'
if ((Test-Path -LiteralPath $sortLockApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cmd_general.cpp') -PathType Leaf)) {
    $sortLockResult = & $sortLockApply -SourceDir $engineGameSource
    if ($sortLockResult.Changed) {
        $syncedFiles++
        Write-Host 'Locked inventory items stay put when the bag is sorted.' -ForegroundColor DarkGray
    }
}
# The sale tax between players and bots (server-patches/saletax,
# MT2009_PLUS_SALE_TAX_V1): the panels' SALE_TAX slider (playerbot_sale_tax.h)
# taken off what a stall, an offline counter, an accepted offer or an auction
# pays its seller - game core (shop.cpp, ikarus_shop_manager.cpp, char_item.cpp)
# and db core (ClientManagerIkarusShop.cpp). Last: it anchors on shopsearch2's
# part-stack lines.
$saleTaxApply = Join-Path $repo 'server-patches/saletax/Apply-SaleTaxPatch.ps1'
if ((Test-Path -LiteralPath $saleTaxApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'shop.cpp') -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'ikarus_shop_manager.cpp') -PathType Leaf)) {
    $saleTaxResult = & $saleTaxApply -SourceDir $engineGameSource
    if ($saleTaxResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} sale tax edit(s).' -f $saleTaxResult.Applied) -ForegroundColor DarkGray
    }
}
# Kolczan, the ItemShop's quiver (server-patches/quiver, MT2009_PLUS_QUIVER_V1):
# an arrow with a real-time limit never runs out - GetArrowAndBow hands out
# every arrow a shot asks while it has time left and UseArrow spends none
# (char_battle.cpp; the bots' twin is IsPlayerBotQuiver in playerbot_gear.h).
$quiverApply = Join-Path $repo 'server-patches/quiver/Apply-QuiverPatch.ps1'
if ((Test-Path -LiteralPath $quiverApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_battle.cpp') -PathType Leaf)) {
    $quiverResult = & $quiverApply -SourceDir $engineGameSource
    if ($quiverResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} quiver edit(s).' -f $quiverResult.Applied) -ForegroundColor DarkGray
    }
}
# Seal mounts like a horse (server-patches/mountquickswap,
# MT2009_PLUS_MOUNT_QUICKSWAP_V1): Ctrl+G gets off a seal mount and leaves the
# seal worn, the next Ctrl+G is back in the saddle at once (do_ride,
# cmd_general.cpp); a seal is put on right after an attack or a skill too
# (EquipItem, char_item.cpp). With Digi Rasta's three crash fixes for a mount
# character destroyed from outside (MountSystem.cpp,
# MT2009_PLUS_MOUNT_CRASH_FIX_V1). After mountbonus/mountpermanent and
# playerqol; its anchors are the engine's own lines.
$mountQuickswapApply = Join-Path $repo 'server-patches/mountquickswap/Apply-MountQuickswapPatch.ps1'
if ((Test-Path -LiteralPath $mountQuickswapApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cmd_general.cpp') -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'MountSystem.cpp') -PathType Leaf)) {
    $mountQuickswapResult = & $mountQuickswapApply -SourceDir $engineGameSource
    if ($mountQuickswapResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} mount quick swap edit(s).' -f $mountQuickswapResult.Applied) -ForegroundColor DarkGray
    }
}
# Digi Rasta's fixes and stacking (server-patches/digirasta-fixes, "Autor: Digi
# Rasta", nowy-system v0.23): the safebox's grid rebuilt when an open safebox
# grows and "/reload c" rebuilding the cube window's recipe lists
# (MT2009_PLUS_DIGI_FIXES_V1, safebox.cpp, cube.cpp); a refine and a socket
# taking one piece of a stack (MT2009_PLUS_DIGI_STACK_V1, char_item.cpp - the
# stacks of 200 are apply.sh's). After the existing patches.
$digiRastaFixesApply = Join-Path $repo 'server-patches/digirasta-fixes/Apply-DigiRastaFixesPatch.ps1'
if ((Test-Path -LiteralPath $digiRastaFixesApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'safebox.cpp') -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cube.cpp') -PathType Leaf)) {
    $digiRastaFixesResult = & $digiRastaFixesApply -SourceDir $engineGameSource
    if ($digiRastaFixesResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Digi Rasta fix and stacking edit(s).' -f $digiRastaFixesResult.Applied) -ForegroundColor DarkGray
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
