#!/usr/bin/env python3
"""ochao_bot_map.py - the Temple of Ochao's map knowledge for the bots
(MT2009_PLUS_OCHAO_BOTS_V1, playerbot_ochao_bots.h).

    ochao_bot_map.py decode <server_attr> <grid.bin>    (needs python-lzo)
    ochao_bot_map.py gen <workdir> <regen.txt>           (workdir holds grid.bin)

`decode` expands the map's server_attr (SECTREE_MANAGER::LoadAttribute: int32
width/height in sectors, then per sector an lzo1x block of 128x128 uint32) to
one byte per 50-unit cell. `gen` measures the labyrinth on it - the clearance
of every cell, a Dijkstra from the Teleporter (npc.txt 400,385) that prefers
the corridor middles - and writes hubs.txt (the regen's spawn lines clustered
into hunting spots) and tree.txt (the way out: every corner of the shortest
walk from the gate, the eleven rooms, the boss points and the spots to the
Teleporter, each edge a straight line with three open cells either side).
The two tables in playerbot_ochao_bots.h are these files.
One-shot analysis, not part of the server build.
"""
import sys
if len(sys.argv) >= 2 and sys.argv[1] == 'decode':
    import struct, lzo
    d = open(sys.argv[2], 'rb').read()
    w, h = struct.unpack_from('<ii', d, 0); off = 8
    W = w * 128; H = h * 128
    grid = bytearray(W * H)
    for sy in range(h):
        for sx in range(w):
            (n,) = struct.unpack_from('<I', d, off); off += 4
            raw = lzo.decompress(d[off:off + n], False, 128 * 128 * 4); off += n
            a = struct.unpack('<16384I', raw)
            for cy in range(128):
                for cx in range(128):
                    grid[(sy * 128 + cy) * W + sx * 128 + cx] = a[cy * 128 + cx] & 0xff
    open(sys.argv[3], 'wb').write(struct.pack('<ii', W, H) + bytes(grid))
    sys.exit(0)
if len(sys.argv) < 2 or sys.argv[1] != 'gen':
    sys.exit(__doc__)
sys.argv = [sys.argv[0]] + sys.argv[2:]
import struct, sys, math
from collections import deque
S=sys.argv[1]; REGEN=sys.argv[2]
d=open(S+'/grid.bin','rb').read();W,H=struct.unpack_from('<ii',d);g=d[8:]
BX,BY=844800,1408000
def blk(x,y): return x<0 or y<0 or x>=W or y>=H or (g[y*W+x]&1)
# clearance: distance (in cells) to nearest blocked, capped at 8 (BFS multi-source)
clr=[99]*(W*H); q=deque()
for i in range(W*H):
  if g[i]&1: clr[i]=0; q.append(i)
while q:
  j=q.popleft(); x,y=j%W,j//W; c=clr[j]
  if c>=8: continue
  for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
    X,Y=x+dx,y+dy
    if 0<=X<W and 0<=Y<H:
      k=Y*W+X
      if clr[k]>c+1: clr[k]=c+1; q.append(k)
