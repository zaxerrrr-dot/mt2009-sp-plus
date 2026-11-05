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
#   Digi Rasta's conveniences char_item.cpp, input_main.cpp, exchange.cpp, char.cpp,
#                      guild.cpp, cmd_general.cpp, cmd_emotion.cpp, input_login.cpp,
#                      char_battle.cpp, cmd.cpp (MT2009_PLUS_DIGI_SERVER_QOL_V1;
#                      server-patches/digirasta-qol)
#   quick chest opening char_item.cpp         (MT2009_PLUS_VEKIRION_V1; server-patches/vekirion,
#                      Autor: Vekirion)
#   guild war entry    guild_war.cpp, cmd.cpp, cmd_general.cpp
#                      (MT2009_PLUS_GUILD_WAR_JOIN_V1; server-patches/guildwarjoin)
#   Monster Cards      cmd.cpp, char_battle.cpp, char_item.cpp, input_login.cpp
#                      (MT2009_PLUS_MONSTER_CARDS_V1; server-patches/monstercard,
#                      Autor: Digi Rasta)
#   Punkty Rangi       cmd.cpp, char_battle.cpp, char_item.cpp, input_login.cpp,
#                      char.cpp, item_manager.cpp (MT2009_PLUS_RANK_POINTS_V1;
#                      server-patches/rankpoints)
#   Swiatynia Zodiaku  24 engine files, ENABLE_12ZI (MT2009_PLUS_ZODIAC_V1;
#                      server-patches/zodiak, Autor: Digi Rasta)
#   Obrona Statku      dungeon.cpp, char_battle.cpp, pvp.cpp, char.cpp, input_login.cpp,
#                      regen.cpp, sectree.cpp, char_state.cpp, questlua.cpp, cmd.cpp
#                      (MT2009_PLUS_SHIP_DEFENSE_V1; server-patches/shipdefense)
#   Poziom Czempiona   common length.h/tables.h/CommonDefines.h, db ClientManagerPlayer.cpp,
#                      char.h, char.cpp, char_battle.cpp, battle.cpp, char_resist.cpp,
#                      input_login.cpp, cmd.cpp, questlua.cpp, ENABLE_CONQUEROR_LEVEL
#                      (MT2009_PLUS_CHAMPION_V1, MT2009_PLUS_SUNGMA_V1; server-patches/czempion)
#   Talizmany Woli     item_attribute.cpp, item_manager.cpp (MT2009_PLUS_WILL_TALISMAN_V1;
#                      server-patches/talizmanwoli)
#   Zyly Jadeitu       mining.cpp (MT2009_PLUS_JADE_VEINS_V1; server-patches/jadeit)
#   Obrecze Jadeitu    item_attribute.cpp, item_manager.cpp (MT2009_PLUS_JADE_BRACELET_V1;
#                      server-patches/obreczjadeitu, after talizmanwoli)
#   Zestawy Yohary     item.h, item.cpp, item_manager.cpp, item_attribute.cpp, char.h, char.cpp,
#                      char_item.cpp, input_login.cpp, safebox.cpp, cube.h, cube.cpp
#                      (MT2009_PLUS_YOHARA_SETS_V1; server-patches/ysets)
#   Strefy na ziemi    questlua_dungeon.cpp, char_battle.cpp (MT2009_PLUS_DUNGEON_ZONE_V1,
#                      MT2009_PLUS_DUNGEON_RAGE_V1; server-patches/strefy)
#   Wieza Sung Mahi    char_skill.cpp, char_item.cpp (MT2009_PLUS_SMH_TOWER_V1, MT2009_PLUS_QUEST_USE_V1;
#                      server-patches/wiezasm)
#   Transmutacja       common tables.h/CommonDefines.h, db ClientManager*.cpp/Cache.cpp/IkarusShopCache.cpp,
#                      item.h/.cpp, item_manager.cpp, input_db.cpp, char.cpp, char_item.cpp, packet.h, safebox.cpp,
#                      exchange.cpp, ikarus_shop_manager.cpp, MountSystem.cpp, cmd_general.cpp, questlua.cpp, cmd.cpp,
#                      ENABLE_CHANGELOOK_SYSTEM (MT2009_PLUS_CHANGE_LOOK_V1; server-patches/transmutacja)
#   Ukryj kostium      CommonDefines.h, char.cpp, input_login.cpp, cmd_general.cpp, cmd.cpp, ENABLE_HIDE_COSTUME_SYSTEM
#                      (MT2009_PLUS_HIDE_COSTUME_V1; server-patches/ukryjkostium)
#   Gaya               cube.h, cube.cpp (MT2009_PLUS_GAYA_V1; server-patches/gaya, after ysets)
#   Helmy 100 poz.     cube.h, cube.cpp - cube "fail_keep" (MT2009_PLUS_HELM100_CUBE_V1; server-patches/yhelm100, after gaya)
#   Przebudzeni bossowie char_battle.cpp (MT2009_PLUS_YOHARA_PB_V1; server-patches/przebudzeni)
#   Umiejetnosci 9.    common skill_length.h, char_skill.cpp, char_battle.cpp, char_affect.cpp,
#                      constants.cpp, battle.cpp (MT2009_PLUS_SKILL9_V1; server-patches/skill9)
#   Szczelina Czasu    char_battle.cpp (MT2009_PLUS_YOHARA_CRACK_V1; server-patches/szczelina, after skill9)
#   M2_BONUS_MODE      item_manager.cpp, item_attribute.cpp (MT2009_PLUS_GLOBAL_BONUS_V1; server-patches/bonusyglobal)
#   Rudy poza mapa     regen.cpp (MT2009_PLUS_ORE_ATLAS_V1; server-patches/oreatlas, after szczelina)
#   Precyzja           common length.h/skill_length.h, char.cpp, char_item.cpp, char_skill.cpp (MT2009_PLUS_PRECISION_V1,
#                      the passive skill Precyzja MT2009_PLUS_PRECISION_SKILL_V1; server-patches/precyzja, after szczelina)
#   Rekawice Sung Ma   common CommonDefines.h/item_length.h, item.cpp, item_manager.cpp, item_attribute.cpp,
#                      char_item.cpp, ENABLE_GLOVE_SYSTEM (MT2009_PLUS_GLOVES_V1; the Will as the base attribute in the
#                      item's yextra MT2009_PLUS_GLOVE_BASE_V1; server-patches/rekawice, after precyzja and ysets)
#   Obrecze Jadeitu V2 item.cpp, item_manager.cpp, item_attribute.cpp (MT2009_PLUS_JADE_BRACELET_V2;
#                      server-patches/obreczjadeitu2, after obreczjadeitu and rekawice)
#   Szata Aury         common CommonDefines.h/length.h/item_length.h, item.cpp, char.cpp, char_item.cpp,
#                      char_battle.cpp, questlua.cpp, cmd.cpp, ENABLE_AURA_COSTUME_SYSTEM (MT2009_PLUS_AURA_V1;
#                      server-patches/aura, after transmutacja, ukryjkostium, rankpoints and rekawice)
#   Kamien Rytualny    char_item.cpp - the wheels' Kamien Rytualny (25046) only above level 80 (MT2009_PLUS_KOLA_ITEMS_V1;
#                      server-patches/kolaprzedmioty)
#   Bonusy 6/7 z wiki  common length.h (points 198-251), char.cpp, battle.cpp, char_battle.cpp, char_skill.cpp, item.cpp,
#                      item_attribute.cpp (MT2009_PLUS_BONUS67_V1; server-patches/bonusy67, after precyzja and rekawice)
#   Riposty/Dopalacze  common skill_length.h, char_skill.cpp, cmd_general.cpp (MT2009_PLUS_RIPOSTY_V1;
#                      server-patches/riposty, after skill9 and precyzja)
#   Boss Swiata        char_battle.cpp, item_manager.cpp, cmd.cpp (MT2009_PLUS_WORLDBOSS_V1; server-patches/worldboss,
#                      after shipdefense, zestawy and ysets)
#   Buffi              char.cpp, char_item.cpp, char_skill.cpp, input_login.cpp, cmd.cpp (MT2009_PLUS_BUFFI_V1;
#                      server-patches/buffi, after monstercard and riposty)
#   Dodatkowy ekwip.   common length.h, char.h, char.cpp, char_item.cpp, item.cpp, item_manager.cpp, input_db.cpp,
#                      input_main.cpp, exchange.cpp, shop.cpp, shop_manager.cpp, cube.cpp, cmd_gm.cpp, cmd.cpp,
#                      db ClientManagerPlayer.cpp (MT2009_PLUS_EKWIPUNEK_V1; server-patches/ekwipunek, after buffi)
#   Bonus Switcher     common length.h, packet.h, packet_info.cpp, input_main.cpp, input_p2p.cpp, char.cpp,
#                      char_item.cpp, cmd.cpp; takes the old bonus switcher's lines out of cmd.cpp / cmd_general.cpp
#                      (MT2009_PLUS_SWITCHBOT_V1; server-patches/switchbot, after ekwipunek)
#   Druga strona EQ    char.h, char.cpp, char_item.cpp, item.cpp, char_skill.cpp, cmd.cpp - the second equipment page,
#                      its store, unlock items 38306 / 76055, skill 200, "/addeq" (MT2009_PLUS_ADDEQ_V1;
#                      server-patches/addeq, the last one - after balathor)
#   Magazyn Item-Shopu common tables.h, cmd_general.cpp, db ClientManager.cpp - item_award deliveries fill the 3
#                      pages of a new client's paged item-shop storage, an old client's stay on page 1
#                      (MT2009_PLUS_MALL_PAGES_V1; server-patches/mall3, after addeq)
#   Seon-Pyeong        constants.cpp IsEliteRefine (+ refine_proto 39900-39999), char_item.cpp - the guild and Demon
#                      Tower smiths refuse his steps (MT2009_PLUS_SEONPYEONG_ELITE_V1; server-patches/seonpyeong)
#   Przypisane do konta item.h, item.cpp, item_attribute.cpp, char_shop.cpp, ikarus_shop_manager.cpp, shop.cpp - an
#                      account-bound item instance (the bots' G0 package): no drop, trade, merchant or shop, carried by
#                      a refine (MT2009_PLUS_ITEM_ACCOUNT_BOUND_V1; server-patches/g0bind)
#   Mlodzi Bohaterowie questlua.cpp (the "mlodzi" module), char_item.cpp (nothing used on the weapons), item_attribute.cpp
#                      (no bonus change / addition, 1-5 and 6/7), char.cpp (no sash absorption) - Bronie dla Mlodych
#                      Bohaterow 21900-21975 (MT2009_PLUS_MLODZI_BOHATEROWIE_V1; server-patches/mlodzi, last)
#   Blyskawice rekawic common length.h - SE_ELEC_ATTACK_HIT (54), the hit effect of the gloves' 6/7 lightning
#                      (POINT_GLOVE_LIGHTNING, playerbot_bonus67.cpp) (MT2009_PLUS_ELEC_GLOVE_V1; server-patches/elecglove)
#   Wezowy Czepiec item.cpp - the level-120 helmet's one random second bonus (12880-12895, the serpent gear's yextra
#                      line of server-patches/ysets: kind 2, one line) (MT2009_PLUS_SERPENT_HOOD_V1; server-patches/czepiec)
#   Bonus Reliktu      char.h, char.cpp, char_item.cpp, item.cpp, char_battle.cpp, char_skill.cpp, item_manager.cpp,
#                      cmd.cpp - the relic pages, their hooks and "/relikt" (MT2009_PLUS_RELIC_V1; server-patches/relikty,
#                      after dmgprint, last)
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
# the database editor's rare drop switches (MT2009_PLUS_RARE_DROP_SWITCHES_V1,
# also item_manager.h, item_manager_read_tables.cpp, char_item.cpp); after metindrops.
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
# Other-PC block without a character (server-patches/questpcblock, MT2009_PLUS_QUEST_PCBLOCK_V1): a server timer has
# no current character, and q.begin_other_pc_block(pid) only wrote "NULL?" - every dungeon tick that walks its
# players skipped them all. The block now selects the player and gives back exactly what it found at its end.
$questPcBlockApply = Join-Path $repo 'server-patches/questpcblock/Apply-QuestPcBlockPatch.ps1'
if ((Test-Path -LiteralPath $questPcBlockApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'questmanager.cpp') -PathType Leaf)) {
    $questPcBlockResult = & $questPcBlockApply -SourceDir $engineGameSource
    if ($questPcBlockResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} other-PC block edit(s).' -f $questPcBlockResult.Applied) -ForegroundColor DarkGray
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
# Bot friends (server-patches/botfriends): a friend invitation sent to a bot
# is answered by the bot at once - it has no client for the question
# (MT2009_PLUS_BOT_FRIENDS_V1, playerbot_bot_friends.h).
$botFriendsApply = Join-Path $repo 'server-patches/botfriends/Apply-BotFriendsPatch.ps1'
if ((Test-Path -LiteralPath $botFriendsApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'messenger_manager.cpp') -PathType Leaf)) {
    $botFriendsResult = & $botFriendsApply -SourceDir $engineGameSource
    if ($botFriendsResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} bot friends edit(s).' -f $botFriendsResult.Applied) -ForegroundColor DarkGray
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
# The belt system (server-patches/pasy, "Autor: Digi Rasta", nowy-system
# v0.27.0, MT2009_PLUS_BELTS_V1): the belt inventory also takes ITEM_POTION
# (green / purple potions) and the roasted fish 27863-27883
# (belt_inventory_helper.h). The recipes, Mistrz, the quests and the chests'
# materials are share files (linux-port/docker/game/Dockerfile).
$pasyApply = Join-Path $repo 'server-patches/pasy/Apply-PasyPatch.ps1'
if ((Test-Path -LiteralPath $pasyApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'belt_inventory_helper.h') -PathType Leaf)) {
    $pasyResult = & $pasyApply -SourceDir $engineGameSource
    if ($pasyResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} belt system edit(s).' -f $pasyResult.Applied) -ForegroundColor DarkGray
    }
}
# Digi Rasta's server conveniences (server-patches/digirasta-qol, "Autor:
# Digi Rasta", MT2009_PLUS_DIGI_SERVER_QOL_V1): the refine failure's reason,
# the messenger block over trade / party / guild / emotes / duel, the level-up
# congratulation and announcement, the daily gift, the kill bar and streak,
# skills ready after death, the death window's countdown and Seon-Hae's book
# exchange (playerbot_digi_qol.h); after seonhae, whose cmd.cpp lines it
# anchors on.
$digiQolApply = Join-Path $repo 'server-patches/digirasta-qol/Apply-DigiRastaQolPatch.ps1'
if ((Test-Path -LiteralPath $digiQolApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cmd_emotion.cpp') -PathType Leaf)) {
    $digiQolResult = & $digiQolApply -SourceDir $engineGameSource
    if ($digiQolResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Digi Rasta convenience edit(s).' -f $digiQolResult.Applied) -ForegroundColor DarkGray
    }
}
# The companion's emotions (server-patches/sidekickemotion,
# MT2009_PLUS_SIDEKICK_EMOTIONS_V1): one call in do_emotion (cmd_emotion.cpp)
# after an emotion goes out, so the player's companion may answer its owner's
# kiss, slap, dance or cheer (playerbot_sidekick.h). The consent for an
# emotion for two needs no engine change. After digirasta-qol, which edits the
# same function.
$sidekickEmotionApply = Join-Path $repo 'server-patches/sidekickemotion/Apply-SidekickEmotionPatch.ps1'
if ((Test-Path -LiteralPath $sidekickEmotionApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cmd_emotion.cpp') -PathType Leaf)) {
    $sidekickEmotionResult = & $sidekickEmotionApply -SourceDir $engineGameSource
    if ($sidekickEmotionResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} companion emotion edit(s).' -f $sidekickEmotionResult.Applied) -ForegroundColor DarkGray
    }
}
# Quick chest opening (server-patches/vekirion, MT2009_PLUS_VEKIRION_V1,
# "Autor: Vekirion"): a box opened by a plain use (ITEM_GIFTBOX) has its own
# limit of 60 in 500 ms for the client's Ctrl + right click on a stack, every
# other item keeps the engine's 5; a full bag's refusal line once a second
# (UseItem, UseItemEx, char_item.cpp). Its anchors are the engine's own lines.
$vekirionApply = Join-Path $repo 'server-patches/vekirion/Apply-VekirionPatch.ps1'
if ((Test-Path -LiteralPath $vekirionApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_item.cpp') -PathType Leaf)) {
    $vekirionResult = & $vekirionApply -SourceDir $engineGameSource
    if ($vekirionResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} quick chest opening edit(s).' -f $vekirionResult.Applied) -ForegroundColor DarkGray
    }
}
# The guild war's "Wejdz na wojne" (server-patches/guildwarjoin,
# MT2009_PLUS_GUILD_WAR_JOIN_V1): /guild_war_enter for the client's button,
# and a field war on a bot guild entered at the guild's camp on the kingdom's
# guild map (GuildWarEntryAccept returned at once for every field war). Its
# anchors are the engine's own lines.
$guildWarJoinApply = Join-Path $repo 'server-patches/guildwarjoin/Apply-GuildWarJoinPatch.ps1'
if ((Test-Path -LiteralPath $guildWarJoinApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'guild_war.cpp') -PathType Leaf)) {
    $guildWarJoinResult = & $guildWarJoinApply -SourceDir $engineGameSource
    if ($guildWarJoinResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} guild war entry edit(s).' -f $guildWarJoinResult.Applied) -ForegroundColor DarkGray
    }
}
# The collector's storage (server-patches/collector,
# MT2009_PLUS_COLLECTOR_STORAGE_V1): "/kolekcjoner" in the command table and
# off the engine's flood guard; the work is playerbot_collector.cpp (overlay).
$collectorApply = Join-Path $repo 'server-patches/collector/Apply-CollectorPatch.ps1'
if ((Test-Path -LiteralPath $collectorApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cmd.cpp') -PathType Leaf)) {
    $collectorResult = & $collectorApply -SourceDir $engineGameSource
    if ($collectorResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} collector storage edit(s).' -f $collectorResult.Applied) -ForegroundColor DarkGray
    }
}
# The /usunmisje window (server-patches/clearmissions,
# MT2009_PLUS_CLEAR_MISSIONS_V1): pc.clear_quest_letter takes another quest's
# letter off the client's quest list and its arrows off the map (questlua_pc.cpp).
$clearMissionsApply = Join-Path $repo 'server-patches/clearmissions/Apply-ClearMissionsPatch.ps1'
if ((Test-Path -LiteralPath $clearMissionsApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'questlua_pc.cpp') -PathType Leaf)) {
    $clearMissionsResult = & $clearMissionsApply -SourceDir $engineGameSource
    if ($clearMissionsResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} mission removal edit(s).' -f $clearMissionsResult.Applied) -ForegroundColor DarkGray
    }
}
# The weekly ranking and its titles (server-patches/weeklyrank,
# MT2009_PLUS_WEEKLY_RANKING_V1, on the basis of the Arezzo files' weekly
# ranking): /ranking for the client's window, the alchemy count at a Dragon
# Stone refine that took (DragonSoul.cpp) and the title holder's bonuses at
# login (input_login.cpp). The rest is the overlay's playerbot_weekly_rank.h.
$weeklyRankApply = Join-Path $repo 'server-patches/weeklyrank/Apply-WeeklyRankPatch.ps1'
if ((Test-Path -LiteralPath $weeklyRankApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'DragonSoul.cpp') -PathType Leaf)) {
    $weeklyRankResult = & $weeklyRankApply -SourceDir $engineGameSource
    if ($weeklyRankResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} weekly ranking edit(s).' -f $weeklyRankResult.Applied) -ForegroundColor DarkGray
    }
}
# The drop wiki (server-patches/dropwiki, MT2009_PLUS_DROP_WIKI_V1): /drop_wiki
# for the client's window uidropwiki.py and ITEM_MANAGER::GetDropWikiRows.
$dropWikiApply = Join-Path $repo 'server-patches/dropwiki/Apply-DropWikiPatch.ps1'
if ((Test-Path -LiteralPath $dropWikiApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item_manager.cpp') -PathType Leaf)) {
    $dropWikiResult = & $dropWikiApply -SourceDir $engineGameSource
    if ($dropWikiResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} drop wiki edit(s).' -f $dropWikiResult.Applied) -ForegroundColor DarkGray
    }
}
# Karty Potworow, the Monster Card System (server-patches/monstercard,
# MT2009_PLUS_MONSTER_CARDS_V1, "Autor: Digi Rasta"): /cardmonster for the
# client's window, a card monster's kill (char_battle.cpp), the cards' use
# (char_item.cpp) and the set bonuses at login (input_login.cpp); after the
# drop wiki and the weekly ranking, whose lines it anchors on. The rest is the
# overlay's playerbot_monster_card.h.
$monsterCardApply = Join-Path $repo 'server-patches/monstercard/Apply-MonsterCardPatch.ps1'
if ((Test-Path -LiteralPath $monsterCardApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'input_login.cpp') -PathType Leaf)) {
    $monsterCardResult = & $monsterCardApply -SourceDir $engineGameSource
    if ($monsterCardResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Monster Card edit(s).' -f $monsterCardResult.Applied) -ForegroundColor DarkGray
    }
}
# Punkty Rangi (server-patches/rankpoints, MT2009_PLUS_RANK_POINTS_V1): the rank
# fruits' use (char_item.cpp), their drop from Metins and bosses (char_battle.cpp),
# the bonus at login (input_login.cpp), the alignment's crossing of 20 000 (V2, the
# one scale: char_battle.cpp UpdateAlignment), the title for whoever sees a character
# (char.cpp), "/ranga" (cmd.cpp) and the drop wiki's row (item_manager.cpp); after
# the Monster Cards and the drop wiki, whose lines it anchors on. The rest is the
# overlay's playerbot_rank_points.h.
$rankPointsApply = Join-Path $repo 'server-patches/rankpoints/Apply-RankPointsPatch.ps1'
if ((Test-Path -LiteralPath $rankPointsApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'input_login.cpp') -PathType Leaf)) {
    $rankPointsResult = & $rankPointsApply -SourceDir $engineGameSource
    if ($rankPointsResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} rank points edit(s).' -f $rankPointsResult.Applied) -ForegroundColor DarkGray
    }
}

