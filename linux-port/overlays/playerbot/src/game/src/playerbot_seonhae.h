// MT2009 PLUS Seon-Hae: the 6th and 7th bonus - MT2009_PLUS_SEONHAE_V1
// (the owner, 30 September: "ONLY the Seon-Hae version (NPC 20095), not the
// classic 71051 toggle"; 1 October: no new exe for this one).
//
// Owsap v6.2.6's __ATTR_6TH_7TH__ (CHARACTER::Attr67Add, questlua_attr67add.cpp,
// add_attr67.quest, uiattr67add.py) on our chat-command protocol - no packet,
// no NPC_STORAGE window, nothing in the client's exe:
//  - talking to Seon-Hae (20095, the first villages) is the quest seonhae: it
//    writes seonhae.npc_vid / seonhae.npc_time and sends "SEONHAE open"; the
//    client's window (uiseonhae.py) answers "/seonhae open".
//  - the player puts a weapon or an armour/jewel with all five ordinary bonuses
//    and fewer than two extra ones, 1-10 Powershards of the item's level band
//    (the band table below - Owsap's item_proto column 67AttrMaterial, which our
//    protos have not) and 0-5 Additives (72064-72067: 5/10/20/50 for five) and sends
//    "/seonhae add <cell> <shards> <additive cell> <additives> [<additive window>]"
//    (the window: MT2009_PLUS_EKWIPUNEK_CATS_V2, a supplement of the extra inventory). The chance is
//    the wiki's (MT2009_PLUS_SEONHAE_WIKI_V1): shards x 2 + additive% x additives / 5,
//    at most 100 (10 shards 20 %, with 5 Power Additives 70 %; 1 shard + 5 Power 52 %).
//  - everything is checked here again (the client's window is only a form):
//    the NPC by its vid on the same map within 25 m, the flag, no other window
//    or trade, the item's cell, type, bonuses, the rare pool, the shard vnum by
//    the item's level, the counts against the caps and against what the
//    inventory holds, the additive by its vnum (never a proto value). Owsap's
//    holes: uncapped shard / additive counts, any item as an "additive",
//    shards taken before the last check, a 7-bonus item eaten - all closed.
//  - Seon-Hae keeps the item while he works (Owsap: 24 h; here the panel's
//    m2_seonhae_wait_min, 0 = 1440). The item leaves the inventory and lives in
//    the player's quest flags (vnum, count, 3 sockets, 7 bonuses - every field
//    the item table has), so there is no new window type, no DB enum, nothing
//    stuck when the quest is off: "/seonhae collect" at the NPC remakes the
//    item (a new id) once the time is up. The roll is made at hand-in and kept
//    in seonhae.result; the bonus itself is added to the remade item
//    (AddRareAttribute, as 71051: the level by the panel's m2_rare_lv1..5 -
//    MT2009_PLUS_SEONHAE_WIKI_V1).
//    Order for a crash: at hand-in the item's destroy reaches the db core at
//    once and the flags right after it (ch->Save()); at collection the cleared
//    flags go first and the remade item after them - at worst an item is lost,
//    never doubled.
//  - the switch: event flag m2_seonhae_on (1 on; apply.sh from M2_SEONHAE,
//    default 1 since 28 October 2026; the classic panel's "Seon-Hae" page, web_admin.quest SEONHAE).
//    Off stops new hand-ins only - an item already with Seon-Hae can always be
//    collected.
//  - bots never: every command needs a real descriptor (not IsBot), the quest
//    skips pc.is_bot().
//
// To the client (game.py "SEONHAE", uiseonhae.py):
//   SEONHAE cfg <on>                                         (the quest, at login)
//   SEONHAE open                                             (the quest, at the NPC)
//   SEONHAE state <on> <holding> <vnum> <seconds left> <wait minutes>
//   SEONHAE item <vnum> <s0> <s1> <s2> <t0> <v0> ... <t6> <v6> (the item he keeps)
//   SEONHAE close                                            (handed in)
//   SEONHAE done <1 bonus added | 2 not this time> <vnum>
//   SEONHAE msg <id> <data>
// From the client: "/seonhae open|add|collect|close", for a GM "/seonhae gm now"
// (the time of the item he keeps to zero, Owsap's GM question).
#include "item_manager.h"
#include "char_manager.h"
#include "questmanager.h"
#include "log.h"
#include "constants.h"
#include "playerbot_bonus67.h" // MT2009_PLUS_BONUS67_SKILL_V1: Bonus67RareFits

// MT2009_PLUS_SEONHAE_RESERVED_V1: items whose 6th/7th slots hold their own lines (Talizman Woli) - AddRareAttribute(2)
// refuses them, so Seon-Hae must not take them. The gloves' Will (MT2009_PLUS_GLOVE_BASE_V1) and - MT2009_PLUS_JADE_BASE_V1,
// 3.0.7 - the jade jewellery's two lines (Obrecz / Kolia / Klipsy Jadeitu) are their base attribute, not bonus slots:
// those pieces take the 6th and 7th bonus as any other jewellery.
bool Mt2009WillTalismanType(DWORD dwVnum, BYTE& bWillType);	// item_attribute.cpp (server-patches/talizmanwoli)
bool Mt2009JadeBraceletType(DWORD dwVnum, BYTE& bWillType);	// item_attribute.cpp (server-patches/obreczjadeitu)
bool Mt2009GloveType(DWORD dwVnum, BYTE& bWillType);	// playerbot_yohara_gear.cpp
bool MlodziIsWeaponVnum(unsigned int vnum);	// MT2009_PLUS_MLODZI_BOHATEROWIE_V1: playerbot_mlodzi.cpp
// MT2009_PLUS_GLOVE_BASE_V1: a glove's Will is its base attribute (its yextra, by item id) - the remade glove gets the
// kept one back (playerbot_yohara_gear.cpp)
void Mt2009GloveRestore(LPITEM item, DWORD dwYExtra);
// MT2009_PLUS_JADE_BASE_V1: the jade's old 6th/7th base lines out of the bonus slots, the kept base back (playerbot_yohara_gear.cpp)
void Mt2009JadeBaseMigrate(LPITEM item);
void Mt2009JadeBaseRestore(LPITEM item, DWORD dwYExtra);

namespace mt2009_seonhae
{
	const DWORD NPC_VNUM = 20095;
	const int NPC_RANGE = 2500;				// server units from Seon-Hae (Owsap's window closes at 10 m from where it opened)
	const int NPC_TALK_SECONDS = 1800;		// the quest's npc_time is that fresh at most
	const int MATERIAL_MAX = 10;			// ATTR67_MATERIAL_MAX_COUNT
	const int SUPPORT_MAX = 5;				// ATTR67_SUPPORT_MAX_COUNT
	const int PCT_PER_MATERIAL = 2;			// ATTR67_SUCCESS_PER_MATERIAL
	const int DEFAULT_WAIT_MIN = 1440;		// ATTR67_ADD_WAIT_TIME (24 h)
	const int WAIT_MIN_MAX = 7 * 1440;

	const char* const E_ON = "m2_seonhae_on";
	const char* const E_WAIT = "m2_seonhae_wait_min";

