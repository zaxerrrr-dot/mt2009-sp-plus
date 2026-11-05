#include <stdio.h>
#include "lua.h"
#include "lualib.h"
#include "lauxlib.h"
int main(int argc, char** argv) {
  lua_State* L = lua_open();
  luaopen_base(L); luaopen_table(L); luaopen_io(L); luaopen_string(L); luaopen_debug(L);
  lua_settop(L, 0);
  lua_newtable(L);
  for (int i = 2; i < argc; i++) { lua_pushstring(L, argv[i]); lua_rawseti(L, -2, i - 1); }
  lua_setglobal(L, "arg");
  int r = lua_dofile(L, argv[1]);
  lua_close(L);
  return r;
}
