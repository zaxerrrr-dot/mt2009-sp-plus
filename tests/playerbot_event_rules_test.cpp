// MT2009_PLUS_CHEST_DROP_TARGET_V1: g++ -std=c++17 tests/playerbot_event_rules_test.cpp && ./a.out
// The chest drop line's seventh column (who drops it) and its grouping.
#include "../linux-port/overlays/playerbot/src/game/src/playerbot_event_rules.h"
#undef NDEBUG
#include <cassert>
#include <cstdio>
using namespace playerbot_events;
int main(){
  Window w;
  assert(ParseLine("chestdrop\t3\t00:00\t12:00\t70\t51501\t1", w) && w.kind==KIND_CHESTDROP && w.map==51501 && w.target==1 && w.value==70);
  assert(ParseLine("chestdrop\t3\t00:00\t12:00\t70\t51501", w) && w.target==0);
  assert(ParseLine("chestdrop\t3\t00:00\t12:00\t70\t51501\t9", w) && w.target==0);
  assert(ParseLine("zuo\t3\t00:00\t12:00\t8\t63\t1", w) && w.target==0);
  // MT2009_PLUS_FISH_PUZZLE_V1: the fishing puzzle event's kind is read by its name.
  assert(ParseLine("fishpuzzle\t3\t00:00\t12:00\t0", w) && w.kind==KIND_FISHPUZZLE);
  assert(ParseLine("now\tchestdrop\t2000000000\t70\t50011\t0\t2", w) && w.now && w.target==2);
  std::vector<Window> v; Window a,b,c;
  ParseLine("chestdrop\t*\t00:00\t24:00\t70\t51501\t1", a);
  ParseLine("chestdrop\t*\t00:00\t24:00\t30\t51501\t2", b);
  ParseLine("chestdrop\t*\t00:00\t24:00\t50\t51501\t1", c);
  v.push_back(a); v.push_back(b); v.push_back(c);
  std::vector<Status> out; EvaluateWorldByMap(v, KIND_CHESTDROP, 1700000000, 0, 600, out);
  assert(out.size()==2 && out[0].target==1 && out[0].value==70 && out[1].target==2 && out[1].value==30);
  puts("ok"); return 0; }
