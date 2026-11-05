local P = arg[1]
function color256(r, g, b) return "[COLOR r;"..(r/255.0).."|g;"..(g/255.0).."|b;"..(b/255.0).."]" end
function color(r,g,b) return "[COLOR r;"..r.."|g;"..g.."|b;"..b.."]" end
local dummy = {}
setmetatable(dummy, {__call = function() return "" end, __index = function(t, k) return dummy end, __newindex = function() end})
setmetatable(getfenv(0), {__index = function(t, k) return dummy end})
dofile(P .. "/translate.lua")
dofile(P .. "/quest/libs/translate/translate.lua")
local ok, err = pcall(dofile, P .. "/quest/locale.lua")
if not ok then io.stderr:write("locale.lua: " .. tostring(err) .. "\n") end
local out = io.open(arg[2], "wb")
local function esc(s)
  s = string.gsub(s, "\\", "\\\\")
  s = string.gsub(s, "\t", "\\t")
  s = string.gsub(s, "\n", "\\n")
  s = string.gsub(s, "\r", "")
  return s
end
local seen = {}
local function walk(t, path, depth)
  if depth > 20 or seen[t] then return end
  seen[t] = true
  for k, v in pairs(t) do
    local p = path .. "." .. tostring(k)
    if type(v) == "string" then out:write(p .. "\t" .. esc(v) .. "\n")
    elseif type(v) == "table" then walk(v, p, depth + 1) end
  end
  seen[t] = nil
end
walk(gameforge, "gameforge", 0)
walk(translate, "translate", 0)
walk(locale, "locale", 0)
out:close()