	// the player's flags (quest seonhae: pc.getqf("vnum") reads seonhae.vnum)
	const char* const F_NPC_VID = "seonhae.npc_vid";
	const char* const F_NPC_TIME = "seonhae.npc_time";
	const char* const F_VNUM = "seonhae.vnum";
	const char* const F_COUNT = "seonhae.count";
	const char* const F_READY = "seonhae.ready";
	const char* const F_RESULT = "seonhae.result";	// 1 success, 2 failure
	const char* const F_PCT = "seonhae.pct";
	const char* const F_SOCKET[ITEM_SOCKET_MAX_NUM] = { "seonhae.s0", "seonhae.s1", "seonhae.s2" };
	const char* const F_ATTR[ITEM_ATTRIBUTE_MAX_NUM] = { "seonhae.a0", "seonhae.a1", "seonhae.a2", "seonhae.a3",
		"seonhae.a4", "seonhae.a5", "seonhae.a6" };
	const char* const F_YEXTRA = "seonhae.yx";	// MT2009_PLUS_GLOVE_BASE_V1: the item's yextra (a glove's Will; MT2009_PLUS_JADE_BASE_V1 the jade's lines)

	enum
	{
		RESULT_SUCCESS = 1,
		RESULT_FAIL = 2,
	};

	enum
	{
		MSG_OFF = 1,
		MSG_FAR = 2,
		MSG_BUSY = 3,
		MSG_HOLDING = 4,
		MSG_BAD_ITEM = 5,
		MSG_NEED_FIVE = 6,
		MSG_HAS_TWO = 7,
		MSG_ITEM_LOCKED = 8,
		MSG_NO_MATERIAL = 9,		// data: the shard's vnum
		MSG_MATERIAL_COUNT = 10,
		MSG_BAD_SUPPORT = 11,
		MSG_NO_SUPPORT = 12,		// data: the additive's vnum
		MSG_HANDED_IN = 13,			// data: minutes
		MSG_NOT_READY = 14,			// data: seconds left
		MSG_NO_SPACE = 15,
		MSG_NOTHING = 18,
		MSG_ERROR = 19,
		MSG_NO_POOL = 20,
	};

	// Owsap's 67AttrMaterial by the item's level (its item_proto, weapons and
	// armours): Grey 0-29, White 30-39, Green 40-49, Yellow 50-59, Blue 60-74,
	// Purple 75-89, Red 90-104, Rainbow 105-119, Holy 120+.
	// MT2009_PLUS_SEONHAE_LUCENT_V1 (fix 3.0 #9): the Lucent shards as the
	// pl-wiki's "6. i 7. bonus" table has them - Grey Lucent (39078) for the
	// level-30 items, Green Lucent (39079) for 75, Yellow Lucent (39080) for 105
	// (Zodiac, the 105 jewellery, Talizmany Woli), the level-96 weapons, armours
	// and helmets (Smoka Mroku) and the talismans. The client (uiseonhae.py) has
	// the same table.
	DWORD MaterialVnum(LPITEM item)
	{
		// MT2009_PLUS_SEONHAE_LEVEL_FIX_V1 (vps3, 7 November 2026: "niebieskim odlamkiem go nie zabiera"): the highest level
		// limit, not the last - Kapelusz Kardynala (12670-12679) has LIMIT_LEVEL 60 and a second LIMIT_LEVEL 0, the last
		// one read made it a level-0 item that took Szare Odlamki (39070) instead of Niebieskie (39074).
		int level = 0;
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
			if (item->GetLimitType(i) == LIMIT_LEVEL)
				level = MAX(level, (int)item->GetLimitValue(i));
		if (item->GetType() == ITEM_ARMOR && item->GetSubType() == ARMOR_PENDANT)
			return 39080;
		if (level == 96 && (item->GetType() == ITEM_WEAPON || (item->GetType() == ITEM_ARMOR &&
				(item->GetSubType() == ARMOR_BODY || item->GetSubType() == ARMOR_HEAD))))
			return 39080;
		if (level == 30) return 39078;
		if (level == 75) return 39079;
		if (level == 105) return 39080;
		if (level < 30) return 39070;
		if (level < 40) return 39071;
		if (level < 50) return 39072;
		if (level < 60) return 39073;
		if (level < 75) return 39074;
		if (level < 90) return 39075;
		if (level < 105) return 39076;
		if (level < 120) return 39077;
		return 39081;
	}

	// The Additives by vnum - the bonus is never read from a proto or the client.
	int SupportPct(DWORD vnum)
	{
		switch (vnum)
		{
			case 72064: return 5;
			case 72065: return 10;
			case 72066: return 20;
			case 72067: return 50;
		}
		return 0;
	}

	// MT2009_PLUS_SEONHAE_WIKI_V1 (the owner, 20 October: "as the wiki"): the wiki's chance - 2% a shard plus the
	// additive's own per cent for each one (Maly 1, Sredni 2, Duzy 4, Silny 10; SupportPct is the 5-piece total),
	// independent of the shard count: 1 shard + 5 Silne = 52%, 10 + 5 Silne = 70%. Owsap's scaled the additives
	// by shards / 10 (1 shard + 5 Silne = 7%).
	int ChancePct(int materials, int supportPct, int supports)
	{
		int pct = materials * PCT_PER_MATERIAL;
		if (supports > 0 && supportPct > 0)
			pct += supportPct * supports / SUPPORT_MAX;
		return std::max(0, std::min(100, pct));
	}

	bool IsOn()
	{
		return quest::CQuestManager::instance().GetEventFlag(E_ON) == 1;
	}

	int WaitMinutes()
	{
		const int m = quest::CQuestManager::instance().GetEventFlag(E_WAIT);
		return m > 0 ? std::min(m, WAIT_MIN_MAX) : DEFAULT_WAIT_MIN;
	}

	bool Eligible(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && !ch->GetDesc()->IsBot();
	}

