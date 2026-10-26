#ifndef __INC_METIN2_PLAYERBOT_NAVIGATION_H__
#define __INC_METIN2_PLAYERBOT_NAVIGATION_H__

// Where a bot may stand, and how it gets from one place to another.
//
// Same kind of file as playerbot_types.h: an implementation fragment, not a
// normal header. It defines objects, it relies on the engine headers
// playerbot_manager.cpp includes above it, and its anonymous namespace is
// deliberately the same one the manager reopens -- in a single translation
// unit those merge. Include it exactly once, from playerbot_manager.cpp.
//
// Nothing here knows what a bot wants. It answers only questions about the
// world: is this cell standable, can these two points reach each other, what
// is the route. That is why it is the one subsystem that can be lifted out
// whole -- it calls nothing above it.

// MT2009_PLUS_BOT_NAV_GUILD_BUILDINGS_V1: g_pfnMt2009ObjectAreaChanged (enginefixes).
#include "building.h"

namespace
{
	// ------------------------------------------------------------------------
	// Playerbot navigation
	//
	// The stock CHARACTER::Goto() does not perform collision checks, so every
	// segment handed to it has to be proven safe here first. That is the whole
	// reason this exists: a route is emitted only once each of its segments has
	// been validated against server_attr, at the native 50-unit resolution so
	// that narrow bridges survive and a character standing on a valid cell can
	// always attach to the planning graph.
	// ------------------------------------------------------------------------

	// Plan at the native server_attr resolution.  Besides preserving narrow
	// bridges and walls, this guarantees that a character standing on a valid
	// native cell can always attach to the planning graph.
	const int PLAYERBOT_NAV_CELL = 50;
	// How far the goal of a portal walk may be snapped, in cells.
	//
	// It was twenty-four - twelve hundred world units - against a switch
	// distance of two hundred, so a route could legitimately end a thousand
	// units short of the portal and the arrival test could never pass. The bot
	// stood at the end of its route, the walk timed out after twenty seconds,
	// and the next tick planned the same thing again: "portal walk stalled ...
	// distance=323" a hundred times a minute, bots piled at the Bokjung
	// teleporter, and of a hundred and fifteen that set off across the desert
	// for the Spider Dungeon not one ever arrived.
	//
	// This is the trap MovePlayerBotTownLeg already sprang once and the same
	// rule closes it: a snapped goal must stay inside the radius that tests
	// arrival. Half of that radius, so the walk still has somewhere to land if
	// the exact cell is occupied - every portal point in this world stands on
	// open ground, checked against server_attr, so it rarely has to.
	const int PLAYERBOT_PORTAL_SNAP_CELLS =
			PLAYERBOT_PORTAL_SWITCH_DISTANCE / PLAYERBOT_NAV_CELL / 2;
	// What a step through water costs on top of the ordinary ten. High enough
	// that a bot walks round a lake it could wade across, low enough that a
	// twelve-cell bridge - which is the only way off an island - is never worth
	// refusing: crossing one costs 240 against a detour measured in thousands.
	const int PLAYERBOT_NAV_WATER_PENALTY = 20;
	const int PLAYERBOT_NAV_NATIVE_SAMPLE = 50;
	const int PLAYERBOT_NAV_CLUSTER_CELLS = 16;
	const int PLAYERBOT_NAV_MAX_PORTALS_PER_NEIGHBOR = 4;
	const int PLAYERBOT_NAV_MAX_SEGMENT = 700;
	// Must stay below half a native cell.  A wider threshold lets the bot skip a
	// corner waypoint before clearing the wall and then oscillate on replans.
	// The desktop client interpolates a MOVE packet slightly ahead of the
	// authoritative position. Waiting until the server is within only 25 units
	// (25 cm) of a waypoint made the next packet point briefly behind the model,
	// which looked like a one-metre back-step at every small direction change.
	// Switch segments with a modest look-ahead and tolerate small drift of a
	// moving target; SegmentClearWorld still validates every new segment.
	const int PLAYERBOT_NAV_ARRIVAL_DISTANCE = 100;
	// How far to look for ground a character stuck inside scenery can step onto.
	// Three cells is a hundred and fifty units - wide enough for the doorway,
	// the plinth and the shop awning bots were found welded to, and narrow
	// enough that the step is a step and not a teleport.
	const int PLAYERBOT_NAV_ESCAPE_CELLS = 3;
	const int PLAYERBOT_NAV_GOAL_REPLAN_DISTANCE = 400;
	// A parked route is worth keeping from this many waypoints left, and is
	// resumed from a waypoint within this reach of where the fight ended.
	const size_t PLAYERBOT_NAV_PARK_MIN_WAYPOINTS = 6;
	const int PLAYERBOT_NAV_RESUME_DISTANCE = 2500;
	// This is one global budget for the manager update, not one budget per map.
	// Giving M1, M2, M3 and the Monkey Dungeon 64 searches each multiplied the
	// old M1 load by four. Already built routes still advance every update; only
	// new expensive HPA/A* requests wait for a later staggered slot.
	const int PLAYERBOT_NAV_MAX_HEAVY_PLANS_PER_TICK = 32;
	// What a plan costs against that budget, by distance bucket - because the
	// comment below says a count is the wrong unit and the code then charged
	// every plan one slot anyway.
	//
	// Measured over a minute at 839 bots: 7086 of 7440 plans were sub-64-cell
	// hops to the next monster, costing 41 milliseconds between them, while 148
	// long ones cost eleven of the twelve seconds. The hops filled the tick and
	// the long plans were the ones turned away - half of every request deferred,
	// and the walks to a portal starved outright: a bot was found waiting
	// thirteen minutes for a route, standing at the Sohan exit mounting and
	// dismounting its horse every twenty seconds. A hop is free now and distance
	// pays; the microsecond budget below still bounds the whole tick.
	const int PLAYERBOT_NAV_PLAN_COST[4] = { 0, 1, 3, 8 };
	// A request nobody has answered for this many attempts stops queueing behind
	// the count. It still waits for the microsecond budget and for the far-plan
	// minute, so this cannot open a hole - it only stops one bot being last in
	// the queue for ever, which is what a fair queue exists to prevent and what
	// this world did not have.
	const BYTE PLAYERBOT_NAV_STARVED_ATTEMPTS = 20;
	const int PLAYERBOT_NAV_MAX_EXPANDED_NODES = 120000;
	// A count is the wrong unit for the budget: a hop to the next monster plans
	// in a fifth of a millisecond and a crossing of Orc Valley in eighty, so
	// thirty-two of the latter held the whole core for half a second and every
	// player on it felt the tick. The clock is the budget now, alongside the
	// count: once a tick has spent this long planning, the rest of the requests
	// take the deferred path and come back within two seconds. Fifty
	// milliseconds four times a second is a fifth of the core at the most;
	// the population asks for a tenth in the steady state, so this binds only
	// in the minute after a start, which is exactly when it should.
	const DWORD PLAYERBOT_NAV_PLAN_TIME_BUDGET_US = 50000;
	// The tick budget cannot stop a plan that has already started, and a far
	// plan on Orc Valley runs 150-700 ms: a hundred and twenty of them a
	// minute were twenty-five seconds of every sixty at 850 bots, with the
	// tick at 28 s and the core at 55%. Past this many far plans in a minute
	// the rest take the deferred path - the bot stands a second or two and
	// asks again - so the worst minute costs what this many plans cost.
	const int PLAYERBOT_NAV_MAX_FAR_PLANS_PER_MINUTE = 80;
	// The corridor search weighs its heuristic double, which is already a
	// greedy search. A corridor this many regions long - sixteen cells each,
	// so forty is a walk of six hundred cells - takes triple: the route bends
	// a little more and the search expands a third as much.
	const int PLAYERBOT_NAV_GREEDY_CORRIDOR_REGIONS = 40;
	const int PLAYERBOT_NAV_GREEDY_WEIGHT = 3;
	// A cell the corridor search has taken off the heap stays closed. A
	// weighted heuristic is inconsistent - a cell can be reached cheaper
	// after it was expanded - and the search used to reopen it every time,
	// so on a map whose water penalties make many routes nearly equal the
	// same cells were expanded again and again: single plans of four and
	// five seconds on Orc Valley, each a tick the whole core stood still
	// for, and the client lagging every ten to twenty seconds (sizowski,
	// 12 September; my own world planned the same map in under half a
	// second). Closed once, a cell costs one expansion and the corridor
	// bounds the search; the route is a shade longer at worst. A hard cap
	// stands behind that: past it the search hands back the best partial
	// route it has - to the cell nearest the goal - and the walk plans the
	// rest from there (TPlayerBotAIState::bRoutePartial).
	const int PLAYERBOT_NAV_MAX_CORRIDOR_EXPANSIONS = 60000;
	// What a partial route has to gain to be worth walking: this many cells
	// nearer the goal than where the bot stands, or the search has failed.
	const int PLAYERBOT_NAV_PARTIAL_MIN_GAIN_CELLS = 16;
	// A plan this long, whatever its distance bucket, says so in the log
	// with its parts - the abstract search, the corridor, the cells it
	// expanded - so the next slow world can be read rather than guessed.
	const DWORD PLAYERBOT_NAV_SLOW_PLAN_MS = 250;
	// The route cache. A far plan on Orc Valley costs 150-250 ms and most of
	// them are the same trip - the entrance to a hub, a hub to the exit, hub
	// to hub - asked for by bot after bot from within a few hundred units of
	// the same spot. Start and goal are quantised to this many cells, a hit
	// must stand within this reach of the cached start, and a route is kept
	// this long: the grid it was planned on is static, only the live objects
	// the walk checks for could have moved.
	// Keyed by the goal alone, and joined wherever the bot stands nearest to
	// the line: the goals are a few dozen hubs and exits, the starts are
	// everywhere, and a route to a hub is as good from its middle as from its
	// start. Several routes are kept per goal so the join is from a route that
	// came from this side.
	const int PLAYERBOT_NAV_CACHE_QUANTUM_CELLS = 24;
	const int PLAYERBOT_NAV_CACHE_MIN_CELLS = 256;
	// Sixteen routes a goal and half an hour, up from six and ten minutes:
	// the same four hub goals took half the far plans in a minute, and six
	// routes cover six approaches to a hub that is walked to from every
	// island. A route is a few hundred waypoints; fifteen hundred of them are
	// a couple of megabytes.
	const int PLAYERBOT_NAV_CACHE_JOIN_DISTANCE = 2400;
	const DWORD PLAYERBOT_NAV_CACHE_TTL = 1800000;
	const size_t PLAYERBOT_NAV_CACHE_PER_GOAL = 16;
	const size_t PLAYERBOT_NAV_CACHE_LIMIT = 1500;
	DWORD s_dwPlayerBotNavBudgetStamp = 0;
	int s_iPlayerBotNavHeavyPlansThisTick = 0;
	DWORD s_uPlayerBotNavPlanUsThisTick = 0;
	DWORD s_dwPlayerBotNavFarMinuteStamp = 0;
	int s_iPlayerBotNavFarPlansThisMinute = 0;
	// Which budget refused the last plan. Three different limits returned the
	// same DEFERRED and the log could not tell them apart, so a deferral was
	// read more than once as a destination with no route to it.
	const char* s_szPlayerBotNavDeferReason = "none";
	// A walk to a world portal (MovePlayerBotToWorldPortal) sets this for its
	// one plan: such a plan is not queued behind the per-tick count nor the
	// far plans of the minute - on the busiest channel those turned the long
	// walks to the Teleporter away until the walk stalled and the bot went
	// back to its hunting ground (upstream 2.2.39). The tick's microsecond
	// budget still applies.
	bool s_bPlayerBotNavPortalPlan = false;

	// MT2009_PLUS_BOT_NAV_SHARED_SCRATCH_V1: the working arrays of a path search
	// (the cell stamps, g-costs and parents of the fine A*/BFS, ten bytes a cell,
	// and the same for the abstract region search) used to sit in every map's
	// grid - 94 MB on each 3072x3072 map, idle whenever another map planned. The
	// core is single-threaded and plans one route at a time, so every map now
	// shares one set, grown on demand to the largest grid that has searched.
	// What a map owns stays its own: walkability, water, clearance, component
	// and region ids (PLAYERBOT_NAV_GRID_BYTES_PER_CELL) and the HPA graph.
	// The stamps are global too, so a stamp left by another map's search never
	// matches the running one.
	// MT2009_PLUS_BOT_NAV_PACKED_CELLS_V1: the flags byte (1) and the 16-bit
	// component and region ids (2 + 2); 11 before.
	const unsigned int PLAYERBOT_NAV_GRID_BYTES_PER_CELL = 5;
	const BYTE PLAYERBOT_NAV_CELL_BLOCKED = 1 << 0;
	const BYTE PLAYERBOT_NAV_CELL_WATER = 1 << 1;
	const int PLAYERBOT_NAV_CELL_CLEARANCE_SHIFT = 2;
	const int PLAYERBOT_NAV_CELL_CLEARANCE_MASK = 7;
	const unsigned int PLAYERBOT_NAV_SCRATCH_BYTES_PER_CELL = 10;
	// A grid (or a scratch growth) that did not fit in the 32-bit address space
	// is not retried before this: the map's bots walk without route planning.
	const DWORD PLAYERBOT_NAV_NOGRID_RETRY_MS = 10 * 60 * 1000;
	struct TPlayerBotNavScratch
	{
		std::vector<uint16_t> nodeToken;
		std::vector<int> nodeCost;
		std::vector<int> parent;
		uint16_t searchToken;
		std::vector<DWORD> regionToken;
		std::vector<int> regionCost;
		std::vector<int> regionParent;
		std::vector<int> regionParentEdge;
		DWORD regionSearchToken;
		// Set while a search runs: a search started from inside another one
		// would overwrite its stamps, so it is refused instead (none does today).
		bool bBusy;
		bool bReentryLogged;
	};
	TPlayerBotNavScratch s_playerBotNavScratch = TPlayerBotNavScratch();