# The quest reward overrides (server-patches/questrewards,
# MT2009_PLUS_QUEST_REWARD_OVERRIDES_V1): the Seban panel's "Questy" rules -
# another item, count, yang, experience or Biologist bonus, and extra rewards -
# through one call of playerbot_quest_rewards.h (overlay) in each of the quests'
# reward functions (questlua_pc.cpp, questlua_affect.cpp) and at set_state
# (questlua_quest.cpp, questlua_global.cpp). After clearmissions, whose include
# line in questlua_pc.cpp it sits near.
$questRewardsApply = Join-Path $repo 'server-patches/questrewards/Apply-QuestRewardsPatch.ps1'
if ((Test-Path -LiteralPath $questRewardsApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'questlua_quest.cpp') -PathType Leaf)) {
    $questRewardsResult = & $questRewardsApply -SourceDir $engineGameSource
    if ($questRewardsResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} quest reward override edit(s).' -f $questRewardsResult.Applied) -ForegroundColor DarkGray
    }
}
# The Arezzo costume sets' sash skins (server-patches/azcostume,
# MT2009_PLUS_AREZZO_COSTUME_SETS_V1): a skin (85200-85299) dragged onto a sash
# puts its vnum in the sash's socket 2 (char_item.cpp UseItemEx), the sash shows
# it (item.h GetAcceVnum) and keeps it through Uriel's combination (char.cpp).
# MT2009_PLUS_AREZZO_COSTUME_SETS_V2: the ItemShop lists and sells the sets only while the
# Arezzo module is on (itemshop_manager.cpp; the vnums: overlay playerbot_arezzo_costumes.h).
# Its anchors are the engine's own lines.
$azCostumeApply = Join-Path $repo 'server-patches/azcostume/Apply-AzCostumePatch.ps1'
if ((Test-Path -LiteralPath $azCostumeApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item.h') -PathType Leaf)) {
    $azCostumeResult = & $azCostumeApply -SourceDir $engineGameSource
    if ($azCostumeResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Arezzo sash skin edit(s).' -f $azCostumeResult.Applied) -ForegroundColor DarkGray
    }
}
# The companion's "Drop: tylko dla mnie" (server-patches/sidekicknoloot,
# MT2009_PLUS_SIDEKICK_NO_LOOT_V1): a drop's share that falls to a companion
# whose owner switched the split off goes to the owner (char_battle.cpp,
# CHARACTER::Reward), so do the owner's pick-up of a drop under its name
# (char_item.cpp, PickupItem's party branch) and its Cor and cloth
# (item_manager.cpp). After rankpoints and botrareshare, whose lines it sits
# beside; the rest is the overlay's playerbot_sidekick.h.
$sidekickNoLootApply = Join-Path $repo 'server-patches/sidekicknoloot/Apply-SidekickNoLootPatch.ps1'
if ((Test-Path -LiteralPath $sidekickNoLootApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_battle.cpp') -PathType Leaf)) {
    $sidekickNoLootResult = & $sidekickNoLootApply -SourceDir $engineGameSource
    if ($sidekickNoLootResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} companion loot share edit(s).' -f $sidekickNoLootResult.Applied) -ForegroundColor DarkGray
    }
}
# Yang limits (server-patches/yanglimits, "Autor: Digi Rasta", nowy-system
# v0.26.0, MT2009_PLUS_YANG_LIMITS_V1): GOLD_MAX 100 bn in the pocket,
# EXCHANGE_GOLD_MAX 10 bn in one trade, SHOP_PRICE_MAX 50 bn for one line of a
# player's shop (common/length.h, reached as ../../common/length.h); a
# playerbot's purse stays at PLAYERBOT_GOLD_MAX 2 bn (char.cpp ChangeGold).
# input_main.cpp, shop_manager.cpp, char_shop.cpp, ikarus_shop_manager.cpp.
$yangLimitsApply = Join-Path $repo 'server-patches/yanglimits/Apply-YangLimitsPatch.ps1'
if ((Test-Path -LiteralPath $yangLimitsApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource '../../common/length.h') -PathType Leaf)) {
    $yangLimitsResult = & $yangLimitsApply -SourceDir $engineGameSource
    if ($yangLimitsResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} yang limit edit(s).' -f $yangLimitsResult.Applied) -ForegroundColor DarkGray
    }
}
# Elements and talismans (server-patches/zywioly, "Autor: Digi Rasta", nowy-system
# 0.28.0, MT2009_PLUS_ELEMENTS_V1): the six element powers as server-only points
# 178-183 (common/length.h, packet.h, char.cpp), the damage hook in CalcAttBonus
# (battle.cpp), /state (cmd_gm.cpp), the talisman drop of the element bosses
# (char_battle.cpp, beside digirasta's awakening drop) and the refine material of
# the item's own vnum (char_item.cpp, after playerqol's goblin and digirasta-fixes'
# stack lines in DoRefine). Last, so every edit it sits beside is there; the work
# is the overlay's playerbot_elements.cpp.
$zywiolyApply = Join-Path $repo 'server-patches/zywioly/Apply-ZywiolyPatch.ps1'
if ((Test-Path -LiteralPath $zywiolyApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'battle.cpp') -PathType Leaf)) {
    $zywiolyResult = & $zywiolyApply -SourceDir $engineGameSource
    if ($zywiolyResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} elements and talismans edit(s).' -f $zywiolyResult.Applied) -ForegroundColor DarkGray
    }
}
# The special items' experience (server-patches/specialexp, "Autor: Digi Rasta",
# nowy-system 0.28.1, MT2009_PLUS_NS_SPECIAL_EXP_V1): POINT_RAMADAN_CANDY_BONUS_EXP
# adds up in CHARACTER::PointChange (char.cpp) instead of being set, so the rings',
# the lollipop's, the medal's and the amulet's fixed +30% / +50% experience
# (special_item_group.unique_attr.txt, point 127) comes off with the item.
$specialExpApply = Join-Path $repo 'server-patches/specialexp/Apply-SpecialExpPatch.ps1'
if ((Test-Path -LiteralPath $specialExpApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char.cpp') -PathType Leaf)) {
    $specialExpResult = & $specialExpApply -SourceDir $engineGameSource
    if ($specialExpResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} special item experience edit(s).' -f $specialExpResult.Applied) -ForegroundColor DarkGray
    }
}

