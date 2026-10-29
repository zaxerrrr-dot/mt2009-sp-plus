#pragma once
// MT2009_PLUS_NAVGRID_V1 (ENABLE_MT2009_NAVGRID, Locale_inc.h): Auto Lowy navigation on the client's own attr grid,
// based on Path-Finder V1.0 by @coanitoa97 (tutorial by Kolen), reworked for a hunt that plans many times a minute:
//  - the grid is maps/<map>/navgrid.bin (1 cell = 100 units, the client's attr resolution; the "navgrid" pack built by
//    client-2.0.30/tools/navgrid), loaded once per map; a map without one is remembered (no lookups, no syserr lines);
//  - A* runs in a window round start and target (+48 cells, once more with +160) with work buffers kept between calls
//    (a generation stamp instead of a memset) and a node cap (60000 by default);
//  - the components (the O(1) "can I get there" answer) use the same corner rule as the search, so the two agree;
//  - near-wall penalty precomputed at load (a bit per cell); the temporary blocks (NavBlock) are a bit layer too;
//  - every coordinate is in the map's local pixel units (as player.GetMainCharacterPosition), the path's points are cell
//    centres (x*100+50).
#include "Locale_inc.h"
#ifdef ENABLE_MT2009_NAVGRID

#include <vector>
#include <string>

class CNavGrid
{
public:
	enum { CLS_ROAD = 0, CLS_NORMAL = 1, CLS_ROUGH = 2, CLS_WATER = 3 };
	enum { REACH_UNKNOWN = -1, REACH_NO = 0, REACH_YES = 1 };
	enum { DEFAULT_MAX_NODES = 60000, NAV_CELL = 100 };

	static CNavGrid& Instance();

	// The grid of this map (a name already tried and missing answers false at once).
	bool Load(const char* c_szMapName);
	bool IsLoaded() const { return m_bLoaded; }

	// Cell coordinates (map metres).
	bool IsWalkable(int x, int y) const;
	BYTE Component(int x, int y) const;
	bool NearestWalkable(int x, int y, int iRadius, BYTE byComp, int* pOutX, int* pOutY) const;

	// Pixel coordinates (local to the map).
	int Reach(long sx, long sy, long dx, long dy) const;
	bool FindPath(long sx, long sy, long dx, long dy, int iMaxNodes, std::vector<std::pair<long, long> >& rvecOut);
	bool IsWalkablePixel(long x, long y) const { return IsWalkable(ToCell(x), ToCell(y)); }
	void BlockTemp(long x, long y, long lRadius);
	void ClearTemp();

	static int ToCell(long v) { return v >= 0 ? (int)(v / NAV_CELL) : (int)((v - NAV_CELL + 1) / NAV_CELL); }
	static long ToPixel(int c) { return (long)c * NAV_CELL + NAV_CELL / 2; }

protected:
	CNavGrid();
	void Clear();
	bool __Parse(const BYTE* p, DWORD dwSize);
	void __BuildNearWall();
	void __BuildComponents();
	bool __Inside(int x, int y) const { return x >= m_iX0 && y >= m_iY0 && x < m_iX0 + m_iW && y < m_iY0 + m_iH; }
	bool __StaticWalk(DWORD i) const { return ((m_walk[i >> 3] >> (i & 7)) & 1) != 0; }
	int __CellCost(int x, int y) const;
	bool __LineOfSight(int x0, int y0, int x1, int y1) const;
	bool __SnapPair(long sx, long sy, long dx, long dy, int& fx, int& fy, int& tx, int& ty) const;
	bool __Search(int sx, int sy, int dx, int dy, int iMargin, int iMaxNodes, std::vector<std::pair<int, int> >& rvecRaw);

	bool m_bLoaded;
	std::string m_strMapName;	// the map of the grid, or the last one without one
	std::vector<BYTE> m_walk;	// 1 bit per cell
	std::vector<BYTE> m_near;	// 1 bit per cell: a blocked cell next to it
	std::vector<BYTE> m_cls;	// 2 bits per cell, empty for a single class
	std::vector<BYTE> m_temp;	// 1 bit per cell, empty while nothing is blocked
	std::vector<BYTE> m_comp;	// component per cell, 0 blocked, 255 unknown (more than 254)
	BYTE m_bySingleClass;
	int m_iW, m_iH, m_iX0, m_iY0;

	// Work memory of the search, kept between calls.
	struct SNode { int f, idx; };
	std::vector<DWORD> m_stamp;
	std::vector<int> m_g;
	std::vector<BYTE> m_dir;	// the step that reached the cell, bit 7 closed
	std::vector<SNode> m_open;
	DWORD m_dwGeneration;
};

#endif