	enum EPlayerBotNavPlanResult
	{
		PLAYERBOT_NAV_PLAN_FOUND,
		PLAYERBOT_NAV_PLAN_DEFERRED,
		PLAYERBOT_NAV_PLAN_UNREACHABLE
	};

	DWORD PlayerBotNavHash(DWORD value)
	{
		value ^= value >> 16;
		value *= 0x7feb352dU;
		value ^= value >> 15;
		value *= 0x846ca68bU;
		value ^= value >> 16;
		return value;
	}

	bool IsPlayerBotPositionBlocked(long lMapIndex, long x, long y)
	{
		LPSECTREE_MAP map = SECTREE_MANAGER::instance().GetMap(lMapIndex);
		if (!map)
			return true;

		const TMapSetting& setting = map->m_setting;
		if (x < setting.iBaseX || y < setting.iBaseY ||
			x >= setting.iBaseX + setting.iWidth || y >= setting.iBaseY + setting.iHeight)
			return true;

		LPSECTREE tree = SECTREE_MANAGER::instance().Get(lMapIndex, x, y);
		if (!tree || !tree->GetAttributePtr())
			return true;

		// ATTR_BLOCK is the map's statement that nothing may stand here, and it
		// is the only one the engine itself tests for movement. ATTR_WATER
		// describes the terrain: a river carries both bits, a bridge deck over
		// that river carries water without block, and so does a shallow shore.
		// Refusing water refused the bridges - see IsPlayerBotPositionWater.
		return tree->IsAttr(x, y, ATTR_BLOCK | ATTR_OBJECT);
	}

	// Passable, but wet. Orc Valley is islands in a delta and its twenty-two
	// bridges are the only cells joining them; the desert's shallows are eighty
	// thousand cells of water nobody needs to wade through. Both are walkable and
	// only one of them should be attractive, so this feeds a path cost rather
	// than a wall.
	bool IsPlayerBotPositionWater(long lMapIndex, long x, long y)
	{
		LPSECTREE tree = SECTREE_MANAGER::instance().Get(lMapIndex, x, y);
		if (!tree || !tree->GetAttributePtr())
			return false;
		return tree->IsAttr(x, y, ATTR_WATER) &&
				!tree->IsAttr(x, y, ATTR_BLOCK);
	}

	bool IsPlayerBotSafeZone(long lMapIndex, long x, long y)
	{
		LPSECTREE tree = SECTREE_MANAGER::instance().Get(lMapIndex, x, y);
		return tree && tree->GetAttributePtr() && tree->IsAttr(x, y, ATTR_BANPK);
	}

	class CPlayerBotNavigation
	{
		private:
			struct TAbstractEdge
			{
				DWORD toRegion;
				int fromCell;
				int toCell;
				BYTE clearance;
			};

			struct TAbstractRegion
			{
				int clusterX;
				int clusterY;
				std::vector<TAbstractEdge> edges;
			};

		public:
			static CPlayerBotNavigation& instance(long mapIndex = PLAYERBOT_MAP_CHUNJO_M1)
			{
				// Each map owns its grid, component labels, HPA regions and per-tick
				// search budget. A single mutable instance would rebuild millions of
				// cells whenever updates alternated between M1, M2 and the dungeon.
				// A dungeon instance walks its map's own ground: the grid is the
				// base map's, keyed and built by its index (a private map carries
				// the same attributes), so no instance builds one of its own.
				if (mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN)
					mapIndex /= 10000;
				static std::map<long, CPlayerBotNavigation*> s_navigations;
				std::map<long, CPlayerBotNavigation*>::iterator it =
						s_navigations.find(mapIndex);
				if (it == s_navigations.end())
				{
					CPlayerBotNavigation* navigation = new CPlayerBotNavigation();
					s_navigations.insert(std::make_pair(mapIndex, navigation));
					return *navigation;
				}
				return *it->second;
			}

			CPlayerBotNavigation() :
				m_initialized(false),
				m_mapIndex(0),
				m_baseX(0),
				m_baseY(0),
				m_width(0),
				m_height(0)
			{
			}

			bool Init(long mapIndex)
			{
				if (mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN)
					mapIndex /= 10000;
				// MT2009_PLUS_ZODIAC_NAV_V1: no grid for an open arena map (playerbot_types.h).
				if (IsPlayerBotOpenArenaMap(mapIndex))
					return false;
				// Every kingdom's own four maps, not only Chunjo's: a Shinsoo bot
				// standing on map 1 with no grid here cannot plan a step, and the
				// whole of its local life is on 1, 3, 4 and 5. IsKingdomMap covers
				// all twelve; the shared maps are named one by one below because
				// only some of them are ours to walk.
				if (!playerbot_empire_rules::IsKingdomMap(mapIndex) &&
						!IsPlayerBotMonkeyMap(mapIndex) &&
						mapIndex != PLAYERBOT_MAP_ORC_VALLEY &&
						mapIndex != PLAYERBOT_MAP_DESERT &&
						mapIndex != PLAYERBOT_MAP_SOHAN &&
						mapIndex != PLAYERBOT_MAP_SPIDER_V1 &&
						mapIndex != PLAYERBOT_MAP_SPIDER_V2 &&
						mapIndex != PLAYERBOT_MAP_HWANG &&
						mapIndex != PLAYERBOT_MAP_FOREST &&
						mapIndex != PLAYERBOT_MAP_RED_FOREST &&
						mapIndex != PLAYERBOT_MAP_DEMON_TOWER &&
						mapIndex != PLAYERBOT_MAP_FIRE_LAND &&
						mapIndex != PLAYERBOT_MAP_GROTTO_V1 &&
						mapIndex != PLAYERBOT_MAP_GROTTO_V2 &&
						mapIndex != PLAYERBOT_MAP_OCHAO && // MT2009_PLUS_OCHAO_BOTS_V1
						!IsPlayerBotWzMap(mapIndex) && // MT2009_PLUS_MAPS_WZ_BOTS_V1 (Wezowe Pole / Kraina Gigantow, when hosted)
						!IsPlayerBotArezzoMap(mapIndex) && // MT2009_PLUS_AREZZO_BOTS_V1 (TransitionPlayerBotMap lets only the test cohorts in)
						!(mapIndex >= 364 && mapIndex <= 366) && // MT2009_PLUS_AREZZO_DUNGEON_BOTS_V1 (the dungeon cohort's lobbies and runs)
						!IsPlayerBotPartyDungeonMap(mapIndex) && // MT2009_PLUS_BOT_DUNGEONS_ALL_V1 (208, 351, 352, 363: a person's party bots inside)
						mapIndex != PLAYERBOT_MAP_CATACOMB &&
						mapIndex != 110 && // MT2009_PLUS_GUILD_WAR_ARENA_V1 (the battle arena, playerbot_guild_war.h)
						// MT2009_PLUS_BOT_YOHARA_HANDOVER_V1: Zaklety Las (353) and the 90-level maps 301-304 of the
						// loot runs, all on game3 (MT2009_PLUS_237_NEWCORE_V1; the Yohara core on the Yohara line) -
						// built only where a handed-over bot stands (playerbot_yohara_bots.h); 353 ~53 MB, 301-304 80-160 MB.
						mapIndex != PLAYERBOT_MAP_ZAKLETY && !(mapIndex >= 301 && mapIndex <= 304))
					return false;

				if (m_initialized && m_mapIndex == mapIndex)
					return true;
				// MT2009_PLUS_BOT_NAV_SHARED_SCRATCH_V1: a grid that did not fit is not
				// retried on every call - its bots walk without route planning for a while.
				if (m_dwNavOffUntil && (long)(get_dword_time() - m_dwNavOffUntil) < 0)
					return false;

				LPSECTREE_MAP map = SECTREE_MANAGER::instance().GetMap(mapIndex);
				if (!map)
					return false;

				const TMapSetting& setting = map->m_setting;
				if (setting.iWidth <= 0 || setting.iHeight <= 0)
					return false;

				m_initialized = false;
				m_mapIndex = mapIndex;
				m_baseX = setting.iBaseX;
				m_baseY = setting.iBaseY;
				m_width = (setting.iWidth + PLAYERBOT_NAV_CELL - 1) / PLAYERBOT_NAV_CELL;
				m_height = (setting.iHeight + PLAYERBOT_NAV_CELL - 1) / PLAYERBOT_NAV_CELL;

				const size_t cellCount = (size_t)m_width * (size_t)m_height;
				// MT2009_PLUS_NAV_GRID_NOMEM_V1: the 32-bit core runs close to its
				// address-space limit; a failed grid allocation must not abort it.
				// MT2009_PLUS_BOT_NAV_SHARED_SCRATCH_V1: the whole build is guarded now,
				// not only the first four arrays - the components, the HPA regions and
				// their temporary queues allocate too, and any of them used to abort.
				size_t walkableCount = 0;
				DWORD componentCount = 0;
				DWORD abstractRegionCount = 0;
				try
				{
					// MT2009_PLUS_BOT_NAV_PACKED_CELLS_V1: one byte of flags and 16-bit ids.
					m_cell.assign(cellCount, PLAYERBOT_NAV_CELL_BLOCKED);
					std::vector<DWORD>().swap(m_componentWide);
					m_component.assign(cellCount, 0);

					for (int gy = 0; gy < m_height; ++gy)
					{
						for (int gx = 0; gx < m_width; ++gx)
						{
							bool blocked = false;
							bool wet = false;
							const long cellX = m_baseX + gx * PLAYERBOT_NAV_CELL;
							const long cellY = m_baseY + gy * PLAYERBOT_NAV_CELL;

							// A planning cell is safe only if every native 50x50 cell
							// inside it is safe.  This prevents thin walls and shorelines
							// from disappearing through downsampling.
							for (int oy = PLAYERBOT_NAV_NATIVE_SAMPLE / 2;
									oy < PLAYERBOT_NAV_CELL && !blocked;
									oy += PLAYERBOT_NAV_NATIVE_SAMPLE)
							{
								for (int ox = PLAYERBOT_NAV_NATIVE_SAMPLE / 2;
										ox < PLAYERBOT_NAV_CELL;
										ox += PLAYERBOT_NAV_NATIVE_SAMPLE)
								{
									if (IsPlayerBotPositionBlocked(mapIndex, cellX + ox, cellY + oy))
									{
										blocked = true;
										break;
									}
									if (IsPlayerBotPositionWater(mapIndex, cellX + ox, cellY + oy))
										wet = true;
								}
							}

							const int index = Index(gx, gy);
							m_cell[index] = blocked ? PLAYERBOT_NAV_CELL_BLOCKED :
									(wet ? PLAYERBOT_NAV_CELL_WATER : 0);
							if (!blocked)
								++walkableCount;
						}
					}
					m_walkableCells = (DWORD)walkableCount;

					BuildClearance();
					componentCount = BuildComponents();
					abstractRegionCount = BuildAbstractRegions();
				}
				catch (const std::bad_alloc&)
				{
					ReleaseGrid();
					m_mapIndex = 0;
					OnNavAllocFailed(mapIndex, (unsigned long long)cellCount * PLAYERBOT_NAV_GRID_BYTES_PER_CELL,
							"grid");
					return false;
				}
				m_dwNavOffUntil = 0;
				m_initialized = true;

				sys_log(0, "PLAYERBOT_NAV: initialized map=%ld base=(%ld,%ld) grid=%dx%d cell=%d walkable=%u components=%u abstract_regions=%u",
						m_mapIndex, m_baseX, m_baseY, m_width, m_height, PLAYERBOT_NAV_CELL,
						(unsigned int)walkableCount, (unsigned int)componentCount,
						(unsigned int)abstractRegionCount);
				return true;
			}

			// MT2009_PLUS_BOT_NAV_PACKED_CELLS_V1: the packed cell and the 16-bit ids.
			bool IsBlockedIndex(int index) const
			{
				return (m_cell[index] & PLAYERBOT_NAV_CELL_BLOCKED) != 0;
			}

			bool IsWaterIndex(int index) const
			{
				return (m_cell[index] & PLAYERBOT_NAV_CELL_WATER) != 0;
			}

			BYTE Clearance(int index) const
			{
				return (BYTE)((m_cell[index] >> PLAYERBOT_NAV_CELL_CLEARANCE_SHIFT) & PLAYERBOT_NAV_CELL_CLEARANCE_MASK);
			}

			void SetClearance(int index, BYTE clearance)
			{
				m_cell[index] = (BYTE)((m_cell[index] & ~(PLAYERBOT_NAV_CELL_CLEARANCE_MASK << PLAYERBOT_NAV_CELL_CLEARANCE_SHIFT)) |
						((clearance & PLAYERBOT_NAV_CELL_CLEARANCE_MASK) << PLAYERBOT_NAV_CELL_CLEARANCE_SHIFT));
			}

			DWORD ComponentAt(int index) const
			{
				return m_componentWide.empty() ? (DWORD)m_component[index] : m_componentWide[index];
			}

			void SetComponent(int index, DWORD component)
			{
				if (m_componentWide.empty() && component > 0xffffU)
					WidenIds(m_component, m_componentWide, "component");
				if (m_componentWide.empty())
					m_component[index] = (uint16_t)component;
				else
					m_componentWide[index] = component;
			}

			DWORD CellRegion(int index) const
			{
				return m_cellRegionWide.empty() ? (DWORD)m_cellRegion[index] : m_cellRegionWide[index];
			}

			void SetCellRegion(int index, DWORD region)
			{
				if (m_cellRegionWide.empty() && region > 0xffffU)
					WidenIds(m_cellRegion, m_cellRegionWide, "region");
				if (m_cellRegionWide.empty())
					m_cellRegion[index] = (uint16_t)region;
				else
					m_cellRegionWide[index] = region;
			}