# Swiatynia Zodiaku (server-patches/zodiak, "Autor: Digi Rasta", nowy-system 0.35.0,
# MT2009_PLUS_ZODIAC_V1): 65 short hooks in 24 engine files (char, party, dungeon,
# regen, battle, quest, commands, login, shop; packet GC 220, chat types 13-15,
# AFFECT_CZ_UNLIMIT_ENTER 600) and ENABLE_12ZI last in CommonDefines.h. The work is
# the overlay's playerbot_zodiac_*. After every other patch: its anchors are lines
# the others leave or add.
$zodiakApply = Join-Path $repo 'server-patches/zodiak/Apply-ZodiakPatch.ps1'
if ((Test-Path -LiteralPath $zodiakApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'regen.cpp') -PathType Leaf)) {
    $zodiakResult = & $zodiakApply -SourceDir $engineGameSource
    if ($zodiakResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Zodiac Temple edit(s).' -f $zodiakResult.Applied) -ForegroundColor DarkGray
    }
}
# Metins apart from bosses in the respawn settings (server-patches/regenmetin,
# MT2009_PLUS_REGEN_METIN_SPLIT_V1): a regen line with a Metin stone reads
# fastMetinSpawn(<map>) and m2_metin_count, a boss's line fastBossSpawn and
# m2_boss_count (regen.h, regen.cpp; the Easter metins' cap too). After the
# playerqol and Zodiac edits it sits beside.
$regenMetinApply = Join-Path $repo 'server-patches/regenmetin/Apply-RegenMetinPatch.ps1'
if ((Test-Path -LiteralPath $regenMetinApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'regen.cpp') -PathType Leaf)) {
    $regenMetinResult = & $regenMetinApply -SourceDir $engineGameSource
    if ($regenMetinResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Metin respawn edit(s).' -f $regenMetinResult.Applied) -ForegroundColor DarkGray
    }
}
# The chance of bonuses on dropped weapons and armour (server-patches/dropbonus,
# MT2009_PLUS_DROP_BONUS_PCT_V1): the event flag m2_drop_bonus_pct, a percent of
# the game's own chance, for monster drops only (item_manager.cpp CreateItem and
# SetDropRarePct, item.cpp AlterToMagicItem).
$dropBonusApply = Join-Path $repo 'server-patches/dropbonus/Apply-DropBonusPatch.ps1'
if ((Test-Path -LiteralPath $dropBonusApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item_manager.cpp') -PathType Leaf)) {
    $dropBonusResult = & $dropBonusApply -SourceDir $engineGameSource
    if ($dropBonusResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} drop bonus chance edit(s).' -f $dropBonusResult.Applied) -ForegroundColor DarkGray
    }
}
# The shop search's bounded result list (server-patches/flealimit,
# MT2009_PLUS_FLEA_MARKET_BOUND_V1): a search by filters alone no longer takes
# every listing of the world into memory (ikarus_shop_manager.cpp).
$fleaLimitApply = Join-Path $repo 'server-patches/flealimit/Apply-FleaLimitPatch.ps1'
if ((Test-Path -LiteralPath $fleaLimitApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'ikarus_shop_manager.cpp') -PathType Leaf)) {
    $fleaLimitResult = & $fleaLimitApply -SourceDir $engineGameSource
    if ($fleaLimitResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} shop search bound edit(s).' -f $fleaLimitResult.Applied) -ForegroundColor DarkGray
    }
}
# The way out of a guild war arena (server-patches/guildwarexit, MT2009_PLUS_GUILD_WAR_EXIT_V1,
# Autor: Krystian): char.cpp ExitToSavedLocation / leave_guild_war_event, war_map.cpp.
$guildWarExitApply = Join-Path $repo 'server-patches/guildwarexit/Apply-GuildWarExitPatch.ps1'
if ((Test-Path -LiteralPath $guildWarExitApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'war_map.cpp') -PathType Leaf)) {
    $guildWarExitResult = & $guildWarExitApply -SourceDir $engineGameSource
    if ($guildWarExitResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} guild war exit edit(s).' -f $guildWarExitResult.Applied) -ForegroundColor DarkGray
    }
}
# No fight of an onlooker on a guild war arena (server-patches/guildwarwatch,
# MT2009_PLUS_GUILD_WAR_WATCH_V1): battle.cpp battle_is_attackable.
$guildWarWatchApply = Join-Path $repo 'server-patches/guildwarwatch/Apply-GuildWarWatchPatch.ps1'
if ((Test-Path -LiteralPath $guildWarWatchApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'battle.cpp') -PathType Leaf)) {
    $guildWarWatchResult = & $guildWarWatchApply -SourceDir $engineGameSource
    if ($guildWarWatchResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} guild war watch edit(s).' -f $guildWarWatchResult.Applied) -ForegroundColor DarkGray
    }
}
# No rank penalty for a guild war's kill, the deaths after the war's end and on the arena included
# (server-patches/warrankkeep, MT2009_PLUS_WAR_RANK_KEEP_V1): char_battle.cpp Dead, guild_war.cpp EndWar.
$warRankKeepApply = Join-Path $repo 'server-patches/warrankkeep/Apply-WarRankKeepPatch.ps1'
if ((Test-Path -LiteralPath $warRankKeepApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'guild_war.cpp') -PathType Leaf)) {
    $warRankKeepResult = & $warRankKeepApply -SourceDir $engineGameSource
    if ($warRankKeepResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} war rank keep edit(s).' -f $warRankKeepResult.Applied) -ForegroundColor DarkGray
    }
}
# The Combo skill remembered over a relog, a teleport and a channel change
# (server-patches/combosave, MT2009_PLUS_COMBO_SAVE_V1, Autor: Mur4s).
$comboSaveApply = Join-Path $repo 'server-patches/combosave/Apply-ComboSavePatch.ps1'
if ((Test-Path -LiteralPath $comboSaveApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'input_login.cpp') -PathType Leaf)) {
    $comboSaveResult = & $comboSaveApply -SourceDir $engineGameSource
    if ($comboSaveResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} combo save edit(s).' -f $comboSaveResult.Applied) -ForegroundColor DarkGray
    }
}
# The Auction House (Dom Aukcyjny, AH_V1) and the mini games' "Liczba gier" row
# (MT2009_PLUS_PLAY_COUNT_V1), Autor: Vekirion (server-patches/auctionhouse): the /ah_* and
# /minigame_count commands in cmd.cpp, the buy hooks in ikarus_shop_manager.cpp. The rest is the
# overlay's auction_house.cpp and playerbot_{rumi,yutnori,catchking,wheel}.h.
$auctionHouseApply = Join-Path $repo 'server-patches/auctionhouse/Apply-AuctionHousePatch.ps1'
if ((Test-Path -LiteralPath $auctionHouseApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'ikarus_shop_manager.cpp') -PathType Leaf)) {
    $auctionHouseResult = & $auctionHouseApply -SourceDir $engineGameSource
    if ($auctionHouseResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} auction house edit(s).' -f $auctionHouseResult.Applied) -ForegroundColor DarkGray
    }
}
# The pick-up filter's detailed rules (MT2009_PLUS_PICKUP_RULES_V1, MT2009_PLUS_PICKUP_SYNC_V1),
# Autor: Vekirion (server-patches/pickuprules): /pickup_rules and /pickup_items in
# char_item.cpp, cmd_general.cpp and cmd.cpp, after playerqol's pick-up filter.
$pickupRulesApply = Join-Path $repo 'server-patches/pickuprules/Apply-PickupRulesPatch.ps1'
if ((Test-Path -LiteralPath $pickupRulesApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_item.cpp') -PathType Leaf)) {
    $pickupRulesResult = & $pickupRulesApply -SourceDir $engineGameSource
    if ($pickupRulesResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} pick-up rules edit(s).' -f $pickupRulesResult.Applied) -ForegroundColor DarkGray
    }
}
# The offline shops' second round (MT2009_PLUS_SHOP_QOL_V2) and the skill book's name in the
# shop's notices (MT2009_PLUS_SHOP_SOLD_BOOK_NAME_V1, MT2009_PLUS_SHOP_BOOK_NOTIFICATION_V1),
# Autor: Vekirion (server-patches/shopqol): new GD/DG subheaders in common/tables.h, so the
# game and db cores are built together; ikashop_qol.h comes from the overlay. After the
# auction house: its include line is the anchor in ikarus_shop_manager.cpp.
$shopQolApply = Join-Path $repo 'server-patches/shopqol/Apply-ShopQolPatch.ps1'
if ((Test-Path -LiteralPath $shopQolApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'ikarus_shop_manager.cpp') -PathType Leaf)) {
    $shopQolResult = & $shopQolApply -SourceDir $engineGameSource
    if ($shopQolResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} offline shop QoL edit(s).' -f $shopQolResult.Applied) -ForegroundColor DarkGray
    }
}
# Auto Lowy without the bots' revenge (server-patches/autohuntnorevenge,
# MT2009_PLUS_AUTOHUNT_NO_REVENGE_V1, Autor: mur4s): /autohunt_target and /autohunt_loot mark the
# person as hunting, /autohunt_stop ends it - cmd_general.cpp and cmd.cpp, after pickuprules
# (its unthrottled list). The rest is the overlay's playerbot_anti_pk.h.
$autoHuntNoRevengeApply = Join-Path $repo 'server-patches/autohuntnorevenge/Apply-AutoHuntNoRevengePatch.ps1'
if ((Test-Path -LiteralPath $autoHuntNoRevengeApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cmd_general.cpp') -PathType Leaf)) {
    $autoHuntNoRevengeResult = & $autoHuntNoRevengeApply -SourceDir $engineGameSource
    if ($autoHuntNoRevengeResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Auto Lowy no-revenge edit(s).' -f $autoHuntNoRevengeResult.Applied) -ForegroundColor DarkGray
    }
}
# The TEST auto hunt (server-patches/autohunttest, MT2009_PLUS_AUTOHUNT_TEST_V1; the owner, 28 October 2026): /autohunt_test
# tells root's uiautohunt_test.py (Alt+H) whether the exe's own hunt may run (event flags autohunt_test_off,
# autohunt_test_ticket) - cmd.cpp and cmd_general.cpp, after autohuntnorevenge (it anchors on /autohunt_stop).
$autoHuntTestApply = Join-Path $repo 'server-patches/autohunttest/Apply-AutoHuntTestPatch.ps1'
if ((Test-Path -LiteralPath $autoHuntTestApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cmd_general.cpp') -PathType Leaf)) {
    $autoHuntTestResult = & $autoHuntTestApply -SourceDir $engineGameSource
    if ($autoHuntTestResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} test auto hunt edit(s).' -f $autoHuntTestResult.Applied) -ForegroundColor DarkGray
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

# Obrona Statku / Hydra (server-patches/shipdefense, MT2009_PLUS_SHIP_DEFENSE_V1): 22 short hooks
# in 11 engine files - the dungeon's destroy, d.kill_all and d.purge, the attack, damage, death and
# aggro of the ship's monsters, the mast as a target (pvp.cpp), the attack ranges and the lasers'
# fields (char.cpp), the entry (input_login.cpp), the waves' respawn (regen.cpp), the AI with nobody
# near (sectree.cpp, char_state.cpp), the quests' "dw" module and the GM command /dw; in char_item.cpp
# Skrzynia Hydry's three openings. The work is
# the overlay's playerbot_ship_defense*. Last: its anchors are lines the Blue Dragon, Goblin and
# Zodiac edits leave or add.
$shipDefenseApply = Join-Path $repo 'server-patches/shipdefense/Apply-ShipDefensePatch.ps1'
if ((Test-Path -LiteralPath $shipDefenseApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'dungeon.cpp') -PathType Leaf)) {
    $shipDefenseResult = & $shipDefenseApply -SourceDir $engineGameSource
    if ($shipDefenseResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Ship Defense (Hydra) edit(s).' -f $shipDefenseResult.Applied) -ForegroundColor DarkGray
    }
}

# Poziom Czempiona + Sung Ma (server-patches/czempion, MT2009_PLUS_CHAMPION_V1 / MT2009_PLUS_SUNGMA_V1): the
# player table's eight champion columns (common tables.h, db ClientManagerPlayer.cpp load/save - db and game
# from the same header), POINT_SUNGMA_* after the elements (server-only), the champion level and its experience
# (char.h/char.cpp, char_battle.cpp DistributeExp), the bar filling at the top level, the Sung Ma map penalties
# (max HP, move speed, damage, poison/fire/bleeding, no attack without the level), /conqueror_stat, /champion,
# the quests' pc.*conqueror* / pc.*sungma* and ENABLE_CONQUEROR_LEVEL last in CommonDefines.h. The work is the
# overlay's playerbot_champion.*. After Obrona Statku: its cmd.cpp and questlua.cpp anchors sit beside those.
$czempionApply = Join-Path $repo 'server-patches/czempion/Apply-CzempionPatch.ps1'
if ((Test-Path -LiteralPath $czempionApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_resist.cpp') -PathType Leaf)) {
    $czempionResult = & $czempionApply -SourceDir $engineGameSource
    if ($czempionResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Champion level (Sung Ma) edit(s).' -f $czempionResult.Applied) -ForegroundColor DarkGray
    }
}

# Talizmany Woli (server-patches/talizmanwoli, MT2009_PLUS_WILL_TALISMAN_V1): the two standard bonus lines of the
# Will talismans 81000-81559 (Sung Ma Will, an element's power) in the 6th/7th bonus slots - rolled when one is made
# (item_manager.cpp CreateItem), carried at the new level and completed by a refine (item_attribute.cpp
# CopyAttributeTo), never touched by a 6/7 changer. After Poziom Czempiona: POINT_SUNGMA_* are its.
$talizmanWoliApply = Join-Path $repo 'server-patches/talizmanwoli/Apply-TalizmanWoliPatch.ps1'
if ((Test-Path -LiteralPath $talizmanWoliApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item_attribute.cpp') -PathType Leaf)) {
    $talizmanWoliResult = & $talizmanWoliApply -SourceDir $engineGameSource
    if ($talizmanWoliResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Will talisman edit(s).' -f $talizmanWoliResult.Applied) -ForegroundColor DarkGray
    }
}

# Obrecze Jadeitu (server-patches/obreczjadeitu, MT2009_PLUS_JADE_BRACELET_V1): the Sung Ma Will line of the jade
# bracelets 14580-14619 in the 6th bonus slot - rolled when one is made, carried and completed by a refine, never
# touched by a 6/7 changer. After the Will talismans: its edits sit next to theirs and use their chance flags.
$obreczJadeituApply = Join-Path $repo 'server-patches/obreczjadeitu/Apply-ObreczJadeituPatch.ps1'
if ((Test-Path -LiteralPath $obreczJadeituApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item_attribute.cpp') -PathType Leaf)) {
    $obreczJadeituResult = & $obreczJadeituApply -SourceDir $engineGameSource
    if ($obreczJadeituResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} jade bracelet edit(s).' -f $obreczJadeituResult.Applied) -ForegroundColor DarkGray
    }
}

# Zyly Jadeitu (server-patches/jadeit, MT2009_PLUS_JADE_VEINS_V1): the four jade veins of Yohara (30310-30313 ->
# Ruda Jadeitu 50641-50644 -> 50661-50664) in mining.cpp's ore table, so a pickaxe mines them (quest yohara_mapy2).
$jadeitApply = Join-Path $repo 'server-patches/jadeit/Apply-JadeitPatch.ps1'
if ((Test-Path -LiteralPath $jadeitApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'mining.cpp') -PathType Leaf)) {
    $jadeitResult = & $jadeitApply -SourceDir $engineGameSource
    if ($jadeitResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} jade vein edit(s).' -f $jadeitResult.Applied) -ForegroundColor DarkGray
    }
}

# Zestawy Yohary (server-patches/ysets, MT2009_PLUS_YOHARA_SETS_V1): the set effects of the set blacksmiths (cube
# set_value / set_part), the set bonus of the worn weapon / armour / helmet, the serpent gear's three random base
# bonuses - each item's "yextra" in player.item_yextra (mariadb/playerbot/yohara_sets.sql), the client's tooltip
# hears it by "YITEM". After Talizmany Woli (its anchors in item_manager.cpp / item_attribute.cpp come first).
$ysetsApply = Join-Path $repo 'server-patches/ysets/Apply-YSetsPatch.ps1'
if ((Test-Path -LiteralPath $ysetsApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cube.cpp') -PathType Leaf)) {
    $ysetsResult = & $ysetsApply -SourceDir $engineGameSource
    if ($ysetsResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Yohara set edit(s).' -f $ysetsResult.Applied) -ForegroundColor DarkGray
    }
}

# Strefy na ziemi (server-patches/strefy, MT2009_PLUS_DUNGEON_ZONE_V1): d.zone_attack / d.zone_hurt - telegraphed ground
# zones of a dungeon (an invisible marker 3975 with the warning effect, then real damage to the players inside; a kill
# is a real death) for Glebie Polnocnego Wiatru (ice spikes, Deadly Cold) and Swiatynia Wezy (surface attack).
$strefyApply = Join-Path $repo 'server-patches/strefy/Apply-StrefyPatch.ps1'
if ((Test-Path -LiteralPath $strefyApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'questlua_dungeon.cpp') -PathType Leaf)) {
    $strefyResult = & $strefyApply -SourceDir $engineGameSource
    if ($strefyResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} ground zone edit(s).' -f $strefyResult.Applied) -ForegroundColor DarkGray
    }
}

# Wieza Sung Mahi (server-patches/wiezasm, MT2009_PLUS_SMH_TOWER_V1): the tower's curse "Umiejetnosci sa zablokowane"
# (affect 1849, quest wieza_sung_mahi) refuses every skill in char_skill.cpp's UseSkill. The floors' Sung Ma
# requirements are the overlay's (playerbot_champion.cpp, d.set_sungma).
# MT2009_PLUS_QUEST_USE_V1: char_item.cpp - an ITEM_QUEST item with ITEM_FLAG_QUEST_USE reaches its quest "use" too.
$wiezaSmApply = Join-Path $repo 'server-patches/wiezasm/Apply-WiezaSmPatch.ps1'
if ((Test-Path -LiteralPath $wiezaSmApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_skill.cpp') -PathType Leaf)) {
    $wiezaSmResult = & $wiezaSmApply -SourceDir $engineGameSource
    if ($wiezaSmResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Sung Mahi tower edit(s).' -f $wiezaSmResult.Applied) -ForegroundColor DarkGray
    }
}

# Transmutacja (server-patches/transmutacja, MT2009_PLUS_CHANGE_LOOK_V1): the look of an item - TPlayerItem /
# player.item.transmutation (db and game from one header; transmutacja.sql before the db core), the item packets of
# the 3.0 exe, the worn looks as the parts, the mount of a polymorphed seal, the equip check, Anulacja Transmutacji,
# the window at Teowaden (/transmutacja, game.open_changelook) and the Ikarus shop's own ENABLE_CHANGELOOK_SYSTEM
# lines (ENABLE_CHANGELOOK_SYSTEM last in CommonDefines.h). The work is the overlay's playerbot_changelook.cpp. After
# playerqol ("Ukryj cudze" shows the looks) and the Yohara sets (safebox.cpp).
$transmutacjaApply = Join-Path $repo 'server-patches/transmutacja/Apply-TransmutacjaPatch.ps1'
if ((Test-Path -LiteralPath $transmutacjaApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'MountSystem.cpp') -PathType Leaf)) {
    $transmutacjaResult = & $transmutacjaApply -SourceDir $engineGameSource
    if ($transmutacjaResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Transmutation edit(s).' -f $transmutacjaResult.Applied) -ForegroundColor DarkGray
    }
}

# Ukryj kostium (server-patches/ukryjkostium, MT2009_PLUS_HIDE_COSTUME_V1): Owsap's hiding of the costume, hairstyle,
# weapon skin and sash per character (quest flags costume_option.*) in the add/update packets' parts, /hide_costume_part,
# the login's state and playerqol's old /kostiumy_ukryj taken once. The work is playerbot_hidecostume.cpp. After
# Transmutacja (a hidden costume shows the armour's look).
$ukryjKostiumApply = Join-Path $repo 'server-patches/ukryjkostium/Apply-UkryjkostiumPatch.ps1'
if ((Test-Path -LiteralPath $ukryjKostiumApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'input_login.cpp') -PathType Leaf)) {
    $ukryjKostiumResult = & $ukryjKostiumApply -SourceDir $engineGameSource
    if ($ukryjKostiumResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} costume hiding edit(s).' -f $ukryjKostiumResult.Applied) -ForegroundColor DarkGray
    }
}

