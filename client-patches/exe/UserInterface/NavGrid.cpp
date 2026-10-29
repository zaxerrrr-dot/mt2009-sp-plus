#include "StdAfx.h"
#include "NavGrid.h"

// MT2009_PLUS_NAVGRID_V1 - see NavGrid.h. Based on Path-Finder V1.0 by @coanitoa97 (tutorial by Kolen).
#ifdef ENABLE_MT2009_NAVGRID

#include "../EterPack/EterPackManager.h"
#include <algorithm>

namespace
{
	const DWORD NAV_MAGIC = 0x564E5850;	// "PXNV"
	const WORD FLAG_COST = 1;

	// Costs x10: road, normal ground, rough ground, water; a cell beside a blocked one costs more, so the way keeps
	// off the walls (the client stops dead on attr, it slides only along objects).
	const int COST_ROAD = 10;
	const int COST_NORMAL = 15;
	const int COST_ROUGH = 20;
	const int COST_WATER = 16;
	const int PEN_NEAR_WALL = 12;
	const int DIAG = 14, ORTHO = 10;

	const int SNAP_START = 6;	// cells round the character where its ground is looked for
	const int SNAP_TARGET = 6;	// cells round the target
	const int SNAP_TARGET_OWN = 2;	// a target across a thin wall: a cell of our ground this close still reaches it
	const int WINDOW_MARGIN_FIRST = 48;
	const int WINDOW_MARGIN_SECOND = 160;
	const int WINDOW_MAX_SIDE = 400;
	const int MAX_NODES_LIMIT = 400000;
	const int SMOOTH_LOOKAHEAD = 80;
	const int SMOOTH_MISSES = 6;

	const int VDX[8] = { 1, -1, 0, 0, 1, 1, -1, -1 };
	const int VDY[8] = { 0, 0, 1, -1, 1, -1, 1, -1 };

	inline WORD ReadWord(const BYTE* p) { return (WORD)(p[0] | (p[1] << 8)); }
	inline DWORD ReadDword(const BYTE* p) { return (DWORD)p[0] | ((DWORD)p[1] << 8) | ((DWORD)p[2] << 16) | ((DWORD)p[3] << 24); }

	struct SNodeLess
	{
		template <typename T> bool operator()(const T& a, const T& b) const { return a.f > b.f; }
	};

	template <typename T> void FreeVector(std::vector<T>& v)
	{
		std::vector<T>().swap(v);
	}
}

CNavGrid& CNavGrid::Instance()
{
	static CNavGrid s_kNav;
	return s_kNav;
}

CNavGrid::CNavGrid() :
	m_bLoaded(false), m_bySingleClass(CLS_NORMAL), m_iW(0), m_iH(0), m_iX0(0), m_iY0(0), m_dwGeneration(0)
{
}

void CNavGrid::Clear()
{
	m_bLoaded = false;
	m_strMapName.clear();
	FreeVector(m_walk);
	FreeVector(m_near);
	FreeVector(m_cls);
	FreeVector(m_temp);
	FreeVector(m_comp);
	FreeVector(m_stamp);
	FreeVector(m_g);
	FreeVector(m_dir);
	FreeVector(m_open);
	m_dwGeneration = 0;
	m_bySingleClass = CLS_NORMAL;
	m_iW = m_iH = m_iX0 = m_iY0 = 0;
}

bool CNavGrid::Load(const char* c_szMapName)
{
	if (!c_szMapName || !c_szMapName[0])
		return false;
	// The same map: the grid, or the answer that it has none - asked once, not on every call.
	if (m_strMapName == c_szMapName)
		return m_bLoaded;

	Clear();
	m_strMapName = c_szMapName;

	static const char* s_aszKeys[] = { "maps/%s/navgrid.bin", "%s/navgrid.bin" };
	for (int i = 0; i < 2; ++i)
	{
		char szFile[256];
		_snprintf(szFile, sizeof(szFile), s_aszKeys[i], c_szMapName);
		szFile[sizeof(szFile) - 1] = '\0';
		CMappedFile kFile;
		LPCVOID pvData = NULL;
		if (!CEterPackManager::Instance().Get(kFile, szFile, &pvData) || !pvData)
			continue;
		if (!__Parse((const BYTE*)pvData, kFile.Size()))
		{
			// Once per map: a damaged or foreign file.
			TraceError("NavGrid: %s is not a usable navigation grid", szFile);
			FreeVector(m_walk);
			FreeVector(m_cls);
			return false;
		}
		__BuildNearWall();
		__BuildComponents();
		m_bLoaded = true;
		return true;
	}
	// No grid for this map: Auto Lowy walks as before; nothing logged.
	return false;
}