			// The 32-bit fallback: copies the ids built so far and drops the
			// 16-bit array (a bad_alloc here ends the build like any other).
			void WidenIds(std::vector<uint16_t>& narrow, std::vector<DWORD>& wide, const char* what)
			{
				wide.assign(narrow.begin(), narrow.end());
				std::vector<uint16_t>().swap(narrow);
				sys_log(0, "PLAYERBOT_NAV: map=%ld %s ids exceed 16 bits, using 32-bit ids for it", m_mapIndex, what);
			}

			bool IsInitializedFor(long mapIndex) const
			{
				return m_initialized && m_mapIndex == mapIndex;
			}

			bool IsInsideWorld(long x, long y) const
			{
				return m_initialized && x >= m_baseX && y >= m_baseY &&
					x < m_baseX + m_width * PLAYERBOT_NAV_CELL &&
					y < m_baseY + m_height * PLAYERBOT_NAV_CELL;
			}

			void ClampWorld(long& x, long& y) const
			{
				if (!m_initialized)
					return;
				x = std::max(m_baseX + (long)PLAYERBOT_NAV_CELL,
						std::min(m_baseX + (long)m_width * PLAYERBOT_NAV_CELL - PLAYERBOT_NAV_CELL, x));
				y = std::max(m_baseY + (long)PLAYERBOT_NAV_CELL,
						std::min(m_baseY + (long)m_height * PLAYERBOT_NAV_CELL - PLAYERBOT_NAV_CELL, y));
			}

			bool IsBlockedCell(int gx, int gy) const
			{
				return !IsInsideCell(gx, gy) || IsBlockedIndex(Index(gx, gy)) != 0;
			}

			// Is the character standing somewhere no step can be taken from?
			//
			// SegmentClearWorld tests the character's own cell before anything
			// else and gives up on it, so a bot whose cell the live world calls
			// blocked cannot walk anywhere at all: the planner reads the static
			// grid, plans a route out perfectly happily, and the first waypoint
			// is refused. The route is dropped and replanned two hundred
			// milliseconds later, identically, for as long as the bot lives.
			// Measured at four different portals on three maps: forty-two
			// refusals in twenty seconds, no movement, and not one line in any
			// log. The two grids disagree wherever something was placed after
			// the static one was built, and near a portal that is common -
			// portals stand against scenery.
			//
			// Returns a nearby cell that both grids call free, so the caller can
			// step off before asking for a route again.
			bool FindEscapeFromBlockedCell(long x, long y, long& outX, long& outY) const
			{
				if (!m_initialized || !IsInsideWorld(x, y))
					return false;
				int gx, gy;
				WorldToCell(x, y, gx, gy);
				if (!IsLiveBlockedCell(gx, gy))
					return false;

				for (int radius = 1; radius <= PLAYERBOT_NAV_ESCAPE_CELLS; ++radius)
				{
					for (int dy = -radius; dy <= radius; ++dy)
					{
						for (int dx = -radius; dx <= radius; ++dx)
						{
							if (std::max(abs(dx), abs(dy)) != radius)
								continue;
							const int cx = gx + dx;
							const int cy = gy + dy;
							if (!IsInsideCell(cx, cy) || IsBlockedCell(cx, cy) ||
									IsLiveBlockedCell(cx, cy))
								continue;
							int wx = 0, wy = 0;
							CellToWorld(cx, cy, wx, wy);
							outX = wx;
							outY = wy;
							return true;
						}
					}
				}
				return false;
			}

			// The middle of the cell a point falls in - the point the planner
			// actually planned from and to.
			void CellCentreWorld(long x, long y, long& outX, long& outY) const
			{
				int gx = 0, gy = 0;
				WorldToCell(x, y, gx, gy);
				int wx = 0, wy = 0;
				CellToWorld(gx, gy, wx, wy);
				outX = wx;
				outY = wy;
			}

			bool SegmentClearWorld(long x0, long y0, long x1, long y1) const
			{
				if (!m_initialized || !IsInsideWorld(x0, y0) || !IsInsideWorld(x1, y1))
					return false;

				int gx0, gy0, gx1, gy1;
				WorldToCell(x0, y0, gx0, gy0);
				WorldToCell(x1, y1, gx1, gy1);

				// Exact supercover traversal for arbitrary endpoints, not merely a
				// Bresenham line between cell centres.  Every native cell touched by
				// the geometric segment is checked against live sectree attributes so
				// even a very short corner crossing and a newly placed ATTR_OBJECT are
				// detected.
				const long deltaX = x1 - x0;
				const long deltaY = y1 - y0;
				const int stepX = deltaX > 0 ? 1 : (deltaX < 0 ? -1 : 0);
				const int stepY = deltaY > 0 ? 1 : (deltaY < 0 ? -1 : 0);
				const long long absDeltaX = llabs((long long)deltaX);
				const long long absDeltaY = llabs((long long)deltaY);
				int gx = gx0;
				int gy = gy0;

				if (IsLiveBlockedCell(gx, gy))
					return false;

				while (gx != gx1 || gy != gy1)
				{
					long long crossX = LLONG_MAX;
					long long crossY = LLONG_MAX;
					if (stepX != 0)
					{
						const long boundaryX = m_baseX +
							(stepX > 0 ? (gx + 1) * PLAYERBOT_NAV_CELL : gx * PLAYERBOT_NAV_CELL);
						crossX = llabs((long long)boundaryX - x0) * absDeltaY;
					}
					if (stepY != 0)
					{
						const long boundaryY = m_baseY +
							(stepY > 0 ? (gy + 1) * PLAYERBOT_NAV_CELL : gy * PLAYERBOT_NAV_CELL);
						crossY = llabs((long long)boundaryY - y0) * absDeltaX;
					}

					if (crossX == crossY)
					{
						// A geometric corner belongs to both side cells.  Requiring both
						// to be clear also forbids diagonal corner cutting.
						if ((stepX != 0 && IsLiveBlockedCell(gx + stepX, gy)) ||
							(stepY != 0 && IsLiveBlockedCell(gx, gy + stepY)))
							return false;
						gx += stepX;
						gy += stepY;
					}
					else if (crossX < crossY)
						gx += stepX;
					else
						gy += stepY;

					if (IsLiveBlockedCell(gx, gy))
						return false;
				}

				return true;
			}

			bool CanReach(long startX, long startY, long targetX, long targetY) const
			{
				if (!m_initialized || !IsInsideWorld(startX, startY) ||
						!IsInsideWorld(targetX, targetY))
					return false;

				int sx, sy, tx, ty;
				WorldToCell(startX, startY, sx, sy);
				WorldToCell(targetX, targetY, tx, ty);
				if (!FindNearestWalkableCell(sx, sy, 4, 0, 0))
					return false;
				const DWORD component = ComponentAt(Index(sx, sy));
				if (component == 0)
					return false;
				// Resolve the target on its own terrain first and only then compare
				// components. Searching directly for our component near the target
				// would incorrectly bridge a lake or wall.
				if (!FindNearestWalkableCell(tx, ty, 2, 0, 0))
					return false;
				return ComponentAt(Index(tx, ty)) == component;
			}

			// A component under PLAYERBOT_NAV_POCKET_PERMILLE of the map's
			// walkable ground (see there).
			bool IsPocketComponent(DWORD component) const
			{
				return component != 0 && component < m_componentCells.size() &&
						(unsigned long long)m_componentCells[component] * 1000ULL <
						(unsigned long long)m_walkableCells * PLAYERBOT_NAV_POCKET_PERMILLE;
			}

			bool IsInPocketWorld(long x, long y) const
			{
				return IsPocketComponent(GetComponentAtWorld(x, y, 1));
			}

			// The nearest open cell that is no pocket's, ring by ring, as
			// FindNearestWalkableCell looks.
			bool FindNearestGroundOutsidePocketsWorld(long x, long y, int maxRadiusCells,
					PIXEL_POSITION& out, DWORD seed = 0) const
			{
				if (!m_initialized)
					return false;
				int originX, originY;
				WorldToCell(x, y, originX, originY);
				for (int radius = 0; radius <= maxRadiusCells; ++radius)
				{
					bool found = false;
					DWORD bestTie = 0xffffffffU;
					int bestX = originX;
					int bestY = originY;
					for (int gy = originY - radius; gy <= originY + radius; ++gy)
						for (int gx = originX - radius; gx <= originX + radius; ++gx)
						{
							if (std::max(abs(gx - originX), abs(gy - originY)) != radius ||
									IsBlockedCell(gx, gy))
								continue;
							const int index = Index(gx, gy);
							if (ComponentAt(index) == 0 || IsPocketComponent(ComponentAt(index)))
								continue;
							const DWORD tie = PlayerBotNavHash(seed ^ (DWORD)index);
							if (!found || tie < bestTie)
							{
								found = true;
								bestTie = tie;
								bestX = gx;
								bestY = gy;
							}
						}
					if (found)
					{
						CellToWorld(bestX, bestY, out.x, out.y);
						out.z = 0;
						return true;
					}
				}
				return false;
			}

			DWORD GetComponentAtWorld(long x, long y, int maxRadiusCells = 4) const
			{
				if (!m_initialized || !IsInsideWorld(x, y))
					return 0;
				int gx, gy;
				WorldToCell(x, y, gx, gy);
				if (!FindNearestWalkableCell(gx, gy, maxRadiusCells, 0, 0))
					return 0;
				return ComponentAt(Index(gx, gy));
			}

			bool FindNearestWalkableWorld(long x, long y, int maxRadiusCells,
					PIXEL_POSITION& out, DWORD seed = 0) const
			{
				if (!m_initialized)
					return false;
				int gx, gy;
				WorldToCell(x, y, gx, gy);
				if (!FindNearestWalkableCell(gx, gy, maxRadiusCells, 0, seed))
					return false;
				CellToWorld(gx, gy, out.x, out.y);
				out.z = 0;
				return true;
			}

			// MT2009_PLUS_BOT_NAV_SNAP_V1: the nearest cell of one component
			// (the bot's own ground) within maxRadiusCells of a point - the
			// shore under a monster standing in a river, the reachable side of
			// an NPC whose approach point fell in a wall.
			bool FindNearestComponentWorld(long x, long y, int maxRadiusCells,
					DWORD component, PIXEL_POSITION& out) const
			{
				if (!m_initialized || component == 0 || !IsInsideWorld(x, y))
					return false;
				int gx, gy;
				WorldToCell(x, y, gx, gy);
				if (!FindNearestWalkableCell(gx, gy, maxRadiusCells, component, 0))
					return false;
				CellToWorld(gx, gy, out.x, out.y);
				out.z = 0;
				return true;
			}

			// The route just planned ends short of its goal on purpose: the
			// corridor search hit PLAYERBOT_NAV_MAX_CORRIDOR_EXPANSIONS.
			bool LastPlanWasPartial() const
			{
				return m_bLastPartial;
			}

			// A far plan is the one thing the load line cannot attribute: it costs
			// a hundred times a near one, and only the destination and the price
			// say which subsystem asked for it and whether the search failed. A
			// slow plan of any size gets the same line, with what it spent where.
			EPlayerBotNavPlanResult FindRoute(long startX, long startY, long targetX, long targetY,
					DWORD seed, DWORD now, int targetSnapRadius, bool flexibleTargetSnap,
					std::vector<PIXEL_POSITION>& outWaypoints, bool starved = false)
			{
				const DWORD usBefore = s_uPlayerBotLoadPlanUs;
				const DWORD farCountBefore = s_uPlayerBotLoadPlanBucket[3];
				m_lastAbstractUs = 0;
				m_lastFineUs = 0;
				m_lastCorridorRegions = 0;
				m_lastFineExpanded = 0;
				m_bLastPartial = false;
				const EPlayerBotNavPlanResult result = FindRouteInner(startX, startY, targetX, targetY,
						seed, now, targetSnapRadius, flexibleTargetSnap, outWaypoints, starved);
				const DWORD costMs = (s_uPlayerBotLoadPlanUs - usBefore) / 1000;
				const bool bFar = s_uPlayerBotLoadPlanBucket[3] != farCountBefore;
				if (bFar || costMs >= PLAYERBOT_NAV_SLOW_PLAN_MS)
					sys_log(0, "PLAYERBOT_NAV: %s map=%ld from=(%ld,%ld) to=(%ld,%ld) result=%s cost_ms=%u waypoints=%u abstract_ms=%u regions=%d fine_ms=%u expanded=%d partial=%d",
							bFar ? "far plan" : "slow plan",
							m_mapIndex, startX, startY, targetX, targetY,
							result == PLAYERBOT_NAV_PLAN_FOUND ? "found" :
							(result == PLAYERBOT_NAV_PLAN_DEFERRED ? "deferred" : "unreachable"),
							(unsigned int)costMs, (unsigned int)outWaypoints.size(),
							(unsigned int)(m_lastAbstractUs / 1000), m_lastCorridorRegions,
							(unsigned int)(m_lastFineUs / 1000), m_lastFineExpanded,
							m_bLastPartial ? 1 : 0);
				return result;
			}