# Gaya (server-patches/gaya, MT2009_PLUS_GAYA_V1): a cube recipe's "gaya N" - N of the Gaya item (95927, quest ygaya)
# from the inventory, checked first and taken with the materials (the set blacksmiths, Statua Wezy, the elemental pet
# chests of Statua Wojownika). After Zestawy Yohary (one edit is in its Mt2009YSetsCubeMake).
$gayaApply = Join-Path $repo 'server-patches/gaya/Apply-GayaPatch.ps1'
if ((Test-Path -LiteralPath $gayaApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cube.cpp') -PathType Leaf)) {
    $gayaResult = & $gayaApply -SourceDir $engineGameSource
    if ($gayaResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Gaya edit(s).' -f $gayaResult.Applied) -ForegroundColor DarkGray
    }
}

# Helmy na 100 poziom (server-patches/yhelm100, MT2009_PLUS_HELM100_CUBE_V1): a cube recipe's "fail_keep <vnum>" - that
# item of the recipe stays on a failure (Straznik Smokow Jaharr's Dragona helmets, cube.helm100.txt). After Gaya (it
# calls its helpers).
$yhelm100Apply = Join-Path $repo 'server-patches/yhelm100/Apply-YHelm100Patch.ps1'
if ((Test-Path -LiteralPath $yhelm100Apply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cube.cpp') -PathType Leaf)) {
    $yhelm100Result = & $yhelm100Apply -SourceDir $engineGameSource
    if ($yhelm100Result.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} level-100 helmet cube edit(s).' -f $yhelm100Result.Applied) -ForegroundColor DarkGray
    }
}

# Przebudzeni bossowie (server-patches/przebudzeni, MT2009_PLUS_YOHARA_PB_V1): Metin Chlodu (PB) (8135) takes damage only
# from a Shaman, Kolumna Smoka Polnocy (PB) (20538) only from a Shaman or a Ninja (the pl-wiki) - CHARACTER::Damage in
# char_battle.cpp. The dungeons themselves are quests (razador_pb, nemere_pb, przebudzeni_bossowie).
$przebudzeniApply = Join-Path $repo 'server-patches/przebudzeni/Apply-PrzebudzeniPatch.ps1'
if ((Test-Path -LiteralPath $przebudzeniApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_battle.cpp') -PathType Leaf)) {
    $przebudzeniResult = & $przebudzeniApply -SourceDir $engineGameSource
    if ($przebudzeniResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} awakened bosses edit(s).' -f $przebudzeniResult.Applied) -ForegroundColor DarkGray
    }
}

# Umiejetnosci 9. (server-patches/skill9, MT2009_PLUS_SKILL9_V1): the 9th skills of Yohara (skill_proto 176-182,
# yskill9.sql) - their vnums, the books from level 0 for a Champion (Champion experience a read), the motions 9/24,
# the shots, Meteor on cast and Tarcza Eteru's protection (affect 608). The logic is playerbot_skill9.cpp. After
# Poziom Czempiona: the books ask the champion level and experience.
$skill9Apply = Join-Path $repo 'server-patches/skill9/Apply-Skill9Patch.ps1'
if ((Test-Path -LiteralPath $skill9Apply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_skill.cpp') -PathType Leaf)) {
    $skill9Result = & $skill9Apply -SourceDir $engineGameSource
    if ($skill9Result.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} 9th skill edit(s).' -f $skill9Result.Applied) -ForegroundColor DarkGray
    }
}

# Szczelina Czasu (server-patches/szczelina, MT2009_PLUS_YOHARA_CRACK_V1): nothing drops in the Time Rift dungeons (map
# 404, the pl-wiki: "potwory nie daja dropu") but the yang of a mob_proto row that has it (Jotun Thrym (SZC)) -
# CHARACTER::Reward in char_battle.cpp. The dungeon itself is quests (szczelina_czasu, jotun_szc).
$szczelinaApply = Join-Path $repo 'server-patches/szczelina/Apply-SzczelinaPatch.ps1'
if ((Test-Path -LiteralPath $szczelinaApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_battle.cpp') -PathType Leaf)) {
    $szczelinaResult = & $szczelinaApply -SourceDir $engineGameSource
    if ($szczelinaResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Time Rift edit(s).' -f $szczelinaResult.Applied) -ForegroundColor DarkGray
    }
}
# M2_BONUS_MODE (server-patches/bonusyglobal, MT2009_PLUS_GLOBAL_BONUS_V1): mt2009 or the global server's bonuses
# (Tieru's 2.2.31) - the double-item chance line in the drop (item_manager.cpp) and a talisman's own resistance
# values (item_attribute.cpp, CItem::AddAttr); the work is the overlay's playerbot_bonus_mode.cpp (event flag
# m2_bonus_global), the element resistance at 30% is playerbot_elements.cpp. After zywioly and szczelina.
$bonusyGlobalApply = Join-Path $repo 'server-patches/bonusyglobal/Apply-BonusyGlobalPatch.ps1'
if ((Test-Path -LiteralPath $bonusyGlobalApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item_manager.cpp') -PathType Leaf)) {
    $bonusyGlobalResult = & $bonusyGlobalApply -SourceDir $engineGameSource
    if ($bonusyGlobalResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} bonus mode edit(s).' -f $bonusyGlobalResult.Applied) -ForegroundColor DarkGray
    }
}

# Rudy poza mapa swiata (server-patches/oreatlas, MT2009_PLUS_ORE_ATLAS_V1): an ore vein (mining.cpp's table - the
# jade veins of Yohara 30310-30313 and every other) is an NPC by type, but gets no mark on the world map (regen.cpp,
# beside the hidden NPC 20403) - as in the official game.
$oreAtlasApply = Join-Path $repo 'server-patches/oreatlas/Apply-OreAtlasPatch.ps1'
if ((Test-Path -LiteralPath $oreAtlasApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'regen.cpp') -PathType Leaf)) {
    $oreAtlasResult = & $oreAtlasApply -SourceDir $engineGameSource
    if ($oreAtlasResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} ore-vein atlas edit(s).' -f $oreAtlasResult.Applied) -ForegroundColor DarkGray
    }
}