bool CNavGrid::__Parse(const BYTE* p, DWORD dwSize)
{
	if (dwSize < 32 || ReadDword(p) != NAV_MAGIC)
		return false;
	const WORD wVersion = ReadWord(p + 4);
	// Version 3 is the package's own (32-byte header); 4 is ours (40 bytes: the stamp of the map's files after it).
	const DWORD dwHeader = wVersion == 3 ? 32 : (wVersion == 4 ? 40 : 0);
	if (!dwHeader || dwSize < dwHeader)
		return false;
	const WORD wFlags = ReadWord(p + 6);
	const WORD wMetres = ReadWord(p + 8);
	const WORD wW = ReadWord(p + 10), wH = ReadWord(p + 12);
	const WORD wX0 = ReadWord(p + 14), wY0 = ReadWord(p + 16);
	const WORD wClass = ReadWord(p + 18);
	if (wMetres != 1 || !wW || !wH || wClass > 3)
		return false;
	const DWORD dwCells = (DWORD)wW * (DWORD)wH;
	const DWORD dwWalkBytes = (dwCells + 7) / 8;
	const DWORD dwCostBytes = (wFlags & FLAG_COST) ? (dwCells + 3) / 4 : 0;
	if (dwSize < dwHeader + dwWalkBytes + dwCostBytes)
		return false;
	m_walk.assign(p + dwHeader, p + dwHeader + dwWalkBytes);
	if (dwCostBytes)
		m_cls.assign(p + dwHeader + dwWalkBytes, p + dwHeader + dwWalkBytes + dwCostBytes);
	m_bySingleClass = (BYTE)wClass;
	m_iW = wW;
	m_iH = wH;
	m_iX0 = wX0;
	m_iY0 = wY0;
	return true;
}

bool CNavGrid::IsWalkable(int x, int y) const
{
	if (!m_bLoaded || !__Inside(x, y))
		return false;
	const DWORD i = (DWORD)(y - m_iY0) * m_iW + (x - m_iX0);
	if (!m_temp.empty() && ((m_temp[i >> 3] >> (i & 7)) & 1))
		return false;
	return __StaticWalk(i);
}

void CNavGrid::__BuildNearWall()
{
	// A walkable cell with a blocked (or off-grid) cell among its 8 neighbours.
	const DWORD dwCells = (DWORD)m_iW * m_iH;
	m_near.assign((dwCells + 7) / 8, 0);
	for (int y = 0; y < m_iH; ++y)
		for (int x = 0; x < m_iW; ++x)
		{
			const DWORD i = (DWORD)y * m_iW + x;
			if (!__StaticWalk(i))
				continue;
			bool bNear = false;
			for (int k = 0; k < 8 && !bNear; ++k)
			{
				const int nx = x + VDX[k], ny = y + VDY[k];
				bNear = nx < 0 || ny < 0 || nx >= m_iW || ny >= m_iH || !__StaticWalk((DWORD)ny * m_iW + nx);
			}
			if (bNear)
				m_near[i >> 3] |= (BYTE)(1 << (i & 7));
		}
}

void CNavGrid::__BuildComponents()
{
	// The search steps diagonally only where both straight neighbours are open, so two cells it can join are always
	// joined by straight steps too: 4-connected components are exactly what the search can reach (the package's
	// 8-connected fill joined areas touching only at a corner, and the search then ran into its cap). Labels 1-254;
	// past that a cell is 255, "unknown", and the answer comes from the search.
	const DWORD dwCells = (DWORD)m_iW * m_iH;
	m_comp.assign(dwCells, 0);
	std::vector<DWORD> vecStack;
	vecStack.reserve(4096);
	int iNextLabel = 1;
	for (DWORD i0 = 0; i0 < dwCells; ++i0)
	{
		if (m_comp[i0] || !__StaticWalk(i0))
			continue;
		const BYTE byLabel = iNextLabel < 255 ? (BYTE)iNextLabel : (BYTE)255;
		if (iNextLabel < 255)
			++iNextLabel;
		m_comp[i0] = byLabel;
		vecStack.clear();
		vecStack.push_back(i0);
		while (!vecStack.empty())
		{
			const DWORD i = vecStack.back();
			vecStack.pop_back();
			const int cx = (int)(i % m_iW), cy = (int)(i / m_iW);
			for (int k = 0; k < 4; ++k)
			{
				const int nx = cx + VDX[k], ny = cy + VDY[k];
				if (nx < 0 || ny < 0 || nx >= m_iW || ny >= m_iH)
					continue;
				const DWORD ni = (DWORD)ny * m_iW + nx;
				if (m_comp[ni] || !__StaticWalk(ni))
					continue;
				m_comp[ni] = byLabel;
				vecStack.push_back(ni);
			}
		}
	}
}