			EPlayerBotNavPlanResult FindRouteInner(long startX, long startY, long targetX, long targetY,
					DWORD seed, DWORD now, int targetSnapRadius, bool flexibleTargetSnap,
					std::vector<PIXEL_POSITION>& outWaypoints, bool starved)
			{
				outWaypoints.clear();
				if (!m_initialized || !IsInsideWorld(startX, startY) ||
						!IsInsideWorld(targetX, targetY))
					return PLAYERBOT_NAV_PLAN_UNREACHABLE;

				// The cache first, before the budget: a hit costs one segment check
				// and must not wait its turn behind the plans it makes unnecessary.
				int cacheSx, cacheSy, cacheTx, cacheTy;
				WorldToCell(startX, startY, cacheSx, cacheSy);
				WorldToCell(targetX, targetY, cacheTx, cacheTy);
				const int cacheCells = std::max(std::abs(cacheSx - cacheTx), std::abs(cacheSy - cacheTy));
				const bool cacheable = cacheCells >= PLAYERBOT_NAV_CACHE_MIN_CELLS;
				(void)cacheSx;
				(void)cacheSy;
				const int cacheKey = (cacheTx / PLAYERBOT_NAV_CACHE_QUANTUM_CELLS) * 4096 +
						cacheTy / PLAYERBOT_NAV_CACHE_QUANTUM_CELLS;
				if (cacheable)
				{
					std::map<int, std::vector<TCachedRoute> >::iterator hit = m_routeCache.find(cacheKey);
					if (hit != m_routeCache.end())
					{
						std::vector<TCachedRoute>& routes = hit->second;
						for (size_t r = 0; r < routes.size(); ++r)
						{
							const TCachedRoute& cached = routes[r];
							if (now - cached.dwStamp >= PLAYERBOT_NAV_CACHE_TTL)
								continue;
							// The nearest waypoint of this route, and it has to be a
							// straight step from where the bot stands; the rest of the
							// line was proven cell by cell when it was planned.
							size_t bestIndex = cached.waypoints.size();
							int bestDistance = PLAYERBOT_NAV_CACHE_JOIN_DISTANCE;
							for (size_t w = 0; w < cached.waypoints.size(); ++w)
							{
								const int distance = DISTANCE_APPROX(startX - cached.waypoints[w].x,
										startY - cached.waypoints[w].y);
								if (distance < bestDistance)
								{
									bestDistance = distance;
									bestIndex = w;
								}
							}
							if (bestIndex >= cached.waypoints.size() ||
									!SegmentClearWorld(startX, startY, cached.waypoints[bestIndex].x,
											cached.waypoints[bestIndex].y))
								continue;
							outWaypoints.assign(cached.waypoints.begin() + bestIndex, cached.waypoints.end());
							++s_uPlayerBotLoadPlanCached;
							return PLAYERBOT_NAV_PLAN_FOUND;
						}
					}
				}

				if (s_dwPlayerBotNavBudgetStamp != now)
				{
					s_dwPlayerBotNavBudgetStamp = now;
					s_iPlayerBotNavHeavyPlansThisTick = 0;
					s_uPlayerBotNavPlanUsThisTick = 0;
				}
				int sx, sy, tx, ty;
				WorldToCell(startX, startY, sx, sy);
				WorldToCell(targetX, targetY, tx, ty);
				const int planCells = std::max(std::abs(sx - tx), std::abs(sy - ty));
				const int planBucket = planCells < 64 ? 0 : planCells < 256 ? 1 : planCells < 1024 ? 2 : 3;
				if (now - s_dwPlayerBotNavFarMinuteStamp >= 60000)
				{
					s_dwPlayerBotNavFarMinuteStamp = now;
					s_iPlayerBotNavFarPlansThisMinute = 0;
				}
				// Three different budgets end in the same answer, and the log
				// could not tell them apart - so "deferred" was read as "no way
				// there" more than once. Say which one it was.
				const int planCost = PLAYERBOT_NAV_PLAN_COST[planBucket];
				const bool overCount = planCost > 0 && !starved && !s_bPlayerBotNavPortalPlan &&
						s_iPlayerBotNavHeavyPlansThisTick + planCost >
							PLAYERBOT_NAV_MAX_HEAVY_PLANS_PER_TICK;
				if (overCount ||
						s_uPlayerBotNavPlanUsThisTick >= PLAYERBOT_NAV_PLAN_TIME_BUDGET_US ||
						(planBucket == 3 && !s_bPlayerBotNavPortalPlan &&
						 s_iPlayerBotNavFarPlansThisMinute >= PLAYERBOT_NAV_MAX_FAR_PLANS_PER_MINUTE))
				{
					s_szPlayerBotNavDeferReason = overCount
								? "plans_per_tick"
								: (s_uPlayerBotNavPlanUsThisTick >= PLAYERBOT_NAV_PLAN_TIME_BUDGET_US
									? "plan_time_budget" : "far_plans_per_minute");
					++s_uPlayerBotLoadPlanDeferred;
					return PLAYERBOT_NAV_PLAN_DEFERRED;
				}
				if (planBucket == 3)
					++s_iPlayerBotNavFarPlansThisMinute;
				s_iPlayerBotNavHeavyPlansThisTick += planCost;
				++s_uPlayerBotLoadPlans;
				TPlayerBotLoadTimer planTickTimer(s_uPlayerBotNavPlanUsThisTick);

				++s_uPlayerBotLoadPlanBucket[planBucket];
				TPlayerBotLoadTimer planTimer(s_uPlayerBotLoadPlanUs);
				TPlayerBotLoadTimer planBucketTimer(s_uPlayerBotLoadPlanBucketUs[planBucket]);
				if (!FindNearestWalkableCell(sx, sy, 4, 0, seed))
					return PLAYERBOT_NAV_PLAN_UNREACHABLE;

				const DWORD component = ComponentAt(Index(sx, sy));
				if (component == 0)
					return PLAYERBOT_NAV_PLAN_UNREACHABLE;
				if (flexibleTargetSnap)
				{
					if (!FindNearestWalkableCell(tx, ty, targetSnapRadius, component,
							seed ^ 0x9e3779b9U))
					{
						sys_log(1, "PLAYERBOT_NAV: goal snap failed map=%ld from=(%ld,%ld) to=(%ld,%ld) component=%u radius=%d",
								m_mapIndex, startX, startY, targetX, targetY,
								(unsigned int)component, targetSnapRadius);
						return PLAYERBOT_NAV_PLAN_UNREACHABLE;
					}
				}
				else
				{
					if (!FindNearestWalkableCell(tx, ty, targetSnapRadius, 0,
							seed ^ 0x9e3779b9U))
					{
						sys_log(1, "PLAYERBOT_NAV: strict goal snap failed map=%ld from=(%ld,%ld) to=(%ld,%ld) radius=%d",
								m_mapIndex, startX, startY, targetX, targetY, targetSnapRadius);
						return PLAYERBOT_NAV_PLAN_UNREACHABLE;
					}
					if (ComponentAt(Index(tx, ty)) != component)
					{
						sys_log(1, "PLAYERBOT_NAV: disconnected goal map=%ld from=(%ld,%ld) to=(%ld,%ld) start_component=%u target_component=%u",
								m_mapIndex, startX, startY, targetX, targetY,
								(unsigned int)component, (unsigned int)ComponentAt(Index(tx, ty)));
						return PLAYERBOT_NAV_PLAN_UNREACHABLE;
					}
				}

				const int startIndex = Index(sx, sy);
				const int targetIndex = Index(tx, ty);
				if (startIndex == targetIndex)
				{
					PIXEL_POSITION point;
					if (!IsPlayerBotPositionBlocked(m_mapIndex, targetX, targetY))
					{
						point.x = targetX;
						point.y = targetY;
					}
					else
						CellToWorld(tx, ty, point.x, point.y);
					point.z = 0;
					outWaypoints.push_back(point);
					return PLAYERBOT_NAV_PLAN_FOUND;
				}

				std::vector<int> rawPath;
				if (!FindHierarchicalRawPath(startIndex, targetIndex, seed, rawPath))
				{
					sys_log(1, "PLAYERBOT_NAV: hierarchical route failed map=%ld from=(%ld,%ld) to=(%ld,%ld) start_region=%u target_region=%u",
							m_mapIndex, startX, startY, targetX, targetY,
							(unsigned int)CellRegion(startIndex),
							(unsigned int)CellRegion(targetIndex));
					return PLAYERBOT_NAV_PLAN_UNREACHABLE;
				}

#if 0
				// Retired fine-grid A*.  Kept temporarily beside the HPA rollout so a
				// runtime comparison can be made without restoring an old source file.
				++s_playerBotNavScratch.searchToken;
				if (s_playerBotNavScratch.searchToken == 0)
				{
					std::fill(s_playerBotNavScratch.nodeToken.begin(), s_playerBotNavScratch.nodeToken.end(), 0);
					s_playerBotNavScratch.searchToken = 1;
				}

				struct TOpenNode
				{
					int f;
					int g;
					int x;
					int y;
					DWORD tie;
				};
				struct TOpenNodeGreater
				{
					bool operator()(const TOpenNode& left, const TOpenNode& right) const
					{
						if (left.f != right.f)
							return left.f > right.f;
						return left.tie > right.tie;
					}
				};

				std::priority_queue<TOpenNode, std::vector<TOpenNode>, TOpenNodeGreater> open;
				s_playerBotNavScratch.nodeToken[startIndex] = s_playerBotNavScratch.searchToken;
				s_playerBotNavScratch.nodeCost[startIndex] = 0;
				s_playerBotNavScratch.parent[startIndex] = -1;
				TOpenNode first;
				first.g = 0;
				// Weighted A*: terrain safety is binary and revalidated later, so a
				// modestly greedier heuristic trades only route optimality for a very
				// large reduction in heap work on this five-million-cell map.
				first.f = OctileDistance(sx, sy, tx, ty) * 2;
				first.x = sx;
				first.y = sy;
				first.tie = PlayerBotNavHash(seed ^ (DWORD)startIndex);
				open.push(first);

				const int moveX[8] = { 1, 1, 0, -1, -1, -1, 0, 1 };
				const int moveY[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };
				const int moveCost[8] = { 10, 14, 10, 14, 10, 14, 10, 14 };
				bool found = false;
				int expanded = 0;

				while (!open.empty() && expanded < PLAYERBOT_NAV_MAX_EXPANDED_NODES)
				{
					const TOpenNode current = open.top();
					open.pop();
					const int currentIndex = Index(current.x, current.y);
					if (s_playerBotNavScratch.nodeToken[currentIndex] != s_playerBotNavScratch.searchToken || current.g != s_playerBotNavScratch.nodeCost[currentIndex])
						continue;
					++expanded;

					if (currentIndex == targetIndex)
					{
						found = true;
						break;
					}

					const int directionOffset = (int)(PlayerBotNavHash(seed) & 7U);
					for (int n = 0; n < 8; ++n)
					{
						const int direction = (directionOffset + n) & 7;
						const int nx = current.x + moveX[direction];
						const int ny = current.y + moveY[direction];
						if (IsBlockedCell(nx, ny))
							continue;

						// Never pass diagonally through the corner of two obstacles.
						if (moveX[direction] != 0 && moveY[direction] != 0 &&
								(IsBlockedCell(current.x + moveX[direction], current.y) ||
								 IsBlockedCell(current.x, current.y + moveY[direction])))
							continue;

						const int nextIndex = Index(nx, ny);
						if (ComponentAt(nextIndex) != component)
							continue;

						int wallPenalty = 0;
						if (Clearance(nextIndex) <= 1) wallPenalty = 8;
						else if (Clearance(nextIndex) == 2) wallPenalty = 3;
						else if (Clearance(nextIndex) == 3) wallPenalty = 1;
						const int waterPenalty =
								IsWaterIndex(nextIndex) ? PLAYERBOT_NAV_WATER_PENALTY : 0;
						const int laneJitter = (int)(PlayerBotNavHash(seed ^ (DWORD)nextIndex) & 1U);
						const int newCost = current.g + moveCost[direction] + wallPenalty +
								waterPenalty + laneJitter;

						if (s_playerBotNavScratch.nodeToken[nextIndex] == s_playerBotNavScratch.searchToken && newCost >= s_playerBotNavScratch.nodeCost[nextIndex])
							continue;

						s_playerBotNavScratch.nodeToken[nextIndex] = s_playerBotNavScratch.searchToken;
						s_playerBotNavScratch.nodeCost[nextIndex] = newCost;
						s_playerBotNavScratch.parent[nextIndex] = currentIndex;

						TOpenNode next;
						next.g = newCost;
						next.f = newCost + OctileDistance(nx, ny, tx, ty) * 2;
						next.x = nx;
						next.y = ny;
						next.tie = PlayerBotNavHash(seed ^ (DWORD)nextIndex);
						open.push(next);
					}
				}

				// A search that consumed its node cap must not restart the identical
				// first 120k nodes forever.  Treat it as a bounded failure; the caller
				// can choose another goal while the one-plan-per-tick budget protects
				// the game loop from a CPU spike.
				if (!found)
				{
					sys_err("PLAYERBOT_NAV: bounded search failed map=%ld from=(%ld,%ld) to=(%ld,%ld) expanded=%d frontier=%u",
							m_mapIndex, startX, startY, targetX, targetY, expanded,
							(unsigned int)open.size());
					return PLAYERBOT_NAV_PLAN_UNREACHABLE;
				}

				std::vector<int> rawPath;
				int cursor = targetIndex;
				while (cursor >= 0)
				{
					rawPath.push_back(cursor);
					if (cursor == startIndex)
						break;
					cursor = s_playerBotNavScratch.parent[cursor];
				}
				if (rawPath.empty() || rawPath.back() != startIndex)
					return PLAYERBOT_NAV_PLAN_UNREACHABLE;
				std::reverse(rawPath.begin(), rawPath.end());
#endif

				// Conservative string pulling.  Each emitted segment is short and
				// crosses only cells proven safe by a supercover test.  The first
				// segment is special: the character can stand anywhere inside the
				// start cell, not necessarily at its centre.  Validating only centre
				// to centre could therefore create a route whose first waypoint was
				// rejected forever by MovePlayerBot (most visibly near town walls).
				const size_t maxCellsPerSegment = std::max(1, PLAYERBOT_NAV_MAX_SEGMENT / PLAYERBOT_NAV_CELL);
				size_t pathIndex = 0;
				bool validateFromExactStart = true;
				while (pathIndex + 1 < rawPath.size())
				{
					const size_t limit = std::min(rawPath.size() - 1, pathIndex + maxCellsPerSegment);
					size_t furthest = pathIndex;
					int fromX, fromY;
					CellFromIndex(rawPath[pathIndex], fromX, fromY);
					for (size_t candidate = limit; candidate > pathIndex; --candidate)
					{
						int toX, toY;
						CellFromIndex(rawPath[candidate], toX, toY);
						bool clear = false;
						if (validateFromExactStart)
						{
							int toWorldX, toWorldY;
							CellToWorld(toX, toY, toWorldX, toWorldY);
							clear = SegmentClearWorld(startX, startY, toWorldX, toWorldY);
						}
						else
							clear = SegmentClearCells(fromX, fromY, toX, toY);
						if (clear)
						{
							furthest = candidate;
							break;
						}
					}

					if (furthest == pathIndex)
					{
						// The raw path itself is valid, but the exact point inside its
						// first cell may need a tiny alignment move before the first
						// corner can be rounded safely.  Emit that centre explicitly;
						// subsequent segments can then use ordinary cell validation.
						if (!validateFromExactStart)
							return PLAYERBOT_NAV_PLAN_UNREACHABLE;
						PIXEL_POSITION alignment;
						CellToWorld(fromX, fromY, alignment.x, alignment.y);
						alignment.z = 0;
						if (!SegmentClearWorld(startX, startY, alignment.x, alignment.y))
							return PLAYERBOT_NAV_PLAN_UNREACHABLE;
						outWaypoints.push_back(alignment);
						validateFromExactStart = false;
						continue;
					}

					int waypointX, waypointY;
					CellFromIndex(rawPath[furthest], waypointX, waypointY);
					PIXEL_POSITION point;
					CellToWorld(waypointX, waypointY, point.x, point.y);
					point.z = 0;
					outWaypoints.push_back(point);
					pathIndex = furthest;
					validateFromExactStart = false;
				}

				if (outWaypoints.empty())
					return PLAYERBOT_NAV_PLAN_UNREACHABLE;

				// Preserve an exact movable destination only when it lies in the
				// selected goal cell and the last tiny segment remains valid.
				int originalTargetX, originalTargetY;
				WorldToCell(targetX, targetY, originalTargetX, originalTargetY);
				PIXEL_POSITION& last = outWaypoints.back();
				if (originalTargetX == tx && originalTargetY == ty &&
						!IsPlayerBotPositionBlocked(m_mapIndex, targetX, targetY) &&
						SegmentClearWorld(last.x, last.y, targetX, targetY))
				{
					last.x = targetX;
					last.y = targetY;
				}

				// Never a partial one: it is a route to wherever the cap fell.
				if (cacheable && !m_bLastPartial)
				{
					// Full: drop a whole goal's routes, the first in key order - a plain
					// rule on the plans that already cost two hundred milliseconds.
					if (m_routeCacheCount >= PLAYERBOT_NAV_CACHE_LIMIT && !m_routeCache.empty())
					{
						m_routeCacheCount -= m_routeCache.begin()->second.size();
						m_routeCache.erase(m_routeCache.begin());
					}
					std::vector<TCachedRoute>& routes = m_routeCache[cacheKey];
					if (routes.size() >= PLAYERBOT_NAV_CACHE_PER_GOAL)
					{
						routes.erase(routes.begin());
						--m_routeCacheCount;
					}
					TCachedRoute entry;
					entry.startX = startX;
					entry.startY = startY;
					entry.dwStamp = now;
					entry.waypoints = outWaypoints;
					routes.push_back(entry);
					++m_routeCacheCount;
				}

				return PLAYERBOT_NAV_PLAN_FOUND;
			}

