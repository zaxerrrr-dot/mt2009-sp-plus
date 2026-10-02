[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDirectory
)

# A dungeon's own monster health (server-patches/dungeonhp, README.md): the
# quest functions d.count_players() and d.mob_hp_percent(vnum, percent) in
# questlua_dungeon.cpp, and (V2) a rescaled monster's regeneration from its
# max HP before the rescale (char.cpp). Same replacements and marker as apply_dungeonhp.py
# (the Linux/VPS twin). A file without the expected code throws and nothing
# is written.

$ErrorActionPreference = 'Stop'
$latin1 = [Text.Encoding]::GetEncoding(28591)
# Both markers (V1, V2) start with this.
$mark = 'MT2009_PLUS_DUNGEON_MOB_HP_V'
$edits = @(
    'questlua_dungeon.cpp',
    "`tALUA(dungeon_spawn_mob)`n`t{`n",
    "`t// MT2009_PLUS_DUNGEON_MOB_HP_V1 (server-patches/dungeonhp): the players in the selected`n`t// instance, bots included - a dungeon sizes its boss by them.`n`tALUA(dungeon_count_players)`n`t{`n`t`tCQuestManager& q = CQuestManager::instance();`n`t`tLPDUNGEON pDungeon = q.GetCurrentDungeon();`n`t`tint n = 0;`n`t`tif (pDungeon)`n`t`t{`n`t`t`tconst long lMapIndex = pDungeon->GetMapIndex();`n`t`t`tfor (auto& kv : CHARACTER_MANAGER::instance().GetCharacterVIDMap())`n`t`t`t{`n`t`t`t`tLPCHARACTER ch = kv.second;`n`t`t`t`tif (ch && ch->IsPC() && ch->GetMapIndex() == lMapIndex)`n`t`t`t`t`t++n;`n`t`t`t}`n`t`t}`n`t`tlua_pushnumber(L, n);`n`t`treturn 1;`n`t}`n`n`t// MT2009_PLUS_DUNGEON_MOB_HP_V1 (percent): d.mob_hp_percent(vnum, percent) - every living`n`t// monster or stone of the vnum in the instance, max HP times percent`n`t// (1..1000), its share of health kept. The real point moves too, so the`n`t// world-health flag (MT2009_PLUS_MOB_HP_V1) sees it set by somebody else.`n`tALUA(dungeon_mob_hp_percent)`n`t{`n`t`tCQuestManager& q = CQuestManager::instance();`n`t`tLPDUNGEON pDungeon = q.GetCurrentDungeon();`n`t`tif (!pDungeon || !lua_isnumber(L, 1) || !lua_isnumber(L, 2))`n`t`t{`n`t`t`tlua_pushnumber(L, 0);`n`t`t`treturn 1;`n`t`t}`n`t`tconst DWORD dwVnum = (DWORD) lua_tonumber(L, 1);`n`t`tconst int iPct = MINMAX(1, (int) lua_tonumber(L, 2), 1000);`n`t`tconst long lMapIndex = pDungeon->GetMapIndex();`n`t`tint n = 0;`n`t`tfor (auto& kv : CHARACTER_MANAGER::instance().GetCharacterVIDMap())`n`t`t{`n`t`t`tLPCHARACTER ch = kv.second;`n`t`t`tif (!ch || ch->IsPC() || ch->IsDead() || ch->GetRaceNum() != dwVnum || ch->GetMapIndex() != lMapIndex)`n`t`t`t`tcontinue;`n`t`t`tconst int oldMax = ch->GetMaxHP();`n`t`t`tif (oldMax <= 0)`n`t`t`t`tcontinue;`n`t`t`tconst int hp = ch->GetHP();`n`t`t`tlong long newMax = (long long) oldMax * iPct / 100;`n`t`t`tif (newMax < 1)`n`t`t`t`tnewMax = 1;`n`t`t`tif (newMax > INT_MAX)`n`t`t`t`tnewMax = INT_MAX;`n`t`t`tch->SetRealPoint(POINT_MAX_HP, (int) newMax);`n`t`t`tch->PointChange(POINT_MAX_HP, 0);`n`t`t`tconst int max = ch->GetMaxHP();`n`t`t`tlong long newHp = (long long) hp * max / oldMax;`n`t`t`tif (hp > 0 && newHp < 1)`n`t`t`t`tnewHp = 1;`n`t`t`tif (newHp > max)`n`t`t`t`tnewHp = max;`n`t`t`tch->SetHP((int) newHp);`n`t`t`tch->BroadcastTargetPacket();`n`t`t`t++n;`n`t`t}`n`t`tsys_log(0, `"DUNGEON_MOB_HP: map %ld vnum %u x%d%%, %d rescaled`", lMapIndex, dwVnum, iPct, n);`n`t`tlua_pushnumber(L, n);`n`t`treturn 1;`n`t}`n`n`tALUA(dungeon_spawn_mob)`n`t{`n",
    'questlua_dungeon.cpp',
    "`t`t`t{ `"spawn_mob`",`t`tdungeon_spawn_mob`t},`n",
    "`t`t`t{ `"spawn_mob`",`t`tdungeon_spawn_mob`t},`n`t`t`t{ `"count_players`",`tdungeon_count_players`t},`t// MT2009_PLUS_DUNGEON_MOB_HP_V1 (register)`n`t`t`t{ `"mob_hp_percent`",`tdungeon_mob_hp_percent`t},`n",
    'questlua_dungeon.cpp',
    "`ntemplate <class Func> Func CDungeon::ForEachMember(Func f)`n",
    "`n// MT2009_PLUS_DUNGEON_MOB_HP_V2 (declare): char.cpp, server-patches/dungeonhp.`nextern void M2SetRegenBaseMaxHP(DWORD dwVID, int iBaseMaxHP);`n`ntemplate <class Func> Func CDungeon::ForEachMember(Func f)`n",
    'questlua_dungeon.cpp',
    "`t`t`tconst int hp = ch->GetHP();`n`t`t`tlong long newMax = (long long) oldMax * iPct / 100;`n",
    "`t`t`tconst int hp = ch->GetHP();`n`t`t`t::M2SetRegenBaseMaxHP((DWORD) ch->GetVID(), oldMax);`t// MT2009_PLUS_DUNGEON_MOB_HP_V2 (base)`n`t`t`tlong long newMax = (long long) oldMax * iPct / 100;`n",
    'char.cpp',
    "void CHARACTER::Destroy()`n{`n",
    "// MT2009_PLUS_DUNGEON_MOB_HP_V2 (server-patches/dungeonhp): a monster whose max HP a`n// dungeon rescaled (d.mob_hp_percent) heals as many points a tick as it did`n// before: the max HP it had before the first rescale, by its VID.`nstatic std::unordered_map<DWORD, int> s_mapM2RegenBaseMaxHP;`n`nvoid M2SetRegenBaseMaxHP(DWORD dwVID, int iBaseMaxHP)`n{`n`tif (iBaseMaxHP > 0)`n`t`ts_mapM2RegenBaseMaxHP.emplace(dwVID, iBaseMaxHP);`n}`n`nstatic int M2RegenMaxHP(const CHARACTER* ch)`n{`n`tif (!s_mapM2RegenBaseMaxHP.empty())`n`t{`n`t`tauto it = s_mapM2RegenBaseMaxHP.find((DWORD) ch->GetVID());`n`t`tif (it != s_mapM2RegenBaseMaxHP.end())`n`t`t`treturn it->second;`n`t}`n`treturn ch->GetMaxHP();`n}`n`nvoid CHARACTER::Destroy()`n{`n`ts_mapM2RegenBaseMaxHP.erase((DWORD) GetVID());`t// MT2009_PLUS_DUNGEON_MOB_HP_V2 (destroy)`n",
    'char.cpp',
    "`t`t`tch->MonsterLog(`"HP_REGEN +%d`", MAX(1, (ch->GetMaxHP() * ch->GetMobTable().bRegenPercent) / 100));`n`t`t`tch->PointChange(POINT_HP, MAX(1, (ch->GetMaxHP() * ch->GetMobTable().bRegenPercent) / 100));`n",
    "`t`t`t// MT2009_PLUS_DUNGEON_MOB_HP_V2 (regen): the max HP before a dungeon's rescale.`n`t`t`tconst int iRegenMaxHP = M2RegenMaxHP(ch);`n`t`t`tch->MonsterLog(`"HP_REGEN +%d`", MAX(1, (iRegenMaxHP * ch->GetMobTable().bRegenPercent) / 100));`n`t`t`tch->PointChange(POINT_HP, MAX(1, (iRegenMaxHP * ch->GetMobTable().bRegenPercent) / 100));`n"
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
        throw "Nie mozna zastosowac poprawki zycia potworow w lochu: nie znaleziono oczekiwanego kodu w $($edits[$i])."
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