BYTE CNavGrid::Component(int x, int y) const
{
	if (!m_bLoaded || !__Inside(x, y))
		return 0;
	return m_comp[(DWORD)(y - m_iY0) * m_iW + (x - m_iX0)];
}

bool CNavGrid::NearestWalkable(int x, int y, int iRadius, BYTE byComp, int* pOutX, int* pOutY) const
{
	// Ring by ring; byComp 0 any ground. A temporary block counts as blocked.
	for (int r = 0; r <= iRadius; ++r)
	{
		int iBest = -1, iBestX = 0, iBestY = 0;
		for (int dy = -r; dy <= r; ++dy)
			for (int dx = -r; dx <= r; ++dx)
			{
				if ((std::max)(abs(dx), abs(dy)) != r)
					continue;
				const int cx = x + dx, cy = y + dy;
				if (!IsWalkable(cx, cy) || (byComp && Component(cx, cy) != byComp))
					continue;
				const int d = dx * dx + dy * dy;
				if (iBest < 0 || d < iBest)
				{
					iBest = d;
					iBestX = cx;
					iBestY = cy;
				}
			}
		if (iBest >= 0)
		{
			*pOutX = iBestX;
			*pOutY = iBestY;
			return true;
		}
	}
	return false;
}

bool CNavGrid::__SnapPair(long sx, long sy, long dx, long dy, int& fx, int& fy, int& tx, int& ty) const
{
	if (!NearestWalkable(ToCell(sx), ToCell(sy), SNAP_START, 0, &fx, &fy))
		return false;
	const BYTE byOwn = Component(fx, fy);
	const int cx = ToCell(dx), cy = ToCell(dy);
	if (!NearestWalkable(cx, cy, SNAP_TARGET, 0, &tx, &ty))
		return false;
	const BYTE byTarget = Component(tx, ty);
	if (byOwn == byTarget || byOwn == 255 || byTarget == 255)
		return true;
	// The target's ground is another one; a cell of ours right beside it (a thin fence) still reaches it.
	return NearestWalkable(cx, cy, SNAP_TARGET_OWN, byOwn, &tx, &ty);
}

int CNavGrid::Reach(long sx, long sy, long dx, long dy) const
{
	if (!m_bLoaded)
		return REACH_UNKNOWN;
	int fx, fy;
	if (!NearestWalkable(ToCell(sx), ToCell(sy), SNAP_START, 0, &fx, &fy))
		return REACH_UNKNOWN;
	int tx, ty;
	const int cx = ToCell(dx), cy = ToCell(dy);
	if (!NearestWalkable(cx, cy, SNAP_TARGET, 0, &tx, &ty))
		return REACH_UNKNOWN;
	const BYTE byOwn = Component(fx, fy), byTarget = Component(tx, ty);
	if (byOwn == 255 || byTarget == 255)
		return REACH_UNKNOWN;
	if (byOwn == byTarget)
		return REACH_YES;
	return NearestWalkable(cx, cy, SNAP_TARGET_OWN, byOwn, &tx, &ty) ? REACH_YES : REACH_NO;
}

int CNavGrid::__CellCost(int x, int y) const
{
	const DWORD i = (DWORD)(y - m_iY0) * m_iW + (x - m_iX0);
	BYTE byClass = m_bySingleClass;
	if (!m_cls.empty())
		byClass = (m_cls[i >> 2] >> ((i & 3) * 2)) & 3;
	int c = COST_NORMAL;
	if (byClass == CLS_ROAD)
		c = COST_ROAD;
	else if (byClass == CLS_ROUGH)
		c = COST_ROUGH;
	else if (byClass == CLS_WATER)
		c = COST_WATER;
	if ((m_near[i >> 3] >> (i & 7)) & 1)
		return c + PEN_NEAR_WALL;
	if (!m_temp.empty())
		for (int k = 0; k < 8; ++k)
			if (!IsWalkable(x + VDX[k], y + VDY[k]))
				return c + PEN_NEAR_WALL;
	return c;
}