			// MT2009_PLUS_BOT_NAV_GUILD_BUILDINGS_V1: a guild building (any
			// building::CObject) put up or taken down after this grid was built.
			// The engine marks its footprint ATTR_OBJECT (CObject::Show) or clears
			// it (CObject::Destroy) and calls this through
			// g_pfnMt2009ObjectAreaChanged with a box round it. The planner reads
			// only this grid, so before this it routed straight through every
			// building raised since the core started; the walk's live check
			// refused the step into the wall, the stuck counter asked for a new
			// plan and the same plan came back - bots stood against the pagoda
			// of a guild land for good (the owner's report of 23 October, the
			// supporters' server; MT2009_PLUS_NAV_LIVE_OBJECT_V1 only kept the
			// rescue of a bot already inside off the footprint). The box is read
			// again cell by cell from the live sectree, as Init reads it, and only
			// what hangs on those cells is redone: the clearance round them, the
			// components of cells that opened, the HPA regions and portals of the
			// clusters the box touches. The packed cell keeps its layout: the
			// blocked and water bits are rewritten, the clearance bits recomputed.
			void RefreshLiveArea(long worldSX, long worldSY, long worldEX, long worldEY)
			{
				if (!m_initialized)
					return;
				if (worldEX < worldSX)
					std::swap(worldSX, worldEX);
				if (worldEY < worldSY)
					std::swap(worldSY, worldEY);
				if (worldEX < m_baseX || worldEY < m_baseY ||
						worldSX >= m_baseX + (long)m_width * PLAYERBOT_NAV_CELL ||
						worldSY >= m_baseY + (long)m_height * PLAYERBOT_NAV_CELL)
					return;
				int gx0, gy0, gx1, gy1;
				WorldToCell(worldSX, worldSY, gx0, gy0);
				WorldToCell(worldEX, worldEY, gx1, gy1);
				gx0 = std::max(0, gx0 - 1);
				gy0 = std::max(0, gy0 - 1);
				gx1 = std::min(m_width - 1, gx1 + 1);
				gy1 = std::min(m_height - 1, gy1 + 1);

				int closed = 0;
				std::vector<int> opened;
				try
				{
					for (int gy = gy0; gy <= gy1; ++gy)
					{
						for (int gx = gx0; gx <= gx1; ++gx)
						{
							bool blocked = false;
							bool wet = false;
							SampleLiveCell(gx, gy, blocked, wet);
							const int index = Index(gx, gy);
							const bool wasBlocked = IsBlockedIndex(index);
							if (blocked == wasBlocked)
							{
								if (!blocked && wet != IsWaterIndex(index))
									m_cell[index] = (BYTE)((m_cell[index] & ~PLAYERBOT_NAV_CELL_WATER) |
											(wet ? PLAYERBOT_NAV_CELL_WATER : 0));
								continue;
							}
							if (blocked)
							{
								// Clearance 0, no component, no region: what Init leaves on a wall.
								const DWORD component = ComponentAt(index);
								if (component != 0 && component < m_componentCells.size() &&
										m_componentCells[component] > 0)
									--m_componentCells[component];
								SetComponent(index, 0);
								m_cell[index] = PLAYERBOT_NAV_CELL_BLOCKED;
								if (m_walkableCells > 0)
									--m_walkableCells;
								++closed;
							}
							else
							{
								m_cell[index] = wet ? PLAYERBOT_NAV_CELL_WATER : 0;
								SetComponent(index, 0);
								++m_walkableCells;
								opened.push_back(index);
							}
						}
					}
					if (closed == 0 && opened.empty())
						return;

					// A cell that opened joins the component of the open ground beside
					// it (a land is one piece with its map), again and again inwards
					// from the edge of the old footprint until nothing more joins.
					const int moveX[8] = { 1, 1, 0, -1, -1, -1, 0, 1 };
					const int moveY[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };
					bool joined = true;
					while (joined)
					{
						joined = false;
						for (size_t i = 0; i < opened.size(); ++i)
						{
							if (ComponentAt(opened[i]) != 0)
								continue;
							int cx, cy;
							CellFromIndex(opened[i], cx, cy);
							for (int direction = 0; direction < 8; ++direction)
							{
								const int nx = cx + moveX[direction];
								const int ny = cy + moveY[direction];
								if (IsBlockedCell(nx, ny))
									continue;
								const DWORD component = ComponentAt(Index(nx, ny));
								if (component == 0)
									continue;
								SetComponent(opened[i], component);
								if (component < m_componentCells.size())
									++m_componentCells[component];
								joined = true;
								break;
							}
						}
					}

					// The clearance never exceeds 4, so nothing farther than that from
					// a changed cell moves: the two passes run over the box and a
					// margin, reading the unchanged values just outside it.
					RecomputeClearance(gx0 - 6, gy0 - 6, gx1 + 6, gy1 + 6);
					RebuildAbstractClusters(gx0, gy0, gx1, gy1);
				}
				catch (const std::bad_alloc&)
				{
					// Half-updated is not safe to plan on: the map goes without
					// planning for a while and is then built again from the live world.
					const long mapIndex = m_mapIndex;
					ReleaseGrid();
					m_mapIndex = 0;
					OnNavAllocFailed(mapIndex, 0, "building refresh");
					return;
				}

				// A remembered route may run through the new walls.
				m_routeCache.clear();
				m_routeCacheCount = 0;
				sys_log(0, "PLAYERBOT_NAV: building area refreshed map=%ld box=(%ld,%ld)-(%ld,%ld) closed=%d opened=%u regions=%u",
						m_mapIndex, worldSX, worldSY, worldEX, worldEY, closed, (unsigned int)opened.size(),
						(unsigned int)m_regions.size());
			}

		private:
			// MT2009_PLUS_BOT_NAV_GUILD_BUILDINGS_V1: one cell from the live world,
			// sampled exactly as Init samples it.
			void SampleLiveCell(int gx, int gy, bool& blocked, bool& wet) const
			{
				blocked = false;
				wet = false;
				const long cellX = m_baseX + gx * PLAYERBOT_NAV_CELL;
				const long cellY = m_baseY + gy * PLAYERBOT_NAV_CELL;
				for (int oy = PLAYERBOT_NAV_NATIVE_SAMPLE / 2;
						oy < PLAYERBOT_NAV_CELL && !blocked;
						oy += PLAYERBOT_NAV_NATIVE_SAMPLE)
				{
					for (int ox = PLAYERBOT_NAV_NATIVE_SAMPLE / 2;
							ox < PLAYERBOT_NAV_CELL;
							ox += PLAYERBOT_NAV_NATIVE_SAMPLE)
					{
						if (IsPlayerBotPositionBlocked(m_mapIndex, cellX + ox, cellY + oy))
						{
							blocked = true;
							break;
						}
						if (IsPlayerBotPositionWater(m_mapIndex, cellX + ox, cellY + oy))
							wet = true;
					}
				}
			}

			// MT2009_PLUS_BOT_NAV_GUILD_BUILDINGS_V1: BuildClearance's two passes
			// over a window only; the cells just outside it are read as they are.
			void RecomputeClearance(int x0, int y0, int x1, int y1)
			{
				x0 = std::max(0, x0);
				y0 = std::max(0, y0);
				x1 = std::min(m_width - 1, x1);
				y1 = std::min(m_height - 1, y1);
				for (int y = y0; y <= y1; ++y)
				{
					for (int x = x0; x <= x1; ++x)
					{
						const int index = Index(x, y);
						if (IsBlockedIndex(index))
						{
							SetClearance(index, 0);
							continue;
						}
						BYTE clearance = 4;
						if (x > 0) clearance = std::min<BYTE>(clearance, (BYTE)(Clearance(Index(x - 1, y)) + 1));
						if (y > 0) clearance = std::min<BYTE>(clearance, (BYTE)(Clearance(Index(x, y - 1)) + 1));
						SetClearance(index, clearance);
					}
				}
				for (int y = y1; y >= y0; --y)
				{
					for (int x = x1; x >= x0; --x)
					{
						const int index = Index(x, y);
						if (IsBlockedIndex(index))
							continue;
						BYTE clearance = Clearance(index);
						if (x + 1 < m_width) clearance = std::min<BYTE>(clearance, (BYTE)(Clearance(Index(x + 1, y)) + 1));
						if (y + 1 < m_height) clearance = std::min<BYTE>(clearance, (BYTE)(Clearance(Index(x, y + 1)) + 1));
						SetClearance(index, clearance);
					}
				}
			}