	void Cmd(LPCHARACTER ch, const char* format, ...)
	{
		if (!Eligible(ch))
			return;
		char buf[480];
		va_list args;
		va_start(args, format);
		vsnprintf(buf, sizeof(buf), format, args);
		va_end(args);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "SEONHAE %s", buf);
	}

	void Msg(LPCHARACTER ch, int id, long data = 0)
	{
		Cmd(ch, "msg %d %ld", id, data);
	}

	bool Holding(LPCHARACTER ch)
	{
		return ch->GetQuestFlag(F_VNUM) != 0;
	}

	// Seon-Hae by the vid the quest wrote, on this map, close enough, talked to lately.
	bool NearNpc(LPCHARACTER ch)
	{
		const DWORD vid = (DWORD)ch->GetQuestFlag(F_NPC_VID);
		const int talked = ch->GetQuestFlag(F_NPC_TIME);
		if (!vid || !talked || (int)get_global_time() - talked > NPC_TALK_SECONDS || (int)get_global_time() < talked)
			return false;
		LPCHARACTER npc = CHARACTER_MANAGER::instance().Find(vid);
		if (!npc || !npc->IsNPC() || npc->GetRaceNum() != NPC_VNUM || npc->GetMapIndex() != ch->GetMapIndex())
			return false;
		return DISTANCE_APPROX(ch->GetX() - npc->GetX(), ch->GetY() - npc->GetY()) <= NPC_RANGE;
	}

	bool Busy(LPCHARACTER ch)
	{
		return ch->IsDead() || !ch->CanHandleItem() || ch->GetExchange() || ch->GetShop() || ch->GetMyShop() ||
			ch->IsOpenSafebox() || ch->IsCubeOpen();
	}

	// An extra bonus this item's set can still get (PutRareAttributeWithLevel's own test).
	bool RarePoolHasRoom(LPITEM item)
	{
		const int set = item->GetAttributeSetIndex();
		if (set < 0 || set >= ATTRIBUTE_SET_MAX_NUM)
			return false;
		for (TItemAttrMap::const_iterator it = g_map_itemRare.begin(); it != g_map_itemRare.end(); ++it)
			if (it->second.bMaxLevelBySet[set] > 0 && it->second.dwProb > 0 && !item->HasRareAttr((WORD)it->first)
					&& Bonus67RareFits(item, it->first)) // MT2009_PLUS_BONUS67_SKILL_V1: a skill's line - the item's class only
				return true;
		return false;
	}

	int CheckItem(LPCHARACTER ch, LPITEM item)
	{
		if (!item || item->GetOwner() != ch || item->GetWindow() != INVENTORY)
			return MSG_BAD_ITEM;
		if (item->GetType() != ITEM_WEAPON && item->GetType() != ITEM_ARMOR)
			return MSG_BAD_ITEM;
		// MT2009_PLUS_MLODZI_BOHATEROWIE_V1 (seon-hae): a young heroes' weapon takes no 6th/7th bonus
		if (MlodziIsWeaponVnum(item->GetVnum()))
			return MSG_BAD_ITEM;
		if (item->GetAttributeSetIndex() < 0)
			return MSG_BAD_ITEM;
		// MT2009_PLUS_JADE_BASE_V1: a piece of jade jewellery whose base lines are still in its 6th/7th slots (a copy of
		// an old one) moves them first - they are no extra bonuses (the owner, 3 Nov: Kolia Jadeitu Nocy+9 "already has")
		Mt2009JadeBaseMigrate(item);
		if (item->IsEquipped() || item->IsExchanging() || item->isLocked() || item->IsChangingAttr() || item->GetCount() != 1)
			return MSG_ITEM_LOCKED;
		if (IS_SET(item->GetFlag(), ITEM_FLAG_UNIQUE))
			return MSG_ITEM_LOCKED;
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
		{
			const BYTE t = item->GetLimitType(i);
			if (t == LIMIT_REAL_TIME || t == LIMIT_REAL_TIME_START_FIRST_USE || t == LIMIT_TIMER_BASED_ON_WEAR)
				return MSG_ITEM_LOCKED;
		}
		if (item->GetAttributeCount() < ITEM_ATTRIBUTE_NORM_NUM)
			return MSG_NEED_FIVE;
		{	// MT2009_PLUS_SEONHAE_RESERVED_V1: the shards would be spent and no bonus could ever be put on it
			BYTE bReserved;
			// MT2009_PLUS_SEONHAE_GLOVE_V1 / MT2009_PLUS_GLOVE_BASE_V1: a glove is taken - its Will is its base
			// attribute, its 6th and then its 7th bonus come from the pool's glove column (server-patches/bonusy67;
			// AddRareAttribute fills the first free slot, as 71051 does). MT2009_PLUS_JADE_BASE_V1: before the count of
			// the extra bonuses - a Talizman Woli's two own lines are none ("no bonus for this item", not "it has two").
			if (Mt2009WillTalismanType(item->GetVnum(), bReserved))
				return MSG_NO_POOL;
		}
		if (item->GetRareAttrCount() >= ITEM_ATTRIBUTE_RARE_NUM)
			return MSG_HAS_TWO;
		if (!RarePoolHasRoom(item))
			return MSG_NO_POOL;
		return 0;
	}

	void SendState(LPCHARACTER ch)
	{
		const DWORD vnum = (DWORD)ch->GetQuestFlag(F_VNUM);
		int left = 0;
		if (vnum)
			left = std::max(0, ch->GetQuestFlag(F_READY) - (int)get_global_time());
		Cmd(ch, "state %d %d %u %d %d", IsOn() ? 1 : 0, vnum ? 1 : 0, vnum, left, WaitMinutes());
		if (!vnum)
			return;
		char buf[400];
		int len = snprintf(buf, sizeof(buf), "item %u", vnum);
		for (int i = 0; i < ITEM_SOCKET_MAX_NUM && len > 0 && len < (int)sizeof(buf); ++i)
			len += snprintf(buf + len, sizeof(buf) - len, " %d", ch->GetQuestFlag(F_SOCKET[i]));
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM && len > 0 && len < (int)sizeof(buf); ++i)
		{
			const unsigned int packed = (unsigned int)ch->GetQuestFlag(F_ATTR[i]);
			len += snprintf(buf + len, sizeof(buf) - len, " %u %d", (packed >> 16) & 0xFFFF, (int)(short)(packed & 0xFFFF)); // MT2009_PLUS_WIDE_ATTR_V1
		}
		Cmd(ch, "%s", buf);
	}

	void Open(LPCHARACTER ch)
	{
		if (!NearNpc(ch))
			return Msg(ch, MSG_FAR);
		SendState(ch);
	}

	void Add(LPCHARACTER ch, const char* argument)
	{
		char a1[16], a2[16], a3[16], a4[16], a5[16];
		const char* rest = one_argument(argument, a1, sizeof(a1));
		rest = one_argument(rest, a2, sizeof(a2));
		rest = one_argument(rest, a3, sizeof(a3));
		rest = one_argument(rest, a4, sizeof(a4));
		one_argument(rest, a5, sizeof(a5));
		if (!*a1 || !*a2 || !*a3 || !*a4)
			return;
		const int cell = atoi(a1);
		const int materials = atoi(a2);
		const int supportCell = atoi(a3);
		const int supports = atoi(a4);
		// MT2009_PLUS_EKWIPUNEK_CATS_V2 (the owner, 3 November 2026: "Suplement z zakladki przeciagany bezposrednio do
		// okna Seon-Hae"): an optional fifth word, the additive's window - the bag (INVENTORY, also when left out, as
		// the older root sends it) or the extra inventory's Zaczarowanie storage the supplements are kept in
		const int supportWindow = *a5 ? atoi(a5) : (int)INVENTORY;

		if (!IsOn())
			return Msg(ch, MSG_OFF);
		if (!NearNpc(ch))
			return Msg(ch, MSG_FAR);
		if (Busy(ch))
			return Msg(ch, MSG_BUSY);
		if (Holding(ch))
			return Msg(ch, MSG_HOLDING);
		if (cell < 0 || cell >= INVENTORY_MAX_NUM)
			return Msg(ch, MSG_BAD_ITEM);
		LPITEM item = ch->GetInventoryItem((WORD)cell);
		if (const int bad = CheckItem(ch, item))
			return Msg(ch, bad);

		const DWORD materialVnum = MaterialVnum(item);
		if (materials < 1 || materials > MATERIAL_MAX)
			return Msg(ch, MSG_MATERIAL_COUNT);
		if (ch->CountSpecifyItem(materialVnum) < (ITEM_COUNT)materials)
			return Msg(ch, MSG_NO_MATERIAL, (long)materialVnum);

		DWORD supportVnum = 0;
		int supportPct = 0;
		if (supports < 0 || supports > SUPPORT_MAX)
			return Msg(ch, MSG_BAD_SUPPORT);
		if (supports > 0)
		{
			LPITEM support = NULL;
			if (supportWindow == (int)INVENTORY)
			{
				if (supportCell < 0 || supportCell >= INVENTORY_MAX_NUM || supportCell == cell)
					return Msg(ch, MSG_BAD_SUPPORT);
				support = ch->GetInventoryItem((WORD)supportCell);
			}
			else if (supportWindow > 0 && supportWindow <= 255 && Mt2009IsSpecialWindow((BYTE)supportWindow))
			{
				if (supportCell < 0 || supportCell >= SPECIAL_INVENTORY_MAX_NUM)
					return Msg(ch, MSG_BAD_SUPPORT);
				support = ch->Mt2009SpecialGetItem((BYTE)supportWindow, (WORD)supportCell);
			}
			else
				return Msg(ch, MSG_BAD_SUPPORT);
			if (!support || support->IsExchanging() || support->isLocked())
				return Msg(ch, MSG_BAD_SUPPORT);
			supportVnum = support->GetVnum();
			supportPct = SupportPct(supportVnum);
			if (!supportPct)
				return Msg(ch, MSG_BAD_SUPPORT);
			if (ch->CountSpecifyItem(supportVnum) < (ITEM_COUNT)supports)
				return Msg(ch, MSG_NO_SUPPORT, (long)supportVnum);
		}

		// Every check passed: from here on nothing refuses.
		const int pct = ChancePct(materials, supportPct, supports);
		const bool success = number(1, 100) <= pct;
		const int wait = WaitMinutes();

		ch->RemoveSpecifyItem(materialVnum, (ITEM_COUNT)materials);
		if (supports > 0)
			ch->RemoveSpecifyItem(supportVnum, (ITEM_COUNT)supports);

		const DWORD vnum = item->GetVnum();
		char hint[96];
		snprintf(hint, sizeof(hint), "%u shards %u x%d additive %u x%d pct %d %s", vnum, materialVnum, materials,
				supportVnum, supports, pct, success ? "OK" : "FAIL");
		LogManager::instance().ItemLog(ch, item, "SEONHAE_HOLD", hint);

		ch->SetQuestFlag(F_COUNT, (int)item->GetCount());
		for (int i = 0; i < ITEM_SOCKET_MAX_NUM; ++i)
			ch->SetQuestFlag(F_SOCKET[i], (int)item->GetSocket(i));
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		{
			const WORD t = item->GetAttributeType(i); // MT2009_PLUS_WIDE_ATTR_V1
			const short v = item->GetAttributeValue(i);
			ch->SetQuestFlag(F_ATTR[i], t ? (int)(((unsigned int)t << 16) | (unsigned short)v) : 0);
		}
		ch->SetQuestFlag(F_YEXTRA, (int)item->GetYExtra()); // MT2009_PLUS_GLOVE_BASE_V1 (hold)
		ch->SetQuestFlag(F_PCT, pct);
		ch->SetQuestFlag(F_RESULT, success ? RESULT_SUCCESS : RESULT_FAIL);
		ch->SetQuestFlag(F_READY, (int)get_global_time() + wait * 60);
		ch->SetQuestFlag(F_VNUM, (int)vnum);

		ITEM_MANAGER::instance().RemoveItem(item, "SEONHAE_HOLD");
		ch->Save();

		sys_log(0, "SEONHAE: %s handed in %u (%s), chance %d%%, %s, ready in %d min", ch->GetName(), vnum, hint, pct,
				success ? "success" : "failure", wait);
		Msg(ch, MSG_HANDED_IN, wait);
		Cmd(ch, "close");
	}

	void ClearHold(LPCHARACTER ch)
	{
		ch->SetQuestFlag(F_VNUM, 0);
		ch->SetQuestFlag(F_COUNT, 0);
		ch->SetQuestFlag(F_READY, 0);
		ch->SetQuestFlag(F_RESULT, 0);
		ch->SetQuestFlag(F_PCT, 0);
		ch->SetQuestFlag(F_YEXTRA, 0); // MT2009_PLUS_GLOVE_BASE_V1
		for (int i = 0; i < ITEM_SOCKET_MAX_NUM; ++i)
			ch->SetQuestFlag(F_SOCKET[i], 0);
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			ch->SetQuestFlag(F_ATTR[i], 0);
	}

	void Collect(LPCHARACTER ch)
	{
		if (!Holding(ch))
			return Msg(ch, MSG_NOTHING);
		if (!NearNpc(ch))
			return Msg(ch, MSG_FAR);
		if (Busy(ch))
			return Msg(ch, MSG_BUSY);
		const int left = ch->GetQuestFlag(F_READY) - (int)get_global_time();
		if (left > 0)
			return Msg(ch, MSG_NOT_READY, left);

		const DWORD vnum = (DWORD)ch->GetQuestFlag(F_VNUM);
		const int count = std::max(1, ch->GetQuestFlag(F_COUNT));
		LPITEM item = ITEM_MANAGER::instance().CreateItem(vnum, (ITEM_COUNT)count, 0, false);
		if (!item)
		{
			sys_err("SEONHAE: %s cannot remake %u - the item stays with Seon-Hae", ch->GetName(), vnum);
			return Msg(ch, MSG_ERROR);
		}
		long sockets[ITEM_SOCKET_MAX_NUM];
		for (int i = 0; i < ITEM_SOCKET_MAX_NUM; ++i)
			sockets[i] = ch->GetQuestFlag(F_SOCKET[i]);
		TPlayerItemAttribute attrs[ITEM_ATTRIBUTE_MAX_NUM];
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		{
			const unsigned int packed = (unsigned int)ch->GetQuestFlag(F_ATTR[i]);
			attrs[i].bType = (WORD)((packed >> 16) & 0xFFFF); // MT2009_PLUS_WIDE_ATTR_V1
			attrs[i].sValue = attrs[i].bType ? (short)(packed & 0xFFFF) : 0;
		}
		item->SetSockets(sockets);
		item->SetAttributes(attrs);
		Mt2009GloveRestore(item, (DWORD)ch->GetQuestFlag(F_YEXTRA)); // MT2009_PLUS_GLOVE_BASE_V1 (collect): a glove's Will back
		Mt2009JadeBaseRestore(item, (DWORD)ch->GetQuestFlag(F_YEXTRA)); // MT2009_PLUS_JADE_BASE_V1 (collect): the jade's base back

		const int cell = ch->GetEmptyInventoryEx(item);
		if (cell < 0)
		{
			M2_DESTROY_ITEM(item);
			return Msg(ch, MSG_NO_SPACE);
		}

		const int result = ch->GetQuestFlag(F_RESULT);
		const int pct = ch->GetQuestFlag(F_PCT);
		// The flags leave first (ch->Save()), the item after them: a crash in
		// between loses the item rather than doubling it.
		ClearHold(ch);
		ch->Save();
		item->AddToCharacter(ch, TItemPos(item->GetWindowInventoryEx(), cell));

		bool added = false;
		if (result == RESULT_SUCCESS)
		{
			const int before = item->GetRareAttrCount();
			if (before < ITEM_ATTRIBUTE_RARE_NUM && RarePoolHasRoom(item))
			{
				// MT2009_PLUS_SEONHAE_WIKI_V1: the level by the panel's odds (m2_rare_lv1..5, 71051/71052's
				// AddRareAttribute) instead of AddRareAttribute2's fixed 40/50/10/0/0 - levels 4-5 (the wiki's
				// maxima) can come from Seon-Hae too.
				item->AddRareAttribute();
				added = item->GetRareAttrCount() > before;
			}
			if (!added)
				sys_err("SEONHAE: %s won %u but no extra bonus could be put on it", ch->GetName(), vnum);
		}
		item->UpdatePacket();
		ITEM_MANAGER::instance().FlushDelayedSave(item);

		char hint[64];
		snprintf(hint, sizeof(hint), "%u pct %d %s", vnum, pct, added ? "ADDED" : "NONE");
		LogManager::instance().ItemLog(ch, item, added ? "SEONHAE_ADD_RARE" : "SEONHAE_RETURN", hint);
		sys_log(0, "SEONHAE: %s collected %u (new id %u): %s", ch->GetName(), vnum, item->GetID(), added ? "extra bonus" : "no bonus");
		Cmd(ch, "done %d %u", added ? RESULT_SUCCESS : RESULT_FAIL, vnum);
		SendState(ch);
	}

	std::map<DWORD, DWORD> s_mapLastCommand;

	bool TooSoon(LPCHARACTER ch)
	{
		const DWORD now = get_dword_time();
		DWORD& last = s_mapLastCommand[ch->GetPlayerID()];
		if (last && now - last < 300)
			return true;
		last = now;
		return false;
	}
}

