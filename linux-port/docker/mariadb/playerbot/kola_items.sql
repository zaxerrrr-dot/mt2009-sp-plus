-- MT2009_PLUS_KOLA_ITEMS_V1: the ItemShop wheels' prizes the server lacked (the owner, 20 October 2026). GENERATED
-- by tools/kola_items/gen_kola_items.py - do not edit, rerun it. Every start (apply.sh), idempotent: INSERT IGNORE -
-- a row the operator changed is kept. Kamien Rytualny (25046; the global 25042 is our Magiczny Kamien): Owsap v6.2.6
-- db/item_proto.txt (its flags) and its Polish client (name, text); the Magic Stone's protection (value0 1) with +15%
-- (value1), only above level 80 (server-patches/kolaprzedmioty). 25046 was free in our world (20 October 2026).
-- Smoczy Plomien (B) / Smoczy Plomien (100700/100701): their Polish names where the world still has the English ones.
SET NAMES utf8mb4;
INSERT IGNORE INTO world.item_proto (`vnum`,`name`,`locale_name`,`type`,`subtype`,`stack`,`weight`,`size`,`antiflag`,`flag`,`wearflag`,`immuneflag`,`gold`,`shop_buy_price`,`refined_vnum`,`refine_set`,`magic_pct`,`specular`,`socket_pct`,`addon_type`,`limittype0`,`limitvalue0`,`limittype1`,`limitvalue1`,`applytype0`,`applyvalue0`,`applytype1`,`applyvalue1`,`applytype2`,`applyvalue2`,`value0`,`value1`,`value2`,`value3`,`value4`,`value5`,`socket0`,`socket1`,`socket2`,`socket3`,`socket4`,`socket5`) VALUES
(25046,'Kamien Rytualny',_cp1250 X'4B616D6965F12052797475616C6E79',3,2,200,0,1,90240,4,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,15,0,0,0,0,-1,-1,-1,-1,-1,-1);
UPDATE world.item_proto SET locale_name=_cp1250 X'536D6F637A792050B36F6D6965F120284229' WHERE vnum=100700 AND locale_name=_cp1250 X'466C616D65206F662074686520447261676F6E20284229';
UPDATE world.item_proto SET locale_name=_cp1250 X'536D6F637A792050B36F6D6965F1' WHERE vnum=100701 AND locale_name=_cp1250 X'466C616D65206F662074686520447261676F6E';