			// MT2009_PLUS_BOT_NAV_GUILD_BUILDINGS_V1: BuildAbstractRegions for the
			// clusters a changed box touches. Their regions are flooded again (the
			// old ids first; one left over keeps no cell and no edge, so no search
			// reaches it), every edge into or out of them is dropped, and the
			// portals on all four borders of each are added again as the full
			// build adds them.
			void RebuildAbstractClusters(int gx0, int gy0, int gx1, int gy1)
			{
				const int cx0 = gx0 / PLAYERBOT_NAV_CLUSTER_CELLS;
				const int cy0 = gy0 / PLAYERBOT_NAV_CLUSTER_CELLS;
				const int cx1 = gx1 / PLAYERBOT_NAV_CLUSTER_CELLS;
				const int cy1 = gy1 / PLAYERBOT_NAV_CLUSTER_CELLS;

				std::vector<BYTE> touched(m_regions.size(), 0);
				std::vector<DWORD> reuse;
				for (size_t r = 1; r < m_regions.size(); ++r)
				{
					const TAbstractRegion& region = m_regions[r];
					if (region.clusterX >= cx0 && region.clusterX <= cx1 &&
							region.clusterY >= cy0 && region.clusterY <= cy1)
					{
						touched[r] = 1;
						reuse.push_back((DWORD)r);
					}
				}
				for (size_t r = 1; r < m_regions.size(); ++r)
				{
					std::vector<TAbstractEdge>& edges = m_regions[r].edges;
					if (touched[r])
					{
						edges.clear();
						continue;
					}
					for (size_t e = edges.size(); e-- > 0; )
						if (edges[e].toRegion < touched.size() && touched[edges[e].toRegion])
							edges.erase(edges.begin() + e);
				}
				for (size_t i = 0; i < reuse.size(); ++i)
				{
					m_regions[reuse[i]].clusterX = -1;
					m_regions[reuse[i]].clusterY = -1;
				}

				const int moveX[8] = { 1, 1, 0, -1, -1, -1, 0, 1 };
				const int moveY[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };
				std::vector<int> queue;
				size_t nextReuse = 0;
				for (int clusterY = cy0; clusterY <= cy1; ++clusterY)
				{
					const int minY = clusterY * PLAYERBOT_NAV_CLUSTER_CELLS;
					const int maxY = std::min(m_height, minY + PLAYERBOT_NAV_CLUSTER_CELLS);
					for (int clusterX = cx0; clusterX <= cx1; ++clusterX)
					{
						const int minX = clusterX * PLAYERBOT_NAV_CLUSTER_CELLS;
						const int maxX = std::min(m_width, minX + PLAYERBOT_NAV_CLUSTER_CELLS);
						for (int y = minY; y < maxY; ++y)
							for (int x = minX; x < maxX; ++x)
								SetCellRegion(Index(x, y), 0);
						for (int y = minY; y < maxY; ++y)
						{
							for (int x = minX; x < maxX; ++x)
							{
								const int firstCell = Index(x, y);
								if (IsBlockedIndex(firstCell) || CellRegion(firstCell) != 0)
									continue;
								DWORD regionID;
								if (nextReuse < reuse.size())
									regionID = reuse[nextReuse++];
								else
								{
									regionID = (DWORD)m_regions.size();
									TAbstractRegion fresh;
									fresh.clusterX = clusterX;
									fresh.clusterY = clusterY;
									m_regions.push_back(fresh);
								}
								m_regions[regionID].clusterX = clusterX;
								m_regions[regionID].clusterY = clusterY;
								queue.clear();
								queue.push_back(firstCell);
								SetCellRegion(firstCell, regionID);
								for (size_t head = 0; head < queue.size(); ++head)
								{
									int currentX, currentY;
									CellFromIndex(queue[head], currentX, currentY);
									for (int direction = 0; direction < 8; ++direction)
									{
										const int nextX = currentX + moveX[direction];
										const int nextY = currentY + moveY[direction];
										if (nextX < minX || nextX >= maxX || nextY < minY || nextY >= maxY ||
												IsBlockedCell(nextX, nextY))
											continue;
										if (moveX[direction] != 0 && moveY[direction] != 0 &&
												(IsBlockedCell(currentX + moveX[direction], currentY) ||
												 IsBlockedCell(currentX, currentY + moveY[direction])))
											continue;
										const int nextCell = Index(nextX, nextY);
										if (CellRegion(nextCell) != 0)
											continue;
										SetCellRegion(nextCell, regionID);
										queue.push_back(nextCell);
									}
								}
							}
						}
					}
				}

				// The portals on every border of the touched clusters, outer and
				// inner (AddAbstractPortal keeps one per spot, so a border met twice
				// is not doubled).
				for (int clusterY = cy0; clusterY <= cy1; ++clusterY)
				{
					const int minY = clusterY * PLAYERBOT_NAV_CLUSTER_CELLS;
					const int maxY = std::min(m_height, minY + PLAYERBOT_NAV_CLUSTER_CELLS) - 1;
					for (int clusterX = cx0; clusterX <= cx1; ++clusterX)
					{
						const int minX = clusterX * PLAYERBOT_NAV_CLUSTER_CELLS;
						const int maxX = std::min(m_width, minX + PLAYERBOT_NAV_CLUSTER_CELLS) - 1;
						for (int y = minY; y <= maxY; ++y)
						{
							AddBorderPortals(minX - 1, y, minX, y);
							AddBorderPortals(maxX, y, maxX + 1, y);
						}
						for (int x = minX; x <= maxX; ++x)
						{
							AddBorderPortals(x, minY - 1, x, minY);
							AddBorderPortals(x, maxY, x, maxY + 1);
						}
					}
				}
			}

			// MT2009_PLUS_BOT_NAV_GUILD_BUILDINGS_V1: one cardinal crossing of a
			// cluster border, both ways, as BuildAbstractRegions adds it.
			void AddBorderPortals(int ax, int ay, int bx, int by)
			{
				if (IsBlockedCell(ax, ay) || IsBlockedCell(bx, by))
					return;
				const int a = Index(ax, ay);
				const int b = Index(bx, by);
				AddAbstractPortal(CellRegion(a), CellRegion(b), a, b);
				AddAbstractPortal(CellRegion(b), CellRegion(a), b, a);
			}

			int Index(int gx, int gy) const
			{
				return gy * m_width + gx;
			}

			bool IsInsideCell(int gx, int gy) const
			{
				return gx >= 0 && gy >= 0 && gx < m_width && gy < m_height;
			}

			// The engine's own answer for the cell's centre point - the same point,
			// and the same bits, that the blocked bit was built from when the grid was made.
			// The planner therefore never asks this: a corridor search put the
			// question to the sectree tree up to twenty-four times for every node it
			// expanded, and a thousand plans a minute spent thirty-one seconds of
			// every sixty answering it. Only the walk keeps asking (SegmentClearWorld,
			// once per tick for the segment in front of the bot) so that anything
			// placed after the grid was built still stops a bot before it walks
			// into it, and the stuck counter then asks for a new plan.
			bool IsLiveBlockedCell(int gx, int gy) const
			{
				if (!IsInsideCell(gx, gy))
					return true;
				const long x = m_baseX + gx * PLAYERBOT_NAV_CELL + PLAYERBOT_NAV_CELL / 2;
				const long y = m_baseY + gy * PLAYERBOT_NAV_CELL + PLAYERBOT_NAV_CELL / 2;
				return IsPlayerBotPositionBlocked(m_mapIndex, x, y);
			}

			void WorldToCell(long x, long y, int& gx, int& gy) const
			{
				gx = (int)((x - m_baseX) / PLAYERBOT_NAV_CELL);
				gy = (int)((y - m_baseY) / PLAYERBOT_NAV_CELL);
				gx = std::max(0, std::min(m_width - 1, gx));
				gy = std::max(0, std::min(m_height - 1, gy));
			}

			void CellToWorld(int gx, int gy, int& x, int& y) const
			{
				x = (int)(m_baseX + gx * PLAYERBOT_NAV_CELL + PLAYERBOT_NAV_CELL / 2);
				y = (int)(m_baseY + gy * PLAYERBOT_NAV_CELL + PLAYERBOT_NAV_CELL / 2);
			}

			void CellFromIndex(int index, int& gx, int& gy) const
			{
				gx = index % m_width;
				gy = index / m_width;
			}

			int OctileDistance(int x0, int y0, int x1, int y1) const
			{
				const int dx = abs(x1 - x0);
				const int dy = abs(y1 - y0);
				const int diagonal = std::min(dx, dy);
				return 10 * (dx + dy) - 6 * diagonal;
			}

			bool SegmentClearCells(int x0, int y0, int x1, int y1) const
			{
				if (IsBlockedCell(x0, y0) || IsBlockedCell(x1, y1) ||
						IsBlockedCell(x0, y0) || IsBlockedCell(x1, y1))
					return false;

				const int dx = x1 - x0;
				const int dy = y1 - y0;
				const int nx = abs(dx);
				const int ny = abs(dy);
				const int signX = (dx > 0) ? 1 : ((dx < 0) ? -1 : 0);
				const int signY = (dy > 0) ? 1 : ((dy < 0) ? -1 : 0);
				int x = x0;
				int y = y0;
				int ix = 0;
				int iy = 0;

				while (ix < nx || iy < ny)
				{
					const long long decisionX = (long long)(1 + 2 * ix) * ny;
					const long long decisionY = (long long)(1 + 2 * iy) * nx;
					if (decisionX == decisionY)
					{
						// The line crosses a cell corner: both side cells must be
						// clear, otherwise this would be diagonal corner cutting.
						if ((signX != 0 && (IsBlockedCell(x + signX, y) ||
								IsBlockedCell(x + signX, y))) ||
								(signY != 0 && (IsBlockedCell(x, y + signY) ||
								IsBlockedCell(x, y + signY))))
							return false;
						x += signX;
						y += signY;
						++ix;
						++iy;
					}
					else if (decisionX < decisionY)
					{
						x += signX;
						++ix;
					}
					else
					{
						y += signY;
						++iy;
					}

					if (IsBlockedCell(x, y))
						return false;
				}
				return true;
			}

			bool FindNearestWalkableCell(int& gx, int& gy, int maxRadius,
					DWORD requiredComponent, DWORD seed) const
			{
				const int originX = gx;
				const int originY = gy;
				for (int radius = 0; radius <= maxRadius; ++radius)
				{
					bool found = false;
					DWORD bestTie = 0xffffffffU;
					int bestX = originX;
					int bestY = originY;
					for (int y = originY - radius; y <= originY + radius; ++y)
					{
						for (int x = originX - radius; x <= originX + radius; ++x)
						{
							if (std::max(abs(x - originX), abs(y - originY)) != radius ||
									IsBlockedCell(x, y))
								continue;
							const int index = Index(x, y);
							if (requiredComponent != 0 && ComponentAt(index) != requiredComponent)
								continue;
							// MT2009_PLUS_NAV_LIVE_OBJECT_V1: and free in the live world
							// too. A guild building (ATTR_OBJECT, placed long after this
							// grid was built) left its footprint walkable here: a bot
							// that walked to a guild smith inside it was "rescued" onto
							// its own blocked cell every second and never moved again.
							if (IsLiveBlockedCell(x, y))
								continue;
							const DWORD tie = PlayerBotNavHash(seed ^ (DWORD)index);
							if (!found || tie < bestTie)
							{
								found = true;
								bestTie = tie;
								bestX = x;
								bestY = y;
							}
						}
					}
					if (found)
					{
						gx = bestX;
						gy = bestY;
						return true;
					}
				}
				return false;
			}

			// MT2009_PLUS_BOT_NAV_PACKED_CELLS_V1: same two passes, the value now
			// lives in three bits of the packed cell (it never exceeds 4).
			void BuildClearance()
			{
				for (int y = 0; y < m_height; ++y)
				{
					for (int x = 0; x < m_width; ++x)
					{
						const int index = Index(x, y);
						if (IsBlockedIndex(index))
						{
							SetClearance(index, 0);
							continue;
						}
						BYTE clearance = 4;
						if (x > 0) clearance = std::min<BYTE>(clearance, (BYTE)(Clearance(Index(x - 1, y)) + 1));
						if (y > 0) clearance = std::min<BYTE>(clearance, (BYTE)(Clearance(Index(x, y - 1)) + 1));
						SetClearance(index, clearance);
					}
				}
				for (int y = m_height - 1; y >= 0; --y)
				{
					for (int x = m_width - 1; x >= 0; --x)
					{
						const int index = Index(x, y);
						if (IsBlockedIndex(index))
							continue;
						BYTE clearance = Clearance(index);
						if (x + 1 < m_width) clearance = std::min<BYTE>(clearance, (BYTE)(Clearance(Index(x + 1, y)) + 1));
						if (y + 1 < m_height) clearance = std::min<BYTE>(clearance, (BYTE)(Clearance(Index(x, y + 1)) + 1));
						SetClearance(index, clearance);
					}
				}
			}

			DWORD BuildComponents()
			{
				DWORD component = 0;
				std::vector<int> queue;
				m_componentCells.assign(1, 0);
				const int moveX[8] = { 1, 1, 0, -1, -1, -1, 0, 1 };
				const int moveY[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };

				for (int y = 0; y < m_height; ++y)
				{
					for (int x = 0; x < m_width; ++x)
					{
						const int firstIndex = Index(x, y);
						if (IsBlockedIndex(firstIndex) || ComponentAt(firstIndex) != 0)
							continue;

						++component;
						queue.clear();
						queue.push_back(firstIndex);
						SetComponent(firstIndex, component);
						for (size_t head = 0; head < queue.size(); ++head)
						{
							int cx, cy;
							CellFromIndex(queue[head], cx, cy);
							for (int direction = 0; direction < 8; ++direction)
							{
								const int nx = cx + moveX[direction];
								const int ny = cy + moveY[direction];
								if (IsBlockedCell(nx, ny))
									continue;
								if (moveX[direction] != 0 && moveY[direction] != 0 &&
										(IsBlockedCell(cx + moveX[direction], cy) || IsBlockedCell(cx, cy + moveY[direction])))
									continue;
								const int nextIndex = Index(nx, ny);
								if (ComponentAt(nextIndex) != 0)
									continue;
								SetComponent(nextIndex, component);
								queue.push_back(nextIndex);
							}
						}
						m_componentCells.push_back((DWORD)queue.size());
					}
				}
				return component;
			}

			void AddAbstractPortal(DWORD fromRegion, DWORD toRegion,
					int fromCell, int toCell)
			{
				if (fromRegion == 0 || toRegion == 0 || fromRegion == toRegion ||
						fromRegion >= m_regions.size() || toRegion >= m_regions.size())
					return;

				TAbstractRegion& region = m_regions[fromRegion];
				const BYTE clearance = std::min(Clearance(fromCell), Clearance(toCell));
				int candidateX, candidateY;
				CellFromIndex(fromCell, candidateX, candidateY);
				int sameNeighbourCount = 0;
				int worstEdge = -1;
				BYTE worstClearance = 255;

				for (size_t i = 0; i < region.edges.size(); ++i)
				{
					TAbstractEdge& existing = region.edges[i];
					if (existing.toRegion != toRegion)
						continue;
					++sameNeighbourCount;
					int existingX, existingY;
					CellFromIndex(existing.fromCell, existingX, existingY);
					if (abs(existingX - candidateX) + abs(existingY - candidateY) < 4)
					{
						if (clearance > existing.clearance)
						{
							existing.fromCell = fromCell;
							existing.toCell = toCell;
							existing.clearance = clearance;
						}
						return;
					}
					if (existing.clearance < worstClearance)
					{
						worstClearance = existing.clearance;
						worstEdge = (int)i;
					}
				}

				TAbstractEdge edge;
				edge.toRegion = toRegion;
				edge.fromCell = fromCell;
				edge.toCell = toCell;
				edge.clearance = clearance;
				if (sameNeighbourCount < PLAYERBOT_NAV_MAX_PORTALS_PER_NEIGHBOR)
					region.edges.push_back(edge);
				else if (worstEdge >= 0 && clearance > worstClearance)
					region.edges[worstEdge] = edge;
			}