void SeonHaeCommand(LPCHARACTER ch, const char* argument)
{
	using namespace mt2009_seonhae;
	if (!Eligible(ch))
		return;
	char sub[32], arg[32];
	const char* rest = one_argument(argument, sub, sizeof(sub));
	if (strcmp(sub, "gm") && strcmp(sub, "close") && TooSoon(ch))
		return;
	if (!strcmp(sub, "open"))
		Open(ch);
	else if (!strcmp(sub, "add"))
		Add(ch, rest);
	else if (!strcmp(sub, "collect"))
		Collect(ch);
	else if (!strcmp(sub, "close"))
		;	// the window closed; nothing is held open on this side
	else if (!strcmp(sub, "gm") && ch->GetGMLevel() > GM_PLAYER)
	{
		one_argument(rest, arg, sizeof(arg));
		if (!strcmp(arg, "now") && Holding(ch))
		{
			ch->SetQuestFlag(F_READY, (int)get_global_time());
			ch->ChatPacket(CHAT_TYPE_INFO, "Seon-Hae: czas ustawiony na zero.");
		}
		else
			ch->ChatPacket(CHAT_TYPE_INFO, "Seon-Hae: %s, czas %d min, trzymany przedmiot %d, wynik %d, szansa %d%%. /seonhae gm now",
					IsOn() ? "wlaczony" : "wylaczony", WaitMinutes(), ch->GetQuestFlag(F_VNUM), ch->GetQuestFlag(F_RESULT),
					ch->GetQuestFlag(F_PCT));
	}
}

