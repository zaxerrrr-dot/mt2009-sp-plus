-- MT2009 PLUS: the two glasses of the private shop search (server-patches/shopsearchplus).
-- 60004 Lupa: opens the search and marks a found shop on the map, 1 hour.
-- 60005 Lupa Handlarza: opens the search and buys from a found shop from anywhere, 7 days.
-- Both sold by the General Store Saleswoman (Handlarka Roznosci, shop 3). Runs once per install.
INSERT IGNORE INTO player.item_proto
 (vnum,name,locale_name,type,subtype,stack,weight,size,antiflag,flag,wearflag,immuneflag,gold,shop_buy_price,
  refined_vnum,refine_set,magic_pct,specular,socket_pct,addon_type,
  limittype0,limitvalue0,limittype1,limitvalue1,
  applytype0,applyvalue0,applytype1,applyvalue1,applytype2,applyvalue2,
  value0,value1,value2,value3,value4,value5,socket0,socket1,socket2,socket3,socket4,socket5)
VALUES
 (60004,'Lupa','Lupa',3,10,1,0,1,123264,0,0,'',50000,0, 0,0,0,0,0,0, 7,3600,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
 (60005,'Lupa Handlarza','Lupa Handlarza',3,10,1,0,1,123264,0,0,'',1000000,0, 0,0,0,0,0,0, 7,604800,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0,-1,-1,-1,-1,-1,-1);
INSERT IGNORE INTO world.shop_item (shop_vnum, item_vnum, count) VALUES (3, 60004, 1), (3, 60005, 1);