			DWORD BuildAbstractRegions()
			{
				const size_t cellCount = (size_t)m_width * (size_t)m_height;
				std::vector<DWORD>().swap(m_cellRegionWide);
				m_cellRegion.assign(cellCount, 0);
				m_regions.clear();
				TAbstractRegion unused;
				unused.clusterX = -1;
				unused.clusterY = -1;
				m_regions.push_back(unused);

				const int moveX[8] = { 1, 1, 0, -1, -1, -1, 0, 1 };
				const int moveY[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };
				std::vector<int> queue;
				queue.reserve(PLAYERBOT_NAV_CLUSTER_CELLS * PLAYERBOT_NAV_CLUSTER_CELLS);
				const int clusterWidth = (m_width + PLAYERBOT_NAV_CLUSTER_CELLS - 1) /
						PLAYERBOT_NAV_CLUSTER_CELLS;
				const int clusterHeight = (m_height + PLAYERBOT_NAV_CLUSTER_CELLS - 1) /
						PLAYERBOT_NAV_CLUSTER_CELLS;

				for (int clusterY = 0; clusterY < clusterHeight; ++clusterY)
				{
					const int minY = clusterY * PLAYERBOT_NAV_CLUSTER_CELLS;
					const int maxY = std::min(m_height, minY + PLAYERBOT_NAV_CLUSTER_CELLS);
					for (int clusterX = 0; clusterX < clusterWidth; ++clusterX)
					{
						const int minX = clusterX * PLAYERBOT_NAV_CLUSTER_CELLS;
						const int maxX = std::min(m_width, minX + PLAYERBOT_NAV_CLUSTER_CELLS);
						for (int y = minY; y < maxY; ++y)
						{
							for (int x = minX; x < maxX; ++x)
							{
								const int firstCell = Index(x, y);
								if (IsBlockedIndex(firstCell) || CellRegion(firstCell) != 0)
									continue;

								const DWORD regionID = (DWORD)m_regions.size();
								TAbstractRegion region;
								region.clusterX = clusterX;
								region.clusterY = clusterY;
								m_regions.push_back(region);
								queue.clear();
								queue.push_back(firstCell);
								SetCellRegion(firstCell, regionID);

								for (size_t head = 0; head < queue.size(); ++head)
								{
									int currentX, currentY;
									CellFromIndex(queue[head], currentX, currentY);
									for (int direction = 0; direction < 8; ++direction)
									{
										const int nextX = currentX + moveX[direction];
										const int nextY = currentY + moveY[direction];
										if (nextX < minX || nextX >= maxX || nextY < minY || nextY >= maxY ||
												IsBlockedCell(nextX, nextY))
											continue;
										if (moveX[direction] != 0 && moveY[direction] != 0 &&
												(IsBlockedCell(currentX + moveX[direction], currentY) ||
												 IsBlockedCell(currentX, currentY + moveY[direction])))
											continue;
										const int nextCell = Index(nextX, nextY);
										if (CellRegion(nextCell) != 0)
											continue;
										SetCellRegion(nextCell, regionID);
										queue.push_back(nextCell);
									}
								}
							}
						}
					}
				}

				// Every cardinal crossing of a cluster border is a portal candidate.
				// AddAbstractPortal retains several spatially separated alternatives
				// per region pair so bots do not all funnel through one arbitrary cell.
				for (int y = 0; y < m_height; ++y)
				{
					for (int x = 0; x < m_width; ++x)
					{
						const int cell = Index(x, y);
						if (IsBlockedIndex(cell))
							continue;
						if (x + 1 < m_width && (x + 1) % PLAYERBOT_NAV_CLUSTER_CELLS == 0)
						{
							const int other = Index(x + 1, y);
							if (!IsBlockedIndex(other))
							{
								AddAbstractPortal(CellRegion(cell), CellRegion(other), cell, other);
								AddAbstractPortal(CellRegion(other), CellRegion(cell), other, cell);
							}
						}
						if (y + 1 < m_height && (y + 1) % PLAYERBOT_NAV_CLUSTER_CELLS == 0)
						{
							const int other = Index(x, y + 1);
							if (!IsBlockedIndex(other))
							{
								AddAbstractPortal(CellRegion(cell), CellRegion(other), cell, other);
								AddAbstractPortal(CellRegion(other), CellRegion(cell), other, cell);
							}
						}
					}
				}

				return (DWORD)(m_regions.size() - 1);
			}

			uint16_t NextCellSearchToken()
			{
				++s_playerBotNavScratch.searchToken;
				if (s_playerBotNavScratch.searchToken == 0)
				{
					std::fill(s_playerBotNavScratch.nodeToken.begin(), s_playerBotNavScratch.nodeToken.end(), 0);
					s_playerBotNavScratch.searchToken = 1;
				}
				return s_playerBotNavScratch.searchToken;
			}

			bool AppendLocalRegionPath(int startCell, int targetCell, DWORD regionID,
					DWORD seed, std::vector<int>& path)
			{
				if (startCell < 0 || targetCell < 0 || regionID == 0 ||
						CellRegion(startCell) != regionID || CellRegion(targetCell) != regionID)
					return false;

				if (startCell == targetCell)
				{
					if (path.empty() || path.back() != startCell)
						path.push_back(startCell);
					return true;
				}

				const uint16_t token = NextCellSearchToken();
				std::vector<int> queue;
				queue.reserve(PLAYERBOT_NAV_CLUSTER_CELLS * PLAYERBOT_NAV_CLUSTER_CELLS);
				queue.push_back(startCell);
				s_playerBotNavScratch.nodeToken[startCell] = token;
				s_playerBotNavScratch.parent[startCell] = -1;

				const int moveX[8] = { 1, 1, 0, -1, -1, -1, 0, 1 };
				const int moveY[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };
				const int directionOffset = (int)(PlayerBotNavHash(seed ^ regionID) & 7U);
				bool found = false;
				for (size_t head = 0; head < queue.size() && !found; ++head)
				{
					int currentX, currentY;
					CellFromIndex(queue[head], currentX, currentY);
					for (int n = 0; n < 8; ++n)
					{
						const int direction = (directionOffset + n) & 7;
						const int nextX = currentX + moveX[direction];
						const int nextY = currentY + moveY[direction];
						if (IsBlockedCell(nextX, nextY))
							continue;
						if (moveX[direction] != 0 && moveY[direction] != 0 &&
								(IsBlockedCell(currentX + moveX[direction], currentY) ||
								 IsBlockedCell(currentX, currentY + moveY[direction])))
							continue;
						const int nextCell = Index(nextX, nextY);
						if (CellRegion(nextCell) != regionID || s_playerBotNavScratch.nodeToken[nextCell] == token)
							continue;
						s_playerBotNavScratch.nodeToken[nextCell] = token;
						s_playerBotNavScratch.parent[nextCell] = queue[head];
						queue.push_back(nextCell);
						if (nextCell == targetCell)
						{
							found = true;
							break;
						}
					}
				}

				if (!found)
					return false;

				std::vector<int> localPath;
				for (int cursor = targetCell; cursor >= 0; cursor = s_playerBotNavScratch.parent[cursor])
				{
					localPath.push_back(cursor);
					if (cursor == startCell)
						break;
				}
				if (localPath.empty() || localPath.back() != startCell)
					return false;
				std::reverse(localPath.begin(), localPath.end());
				for (size_t i = path.empty() ? 0 : 1; i < localPath.size(); ++i)
					path.push_back(localPath[i]);
				return true;
			}

			int AbstractHeuristic(DWORD fromRegion, DWORD toRegion) const
			{
				const TAbstractRegion& from = m_regions[fromRegion];
				const TAbstractRegion& to = m_regions[toRegion];
				return 10 * (abs(from.clusterX - to.clusterX) + abs(from.clusterY - to.clusterY));
			}

			bool FindFinePathInRegionCorridor(int startCell, int targetCell,
					const std::vector<DWORD>& corridor, DWORD seed, std::vector<int>& path,
					int& outExpanded, bool& outPartial)
			{
				path.clear();
				outExpanded = 0;
				outPartial = false;
				if (corridor.empty())
					return false;
				std::vector<BYTE> allowed(m_regions.size(), 0);
				for (size_t i = 0; i < corridor.size(); ++i)
				{
					if (corridor[i] == 0 || corridor[i] >= allowed.size())
						return false;
					allowed[corridor[i]] = 1;
				}

				// See PLAYERBOT_NAV_GREEDY_CORRIDOR_REGIONS.
				const int heuristicWeight =
						corridor.size() >= (size_t)PLAYERBOT_NAV_GREEDY_CORRIDOR_REGIONS
						? PLAYERBOT_NAV_GREEDY_WEIGHT : 2;
				const uint16_t token = NextCellSearchToken();
				struct TFineOpenNode
				{
					int f;
					int g;
					int cell;
					DWORD tie;
				};
				struct TFineOpenGreater
				{
					bool operator()(const TFineOpenNode& left, const TFineOpenNode& right) const
					{
						if (left.f != right.f)
							return left.f > right.f;
						return left.tie > right.tie;
					}
				};

				int targetX, targetY;
				CellFromIndex(targetCell, targetX, targetY);
				std::priority_queue<TFineOpenNode, std::vector<TFineOpenNode>, TFineOpenGreater> open;
				s_playerBotNavScratch.nodeToken[startCell] = token;
				s_playerBotNavScratch.nodeCost[startCell] = 0;
				s_playerBotNavScratch.parent[startCell] = -1;
				int startX, startY;
				CellFromIndex(startCell, startX, startY);
				TFineOpenNode first;
				first.g = 0;
				first.f = OctileDistance(startX, startY, targetX, targetY) * heuristicWeight;
				first.cell = startCell;
				first.tie = PlayerBotNavHash(seed ^ (DWORD)startCell);
				open.push(first);

				const int moveX[8] = { 1, 1, 0, -1, -1, -1, 0, 1 };
				const int moveY[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };
				const int moveCost[8] = { 10, 14, 10, 14, 10, 14, 10, 14 };
				const int directionOffset = (int)(PlayerBotNavHash(seed) & 7U);
				bool found = false;
				int expanded = 0;
				int bestCell = startCell;
				const int startH = OctileDistance(startX, startY, targetX, targetY);
				int bestH = startH;
				while (!open.empty())
				{
					const TFineOpenNode current = open.top();
					open.pop();
					if (s_playerBotNavScratch.nodeToken[current.cell] != token || s_playerBotNavScratch.nodeCost[current.cell] != current.g)
						continue;
					// Closed. A negative cost is one no later, cheaper arrival can
					// beat, so the neighbour test below never reopens the cell, and
					// the stale test above drops any entry still on the heap for it.
					s_playerBotNavScratch.nodeCost[current.cell] = -current.g - 1;
					++expanded;
					if (current.cell == targetCell)
					{
						found = true;
						break;
					}

					int currentX, currentY;
					CellFromIndex(current.cell, currentX, currentY);
					const int currentH = OctileDistance(currentX, currentY, targetX, targetY);
					if (currentH < bestH)
					{
						bestH = currentH;
						bestCell = current.cell;
					}
					if (expanded >= PLAYERBOT_NAV_MAX_CORRIDOR_EXPANSIONS)
						break;
					for (int n = 0; n < 8; ++n)
					{
						const int direction = (directionOffset + n) & 7;
						const int nextX = currentX + moveX[direction];
						const int nextY = currentY + moveY[direction];
						if (IsBlockedCell(nextX, nextY))
							continue;
						if (moveX[direction] != 0 && moveY[direction] != 0 &&
								(IsBlockedCell(currentX + moveX[direction], currentY) ||
								 IsBlockedCell(currentX, currentY + moveY[direction])))
							continue;
						const int nextCell = Index(nextX, nextY);
						const DWORD nextRegion = CellRegion(nextCell);
						if (nextRegion == 0 || nextRegion >= allowed.size() || !allowed[nextRegion])
							continue;

						int wallPenalty = 0;
						if (Clearance(nextCell) <= 1) wallPenalty = 8;
						else if (Clearance(nextCell) == 2) wallPenalty = 3;
						else if (Clearance(nextCell) == 3) wallPenalty = 1;
						const int waterPenalty =
								IsWaterIndex(nextCell) ? PLAYERBOT_NAV_WATER_PENALTY : 0;
						const int laneJitter = (int)(PlayerBotNavHash(seed ^ (DWORD)nextCell) & 1U);
						const int newCost = current.g + moveCost[direction] + wallPenalty +
								waterPenalty + laneJitter;
						if (s_playerBotNavScratch.nodeToken[nextCell] == token && newCost >= s_playerBotNavScratch.nodeCost[nextCell])
							continue;

						s_playerBotNavScratch.nodeToken[nextCell] = token;
						s_playerBotNavScratch.nodeCost[nextCell] = newCost;
						s_playerBotNavScratch.parent[nextCell] = current.cell;
						TFineOpenNode next;
						next.g = newCost;
						next.f = newCost + OctileDistance(nextX, nextY, targetX, targetY) * heuristicWeight;
						next.cell = nextCell;
						next.tie = PlayerBotNavHash(seed ^ (DWORD)nextCell);
						open.push(next);
					}
				}

			outExpanded = expanded;
				int endCell = targetCell;
				if (!found)
				{
					// Only the cap hands back a partial route; an exhausted corridor
					// is a real failure and stays one. And only when the nearest cell
					// reached is worth the walk - otherwise the bot would step out
					// and plan the identical search again.
					if (expanded < PLAYERBOT_NAV_MAX_CORRIDOR_EXPANSIONS || bestCell == startCell ||
							bestH + PLAYERBOT_NAV_PARTIAL_MIN_GAIN_CELLS * 10 > startH)
						return false;
					endCell = bestCell;
					outPartial = true;
				}
				for (int cursor = endCell; cursor >= 0; cursor = s_playerBotNavScratch.parent[cursor])
				{
					path.push_back(cursor);
					if (cursor == startCell)
						break;
				}
				if (path.empty() || path.back() != startCell)
					return false;
				std::reverse(path.begin(), path.end());
				return true;
			}