// MT2009_PLUS_SEONHAE_V1 (drops): where the Powershards and the Additives come
// from (the owner, 1 October, revised). The Additives only for a real player -
// the drop's owner (the killer CreateDropItem is given: the top damage dealer
// or his party's) must not be a bot; the Powershards for a bot too, at the same
// chances (MT2009_PLUS_BOT_SEONHAE_V2) - and nothing while m2_seonhae_on is off. The
// items join the kill's own list, so they fall with its ownership. No shop,
// no ItemShop.
//  - Additives: from Metin stones and bosses (rank boss/king) on the maps of
//    an additive_map line (instances too: map / 10000), each kill rolling
//    additive_chance; a mob line names one monster (any rank, any map) and
//    replaces the map rule for it.
//  - Powershards: from ordinary monsters (not a stone, not boss/king) on the
//    maps of a shard_map line, shard_chance percent a kill (fractions
//    allowed), one shard, its colour drawn from the shard lines' weights.
//
// The rules are a small file the classic panel's Seon-Hae page edits,
// /opt/m2spool/seonhae_drops.tsv, re-read when it changes (looked at every
// 5 s at most); no file, or a kind of line missing from it, means the
// defaults below. One rule a line, tab- or space-separated, '#' a comment:
//   additive_chance <percent>                         (default 60)
//   additive_map <map index> <additive vnum> <count>  (72, 73: 1 x 72065; 353: 1 x 72066)
//   mob <mob vnum> <additive vnum> <count>            (2493 Beran-Setaou, 9714 Krolowa Dzungli: 2 x 72066)
//   shard_chance <percent, e.g. 0.5>                  (default 0.5)
//   shard_map <map index>                             (73, 209, 353, 404 - MT2009_PLUS_BOT_BONUS67_V1)
// MT2009_PLUS_YOHARA_ZAKLETY_V1: the Arezzo forest's (362) rules are Zaklety Las's (353) now - the forest past the
// Temple of Ochao, on the Yohara core.
//   shard <shard vnum> <weight>                       (39070-39077, 39081: 1 each)
//   shard_pick <map index> <shard vnum> <weight>      (353: 39076 x3, 39080 x1; 404: 39077 x3, 39080 x1, 39081 x1)
// MT2009_PLUS_BOT_BONUS67_V1 (drops; the owner, 8 November 2026: "add shard drops to Zaklety Las and Szczelina Czasu,
// the same percentages as in the Grotto of Exile ... a world drop"): Zaklety Las (353) was a shard map already (0.5 %,
// the colour from every band); Szczelina Czasu's forest (Zaklety Las (SZC), 404) joins the shard maps, and both draw
// the colour of their players' item levels instead of the whole table - a shard_pick line names a map's own colours
// (the shard lines stay the other maps'): 353 (monsters 100-108, players 95-109 in item levels 90-105) Czerwony
// 39076 (90-104) x3 and Zolty Lsniacy 39080 (105) x1; 404 (players 110-119 in item levels 105-120) Teczowy 39077
// (106-119) x3, Zolty Lsniacy 39080 x1 and Swiety 39081 (120+) x1. The chance is the Grotto's, shard_chance (0.5 %).
// Map 404 drops nothing else (server-patches/szczelina, MT2009_PLUS_YOHARA_CRACK_V1): its shard comes from
// Mt2009PlusSeonHaeRiftDrop, the one call the engine's no-drop return makes (the edit "MT2009_PLUS_BOT_BONUS67_V1
// (rift shards)" there). A file of the panel with shard_map lines replaces the list, so it must name 404 itself.
// MT2009_PLUS_SEONHAE_YOHARA_V1 (the owner, 10 November 2026: "Dodaj drop wszystkich odlamkow do bonusow 6/7 na mapach
// Yohary", from the ordinary monsters, not on Plaskowyz Iluzji): every Yohara map and dungeon is a shard map of its own
// list, shard_map_yohara (beside shard_map - a file of the old kind, with shard_map lines but none of these, keeps the
// Yohara list at its defaults; the effective shard maps are both lists). Every one of the twelve shards can drop there
// (shard_pick, by the map's profile): the colours of its players' item levels weigh 75 of 100, the nine others share
// the remaining 25 - the nearer the band, the more. Three profiles (the maps' ordinary monsters, tools/yohara_*):
//   Sung Ma (monsters 118-127, level-120 Champions in item levels 120+): 373 374 376 377 385 388 389 393 394, Glebie
//     Pln. Wiatru 395, Tajemnicza Instancja 396, Krolestwo Zywiolow 378-381, Swiatynia Wezy 390 391, Jaskinie Gnolli
//     382-384, Wieza Sung Mahi 386 387 - Swiety 39081 x40, Teczowy 39077 x20, Zolty Lsniacy 39080 x15;
//   110-120 (the Time Rift and Awakening dungeons, the Hydra, monsters 107-125, players 110-119 in item levels 105-120):
//     Obrona Statku 367, Port 368, PB 369 370 371 398, SZC 404-407 - Teczowy 39077 x45, Zolty Lsniacy 39080 x15,
//     Swiety 39081 x15 (404's 3:1:1 of MT2009_PLUS_BOT_BONUS67_V1);
//   the forests' (monsters 97-110, players 90-109 in item levels 90-105): Zaklety Las 353, Schronienie Meley 356 -
//     Czerwony 39076 x56, Zolty Lsniacy 39080 x19 (353's 3:1).
// The rest of every profile, 25: the next band up and down 7-8, the farther ones 1-5 (the table in DefaultDropRules).
// The chance is the Grotto's, shard_chance (0.5 %). Plaskowyz Iluzji (397, the hub) is no shard map. The level rule of
// the Yohara list's maps: no shard from a monster more than shard_level_gap (15) levels under the killer (0: off).
//   shard_map_yohara <map index>                      (the list above; a line of it replaces the whole list)
//   shard_level_gap <levels>                          (default 15)
// A file's shard_pick lines replace the defaults of the maps they name only (the others keep theirs); a file of the old
// kind (no shard_map_yohara line) keeps the new colours of the Yohara list's maps - its shard_pick lines for them (the
// old 353 / 404 defaults) are not read.
#include <sys/stat.h>
#include <fstream>
#include <sstream>

