[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDirectory
)

# The wait between two Soul Stones (server-patches/soulstonewait, README.md):
# the books' wait of the world's difficulty, at most 12 hours, for
# training_grandmaster_skill.quest's next_time. Same replacements and marker
# as apply_soulstonewait.py (the Linux/VPS twin). A file without the expected
# code throws and nothing is written.

$ErrorActionPreference = 'Stop'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$mark = 'MT2009_PLUS_SOUL_STONE_WAIT_V1'
$edits = @(
    'char_skill.cpp',
    "`treturn wait > 0 ? wait : SKILLBOOK_LEARN_DELAY;`n}`n",
    "`treturn wait > 0 ? wait : SKILLBOOK_LEARN_DELAY;`n}`n`n// MT2009_PLUS_SOUL_STONE_WAIT_V1 (server-patches/soulstonewait): the wait between two Soul`n// Stones (G1 -> P) is the books' wait, at most the package's 12 hours.`nint M2SoulStoneWait()`n{`n`tconst int wait = M2SkillBookLearnDelay();`n`treturn wait <= 0 ? 0 : (wait > 12 * 3600 ? 12 * 3600 : wait);`n}`n",
    'questlua_pc.cpp',
    "const int ITEM_BROKEN_METIN_VNUM = 28960;`n",
    "const int ITEM_BROKEN_METIN_VNUM = 28960;`n`n// MT2009_PLUS_SOUL_STONE_WAIT_V1 (declare): training_grandmaster_skill.quest's next_time,`n// never later than the world's Soul Stone wait from now (char_skill.cpp).`nextern int M2SoulStoneWait();`nstatic int M2SoulStoneQuestFlag(const std::string& flag, int value)`n{`n`tif (flag != `"training_grandmaster_skill.next_time`")`n`t`treturn value;`n`tconst int cap = get_global_time() + M2SoulStoneWait();`n`treturn value > cap ? cap : value;`n}`n",
    'questlua_pc.cpp',
    "`t`t`tlua_pushnumber(L,pPC->GetFlag(pPC->GetCurrentQuestName() + `".`"+sz));`n",
    "`t`t`t// MT2009_PLUS_SOUL_STONE_WAIT_V1 (get)`n`t`t`tconst std::string qf = pPC->GetCurrentQuestName() + `".`" + sz;`n`t`t`tlua_pushnumber(L, M2SoulStoneQuestFlag(qf, pPC->GetFlag(qf)));`n",
    'questlua_pc.cpp',
    "`t`t`tpPC->SetFlag(pPC->GetCurrentQuestName()+`".`"+sz, int(rint(lua_tonumber(L,2))));`n",
    "`t`t`t// MT2009_PLUS_SOUL_STONE_WAIT_V1 (set)`n`t`t`tconst std::string qf = pPC->GetCurrentQuestName() + `".`" + sz;`n`t`t`tpPC->SetFlag(qf, M2SoulStoneQuestFlag(qf, int(rint(lua_tonumber(L,2)))));`n"
)
$texts = @{}
for ($i = 0; $i -lt $edits.Count; $i += 3) {
    $file = Join-Path $SourceDirectory $edits[$i]
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Brak pliku: $file" }
    if (-not $texts.ContainsKey($file)) { $texts[$file] = [IO.File]::ReadAllText($file, $latin1) }
}
for ($i = 0; $i -lt $edits.Count; $i += 3) {
    $file = Join-Path $SourceDirectory $edits[$i]
    $text = $texts[$file]
    $old = $edits[$i + 1]; $new = $edits[$i + 2]
    $marked = @($new.Split("`n") | Where-Object { $_.Contains($mark) })
    if ($marked.Count -gt 0 -and $text.Replace("`r`n", "`n").Contains($marked[0])) { continue }
    if ($text.Contains("`r`n")) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
    if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
        throw "Nie mozna zastosowac poprawki czekania na Kamien Duchowy: nie znaleziono oczekiwanego kodu w $($edits[$i])."
    }
    $index = $text.IndexOf($old, [StringComparison]::Ordinal)
    $texts[$file] = $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length)
}
$changed = $false
foreach ($file in @($texts.Keys)) {
    if ($texts[$file] -ne [IO.File]::ReadAllText($file, $latin1)) {
        [IO.File]::WriteAllText($file, $texts[$file], $latin1)
        $changed = $true
    }
}
return [pscustomobject]@{ Changed = $changed }