bool CNavGrid::__LineOfSight(int x0, int y0, int x1, int y1) const
{
	// Bresenham; every cell open with its four neighbours open too (one cell of room), except at the two ends.
	const int ex = x1, ey = y1, bx = x0, by = y0;
	const int dx = abs(x1 - x0), dy = abs(y1 - y0);
	const int sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
	int err = dx - dy;
	for (;;)
	{
		if (!IsWalkable(x0, y0))
			return false;
		const bool bEnd = (x0 == bx && y0 == by) || (x0 == ex && y0 == ey);
		if (!bEnd && (!IsWalkable(x0 + 1, y0) || !IsWalkable(x0 - 1, y0) ||
				!IsWalkable(x0, y0 + 1) || !IsWalkable(x0, y0 - 1)))
			return false;
		if (x0 == ex && y0 == ey)
			return true;
		const int e2 = 2 * err;
		if (e2 > -dy) { err -= dy; x0 += sx; }
		if (e2 < dx) { err += dx; y0 += sy; }
	}
}

bool CNavGrid::__Search(int sx, int sy, int dx, int dy, int iMargin, int iMaxNodes, std::vector<std::pair<int, int> >& rvecRaw)
{
	rvecRaw.clear();
	const int iSpanX = abs(dx - sx) + 1, iSpanY = abs(dy - sy) + 1;
	if (iSpanX > WINDOW_MAX_SIDE || iSpanY > WINDOW_MAX_SIDE)
		return false;
	const int iMarginX = (std::min)(iMargin, (WINDOW_MAX_SIDE - iSpanX) / 2);
	const int iMarginY = (std::min)(iMargin, (WINDOW_MAX_SIDE - iSpanY) / 2);
	const int wx0 = (std::max)(m_iX0, (std::min)(sx, dx) - iMarginX);
	const int wy0 = (std::max)(m_iY0, (std::min)(sy, dy) - iMarginY);
	const int wx1 = (std::min)(m_iX0 + m_iW, (std::max)(sx, dx) + iMarginX + 1);
	const int wy1 = (std::min)(m_iY0 + m_iH, (std::max)(sy, dy) + iMarginY + 1);
	const int W = wx1 - wx0, H = wy1 - wy0;
	if (W <= 0 || H <= 0)
		return false;
	const size_t nCells = (size_t)W * H;
	if (m_stamp.size() < nCells)
	{
		m_stamp.resize(nCells, 0);
		m_g.resize(nCells);
		m_dir.resize(nCells);
	}
	if (++m_dwGeneration == 0)
	{
		std::fill(m_stamp.begin(), m_stamp.end(), 0);
		m_dwGeneration = 1;
	}
	const DWORD gen = m_dwGeneration;
	m_open.clear();

	const int startIdx = (sy - wy0) * W + (sx - wx0);
	const int destIdx = (dy - wy0) * W + (dx - wx0);
	const int hdx = dx - wx0, hdy = dy - wy0;
#define NAV_H(idx) ( (abs((idx) % W - hdx) + abs((idx) / W - hdy)) * COST_ROAD - (2 * COST_ROAD - DIAG) * (std::min)(abs((idx) % W - hdx), abs((idx) / W - hdy)) )

	m_stamp[startIdx] = gen;
	m_g[startIdx] = 0;
	m_dir[startIdx] = 0x7F;
	SNode n0 = { NAV_H(startIdx), startIdx };
	m_open.push_back(n0);

	int iExpanded = 0;
	bool bFound = false;
	while (!m_open.empty())
	{
		std::pop_heap(m_open.begin(), m_open.end(), SNodeLess());
		const int cur = m_open.back().idx;
		m_open.pop_back();
		if (m_dir[cur] & 0x80)
			continue;
		m_dir[cur] |= 0x80;
		if (cur == destIdx)
		{
			bFound = true;
			break;
		}
		if (++iExpanded > iMaxNodes)
			break;
		const int lx = cur % W, ly = cur / W;
		const int cx = lx + wx0, cy = ly + wy0;
		for (int k = 0; k < 8; ++k)
		{
			const int nlx = lx + VDX[k], nly = ly + VDY[k];
			if (nlx < 0 || nly < 0 || nlx >= W || nly >= H)
				continue;
			const int nx = cx + VDX[k], ny = cy + VDY[k];
			if (!IsWalkable(nx, ny))
				continue;
			const bool bDiag = VDX[k] && VDY[k];
			if (bDiag && (!IsWalkable(cx + VDX[k], cy) || !IsWalkable(cx, cy + VDY[k])))
				continue;
			const int ni = nly * W + nlx;
			const bool bSeen = m_stamp[ni] == gen;
			if (bSeen && (m_dir[ni] & 0x80))
				continue;
			const int ng = m_g[cur] + __CellCost(nx, ny) * (bDiag ? DIAG : ORTHO) / ORTHO;
			if (!bSeen || ng < m_g[ni])
			{
				m_stamp[ni] = gen;
				m_g[ni] = ng;
				m_dir[ni] = (BYTE)k;
				SNode nn = { ng + NAV_H(ni), ni };
				m_open.push_back(nn);
				std::push_heap(m_open.begin(), m_open.end(), SNodeLess());
			}
		}
	}
#undef NAV_H
	if (!bFound)
		return false;

	for (int i = destIdx; ; )
	{
		rvecRaw.push_back(std::make_pair(i % W + wx0, i / W + wy0));
		if (i == startIdx)
			break;
		const BYTE k = m_dir[i] & 0x7F;
		if (k > 7)
			break;
		i = (i / W - VDY[k]) * W + (i % W - VDX[k]);
	}
	std::reverse(rvecRaw.begin(), rvecRaw.end());
	return !rvecRaw.empty() && rvecRaw.front().first == sx && rvecRaw.front().second == sy;
}