namespace mt2009_seonhae
{
	const char* const DROPS_PATH = "/opt/m2spool/seonhae_drops.tsv";
	const DWORD DROPS_RECHECK_MS = 5000;
	const int SHARD_CHANCE_SCALE = 100000;	// shard_chance percent x 1000

	struct VnumCount
	{
		DWORD vnum;
		int count;
	};

	struct WeightedVnum
	{
		DWORD vnum;
		int weight;
	};

	struct DropRules
	{
		int additivePermille;					// additive_chance x 10
		std::map<long, VnumCount> additiveMaps;
		std::map<DWORD, VnumCount> mobs;
		int shardChance;						// per SHARD_CHANCE_SCALE
		std::set<long> shardMaps;
		std::vector<WeightedVnum> shards;
		std::map<long, std::vector<WeightedVnum> > shardPicks;	// MT2009_PLUS_BOT_BONUS67_V1: a map's own colours
		std::set<long> yoharaShardMaps;		// MT2009_PLUS_SEONHAE_YOHARA_V1: shard_map_yohara
		int shardLevelGap;					// MT2009_PLUS_SEONHAE_YOHARA_V1: shard_level_gap (0: off)
	};

	// MT2009_PLUS_SEONHAE_YOHARA_V1: the Yohara maps and their profiles (the header above). Not 397, Plaskowyz Iluzji.
	const long YOHARA_SUNGMA_SHARD_MAPS[] = { 373, 374, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388,
			389, 390, 391, 393, 394, 395, 396 };
	const long YOHARA_RIFT_SHARD_MAPS[] = { 367, 368, 369, 370, 371, 398, 404, 405, 406, 407 };
	const long YOHARA_FOREST_SHARD_MAPS[] = { 353, 356 };
	// 39070 Szary, 39071 Bialy, 39072 Zielony, 39073 Zolty, 39074 Niebieski, 39075 Fioletowy, 39076 Czerwony,
	// 39077 Teczowy, 39078 Szary Lsn., 39079 Zielony Lsn., 39080 Zolty Lsn., 39081 Swiety - each list sums to 100
	const WeightedVnum YOHARA_SUNGMA_PICK[] = { { 39081, 40 }, { 39077, 20 }, { 39080, 15 }, { 39076, 8 }, { 39075, 4 },
			{ 39079, 3 }, { 39074, 3 }, { 39073, 2 }, { 39072, 2 }, { 39071, 1 }, { 39078, 1 }, { 39070, 1 } };
	const WeightedVnum YOHARA_RIFT_PICK[] = { { 39077, 45 }, { 39080, 15 }, { 39081, 15 }, { 39076, 8 }, { 39075, 4 },
			{ 39079, 3 }, { 39074, 3 }, { 39073, 2 }, { 39072, 2 }, { 39071, 1 }, { 39078, 1 }, { 39070, 1 } };
	const WeightedVnum YOHARA_FOREST_PICK[] = { { 39076, 56 }, { 39080, 19 }, { 39077, 7 }, { 39075, 5 }, { 39079, 3 },
			{ 39074, 2 }, { 39081, 2 }, { 39073, 2 }, { 39072, 1 }, { 39071, 1 }, { 39078, 1 }, { 39070, 1 } };
	const int YOHARA_SHARD_LEVEL_GAP = 15;

	void AddYoharaShardProfile(DropRules& r, const long* maps, size_t mapCount, const WeightedVnum* pick, size_t pickCount)
	{
		for (size_t i = 0; i < mapCount; ++i)
		{
			r.yoharaShardMaps.insert(maps[i]);
			std::vector<WeightedVnum>& v = r.shardPicks[maps[i]];
			v.assign(pick, pick + pickCount);
		}
	}

	bool IsShardVnum(DWORD vnum)
	{
		return (vnum >= 39070 && vnum <= 39081); // MT2009_PLUS_SEONHAE_LUCENT_V1: the Lucent shards 39078-39080 too
	}

