[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceDirectory
)

# The health of monsters, bosses and Metin stones (server-patches/mobhp,
# README.md): a percent of mob_proto's max_hp from the event flag m2_mob_hp,
# at a spawn and live for every one standing when the flag moves. Same
# replacements and marker as apply_mobhp.py (the Linux/VPS twin). A file
# without the expected code throws and nothing is written.

$ErrorActionPreference = 'Stop'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$mark = 'MT2009_PLUS_MOB_HP_V1'
$edits = @(
    'char.cpp',
    "void CHARACTER::SetProto(const CMob * pkMob)`n{`n",
    "// MT2009_PLUS_MOB_HP_V1 (server-patches/mobhp): the health of monsters, bosses and`n// Metin stones, a percent of mob_proto's max_hp - the event flag m2_mob_hp`n// (10..300; 0 or 100 = the game as it was made), which the launcher's`n// difficulty window and the classic panel's card set. NPCs, ore veins, herb`n// bushes, doors and a still monster with no attack (a dungeon's gate) keep`n// their own.`nstatic int s_iM2MobHpPercent = 100;`n`nstatic bool M2MobHpApplies(const CHARACTER* ch, const TMobTable& t)`n{`n`tif (!ch || ch->IsPC())`n`t`treturn false;`n`tif (ch->IsStone())`n`t`treturn true;`n`tif (!ch->IsMonster())`n`t`treturn false;`n`treturn !(IS_SET(t.dwAIFlag, AIFLAG_NOMOVE) && t.dwDamageRange[1] == 0);`n}`n`nstatic int M2MobScaledMaxHP(DWORD base, int pct)`n{`n`tlong long v = (long long)base * pct / 100;`n`tif (v < 1)`n`t`tv = 1;`n`tif (v > INT_MAX)`n`t`tv = INT_MAX;`n`treturn (int)v;`n}`n`n// The flag moved (CQuestManager::SetEventFlag, on every core): the monsters`n// and stones standing take the new health and keep their share of it. One`n// whose max_hp somebody else set (a dungeon's UniqueSetMaxHP) is left alone.`nvoid M2ApplyMobHpPercent(int value)`n{`n`tconst int pct = value <= 0 ? 100 : (value < 10 ? 10 : (value > 300 ? 300 : value));`n`tconst int prev = s_iM2MobHpPercent;`n`tif (pct == prev)`n`t`treturn;`n`ts_iM2MobHpPercent = pct;`n`tint changed = 0;`n`tfor (auto& kv : CHARACTER_MANAGER::instance().GetCharacterVIDMap())`n`t{`n`t`tLPCHARACTER ch = kv.second;`n`t`tif (!ch || ch->IsPC() || ch->IsPet() || ch->IsDead())`n`t`t`tcontinue;`n`t`tconst TMobTable& t = ch->GetMobTable();`n`t`tif (!M2MobHpApplies(ch, t))`n`t`t`tcontinue;`n`t`tconst int real = ch->GetRealPoint(POINT_MAX_HP);`n`t`tconst int oldMax = ch->GetMaxHP();`n`t`tif (real != M2MobScaledMaxHP(t.dwMaxHP, prev) || oldMax < real || oldMax <= 0)`n`t`t`tcontinue;`n`t`tconst int hp = ch->GetHP();`n`t`tch->SetRealPoint(POINT_MAX_HP, M2MobScaledMaxHP(t.dwMaxHP, pct));`n`t`tch->PointChange(POINT_MAX_HP, 0);`n`t`tconst int newMax = ch->GetMaxHP();`n`t`tlong long newHp = (long long)hp * newMax / oldMax;`n`t`tif (hp > 0 && newHp < 1)`n`t`t`tnewHp = 1;`n`t`tif (newHp > newMax)`n`t`t`tnewHp = newMax;`n`t`tch->SetHP((int)newHp);`n`t`tch->BroadcastTargetPacket();`n`t`t++changed;`n`t}`n`tsys_log(0, `"MOB_HP: %d%% -> %d%% of max_hp, %d standing rescaled`", prev, pct, changed);`n}`n`nvoid CHARACTER::SetProto(const CMob * pkMob)`n{`n",
    'char.cpp',
    "`t`tiMaxHP = m_pkMobData->m_table.dwMaxHP;`n",
    "`t`tiMaxHP = m_pkMobData->m_table.dwMaxHP;`n`t`t// MT2009_PLUS_MOB_HP_V1 (spawn): the world's monster health.`n`t`tif (s_iM2MobHpPercent != 100 && M2MobHpApplies(this, m_pkMobData->m_table))`n`t`t`tiMaxHP = M2MobScaledMaxHP(m_pkMobData->m_table.dwMaxHP, s_iM2MobHpPercent);`n",
    'questmanager.cpp',
    "#include `"event_helper.h`"`n`nDWORD g_GoldDropTimeLimitValue = 0;`n",
    "#include `"event_helper.h`"`n`n// MT2009_PLUS_MOB_HP_V1 (declare): char.cpp, server-patches/mobhp.`nextern void M2ApplyMobHpPercent(int value);`n`nDWORD g_GoldDropTimeLimitValue = 0;`n",
    'questmanager.cpp',
    "`t`tm_mapEventFlag[name] = value;`n`n`t`tif (name == `"mob_item`")`n",
    "`t`tm_mapEventFlag[name] = value;`n`n`t`t// MT2009_PLUS_MOB_HP_V1 (flag): the monsters' health is live on every core.`n`t`tif (name == `"m2_mob_hp`")`n`t`t`t::M2ApplyMobHpPercent(value);`n`n`t`tif (name == `"mob_item`")`n"
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
        throw "Nie mozna zastosowac poprawki wytrzymalosci potworow: nie znaleziono oczekiwanego kodu w $($edits[$i])."
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
