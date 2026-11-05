dofile(arg[1])
local t = getfenv(0)[arg[2]]
local out = io.open(arg[3], "wb")
local function esc(s)
  s = string.gsub(s, "\\", "\\\\"); s = string.gsub(s, "\t", "\\t"); s = string.gsub(s, "\n", "\\n"); s = string.gsub(s, "\r", "")
  return s
end
for sec, list in pairs(t) do
  if sec == "items" then
    for k, v in pairs(list) do out:write("items\t" .. tostring(k) .. "\t\t" .. esc(v) .. "\n") end
  else
    for i = 1, table.getn(list) do
      local e = list[i]
      out:write(sec .. "\t" .. e[1] .. "\t" .. e[2] .. "\t" .. esc(e[3]) .. "\n")
    end
  end
end
out:close()