def w2c(wx,wy): return ((wx-BX)//50,(wy-BY)//50)
def c2w(cx,cy): return (BX+cx*50+25,BY+cy*50+25)
def snap(cx,cy,minclr=4,r=30):
  best=None
  for dy in range(-r,r+1):
    for dx in range(-r,r+1):
      X,Y=cx+dx,cy+dy
      if 0<=X<W and 0<=Y<H and clr[Y*W+X]>=minclr:
        dd=dx*dx+dy*dy
        if best is None or dd<best[0]: best=(dd,X,Y)
  return (best[1],best[2]) if best else None
# BFS from teleporter (8-conn, cost 10/14 via dijkstra-lite using clearance>=2 preference)
import heapq
tele=snap(*w2c(884800,1446500),3)
INF=1<<60
dist=[INF]*(W*H); par=[-1]*(W*H)
s=tele[1]*W+tele[0]; dist[s]=0; h=[(0,s)]
nb=[(1,0,10),(-1,0,10),(0,1,10),(0,-1,10),(1,1,14),(1,-1,14),(-1,1,14),(-1,-1,14)]
while h:
  dd,j=heapq.heappop(h)
  if dd>dist[j]: continue
  x,y=j%W,j//W
  for dx,dy,c in nb:
    X,Y=x+dx,y+dy
    if 0<=X<W and 0<=Y<H:
      k=Y*W+X
      if g[k]&1: continue
      if dx and dy and ((g[y*W+X]&1) or (g[Y*W+x]&1)): continue
      pen = 0 if clr[k]>=5 else (5-clr[k])*8   # prefer corridor middle
      nd=dd+c+pen
      if nd<dist[k]: dist[k]=nd; par[k]=j; heapq.heappush(h,(nd,k))
print('tele',tele,c2w(*tele))
def los(a,b,minclr=3):
  (x0,y0),(x1,y1)=a,b
  n=max(abs(x1-x0),abs(y1-y0))*2+1
  for i in range(n+1):
    t=i/n; x=round(x0+(x1-x0)*t); y=round(y0+(y1-y0)*t)
    if clr[y*W+x]<minclr: return False
  return True
# key points
rooms=[(193,145),(123,216),(224,383),(348,708),(375,608),(430,516),(444,382),(388,195),(446,247),(592,139),(646,152)]
bosses=[('bodyguard',550,138),('bodyguard',221,402),('bodyguard',383,709),('lord',433,82)]
# hubs from regen density
spots=[]
for l in open(REGEN):
  p=l.split()
  if len(p)<11: continue
  spots.append((BX+int(p[1])*100,BY+int(p[2])*100,int(p[-1])))
rem=list(spots); hubs=[]
while rem and len(hubs)<22:
  best=None
  for sx,sy,v in rem:
    n=sum(1 for tx,ty,_ in rem if abs(tx-sx)<3200 and abs(ty-sy)<3200)
    if best is None or n>best[0]: best=(n,sx,sy)
  n,sx,sy=best
  if n<4: break
  pts=[(tx,ty) for tx,ty,_ in rem if abs(tx-sx)<3200 and abs(ty-sy)<3200]
  mx=sum(p[0] for p in pts)//len(pts); my=sum(p[1] for p in pts)//len(pts)
  c=snap(*w2c(mx,my),5)
  hx,hy=c2w(*c)
  if all(math.hypot(hx-a,hy-b)>=5000 for a,b,_ in hubs):
    hubs.append((hx,hy,n))
  rem=[r for r in rem if not(abs(r[0]-sx)<3600 and abs(r[1]-sy)<3600)]
print('hubs',len(hubs))
for h_ in hubs: 
  c=w2c(h_[0],h_[1]); print('  hub',h_, 'walk_to_tele=%.0fk'%(dist[c[1]*W+c[0]]/10*50/1000))
# exit tree
gate=snap(*w2c(853700,1416400),4)
leaves=[('gate',gate)]+[('room%d'%(i+1),snap(r[0]*2,r[1]*2,4)) for i,r in enumerate(rooms)]+[(b[0],snap(b[1]*2,b[2]*2,4)) for b in bosses]+[('hub%d'%i,w2c(h_[0],h_[1])) for i,h_ in enumerate(hubs)]
nodes=[{'c':tele,'next':-1,'name':'teleporter'}]; cell2node={s:0}
intree=set([s])
for name,(cx,cy) in leaves:
  k=cy*W+cx; chain=[k]
  while chain[-1] not in intree and par[chain[-1]]>=0: chain.append(par[chain[-1]])
  join=chain[-1]
  # simplify chain from leaf to join: greedy furthest LOS
  pts=[(c%W,c//W) for c in chain]
  simp=[0]; i=0
  while i<len(pts)-1:
    j=len(pts)-1
    while j>i+1 and not los(pts[i],pts[j]): j-=1
    simp.append(j); i=j
  # join node: if join cell not a node, split: find node whose segment contains join -> simpler: create node at join, with next = node reachable (walk par until a node cell)
  if join not in cell2node:
    sub=[join]
    while sub[-1] not in cell2node: sub.append(par[sub[-1]])
    sp=[(c%W,c//W) for c in sub]
    ss=[0]; i=0
    while i<len(sp)-1:
      j=len(sp)-1
      while j>i+1 and not los(sp[i],sp[j]): j-=1
      ss.append(j); i=j
    nx=cell2node[sub[-1]]
    for idx in reversed(ss[:-1]):
      nodes.append({'c':sp[idx],'next':nx,'name':'join' if idx==0 else ''}); cell2node[sub[idx]]=len(nodes)-1; nx=len(nodes)-1
  nxt=cell2node[join]
  for idx in reversed(simp[:-1]):
    c=chain[idx]
    nodes.append({'c':pts[idx],'next':nxt,'name':name if idx==0 else ''}); cell2node[c]=len(nodes)-1; nxt=len(nodes)-1
  for c in chain: intree.add(c)
  # mark intermediate chain cells as belonging to the node ahead of them (so later joins find a node by following par)
print('tree nodes',len(nodes))
# verify every edge LOS
bad=0
for i,n in enumerate(nodes):
  if n['next']>=0 and not los(n['c'],nodes[n['next']]['c'],1): bad+=1
print('edges without LOS',bad)
open(S+'/tree.txt','w').write('\n'.join('%d %d %d %d %s'%(i,*c2w(*n['c']),n['next'],n['name']) for i,n in enumerate(nodes)))
open(S+'/hubs.txt','w').write('\n'.join('%d %d %d'%h_ for h_ in hubs))
# walk length of each leaf to teleporter
for name,(cx,cy) in leaves[:16]:
  print(name, 'walk %.0fk'%(dist[cy*W+cx]/10*50/1000))