# Precyzja i procentowe bonusy Sung Ma (server-patches/precyzja, MT2009_PLUS_PRECISION_V1): points 193-197 after
# POINT_PACKET_NUM (POINT_SUNGMA_PER_*, POINT_HIT_PCT - the points packet keeps 193), their point change to the
# client, FLY_CONQUEROR_EXP; the passive skill Precyzja (246, Ksiega Precyzji 50325 - MT2009_PLUS_PRECISION_SKILL_V1).
# The logic is playerbot_champion.cpp / playerbot_yohara_gear.cpp.
$precyzjaApply = Join-Path $repo 'server-patches/precyzja/Apply-PrecyzjaPatch.ps1'
if ((Test-Path -LiteralPath $precyzjaApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char.cpp') -PathType Leaf)) {
    $precyzjaResult = & $precyzjaApply -SourceDir $engineGameSource
    if ($precyzjaResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Precision edit(s).' -f $precyzjaResult.Applied) -ForegroundColor DarkGray
    }
}

# Rekawice Sung Ma (server-patches/rekawice, MT2009_PLUS_GLOVES_V1): the glove slot (ENABLE_GLOVE_SYSTEM), the
# glove's Will line, Kamienie Demonow (METIN_SUNGMA) in its sockets. After precyzja.
$rekawiceApply = Join-Path $repo 'server-patches/rekawice/Apply-RekawicePatch.ps1'
if ((Test-Path -LiteralPath $rekawiceApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item.cpp') -PathType Leaf)) {
    $rekawiceResult = & $rekawiceApply -SourceDir $engineGameSource
    if ($rekawiceResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} glove edit(s).' -f $rekawiceResult.Applied) -ForegroundColor DarkGray
    }
}

# Obrecze Jadeitu V2 (server-patches/obreczjadeitu2, MT2009_PLUS_JADE_BRACELET_V2): two random base lines
# (Precyzja, Wola) with the wiki's ranges, the jade in the Diamond's sockets. After obreczjadeitu, precyzja, rekawice.
$obreczJadeitu2Apply = Join-Path $repo 'server-patches/obreczjadeitu2/Apply-ObreczJadeitu2Patch.ps1'
if ((Test-Path -LiteralPath $obreczJadeitu2Apply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item.cpp') -PathType Leaf)) {
    $obreczJadeitu2Result = & $obreczJadeitu2Apply -SourceDir $engineGameSource
    if ($obreczJadeitu2Result.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} jade bracelet V2 edit(s).' -f $obreczJadeitu2Result.Applied) -ForegroundColor DarkGray
    }
}

# Szata Aury (server-patches/aura, MT2009_PLUS_AURA_V1): the aura outfit's costume slot (WEAR_COSTUME_AURA 27,
# COSTUME_AURA 5), its points (the absorbed jewel's / shield's bonuses at level / 10 %), Theowahdan's windows (/aura,
# game.open_aura), Swiadectwo Aury+, the outfit the others see ("AURA view", the 3.0 exe) and Lodowa Runa Aury from the
# monsters. The work is the overlay's playerbot_aura.cpp. After transmutacja and ukryjkostium (its anchors and the
# aura's eye), rankpoints and rekawice.
$auraApply = Join-Path $repo 'server-patches/aura/Apply-AuraPatch.ps1'
if ((Test-Path -LiteralPath $auraApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item.cpp') -PathType Leaf)) {
    $auraResult = & $auraApply -SourceDir $engineGameSource
    if ($auraResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} aura outfit edit(s).' -f $auraResult.Applied) -ForegroundColor DarkGray
    }
}

# The costume sets as on the global server (server-patches/zestawy, MT2009_PLUS_COSTUME_SET_V2; the owner, 20 October
# 2026): the "#Z" sets of costume_sets.txt - parts (costume, hair, weapon skin, pet, mount, ring/amulet, sash), grades
# by the parts worn and each grade's bonuses as affect 545; judged when a set's item goes on or off and at the end of
# the outermost ComputePoints; the drop chance in GetDropPct. Replaces playerqol's V1 judge, so after playerqol; last.
$zestawyApply = Join-Path $repo 'server-patches/zestawy/Apply-ZestawyPatch.ps1'
if ((Test-Path -LiteralPath $zestawyApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item.cpp') -PathType Leaf)) {
    $zestawyResult = & $zestawyApply -SourceDir $engineGameSource
    if ($zestawyResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} costume set edit(s).' -f $zestawyResult.Applied) -ForegroundColor DarkGray
    }
}

# The ItemShop wheels' Kamien Rytualny (server-patches/kolaprzedmioty, MT2009_PLUS_KOLA_ITEMS_V1; the owner, 20 October
# 2026): the global server's Ritual Stone (25046 here - our 25042 is Magiczny Kamien) - the Magic Stone's protection with
# +15%, only on an item above level 80 (the refine by scroll and its roll). Last.
$kolaItemsApply = Join-Path $repo 'server-patches/kolaprzedmioty/Apply-KolaPrzedmiotyPatch.ps1'
if ((Test-Path -LiteralPath $kolaItemsApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_item.cpp') -PathType Leaf)) {
    $kolaItemsResult = & $kolaItemsApply -SourceDir $engineGameSource
    if ($kolaItemsResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} wheel item edit(s).' -f $kolaItemsResult.Applied) -ForegroundColor DarkGray
    }
}

# Bonusy 6/7 z wiki (server-patches/bonusy67, MT2009_PLUS_BONUS67_V1; the owner, 20 October 2026): the 6th/7th bonuses
# the engine lacked - points 198-251 (server-only), the element hit buffs, the "+x% of the total" lines, the boss lines,
# the 1st..5th bonus +x%, the gloves' lines (a glove's 7th slot from the pool). Changes lines of precyzja and rekawice,
# so after them. The logic is playerbot_bonus67.cpp.
$bonusy67Apply = Join-Path $repo 'server-patches/bonusy67/Apply-Bonusy67Patch.ps1'
if ((Test-Path -LiteralPath $bonusy67Apply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item_attribute.cpp') -PathType Leaf)) {
    $bonusy67Result = & $bonusy67Apply -SourceDir $engineGameSource
    if ($bonusy67Result.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} 6th/7th bonus edit(s).' -f $bonusy67Result.Applied) -ForegroundColor DarkGray
    }
}

# Riposty i Dopalacze (server-patches/riposty, MT2009_PLUS_RIPOSTY_V1; the owner, 21 October 2026): the passive 7th/8th
# skills of every character - skill_proto 221-228 / 236-243, their points, books and Kamien Duchowy+, the damage they
# take away / add. Anchors on skill9's and precyzja's code, so after them. The logic is playerbot_riposty.cpp.
$ripostyApply = Join-Path $repo 'server-patches/riposty/Apply-RipostyPatch.ps1'
if ((Test-Path -LiteralPath $ripostyApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_skill.cpp') -PathType Leaf)) {
    $ripostyResult = & $ripostyApply -SourceDir $engineGameSource
    if ($ripostyResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} riposte/boost edit(s).' -f $ripostyResult.Applied) -ForegroundColor DarkGray
    }
}

# Boss Swiata (server-patches/worldboss, MT2009_PLUS_WORLDBOSS_V1; the owner, 21 October 2026): the World Boss event -
# every player's damage to the boss (char_battle.cpp), no drop from its monsters, the loot tier's drop buff
# (item_manager.cpp) and "/worldboss" (cmd.cpp). Anchors on shipdefense's, zestawy's and ysets' lines, so after them.
# The logic is playerbot_worldboss.h.
$worldBossApply = Join-Path $repo 'server-patches/worldboss/Apply-WorldBossPatch.ps1'
if ((Test-Path -LiteralPath $worldBossApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_battle.cpp') -PathType Leaf)) {
    $worldBossResult = & $worldBossApply -SourceDir $engineGameSource
    if ($worldBossResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} World Boss edit(s).' -f $worldBossResult.Applied) -ForegroundColor DarkGray
    }
}

# Buffi (server-patches/buffi, MT2009_PLUS_BUFFI_V1; the owner, 21 October 2026): Ameria's support shaman in place of
# the companion - the seals and the name scroll in UseItemEx, the skills 164-167 learnable by every class and kept by a
# reset, the seal's buffi back at login, the shaman shown as a female shaman, /buffi. Anchors on the Monster Cards' and
# the ripostes' code, so after them. The logic is playerbot_buffi.cpp.
$buffiApply = Join-Path $repo 'server-patches/buffi/Apply-BuffiPatch.ps1'
if ((Test-Path -LiteralPath $buffiApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_skill.cpp') -PathType Leaf)) {
    $buffiResult = & $buffiApply -SourceDir $engineGameSource
    if ($buffiResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Buffi edit(s).' -f $buffiResult.Applied) -ForegroundColor DarkGray
    }
}

# Dodatkowy ekwipunek (server-patches/ekwipunek, MT2009_PLUS_EKWIPUNEK_V1; the owner, 21 October 2026): Ameria's special
# storage - five category storages (windows 11-15, common/length.h), the items of a category routed there for a real
# player whose client said so, the db's item queries (db/src/ClientManagerPlayer.cpp; player.item.window by apply.sh),
# "/ekwipunek". Anchors on Buffi's cmd.cpp lines, so after buffi. The logic is playerbot_ekwipunek.cpp.
$ekwipunekApply = Join-Path $repo 'server-patches/ekwipunek/Apply-EkwipunekPatch.ps1'
if ((Test-Path -LiteralPath $ekwipunekApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_item.cpp') -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource '../../db/src/ClientManagerPlayer.cpp') -PathType Leaf)) {
    $ekwipunekResult = & $ekwipunekApply -SourceDir $engineGameSource
    if ($ekwipunekResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} extra inventory edit(s).' -f $ekwipunekResult.Applied) -ForegroundColor DarkGray
    }
}

# Bonus Switcher (server-patches/switchbot, MT2009_PLUS_SWITCHBOT_V1; the owner, 21 October 2026): Ameria's switchbot
# instead of our "Zmiana bonusow" (MT2009_PLUS_BONUS_SWITCH_V1, server-patches/bonusswitch - removed; this step takes its
# cmd.cpp / cmd_general.cpp lines out of an engine that still has them). The window SWITCHBOT (16, common/length.h), the
# packets CG 170 / GC 171 / GG 39, the hooks of item move / use, warp, logout, equip and swap, "/switchbot". Anchors on
# the extra inventory's lines, so after ekwipunek. The logic is playerbot_switchbot.cpp.
$switchbotApply = Join-Path $repo 'server-patches/switchbot/Apply-SwitchbotPatch.ps1'
if ((Test-Path -LiteralPath $switchbotApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'input_main.cpp') -PathType Leaf)) {
    $switchbotResult = & $switchbotApply -SourceDir $engineGameSource
    if ($switchbotResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} switchbot edit(s), took out {1} old bonus switcher line(s).' -f $switchbotResult.Applied, $switchbotResult.Reverted) -ForegroundColor DarkGray
    }
}

