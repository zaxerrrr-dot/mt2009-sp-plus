-- MT2009_PLUS_MONSTER_CARD_BOXES_V1: the four Monster Card boxes (83036 / 83037 / 83074 / 83073) - the owner, 28 October 2026. GENERATED
-- by tools/cardbox/gen_cardbox.py - do not edit, rerun it. Every start (apply.sh), idempotent: INSERT IGNORE - a
-- row the operator changed (the Seban panel) is kept. The global vnums and flags (Owsap v6.2.6): ITEM_GIFTBOX,
-- stackable; the silver and gold boxes tradable, the platinum and Yohara boxes bound (no trade / shop / drop /
-- storage). Opened by the card system (playerbot_monster_card.h OpenCardBox) - no special_item_group.
SET NAMES utf8mb4;
INSERT IGNORE INTO world.item_proto (`vnum`,`name`,`locale_name`,`type`,`subtype`,`stack`,`weight`,`size`,`antiflag`,`flag`,`wearflag`,`immuneflag`,`gold`,`shop_buy_price`,`refined_vnum`,`refine_set`,`magic_pct`,`specular`,`socket_pct`,`addon_type`,`limittype0`,`limitvalue0`,`limittype1`,`limitvalue1`,`applytype0`,`applyvalue0`,`applytype1`,`applyvalue1`,`applytype2`,`applyvalue2`,`value0`,`value1`,`value2`,`value3`,`value4`,`value5`,`socket0`,`socket1`,`socket2`,`socket3`,`socket4`,`socket5`) VALUES
(83036,'Silver Monster Card Box',_cp1250 X'53726562726E652050756465B36B6F204B61727420506F74776F7261',23,0,200,0,1,0,4,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(83037,'Gold Monster Card Box',_cp1250 X'5AB36F74652050756465B36B6F204B61727420506F74776F7261',23,0,200,0,1,0,4,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(83074,'Plat. Monster Card Box',_cp1250 X'506C6174796E6F77652050756465B36B6F204B61727420506F74776F7261',23,0,200,0,1,221312,4,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(83073,'Yohara Monster Card Box',_cp1250 X'50756465B36B6F204B61727420506F74776F72F37720596F68617279',23,0,200,0,1,221312,4,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1);
