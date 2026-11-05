local dummy = {}
setmetatable(dummy, {__call = function() return "" end, __index = function(t, k) return dummy end, __newindex = function() end})
setmetatable(getfenv(0), {__index = function(t, k) return dummy end})
dofile(arg[1])
local out = io.open(arg[2], "wb")
local function esc(s)
  s = string.gsub(s, "\\", "\\\\"); s = string.gsub(s, "\t", "\\t"); s = string.gsub(s, "\n", "\\n"); s = string.gsub(s, "\r", "")
  return s
end
local function walk(t, path, depth)
  if depth > 20 then return end
  for k, v in pairs(t) do
    local p = path .. "." .. tostring(k)
    if type(v) == "string" then out:write(p .. "\t" .. esc(v) .. "\n")
    elseif type(v) == "table" and v ~= dummy then walk(v, p, depth + 1) end
  end
end
walk(rawget(getfenv(0), arg[3]), arg[3], 0)
out:close()