# Seon-Pyeong (server-patches/seonpyeong, MT2009_PLUS_SEONPYEONG_ELITE_V1; the owner, 22 October 2026): his refine sets
# (IsEliteRefine) are 501 / 530 and the fixed recipes 39900-39999 of refine_global.sql (tools/refineglobal ELITE) - a +9
# piece dragged onto him becomes the next item; the guild smiths (20044-20046) and the Demon Tower's (20074-20076) refuse
# them as the Blacksmith and the scrolls do.
$seonpyeongApply = Join-Path $repo 'server-patches/seonpyeong/Apply-SeonPyeongPatch.ps1'
if ((Test-Path -LiteralPath $seonpyeongApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'constants.cpp') -PathType Leaf)) {
    $seonpyeongResult = & $seonpyeongApply -SourceDir $engineGameSource
    if ($seonpyeongResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Seon-Pyeong edit(s).' -f $seonpyeongResult.Applied) -ForegroundColor DarkGray
    }
}

# Account-bound items (server-patches/g0bind, MT2009_PLUS_ITEM_ACCOUNT_BOUND_V1; the owner, 22 October 2026): the bots'
# G0 package is bound to the account - CItem::IsAccountBound adds DROP / GIVE / SELL / MYSHOP / PKDROP to the item's own
# anti flags, the shops ask the instance's flags, a refine carries it. The store and the bots' logic are
# playerbot_yohara_g0.{h,cpp}. Anchors on the jade's refine line (obreczjadeitu2), so after it; last.
$g0bindApply = Join-Path $repo 'server-patches/g0bind/Apply-G0BindPatch.ps1'
if ((Test-Path -LiteralPath $g0bindApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item_attribute.cpp') -PathType Leaf)) {
    $g0bindResult = & $g0bindApply -SourceDir $engineGameSource
    if ($g0bindResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} account-bound item edit(s).' -f $g0bindResult.Applied) -ForegroundColor DarkGray
    }
}

# Bronie dla Mlodych Bohaterow (server-patches/mlodzi, MT2009_PLUS_MLODZI_BOHATEROWIE_V1; the owner, 22 October 2026): the
# quests' "mlodzi" module, nothing used on the weapons 21900-21975, no bonus change / addition in the item's own functions,
# no sash absorption. The logic is playerbot_mlodzi.{h,cpp}. Anchors on lines of talizmanwoli, switchbot and ship defense;
# last.
$mlodziApply = Join-Path $repo 'server-patches/mlodzi/Apply-MlodziPatch.ps1'
if ((Test-Path -LiteralPath $mlodziApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item_attribute.cpp') -PathType Leaf)) {
    $mlodziResult = & $mlodziApply -SourceDir $engineGameSource
    if ($mlodziResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} young heroes weapon edit(s).' -f $mlodziResult.Applied) -ForegroundColor DarkGray
    }
}

# Szklo Handlu (server-patches/szklohandlu, MT2009_PLUS_SZKLO_HANDLU_V1; the owner, 24 October 2026): while the item 72802
# (the second ItemShop, 7 / 15 / 30 days) is in the bag the Dom Aukcyjny works on any map - ikarus_shop_manager.cpp
# IsFleaMarketMap; the item's use (quest ishop_v3_przedmioty) opens the window.
$szkloHandluApply = Join-Path $repo 'server-patches/szklohandlu/Apply-SzkloHandluPatch.ps1'
if ((Test-Path -LiteralPath $szkloHandluApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'ikarus_shop_manager.cpp') -PathType Leaf)) {
    $szkloHandluResult = & $szkloHandluApply -SourceDir $engineGameSource
    if ($szkloHandluResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Szklo Handlu edit(s).' -f $szkloHandluResult.Applied) -ForegroundColor DarkGray
    }
}

# Auto Lowy 7 / 14 dni (server-patches/autohuntpass, MT2009_PLUS_AUTOHUNT_PASS_V1; the owner, 24 October 2026): calendar
# days - the real-time items 72800 / 72801 in the bag let the auto hunt run (cmd_general.cpp, target and loot).
$autoHuntPassApply = Join-Path $repo 'server-patches/autohuntpass/Apply-AutoHuntPassPatch.ps1'
if ((Test-Path -LiteralPath $autoHuntPassApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cmd_general.cpp') -PathType Leaf)) {
    $autoHuntPassResult = & $autoHuntPassApply -SourceDir $engineGameSource
    if ($autoHuntPassResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Auto Lowy pass edit(s).' -f $autoHuntPassResult.Applied) -ForegroundColor DarkGray
    }
}

# Auto Lowy reachability (server-patches/autohuntreach, MT2009_PLUS_AUTOHUNT_REACH_V1; the owner, 29 October 2026): a
# monster the hunter cannot walk to (another component of the bots' grid, only a grid already built) is never named
# (cmd_general.cpp, Mt2009PlusOffer of enginefixes' TRUE_NEAREST).
$autoHuntReachApply = Join-Path $repo 'server-patches/autohuntreach/Apply-AutoHuntReachPatch.ps1'
if ((Test-Path -LiteralPath $autoHuntReachApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cmd_general.cpp') -PathType Leaf)) {
    $autoHuntReachResult = & $autoHuntReachApply -SourceDir $engineGameSource
    if ($autoHuntReachResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Auto Lowy reachability edit(s).' -f $autoHuntReachResult.Applied) -ForegroundColor DarkGray
    }
}

# Kupon SM (100) from the Metin / boss coupon roll (server-patches/kupon100, MT2009_PLUS_DROP_COUPON_100_V1; the owner,
# 28 October 2026): 80014 in place of 80017 in the drop, the auto hunt's pick-up list, the preview and the drop wiki.
# Last: it anchors on raremobrules', playerqol's and dropwiki's 80017 lines.
$kupon100Apply = Join-Path $repo 'server-patches/kupon100/Apply-Kupon100Patch.ps1'
if ((Test-Path -LiteralPath $kupon100Apply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item_manager.cpp') -PathType Leaf)) {
    $kupon100Result = & $kupon100Apply -SourceDir $engineGameSource
    if ($kupon100Result.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Kupon SM (100) drop edit(s).' -f $kupon100Result.Applied) -ForegroundColor DarkGray
    }
}

# The Community window (server-patches/community, MT2009_PLUS_COMMUNITY_V1; Autor: Best Studio, "Community System
# (Messenger Renewal)"): the messenger's hooks, HEADER_GG_COMMUNITY 40, /community, the guild's member list; the logic is
# playerbot_community.cpp (the playerbot_* lines), the columns community.sql. After kupon100 (last).
$communityApply = Join-Path $repo 'server-patches/community/Apply-CommunityPatch.ps1'
if ((Test-Path -LiteralPath $communityApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'messenger_manager.cpp') -PathType Leaf)) {
    $communityResult = & $communityApply -SourceDir $engineGameSource
    if ($communityResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Community window edit(s).' -f $communityResult.Applied) -ForegroundColor DarkGray
    }
}

# Lokalizator NPC (server-patches/npcloc, MT2009_PLUS_NPC_LOCATION_HELPER_V1; Autor: Best Studio): the improved map's
# packet (header 196) and the activator 79667 - npc_location_helper.cpp/.h come with the overlay's game sources.
$npclocApply = Join-Path $repo 'server-patches/npcloc/Apply-NpcLocPatch.ps1'
if ((Test-Path -LiteralPath $npclocApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'input_main.cpp') -PathType Leaf)) {
    $npclocResult = & $npclocApply -SourceDir $engineGameSource
    if ($npclocResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Lokalizator NPC edit(s).' -f $npclocResult.Applied) -ForegroundColor DarkGray
    }
}

# Guild system update (server-patches/guildsys, MT2009_PLUS_GUILDSYS_V1; on Guild Systems compiled by Nazox): guild
# levels to 40, Balathor's guild skills 158-160 and their books, the guild's and the members' dates for the Balathor port
# (quest guild.check_requirements & co.) - guildsys.cpp/.h come with the overlay's game sources, the columns / skills /
# books with mariadb/playerbot/guildsys.sql. After npcloc; the Balathor patch comes after this one.
$guildsysApply = Join-Path $repo 'server-patches/guildsys/Apply-GuildSysPatch.ps1'
if ((Test-Path -LiteralPath $guildsysApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'guild.cpp') -PathType Leaf)) {
    $guildsysResult = & $guildsysApply -SourceDir $engineGameSource
    if ($guildsysResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} guild system edit(s).' -f $guildsysResult.Applied) -ForegroundColor DarkGray
    }
}