			// MT2009_PLUS_BOT_NAV_SHARED_SCRATCH_V1: every search goes through here -
			// the shared scratch is sized for this map, held for the search and
			// a failed allocation inside it ends the plan, not the core.
			bool FindHierarchicalRawPath(int startCell, int targetCell, DWORD seed,
					std::vector<int>& path)
			{
				path.clear();
				if (m_dwNavOffUntil && (long)(get_dword_time() - m_dwNavOffUntil) < 0)
					return false;
				TPlayerBotNavScratch& scratch = s_playerBotNavScratch;
				if (scratch.bBusy)
				{
					if (!scratch.bReentryLogged)
					{
						scratch.bReentryLogged = true;
						sys_err("PLAYERBOT_NAV: nested search refused map=%ld (the shared scratch is in use)", m_mapIndex);
					}
					return false;
				}
				if (!EnsureSharedScratch())
					return false;

				struct TScratchHold
				{
					TPlayerBotNavScratch& r;
					explicit TScratchHold(TPlayerBotNavScratch& s) : r(s) { r.bBusy = true; }
					~TScratchHold() { r.bBusy = false; }
				} hold(scratch);
				try
				{
					return FindHierarchicalRawPathShared(startCell, targetCell, seed, path);
				}
				catch (const std::bad_alloc&)
				{
					path.clear();
					std::vector<int>().swap(path);
					OnNavAllocFailed(m_mapIndex, (unsigned long long)scratch.nodeToken.size() *
							PLAYERBOT_NAV_SCRATCH_BYTES_PER_CELL, "search");
					return false;
				}
			}

			bool EnsureSharedScratch()
			{
				TPlayerBotNavScratch& scratch = s_playerBotNavScratch;
				const size_t cells = (size_t)m_width * (size_t)m_height;
				const size_t regions = m_regions.size();
				if (scratch.nodeToken.size() >= cells && scratch.regionToken.size() >= regions)
					return true;
				try
				{
					if (scratch.nodeToken.size() < cells)
					{
						// Freed before the bigger one is taken: growing in place
						// would hold both at once, at the worst moment for it.
						std::vector<uint16_t>().swap(scratch.nodeToken);
						std::vector<int>().swap(scratch.nodeCost);
						std::vector<int>().swap(scratch.parent);
						scratch.searchToken = 0;
						scratch.nodeToken.assign(cells, 0);
						scratch.nodeCost.assign(cells, 0);
						scratch.parent.assign(cells, -1);
					}
					if (scratch.regionToken.size() < regions)
					{
						std::vector<DWORD>().swap(scratch.regionToken);
						std::vector<int>().swap(scratch.regionCost);
						std::vector<int>().swap(scratch.regionParent);
						std::vector<int>().swap(scratch.regionParentEdge);
						scratch.regionSearchToken = 0;
						scratch.regionToken.assign(regions, 0);
						scratch.regionCost.assign(regions, 0);
						scratch.regionParent.assign(regions, -1);
						scratch.regionParentEdge.assign(regions, -1);
					}
				}
				catch (const std::bad_alloc&)
				{
					// All of it goes: a smaller map re-grows only what it needs.
					std::vector<uint16_t>().swap(scratch.nodeToken);
					std::vector<int>().swap(scratch.nodeCost);
					std::vector<int>().swap(scratch.parent);
					std::vector<DWORD>().swap(scratch.regionToken);
					std::vector<int>().swap(scratch.regionCost);
					std::vector<int>().swap(scratch.regionParent);
					std::vector<int>().swap(scratch.regionParentEdge);
					scratch.searchToken = 0;
					scratch.regionSearchToken = 0;
					OnNavAllocFailed(m_mapIndex, (unsigned long long)cells * PLAYERBOT_NAV_SCRATCH_BYTES_PER_CELL +
							(unsigned long long)regions * 16, "search scratch");
					return false;
				}
				sys_log(0, "PLAYERBOT_NAV: shared search scratch map=%ld cells=%u regions=%u bytes=%llu",
						m_mapIndex, (unsigned int)scratch.nodeToken.size(), (unsigned int)scratch.regionToken.size(),
						(unsigned long long)scratch.nodeToken.size() * PLAYERBOT_NAV_SCRATCH_BYTES_PER_CELL +
						(unsigned long long)scratch.regionToken.size() * 16);
				return true;
			}

			void OnNavAllocFailed(long mapIndex, unsigned long long bytes, const char* what)
			{
				m_dwNavOffUntil = get_dword_time() + PLAYERBOT_NAV_NOGRID_RETRY_MS;
				if (!m_dwNavOffUntil)
					m_dwNavOffUntil = 1;
				if (!m_bAllocFailLogged)
				{
					m_bAllocFailLogged = true;
					sys_err("PLAYERBOT_NAV: grid allocation failed map=%ld bytes=%llu (%s); no route planning on it for %u min",
							mapIndex, bytes, what, (unsigned int)(PLAYERBOT_NAV_NOGRID_RETRY_MS / 60000));
				}
				else
					sys_log(1, "PLAYERBOT_NAV: grid allocation failed again map=%ld bytes=%llu (%s)",
							mapIndex, bytes, what);
			}

			void ReleaseGrid()
			{
				m_initialized = false;
				std::vector<BYTE>().swap(m_cell);
				std::vector<uint16_t>().swap(m_component);
				std::vector<DWORD>().swap(m_componentWide);
				std::vector<DWORD>().swap(m_componentCells);
				std::vector<uint16_t>().swap(m_cellRegion);
				std::vector<DWORD>().swap(m_cellRegionWide);
				std::vector<TAbstractRegion>().swap(m_regions);
				m_routeCache.clear();
				m_routeCacheCount = 0;
				m_walkableCells = 0;
			}

			bool FindHierarchicalRawPathShared(int startCell, int targetCell, DWORD seed,
					std::vector<int>& path)
			{
				path.clear();
				if (startCell < 0 || targetCell < 0)
					return false;
				const DWORD startRegion = CellRegion(startCell);
				const DWORD targetRegion = CellRegion(targetCell);
				if (startRegion == 0 || targetRegion == 0)
					return false;
				if (startRegion == targetRegion)
					return AppendLocalRegionPath(startCell, targetCell, startRegion, seed, path);

				const DWORD abstractStartUs = PlayerBotClockUs();
				++s_playerBotNavScratch.regionSearchToken;
				if (s_playerBotNavScratch.regionSearchToken == 0)
				{
					std::fill(s_playerBotNavScratch.regionToken.begin(), s_playerBotNavScratch.regionToken.end(), 0);
					s_playerBotNavScratch.regionSearchToken = 1;
				}

				struct TRegionOpenNode
				{
					int f;
					int g;
					DWORD region;
					DWORD tie;
				};
				struct TRegionOpenGreater
				{
					bool operator()(const TRegionOpenNode& left, const TRegionOpenNode& right) const
					{
						if (left.f != right.f)
							return left.f > right.f;
						return left.tie > right.tie;
					}
				};

				std::priority_queue<TRegionOpenNode, std::vector<TRegionOpenNode>, TRegionOpenGreater> open;
				s_playerBotNavScratch.regionToken[startRegion] = s_playerBotNavScratch.regionSearchToken;
				s_playerBotNavScratch.regionCost[startRegion] = 0;
				s_playerBotNavScratch.regionParent[startRegion] = -1;
				s_playerBotNavScratch.regionParentEdge[startRegion] = -1;
				TRegionOpenNode first;
				first.g = 0;
				first.f = AbstractHeuristic(startRegion, targetRegion);
				first.region = startRegion;
				first.tie = PlayerBotNavHash(seed ^ startRegion);
				open.push(first);
				bool found = false;

				while (!open.empty())
				{
					const TRegionOpenNode current = open.top();
					open.pop();
					if (s_playerBotNavScratch.regionToken[current.region] != s_playerBotNavScratch.regionSearchToken ||
							s_playerBotNavScratch.regionCost[current.region] != current.g)
						continue;
					if (current.region == targetRegion)
					{
						found = true;
						break;
					}

					const TAbstractRegion& region = m_regions[current.region];
					for (size_t edgeIndex = 0; edgeIndex < region.edges.size(); ++edgeIndex)
					{
						const TAbstractEdge& edge = region.edges[edgeIndex];
						const int laneJitter = (int)(PlayerBotNavHash(seed ^ (DWORD)edge.fromCell) & 3U);
						const int newCost = current.g + 10 + laneJitter;
						if (s_playerBotNavScratch.regionToken[edge.toRegion] == s_playerBotNavScratch.regionSearchToken &&
								newCost >= s_playerBotNavScratch.regionCost[edge.toRegion])
							continue;
						s_playerBotNavScratch.regionToken[edge.toRegion] = s_playerBotNavScratch.regionSearchToken;
						s_playerBotNavScratch.regionCost[edge.toRegion] = newCost;
						s_playerBotNavScratch.regionParent[edge.toRegion] = (int)current.region;
						s_playerBotNavScratch.regionParentEdge[edge.toRegion] = (int)edgeIndex;
						TRegionOpenNode next;
						next.g = newCost;
						next.f = newCost + AbstractHeuristic(edge.toRegion, targetRegion);
						next.region = edge.toRegion;
						next.tie = PlayerBotNavHash(seed ^ edge.toRegion ^ (DWORD)edge.fromCell);
						open.push(next);
					}
				}

				if (!found)
					return false;

				std::vector<DWORD> corridor;
				for (DWORD cursor = targetRegion; ; )
				{
					corridor.push_back(cursor);
					if (cursor == startRegion)
						break;
					const int parent = s_playerBotNavScratch.regionParent[cursor];
					if (parent <= 0)
						return false;
					cursor = (DWORD)parent;
				}
				std::reverse(corridor.begin(), corridor.end());
				m_lastAbstractUs = PlayerBotClockUs() - abstractStartUs;
				m_lastCorridorRegions = (int)corridor.size();

				// The abstract graph decides which connected local regions form a
				// valid corridor.  A single fine-grained A* then chooses the best
				// real crossings inside that corridor.  This keeps reachability exact
				// without forcing every bot through one arbitrary portal midpoint.
				const DWORD fineStartUs = PlayerBotClockUs();
				const bool bFound = FindFinePathInRegionCorridor(startCell, targetCell,
						corridor, seed, path, m_lastFineExpanded, m_bLastPartial);
				m_lastFineUs = PlayerBotClockUs() - fineStartUs;
				return bFound;
			}

			bool m_initialized;
			long m_mapIndex;
			long m_baseX;
			long m_baseY;
			int m_width;
			int m_height;
			// MT2009_PLUS_BOT_NAV_PACKED_CELLS_V1: a cell is one byte - blocked,
			// water (walkable, but a bridge deck or a shallow: costs extra to cross
			// so that dry ground wins wherever there is a choice) and the clearance
			// (0-4) - where it was three bytes; the component and region ids are
			// 16-bit (largest on any map of either line: 95 components, 28307
			// regions on the desert). A map whose ids outgrow 16 bits is moved to
			// the 32-bit copy (m_componentWide / m_cellRegionWide) as it is built,
			// with a log line - an id is never wrapped.
			std::vector<BYTE> m_cell;
			std::vector<uint16_t> m_component;
			std::vector<DWORD> m_componentWide;
			// Cells in each component (by label, 0 unused), and on the map: what
			// IsPocketComponent measures by.
			std::vector<DWORD> m_componentCells;
			DWORD m_walkableCells = 0;
			// MT2009_PLUS_BOT_NAV_SHARED_SCRATCH_V1: the search stamps, costs and
			// parents live in s_playerBotNavScratch, shared by every map.
			// A grid that could not be allocated (or a search scratch that could
			// not grow) switches the map's route planning off until this stamp.
			DWORD m_dwNavOffUntil = 0;
			bool m_bAllocFailLogged = false;
			std::vector<uint16_t> m_cellRegion;
			std::vector<DWORD> m_cellRegionWide;
			struct TCachedRoute
			{
				long startX;
				long startY;
				DWORD dwStamp;
				std::vector<PIXEL_POSITION> waypoints;
			};
			std::map<int, std::vector<TCachedRoute> > m_routeCache;
			size_t m_routeCacheCount = 0;
			std::vector<TAbstractRegion> m_regions;
			// What the last plan spent where, for the far/slow plan line.
			DWORD m_lastAbstractUs = 0;
			DWORD m_lastFineUs = 0;
			int m_lastCorridorRegions = 0;
			int m_lastFineExpanded = 0;
			bool m_bLastPartial = false;
	};

	// MT2009_PLUS_BOT_NAV_GUILD_BUILDINGS_V1: the engine's word that a building
	// went up or came down (building.cpp, CObject::Show / CObject::Destroy,
	// server-patches/enginefixes). A map whose grid is not built yet reads the
	// building when it is; a dungeon instance has none.
	void OnPlayerBotObjectAreaChanged(long lMapIndex, long sx, long sy, long ex, long ey)
	{
		if (lMapIndex <= 0 || lMapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN)
			return;
		CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(lMapIndex);
		if (navigation.IsInitializedFor(lMapIndex))
			navigation.RefreshLiveArea(sx, sy, ex, ey);
	}

	// Set while this unit's statics are made; the engine's pointer is zero
	// until then (constant-initialised), and the buildings of the boot are
	// shown long before any grid exists.
	struct TPlayerBotObjectAreaHook
	{
		TPlayerBotObjectAreaHook()
		{
			g_pfnMt2009ObjectAreaChanged = &OnPlayerBotObjectAreaChanged;
		}
	};
	TPlayerBotObjectAreaHook s_playerBotObjectAreaHook;
}

#endif