	void DefaultDropRules(DropRules& r)
	{
		r.additivePermille = 600;
		r.additiveMaps.clear();
		r.additiveMaps[72] = VnumCount{ 72065, 1 };
		r.additiveMaps[73] = VnumCount{ 72065, 1 };
		r.additiveMaps[353] = VnumCount{ 72066, 1 };
		r.mobs.clear();
		r.mobs[2493] = VnumCount{ 72066, 2 };
		r.mobs[9714] = VnumCount{ 72066, 2 };
		r.shardChance = 500;	// 0.5 %
		r.shardMaps.clear();
		r.shardMaps.insert(73);
		r.shardMaps.insert(209);
		// MT2009_PLUS_SEONHAE_YOHARA_V1: Zaklety Las (353) and Zaklety Las (SZC) (404) are on the Yohara list now
		r.shards.clear();
		for (DWORD v = 39070; v <= 39077; ++v)
			r.shards.push_back(WeightedVnum{ v, 1 });
		r.shards.push_back(WeightedVnum{ 39081, 1 });
		// MT2009_PLUS_BOT_BONUS67_V1: the colours of the two forests' item levels (the header above)
		// MT2009_PLUS_SEONHAE_YOHARA_V1: every Yohara map draws all twelve shards by its profile (353's 3:1 and 404's
		// 3:1:1 of MT2009_PLUS_BOT_BONUS67_V1 kept as the profiles' main colours)
		r.shardPicks.clear();
		r.yoharaShardMaps.clear();
		AddYoharaShardProfile(r, YOHARA_SUNGMA_SHARD_MAPS, sizeof(YOHARA_SUNGMA_SHARD_MAPS) / sizeof(YOHARA_SUNGMA_SHARD_MAPS[0]),
				YOHARA_SUNGMA_PICK, sizeof(YOHARA_SUNGMA_PICK) / sizeof(YOHARA_SUNGMA_PICK[0]));
		AddYoharaShardProfile(r, YOHARA_RIFT_SHARD_MAPS, sizeof(YOHARA_RIFT_SHARD_MAPS) / sizeof(YOHARA_RIFT_SHARD_MAPS[0]),
				YOHARA_RIFT_PICK, sizeof(YOHARA_RIFT_PICK) / sizeof(YOHARA_RIFT_PICK[0]));
		AddYoharaShardProfile(r, YOHARA_FOREST_SHARD_MAPS, sizeof(YOHARA_FOREST_SHARD_MAPS) / sizeof(YOHARA_FOREST_SHARD_MAPS[0]),
				YOHARA_FOREST_PICK, sizeof(YOHARA_FOREST_PICK) / sizeof(YOHARA_FOREST_PICK[0]));
		r.shardLevelGap = YOHARA_SHARD_LEVEL_GAP;
	}

	DropRules s_drops;
	bool s_dropsLoaded = false;
	time_t s_dropsMtime = (time_t)-1;
	DWORD s_dropsNextCheck = 0;

	void LoadDropRules(DropRules& r)
	{
		DefaultDropRules(r);
		std::ifstream in(DROPS_PATH);
		if (!in)
			return;
		DropRules f;
		f.additivePermille = r.additivePermille;
		f.shardChance = r.shardChance;
		f.shardLevelGap = r.shardLevelGap;	// MT2009_PLUS_SEONHAE_YOHARA_V1
		bool hasYoharaMaps = false;			// MT2009_PLUS_SEONHAE_YOHARA_V1
		bool hasAddPct = false, hasAddMaps = false, hasMobs = false, hasShardPct = false, hasShardMaps = false, hasShards = false;
		bool hasPicks = false;	// MT2009_PLUS_BOT_BONUS67_V1
		std::string line;
		int lineNo = 0;
		while (std::getline(in, line))
		{
			++lineNo;
			const size_t hash = line.find('#');
			if (hash != std::string::npos)
				line.erase(hash);
			std::istringstream ss(line);
			std::string key;
			if (!(ss >> key))
				continue;
			long a = 0, b = 0, c = 0;
			double d = 0.0;
			bool ok = false;
			if (key == "additive_chance")
			{
				ok = (ss >> d) && d >= 0.0 && d <= 100.0;
				if (ok) { f.additivePermille = (int)(d * 10.0 + 0.5); hasAddPct = true; }
			}
			else if (key == "additive_map" || key == "mob")
			{
				ok = (ss >> a >> b >> c) && a > 0 && SupportPct((DWORD)b) > 0 && c >= 1 && c <= 50;
				if (ok && key == "additive_map") { f.additiveMaps[a] = VnumCount{ (DWORD)b, (int)c }; hasAddMaps = true; }
				if (ok && key == "mob") { f.mobs[(DWORD)a] = VnumCount{ (DWORD)b, (int)c }; hasMobs = true; }
			}
			else if (key == "shard_chance")
			{
				ok = (ss >> d) && d >= 0.0 && d <= 100.0;
				if (ok) { f.shardChance = (int)(d * 1000.0 + 0.5); hasShardPct = true; }
			}
			else if (key == "shard_map")
			{
				ok = (ss >> a) && a > 0;
				if (ok) { f.shardMaps.insert(a); hasShardMaps = true; }
			}
			else if (key == "shard_map_yohara")	// MT2009_PLUS_SEONHAE_YOHARA_V1
			{
				ok = (ss >> a) && a > 0;
				if (ok) { f.yoharaShardMaps.insert(a); hasYoharaMaps = true; }
			}
			else if (key == "shard_level_gap")	// MT2009_PLUS_SEONHAE_YOHARA_V1
			{
				ok = (ss >> a) && a >= 0 && a <= 300;
				if (ok) f.shardLevelGap = (int)a;
			}
			else if (key == "shard")
			{
				ok = (ss >> a >> b) && IsShardVnum((DWORD)a) && b > 0;
				if (ok) { f.shards.push_back(WeightedVnum{ (DWORD)a, (int)b }); hasShards = true; }
			}
			else if (key == "shard_pick")	// MT2009_PLUS_BOT_BONUS67_V1: shard_pick <map> <shard vnum> <weight>
			{
				ok = (ss >> a >> b >> c) && a > 0 && IsShardVnum((DWORD)b) && c > 0;
				if (ok) { f.shardPicks[a].push_back(WeightedVnum{ (DWORD)b, (int)c }); hasPicks = true; }
			}
			std::string extra;
			if (ok && (ss >> extra))
				ok = false;
			if (!ok)
				sys_err("SEONHAE: %s line %d ignored: %s", DROPS_PATH, lineNo, line.c_str());
		}
		if (hasAddPct) r.additivePermille = f.additivePermille;
		if (hasAddMaps) r.additiveMaps = f.additiveMaps;
		if (hasMobs) r.mobs = f.mobs;
		if (hasShardPct) r.shardChance = f.shardChance;
		if (hasShardMaps) r.shardMaps = f.shardMaps;
		if (hasShards) r.shards = f.shards;
		// MT2009_PLUS_SEONHAE_YOHARA_V1: a file's colours replace only the maps they name; an old file's (no
		// shard_map_yohara line) for the Yohara list's maps are its old defaults and give way to the profiles
		const std::set<long> defaultYohara = r.yoharaShardMaps;
		if (hasPicks)
			for (std::map<long, std::vector<WeightedVnum> >::const_iterator it = f.shardPicks.begin(); it != f.shardPicks.end(); ++it)
				if (hasYoharaMaps || !defaultYohara.count(it->first))
					r.shardPicks[it->first] = it->second;
		if (hasYoharaMaps) r.yoharaShardMaps = f.yoharaShardMaps;
		r.shardLevelGap = f.shardLevelGap;
	}

	// MT2009_PLUS_SEONHAE_YOHARA_V1: a shard map of either list
	bool IsShardMap(const DropRules& r, long map)
	{
		return r.shardMaps.count(map) || r.yoharaShardMaps.count(map);
	}

	// MT2009_PLUS_SEONHAE_YOHARA_V1: the level rule of the Yohara list's maps - the monster at most shard_level_gap
	// levels under the killer
	bool ShardLevelOk(const DropRules& r, long map, LPCHARACTER victim, LPCHARACTER killer)
	{
		if (r.shardLevelGap <= 0 || !r.yoharaShardMaps.count(map))
			return true;
		return (int)killer->GetLevel() <= (int)victim->GetLevel() + r.shardLevelGap;
	}