# Krypta Balathora (server-patches/balathor, MT2009_PLUS_BALATHOR_V1; author: dracaryS): the guild dungeon's hooks in
# game (and common/service.h, db's ClientManagerEventFlag.cpp) - balathor*.cpp/.h, questlua_balathor.cpp and json.hpp
# come with the overlay's game sources.
$balathorApply = Join-Path $repo 'server-patches/balathor/Apply-BalathorPatch.ps1'
if ((Test-Path -LiteralPath $balathorApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_battle.cpp') -PathType Leaf)) {
    $balathorResult = & $balathorApply -SourceDir $engineGameSource
    if ($balathorResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Krypta Balathora edit(s).' -f $balathorResult.Applied) -ForegroundColor DarkGray
    }
}

# Blyskawice rekawic 6/7 (server-patches/elecglove, MT2009_PLUS_ELEC_GLOVE_V1): SE_ELEC_ATTACK_HIT (54) in common
# length.h - the hit effect playerbot_bonus67.cpp sends to each monster the gloves' lightning strikes.
$elecgloveApply = Join-Path $repo 'server-patches/elecglove/Apply-ElecGlovePatch.ps1'
if ((Test-Path -LiteralPath $elecgloveApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource '../../common/length.h') -PathType Leaf)) {
    $elecgloveResult = & $elecgloveApply -SourceDir $engineGameSource
    if ($elecgloveResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} glove lightning effect edit(s).' -f $elecgloveResult.Applied) -ForegroundColor DarkGray
    }
}

# Gaya as a currency (server-patches/gaya2, MT2009_PLUS_GAYA_CURRENCY_V1): player.gaya (gaya2.sql), the counter next to
# the Yang, the item Gaya changed into it once, pc.get_gaya / pc.change_gaya, the cube's Gaya from the counter. After
# npcloc (last); it edits common/tables.h and db ClientManagerPlayer.cpp too, after czempion's champion columns.
$gaya2Apply = Join-Path $repo 'server-patches/gaya2/Apply-Gaya2Patch.ps1'
if ((Test-Path -LiteralPath $gaya2Apply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource '../../db/src/ClientManagerPlayer.cpp') -PathType Leaf)) {
    $gaya2Result = & $gaya2Apply -SourceDir $engineGameSource
    if ($gaya2Result.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Gaya currency edit(s).' -f $gaya2Result.Applied) -ForegroundColor DarkGray
    }
}

# Kamienie Antymagii (server-patches/antimagic, MT2009_PLUS_ANTI_RESIST_MAGIC_V1; the "Anti Magic penetrate stone"
# package): POINT_ANTI_RESIST_MAGIC (252) in common/length.h, the PvP magic resistance in char_skill.cpp, the metin
# stone draw and its preview, /state, db's ProtoReader name. After npcloc (last); bonusy67 comes before it.
$antimagicApply = Join-Path $repo 'server-patches/antimagic/Apply-AntiMagicPatch.ps1'
if ((Test-Path -LiteralPath $antimagicApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_skill.cpp') -PathType Leaf)) {
    $antimagicResult = & $antimagicApply -SourceDir $engineGameSource
    if ($antimagicResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Kamien Antymagii edit(s).' -f $antimagicResult.Applied) -ForegroundColor DarkGray
    }
}

# Bonusy 6/7 z wiki, runda 2 (server-patches/bonusy67b, MT2009_PLUS_BONUS67_WIKI_V1; the owner, 3 November 2026): the
# points 253-255 (POINT_RESIST_COMBAT, POINT_BLEEDING_PCT, POINT_BLEEDING_REDUCE - POINT_MAX_NUM 256) in common/length.h,
# their point change / point packet / login points in char.cpp, the bleeding in battle.cpp, the bleeding's stopped
# regeneration in char.cpp. Its anchors are antimagic's lines, so after it; the logic is playerbot_bonus67.cpp.
$bonusy67bApply = Join-Path $repo 'server-patches/bonusy67b/Apply-Bonusy67bPatch.ps1'
if ((Test-Path -LiteralPath $bonusy67bApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'battle.cpp') -PathType Leaf)) {
    $bonusy67bResult = & $bonusy67bApply -SourceDir $engineGameSource
    if ($bonusy67bResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} 6th/7th bonus round 2 edit(s).' -f $bonusy67bResult.Applied) -ForegroundColor DarkGray
    }
}

# Druga strona ekwipunku (server-patches/addeq, MT2009_PLUS_ADDEQ_V1; the "Official Additional Equipment Page" package,
# the owner, 28 October 2026): the inactive page's store (char.h cells 308-339 of window INVENTORY, never sent), its
# SetItem / RemoveFromCharacter / ClearItem / flush / item update hooks, the unlock items 38306 / 76055, the support skill
# 200 and "/addeq". Anchors on the extra inventory's and switchbot's lines, so the last one (after balathor). The logic
# is playerbot_addeq.cpp.
$addeqApply = Join-Path $repo 'server-patches/addeq/Apply-AddeqPatch.ps1'
if ((Test-Path -LiteralPath $addeqApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_item.cpp') -PathType Leaf)) {
    $addeqResult = & $addeqApply -SourceDir $engineGameSource
    if ($addeqResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} second equipment page edit(s).' -f $addeqResult.Applied) -ForegroundColor DarkGray
    }
}

# Magazyn Item-Shopu: 3 strony (server-patches/mall3, MT2009_PLUS_MALL_PAGES_V1; the owner, 29 October 2026): the
# client with the paged item-shop storage sends "/mall_password <password> 3", TSafeboxLoadPacket carries the page
# count to db, and item_award deliveries fill that many pages (an old client: page 1 only, as before). After addeq.
$mall3Apply = Join-Path $repo 'server-patches/mall3/Apply-Mall3Patch.ps1'
if ((Test-Path -LiteralPath $mall3Apply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'cmd_general.cpp') -PathType Leaf)) {
    $mall3Result = & $mall3Apply -SourceDir $engineGameSource
    if ($mall3Result.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} item-shop storage page edit(s).' -f $mall3Result.Applied) -ForegroundColor DarkGray
    }
}

# Wezowy Czepiec (server-patches/czepiec, MT2009_PLUS_SERPENT_HOOD_V1): the level-120 helmet's random second bonus in
# ysets' functions of item.cpp - after ysets (above).
$czepiecApply = Join-Path $repo 'server-patches/czepiec/Apply-CzepiecPatch.ps1'
if ((Test-Path -LiteralPath $czepiecApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item.cpp') -PathType Leaf)) {
    $czepiecResult = & $czepiecApply -SourceDir $engineGameSource
    if ($czepiecResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Wezowy Czepiec edit(s).' -f $czepiecResult.Applied) -ForegroundColor DarkGray
    }
}

# Event Super Kamieni (server-patches/superstone, MT2009_PLUS_SUPERSTONE_V1; the owner, 29 October 2026):
# superstone_event 1..4 puts that many extra stones beside every Metin stone SpawnMob puts down on a world map
# (char_manager.cpp, questmanager.cpp, common/service.h ENABLE_SUPERSTONE_EVENT). Last.
$superstoneApply = Join-Path $repo 'server-patches/superstone/Apply-SuperStonePatch.ps1'
if ((Test-Path -LiteralPath $superstoneApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_manager.cpp') -PathType Leaf)) {
    $superstoneResult = & $superstoneApply -SourceDir $engineGameSource
    if ($superstoneResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Super Kamienie edit(s).' -f $superstoneResult.Applied) -ForegroundColor DarkGray
    }
}

# Odnowione okno misji (server-patches/questren, MT2009_PLUS_QUEST_RENEWAL_V1; QUEST_RENEWAL, Autor: Owsap): the quest
# categories as "QuestCategory" command lines at the login (input_login.cpp after ChampionOnLogin) - the logic is
# playerbot_quest_renewal.cpp from the overlay's game sources. No packet change.
$questRenApply = Join-Path $repo 'server-patches/questren/Apply-QuestRenPatch.ps1'
if ((Test-Path -LiteralPath $questRenApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'input_login.cpp') -PathType Leaf)) {
    $questRenResult = & $questRenApply -SourceDir $engineGameSource
    if ($questRenResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} quest window edit(s).' -f $questRenResult.Applied) -ForegroundColor DarkGray
    }
}

# Damage Print Improve (server-patches/dmgprint, MT2009_PLUS_DAMAGE_PRINT_V1; Yohara 3.x): DAMAGE_ATTACKER_PC /
# DAMAGE_MISS in char.h and the damage packet's flag byte (char_battle.cpp) - no packet change. After superstone.
$dmgprintApply = Join-Path $repo 'server-patches/dmgprint/Apply-DmgPrintPatch.ps1'
if ((Test-Path -LiteralPath $dmgprintApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_battle.cpp') -PathType Leaf)) {
    $dmgprintResult = & $dmgprintApply -SourceDir $engineGameSource
    if ($dmgprintResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Damage Print edit(s).' -f $dmgprintResult.Applied) -ForegroundColor DarkGray
    }
}

# Zaczarowanie Zywiolu Broni (server-patches/zywiolbroni, MT2009_PLUS_WEAPON_ELEMENT_V1; the owner, 29 October 2026; based
# on the "[System] Elemental Spell" package by WorldArd): the hooks of weapon_element.cpp (the overlay) in item_manager /
# item_attribute / item / battle / char_item / char / input_login / safebox / exchange / shop / cmd. Anchors on ysets',
# aura's and addeq's lines, so after them (last).
$zywiolbroniApply = Join-Path $repo 'server-patches/zywiolbroni/Apply-ZywiolBroniPatch.ps1'
if ((Test-Path -LiteralPath $zywiolbroniApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item.cpp') -PathType Leaf)) {
    $zywiolbroniResult = & $zywiolbroniApply -SourceDir $engineGameSource
    if ($zywiolbroniResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} weapon element edit(s).' -f $zywiolbroniResult.Applied) -ForegroundColor DarkGray
    }
}

# Bonus Reliktu (server-patches/relikty, MT2009_PLUS_RELIC_V1; the "Official Passive Attr System" package, Best Studio;
# the owner, 29 October 2026): the relic pages (char.h cells 436-437 of window INVENTORY after addeq's four-page store, never
# sent), their SetItem / RemoveFromCharacter / ClearItem / flush / item update hooks, a relic used, the blows / death /
# skill / boss drop / mount lines and "/relikt". Anchors on addeq's store and bonusy67's lines - after dmgprint (last). The
# logic is playerbot_relikty.cpp.
$reliktyApply = Join-Path $repo 'server-patches/relikty/Apply-ReliktyPatch.ps1'
if ((Test-Path -LiteralPath $reliktyApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char.h') -PathType Leaf)) {
    $reliktyResult = & $reliktyApply -SourceDir $engineGameSource
    if ($reliktyResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} Bonus Reliktu edit(s).' -f $reliktyResult.Applied) -ForegroundColor DarkGray
    }
}

# Efekty zakladania pierscieni / amuletow / lizakow (server-patches/ringfx, MT2009_PLUS_RING_EFFECTS_V1; the owner, 30 October
# 2026): SE_EQUIP_WILL_RING..SE_EQUIP_GUARD_PENDANT (55-63, after elecglove's 54) in common/length.h, the vnum helpers in
# common/VnumHelper.h and the EffectPacket on equipping in char_item.cpp (after the Love Pendant). Last (on Linux after konie).
$ringfxApply = Join-Path $repo 'server-patches/ringfx/Apply-RingFxPatch.ps1'
if ((Test-Path -LiteralPath $ringfxApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_item.cpp') -PathType Leaf)) {
    $ringfxResult = & $ringfxApply -SourceDir $engineGameSource
    if ($ringfxResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} ring equip effect edit(s).' -f $ringfxResult.Applied) -ForegroundColor DarkGray
    }
}

# Event Rybacki - Puzzle (server-patches/fishpuzzle, MT2009_PLUS_FISH_PUZZLE_V1; the owner, 3 November 2026): a catch
# during the event may bring a puzzle box (fishing.cpp), the boxes open the window (char_item.cpp UseItemEx, under the
# relic's hook) and "/fishpuzzle" (cmd.cpp). The logic is fish_puzzle.cpp (the overlay). After relikty, e.g. last.
$fishPuzzleApply = Join-Path $repo 'server-patches/fishpuzzle/Apply-FishPuzzlePatch.ps1'
if ((Test-Path -LiteralPath $fishPuzzleApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'fishing.cpp') -PathType Leaf)) {
    $fishPuzzleResult = & $fishPuzzleApply -SourceDir $engineGameSource
    if ($fishPuzzleResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} fishing puzzle edit(s).' -f $fishPuzzleResult.Applied) -ForegroundColor DarkGray
    }
}