bool CNavGrid::FindPath(long sx, long sy, long dx, long dy, int iMaxNodes, std::vector<std::pair<long, long> >& rvecOut)
{
	rvecOut.clear();
	if (!m_bLoaded)
		return false;
	int fx, fy, tx, ty;
	if (!__SnapPair(sx, sy, dx, dy, fx, fy, tx, ty))
		return false;
	if (iMaxNodes <= 0)
		iMaxNodes = DEFAULT_MAX_NODES;
	iMaxNodes = (std::min)(iMaxNodes, (int)MAX_NODES_LIMIT);

	std::vector<std::pair<int, int> > vecRaw;
	if (!__Search(fx, fy, tx, ty, WINDOW_MARGIN_FIRST, iMaxNodes, vecRaw) &&
			!__Search(fx, fy, tx, ty, WINDOW_MARGIN_SECOND, iMaxNodes, vecRaw))
		return false;

	// String pulling, forward only: from each point the farthest one ahead in a clear line (a few misses in a row end
	// the look), so a long winding way costs O(n), not O(n^2).
	rvecOut.push_back(std::make_pair(ToPixel(vecRaw[0].first), ToPixel(vecRaw[0].second)));
	size_t i = 0;
	while (i + 1 < vecRaw.size())
	{
		size_t best = i + 1;
		int iMisses = 0;
		for (size_t j = i + 2; j < vecRaw.size() && j <= i + SMOOTH_LOOKAHEAD; ++j)
		{
			if (__LineOfSight(vecRaw[i].first, vecRaw[i].second, vecRaw[j].first, vecRaw[j].second))
			{
				best = j;
				iMisses = 0;
			}
			else if (++iMisses > SMOOTH_MISSES)
				break;
		}
		rvecOut.push_back(std::make_pair(ToPixel(vecRaw[best].first), ToPixel(vecRaw[best].second)));
		i = best;
	}
	return true;
}

void CNavGrid::BlockTemp(long x, long y, long lRadius)
{
	if (!m_bLoaded)
		return;
	if (m_temp.empty())
		m_temp.assign(((size_t)m_iW * m_iH + 7) / 8, 0);
	const int cx = ToCell(x), cy = ToCell(y);
	const int r = (std::max)(0, (std::min)(20, (int)((lRadius + NAV_CELL / 2) / NAV_CELL)));
	for (int dy = -r; dy <= r; ++dy)
		for (int dx = -r; dx <= r; ++dx)
		{
			if (dx * dx + dy * dy > r * r || !__Inside(cx + dx, cy + dy))
				continue;
			const DWORD i = (DWORD)(cy + dy - m_iY0) * m_iW + (cx + dx - m_iX0);
			m_temp[i >> 3] |= (BYTE)(1 << (i & 7));
		}
}

void CNavGrid::ClearTemp()
{
	FreeVector(m_temp);
}

#endif