	const DropRules& Drops()
	{
		const DWORD now = get_dword_time();
		if (!s_dropsLoaded || (int)(now - s_dropsNextCheck) >= 0)
		{
			s_dropsNextCheck = now + DROPS_RECHECK_MS;
			struct stat st;
			const time_t mtime = stat(DROPS_PATH, &st) == 0 ? st.st_mtime : (time_t)0;
			if (!s_dropsLoaded || mtime != s_dropsMtime)
			{
				LoadDropRules(s_drops);
				s_dropsMtime = mtime;
				s_dropsLoaded = true;
				sys_log(0, "SEONHAE: drop rules %s (additive maps %u, mobs %u, shard maps %u, Yohara shard maps %u, level gap %d)",
						mtime ? "read from the file" : "at their defaults", (unsigned int)s_drops.additiveMaps.size(),
						(unsigned int)s_drops.mobs.size(), (unsigned int)s_drops.shardMaps.size(),
						(unsigned int)s_drops.yoharaShardMaps.size(), s_drops.shardLevelGap);
			}
		}
		return s_drops;
	}

	DWORD PickWeighted(const std::vector<WeightedVnum>& v)
	{
		int total = 0;
		for (size_t i = 0; i < v.size(); ++i)
			total += std::max(0, v[i].weight);
		if (total <= 0)
			return 0;
		int roll = number(1, total);
		for (size_t i = 0; i < v.size(); ++i)
		{
			roll -= std::max(0, v[i].weight);
			if (roll <= 0)
				return v[i].vnum;
		}
		return v.back().vnum;
	}

	// MT2009_PLUS_BOT_BONUS67_V1: the shard of a kill on a shard map - the map's own colours (shard_pick) or the table's
	DWORD PickShard(const DropRules& r, long map)
	{
		std::map<long, std::vector<WeightedVnum> >::const_iterator pick = r.shardPicks.find(map);
		return pick != r.shardPicks.end() && !pick->second.empty() ? PickWeighted(pick->second) : PickWeighted(r.shards);
	}

	void AddDrop(std::vector<LPITEM>& out, DWORD vnum, int count)
	{
		if (!vnum || count <= 0 || !ITEM_MANAGER::instance().GetTable(vnum))
			return;
		LPITEM item = ITEM_MANAGER::instance().CreateItem(vnum, (ITEM_COUNT)count, 0, true);
		if (item)
			out.emplace_back(item);
	}
}

// Asked by the engine's ITEM_MANAGER::CreateDropItem (item_manager.cpp,
// MT2009_PLUS_SEONHAE_V1 (drop)) for every kill that drops at all.
void Mt2009PlusSeonHaeDrop(LPCHARACTER victim, LPCHARACTER killer, std::vector<LPITEM>& out)
{
	using namespace mt2009_seonhae;
#ifdef MT2009_PLUS_BOT_SEONHAE_V2
	// MT2009_PLUS_BOT_SEONHAE_V2 (the owner, 28 October 2026: the ordinary shards drop for the bots too, as for the
	// players): a bot's kill rolls the shards by the same rules and chances; the additives stay the players'.
	if (!victim || victim->IsPC() || !killer || !killer->IsPC() || !killer->GetDesc())
		return;
	const bool botKiller = killer->GetDesc()->IsBot();
#else
	if (!victim || victim->IsPC() || !killer || !killer->IsPC() || !killer->GetDesc() || killer->GetDesc()->IsBot())
		return;
	const bool botKiller = false;
#endif
	if (!IsOn())
		return;
	const DropRules& r = Drops();
	const long map = victim->GetMapIndex() >= 10000 ? victim->GetMapIndex() / 10000 : victim->GetMapIndex();
	const bool bigOne = victim->IsStone() || victim->GetMobRank() >= MOB_RANK_BOSS;

	// the additives: a mob line first (any rank, any map), else the map's rule for Metins and bosses
	const VnumCount* additive = NULL;
	std::map<DWORD, VnumCount>::const_iterator mob = r.mobs.find(victim->GetRaceNum());
	if (mob != r.mobs.end())
		additive = &mob->second;
	else if (bigOne)
	{
		std::map<long, VnumCount>::const_iterator m = r.additiveMaps.find(map);
		if (m != r.additiveMaps.end())
			additive = &m->second;
	}
	if (additive && !botKiller && r.additivePermille > 0 && number(1, 1000) <= r.additivePermille)
		AddDrop(out, additive->vnum, additive->count);

	// the shards: ordinary monsters on the shard maps
	if (!bigOne && victim->IsMonster() && r.shardChance > 0 && IsShardMap(r, map) && ShardLevelOk(r, map, victim, killer) &&
		number(1, SHARD_CHANCE_SCALE) <= r.shardChance)
		AddDrop(out, PickShard(r, map), 1);	// MT2009_PLUS_BOT_BONUS67_V1: the map's own colours
}

// MT2009_PLUS_BOT_BONUS67_V1 (rift shards): Zaklety Las (SZC) (404) drops nothing (server-patches/szczelina,
// Mt2009PlusTimeRiftNoDrop) - the engine's no-drop return asks this one first: the shard of an ordinary monster of a
// shard map, by the rules above (the Grotto's chance, the map's colours), on the ground at the kill with the kill's
// ownership. The additives stay out (the wiki's "no drop" stands for everything else). A world drop: players and bots.
LPCHARACTER Mt2009PlusSidekickLootReceiver(LPCHARACTER ch, long lMapIndex, long x, long y);	// playerbot_manager.cpp

void Mt2009PlusSeonHaeRiftDrop(LPCHARACTER victim, LPCHARACTER killer, const PIXEL_POSITION& pos)
{
	using namespace mt2009_seonhae;
	if (!victim || victim->IsPC() || !victim->IsMonster() || !killer || !killer->IsPC() || !killer->GetDesc() || !IsOn())
		return;
	if (victim->IsStone() || victim->GetMobRank() >= MOB_RANK_BOSS)
		return;
	const DropRules& r = Drops();
	const long map = victim->GetMapIndex() >= 10000 ? victim->GetMapIndex() / 10000 : victim->GetMapIndex();
	if (r.shardChance <= 0 || !IsShardMap(r, map) || !ShardLevelOk(r, map, victim, killer) ||
			number(1, SHARD_CHANCE_SCALE) > r.shardChance)
		return;
	std::vector<LPITEM> out;
	AddDrop(out, PickShard(r, map), 1);
	if (out.empty())
		return;
	LPITEM item = out[0];
	item->AddToGround(victim->GetMapIndex(), pos);
	LPCHARACTER owner = Mt2009PlusSidekickLootReceiver(killer, victim->GetMapIndex(), victim->GetX(), victim->GetY());
	item->SetOwnership(owner ? owner : killer);
	item->StartDestroyEvent();
	sys_log(0, "SEONHAE: rift shard %u map %ld from %s (%u) for %s", item->GetVnum(), map, victim->GetName(),
			(unsigned int)victim->GetRaceNum(), (owner ? owner : killer)->GetName());
}