# The new fishing minigame (server-patches/fishren, MT2009_PLUS_FISHING_RENEWAL_V1; the owner, 3 November 2026): a
# client that said "/fishren hello" casts into the renewal's game (CHARACTER::fishing in char.cpp - after enginefixes'
# MT2009_PLUS_FISHING_FREE_V1), "/fishren" (cmd.cpp). The logic is fish_renewal.cpp (the overlay). After fishpuzzle.
$fishRenApply = Join-Path $repo 'server-patches/fishren/Apply-FishRenPatch.ps1'
if ((Test-Path -LiteralPath $fishRenApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char.cpp') -PathType Leaf)) {
    $fishRenResult = & $fishRenApply -SourceDir $engineGameSource
    if ($fishRenResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} fishing renewal edit(s).' -f $fishRenResult.Applied) -ForegroundColor DarkGray
    }
}

# A worn irremovable item asks whether to destroy it (server-patches/irrem, MT2009_PLUS_IRREMOVABLE_DELETE_V1; the
# owner, 3 November 2026): the player's own ItemUse / ItemMove (input_main.cpp - after switchbot's hooks) open a scope,
# CanUnequipNow's ITEM_FLAG_IRREMOVABLE branch and MoveItem's early test ask (char_item.cpp), "/irrem" (cmd.cpp). The
# logic is irremovable_delete.cpp (the overlay). After fishren.
$irremApply = Join-Path $repo 'server-patches/irrem/Apply-IrremPatch.ps1'
if ((Test-Path -LiteralPath $irremApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_item.cpp') -PathType Leaf)) {
    $irremResult = & $irremApply -SourceDir $engineGameSource
    if ($irremResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} irremovable item edit(s).' -f $irremResult.Applied) -ForegroundColor DarkGray
    }
}

# Dwubajtowy typ bonusu (server-patches/wideattr, MT2009_PLUS_WIDE_ATTR_V1; the owner, 3 November 2026): an item's
# bonus type (TPlayerItemAttribute::bType), an item_proto apply and an affect's point are WORD, POINT_MAX_NUM 512 - every
# packet with them grows (the exe of client-patches/exe the same). Its anchors are every other patch's lines: the LAST.
$wideattrApply = Join-Path $repo 'server-patches/wideattr/Apply-WideattrPatch.ps1'
if ((Test-Path -LiteralPath $wideattrApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item_attribute.cpp') -PathType Leaf)) {
    $wideattrResult = & $wideattrApply -SourceDir $engineGameSource
    if ($wideattrResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} two-byte bonus type edit(s).' -f $wideattrResult.Applied) -ForegroundColor DarkGray
    }
}

# Bonusy 6/7 z wiki, runda 3 - umiejetnosci (server-patches/bonusy67c, MT2009_PLUS_BONUS67_SKILL_V1; the owner, 4 November
# 2026): the first two-byte points (256-318: skill lines, low rank, "+x% of the total" of three races). Its anchor is
# wideattr's POINT_WIDE_END line: after it.
$bonusy67cApply = Join-Path $repo 'server-patches/bonusy67c/Apply-Bonusy67cPatch.ps1'
if ((Test-Path -LiteralPath $bonusy67cApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item_attribute.cpp') -PathType Leaf)) {
    $bonusy67cResult = & $bonusy67cApply -SourceDir $engineGameSource
    if ($bonusy67cResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} 6th/7th bonus round 3 edit(s).' -f $bonusy67cResult.Applied) -ForegroundColor DarkGray
    }
}

# Kolor umiejetnosci (server-patches/skillcolor, MT2009_PLUS_SKILL_COLOR_V1; the owner, 4 November 2026): a character's
# colour of a skill's effects (player.skill_color, playerbot_skillcolor.cpp), packets CG 56 / GC 59 (client 1.3.2).
# Its anchors are the fish puzzle's packet lines and the skill hack's login line: after bonusy67c, the last.
$skillcolorApply = Join-Path $repo 'server-patches/skillcolor/Apply-SkillcolorPatch.ps1'
if ((Test-Path -LiteralPath $skillcolorApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_skill.cpp') -PathType Leaf)) {
    $skillcolorResult = & $skillcolorApply -SourceDir $engineGameSource
    if ($skillcolorResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} skill colour edit(s).' -f $skillcolorResult.Applied) -ForegroundColor DarkGray
    }
}

# Mikstury bez limitu (server-patches/mikstury, MT2009_PLUS_MIKSTURY_V1; the owner, 4 November 2026): different bonuses of
# potions, juices, waters, dews, elixirs and ItemShop buffs always run together; the same bonus refreshes or upgrades, a
# weaker one is refused (MiksturyMayRefresh, char_affect.cpp). Its anchors are the patched UseItemEx: the last.
$miksturyApply = Join-Path $repo 'server-patches/mikstury/Apply-MiksturyPatch.ps1'
if ((Test-Path -LiteralPath $miksturyApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_item.cpp') -PathType Leaf)) {
    $miksturyResult = & $miksturyApply -SourceDir $engineGameSource
    if ($miksturyResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} potion stacking edit(s).' -f $miksturyResult.Applied) -ForegroundColor DarkGray
    }
}

# Lowienie jak na globalu (server-patches/fishglobal, MT2009_PLUS_FISHING_GLOBAL_V1; the owner, 4 November 2026): the
# bite chance with a worn Rybie Wnetrznosci or the golden tuna's bonus, the free rod upgrade at the Rybak's dialog with
# -10% points on a failure (fishing.cpp, char_item.cpp), Skrzynia Nimfy Wodnej from monsters of level 70+
# (item_manager.cpp). The logic is fish_global.cpp (the overlay). After chestsash, konie, fishpuzzle and fishren.
$fishGlobalApply = Join-Path $repo 'server-patches/fishglobal/Apply-FishGlobalPatch.ps1'
if ((Test-Path -LiteralPath $fishGlobalApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'fishing.cpp') -PathType Leaf)) {
    $fishGlobalResult = & $fishGlobalApply -SourceDir $engineGameSource
    if ($fishGlobalResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} global fishing edit(s).' -f $fishGlobalResult.Applied) -ForegroundColor DarkGray
    }
}

# Tytuly (server-patches/tytuly, MT2009_PLUS_TITLES_V1; the owner, 4 November 2026): a character's titles (player.player_title,
# playerbot_titles.cpp), packets CG 185 / GC 189 (only to a client that said hello - an older exe never gets them), the
# certificates 57000-57002, /tytul, the quests' title.*. Its anchors are skill colour's lines: after skillcolor, the last.
$tytulyApply = Join-Path $repo 'server-patches/tytuly/Apply-TytulyPatch.ps1'
if ((Test-Path -LiteralPath $tytulyApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'questlua.cpp') -PathType Leaf)) {
    $tytulyResult = & $tytulyApply -SourceDir $engineGameSource
    if ($tytulyResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} title edit(s).' -f $tytulyResult.Applied) -ForegroundColor DarkGray
    }
}
# System Zwierzat Domowych (server-patches/pety, MT2009_PLUS_GROWTH_PET_V1; the owner, 4 November 2026): the official growth
# pet (growth_pet.cpp, player.growth_pet), packets CG 122-134 / GC 224-236 (client 1.3.3), the db core's growth_pet_db.cpp and
# common/growth_pet_types.h installed from server-patches/pety/files. After tytuly, the last.
$petyApply = Join-Path $repo 'server-patches/pety/Apply-PetyPatch.ps1'
if ((Test-Path -LiteralPath $petyApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_item.cpp') -PathType Leaf)) {
    $petyResult = & $petyApply -SourceDir $engineGameSource
    if ($petyResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} growth pet edit(s).' -f $petyResult.Applied) -ForegroundColor DarkGray
    }
}

# "Ten efekt jest juz aktywny." at most once a minute a character (server-patches/efektaktywny,
# MT2009_PLUS_EFFECT_ACTIVE_QUIET_V1; the owner's report, 4 November 2026): autohunt used Grzaniec 50216 / Znak
# Straznika 72328 while their affect ran and every refusal filled the chat (char_item.cpp). Anywhere in the order.
$efektAktywnyApply = Join-Path $repo 'server-patches/efektaktywny/Apply-EfektAktywnyPatch.ps1'
if ((Test-Path -LiteralPath $efektAktywnyApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_item.cpp') -PathType Leaf)) {
    $efektAktywnyResult = & $efektAktywnyApply -SourceDir $engineGameSource
    if ($efektAktywnyResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} effect-active line edit(s).' -f $efektAktywnyResult.Applied) -ForegroundColor DarkGray
    }
}

# Arrows as on the global server (server-patches/strzaly, MT2009_PLUS_ARROWS_GLOBAL_V1; the owner, 5 November 2026):
# CalcArrowDamage no longer cuts an Archer's extra arrows at monsters by 10-30 per cent, and (V2) fades a stack of
# arrows by the distance as the global server does (5 per cent a metre past 5 m), a quiver never (battle.cpp). After
# enginefixes (its MT2009_PLUS_ARROW_RANGE_V1 block is what V2 replaces).
$strzalyApply = Join-Path $repo 'server-patches/strzaly/Apply-StrzalyPatch.ps1'
if ((Test-Path -LiteralPath $strzalyApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'battle.cpp') -PathType Leaf)) {
    $strzalyResult = & $strzalyApply -SourceDir $engineGameSource
    if ($strzalyResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} arrow edit(s).' -f $strzalyResult.Applied) -ForegroundColor DarkGray
    }
}

# Sesja farmienia (server-patches/sesja, MT2009_PLUS_FARM_SESSION_V1; the owner, 5 November 2026): Digi Rasta's
# p-sesja-farmienia (DR_FARM_SESSION_V1 in CommonDefines.h, dr_farm_session.cpp in the overlay), the tables player.dr_farm_*
# made by the core at its start. Its anchors are the patched files as they stand after pety: the last.
$sesjaApply = Join-Path $repo 'server-patches/sesja/Apply-SesjaPatch.ps1'
if ((Test-Path -LiteralPath $sesjaApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char_battle.cpp') -PathType Leaf)) {
    $sesjaResult = & $sesjaApply -SourceDir $engineGameSource
    if ($sesjaResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} farm session edit(s).' -f $sesjaResult.Applied) -ForegroundColor DarkGray
    }
}

# Braki Yohary wg wiki (server-patches/brakiwiki, MT2009_PLUS_BRAKI_WIKI_V1; the owner, 5 November 2026): Tajemniczy
# Talizman's two random base lines (Will SungMa of a random stat, a random element's power) and a glove's Obrona
# (Rekawice Weza). Anchors on lines of talizmanwoli; after sesja.
$brakiWikiApply = Join-Path $repo 'server-patches/brakiwiki/Apply-BrakiWikiPatch.ps1'
if ((Test-Path -LiteralPath $brakiWikiApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'item_attribute.cpp') -PathType Leaf)) {
    $brakiWikiResult = & $brakiWikiApply -SourceDir $engineGameSource
    if ($brakiWikiResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} wiki item edit(s).' -f $brakiWikiResult.Applied) -ForegroundColor DarkGray
    }
}

# System Energii (server-patches/energia, MT2009_PLUS_ENERGY_V1; the owner, 5 November 2026 - "1:1 jak na Wiki"): Krysztal
# Energii (51002) puts POINT_ENERGY on - the worn items' bonuses +1/3/5/7/10 % for 2 hours (energia.cpp in the overlay).
# Its anchors are the patched files as they stand after yohara sets (item.cpp) and mikstury (char_item.cpp): after sesja.
$energiaApply = Join-Path $repo 'server-patches/energia/Apply-EnergiaPatch.ps1'
if ((Test-Path -LiteralPath $energiaApply -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $engineGameSource 'char.cpp') -PathType Leaf)) {
    $energiaResult = & $energiaApply -SourceDir $engineGameSource
    if ($energiaResult.Changed) {
        $syncedFiles++
        Write-Host ('Applied {0} energy edit(s).' -f $energiaResult.Applied) -ForegroundColor DarkGray
    }
}

Write-Host "MT2009 Plus engine: $syncedFiles file(s) changed."
