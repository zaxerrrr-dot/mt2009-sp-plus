#!/usr/bin/env python3
"""gen_edits.py [<game/src dir>] -- writes edits.json (MT2009_PLUS_DS_DISTINCT_ATTR_V1, README.md) and, given a game/src
dir (an engine tree with every earlier patch applied - the test tree), checks that each edit's code is there exactly
once (or its marker already is). Dragon Stone additional bonuses never repeat: PutAttributes clears all 7 slots (the
reroll's ClearAttribute() cleared only 0-4, so a stale 6th slot came back beside the new roll), the distinct pick is
robust and a hard guard re-picks a repeated type; a stone loaded with a repeated bonus gets it rerolled (event flag
m2_ds_dup_repair_off 1 switches that off). Applied after bonusyglobal (DSStoneTable), e.g. last."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_DS_DISTINCT_ATTR_V1'


def E(file, tag, old, new):
    return {'file': file, 'marker': '%s (%s)' % (M, tag), 'old': old, 'new': new}


OLD_DISTINCT = '''bool MakeDistinctRandomNumberSet(std::list <float> prob_lst, OUT std::vector<int>& random_set)
{
	int size = prob_lst.size();
	int n = random_set.size();
	if (size < n)
		return false;

	std::vector <int> select_bit(size, 0);
	for (int i = 0; i < n; i++)
	{
		float range = 0.f;
		for (std::list <float>::iterator it = prob_lst.begin(); it != prob_lst.end(); it++)
		{
			range += *it;
		}
		float r = fnumber (0.f, range);
		float sum = 0.f;
		int idx = 0;
		for (std::list <float>::iterator it = prob_lst.begin(); it != prob_lst.end(); it++)
		{
			while (select_bit[idx++]);

			sum += *it;
			if (sum >= r)
			{
				select_bit[idx - 1] = 1;
				random_set[i] = idx - 1;
				prob_lst.erase(it);
				break;
			}
		}
	}
	return true;
}
'''

NEW_DISTINCT = '''// %s (distinct set): n distinct indices of prob_lst, each weighted by its prob among the ones not picked
// yet. Every iteration picks (a float sum short of r falls back to the last unpicked index, a positive-prob one when
// there is one), an index is never picked twice, and random_set never keeps a default 0. Same weighting as before.
bool MakeDistinctRandomNumberSet(std::list <float> prob_lst, OUT std::vector<int>& random_set)
{
	const int size = (int) prob_lst.size();
	const int n = (int) random_set.size();
	if (size < n)
		return false;

	std::vector<float> probs(prob_lst.begin(), prob_lst.end());
	std::vector<char> selected(size, 0);
	for (int i = 0; i < n; i++)
	{
		float range = 0.f;
		int lastAny = -1, lastPos = -1;
		for (int j = 0; j < size; j++)
		{
			if (selected[j])
				continue;
			lastAny = j;
			if (probs[j] > 0.f)
			{
				range += probs[j];
				lastPos = j;
			}
		}
		if (lastAny < 0)
			return false;
		int pick = (lastPos >= 0) ? lastPos : lastAny;
		if (range > 0.f)
		{
			const float r = fnumber(0.f, range);
			float sum = 0.f;
			for (int j = 0; j < size; j++)
			{
				if (selected[j] || probs[j] <= 0.f)
					continue;
				sum += probs[j];
				if (sum >= r)
				{
					pick = j;
					break;
				}
			}
		}
		selected[pick] = 1;
		random_set[i] = pick;
	}
	return true;
}

// %s (re-pick): an index of vec_add whose type is in none of used, weighted by prob (the last such one when a
// float sum falls short, any such one when every prob is 0); -1 when every type is used.
static int DSPickUnusedAdditional(const DragonSoulTable::TVecApplys& vec_add, const std::vector<WORD>& used)
{
	std::vector<int> cand;
	float range = 0.f;
	for (size_t j = 0; j < vec_add.size(); ++j)
	{
		const WORD t = vec_add[j].apply_type;
		if (POINT_NONE == t || std::find(used.begin(), used.end(), t) != used.end())
			continue;
		bool twice = false;	// a type listed twice in the table counts once
		for (size_t c = 0; c < cand.size() && !twice; ++c)
			twice = (vec_add[cand[c]].apply_type == t);
		if (twice)
			continue;
		cand.push_back((int) j);
		if (vec_add[j].prob > 0.f)
			range += vec_add[j].prob;
	}
	if (cand.empty())
		return -1;
	if (range <= 0.f)
		return cand[number(0, (int) cand.size() - 1)];
	const float r = fnumber(0.f, range);
	float sum = 0.f;
	int lastPos = cand.back();
	for (size_t c = 0; c < cand.size(); ++c)
	{
		if (vec_add[cand[c]].prob <= 0.f)
			continue;
		lastPos = cand[c];
		sum += vec_add[cand[c]].prob;
		if (sum >= r)
			return cand[c];
	}
	return lastPos;
}
''' % (M, M)

OLD_PUT_BASIC = '''	fWeight /= 100.f;

	int n = MIN(basic_apply_num, vec_basic_applys.size());
	for (int i = 0; i < n; i++)
	{
		const SApply& basic_apply = vec_basic_applys[i];
		WORD bType = basic_apply.apply_type; // MT2009_PLUS_WIDE_ATTR_V1
		short sValue = (short)(ceil((float)basic_apply.apply_value * fWeight - 0.01f));

		pDS->SetForceAttribute(i, bType, sValue);
	}

	BYTE additional_attr_num'''

NEW_PUT_BASIC = '''	fWeight /= 100.f;

	// %s (clear): a full roll - all 7 slots go first. The reroll (DoChangeAttribute) cleared with
	// CItem::ClearAttribute(), which stops at MAX_NORM_ATTR_NUM (5): the 6th slot (index 5, the third additional
	// bonus of a legendary / mythic stone, add_max 3) kept the old roll's bonus, beside the new one when the new
	// roll had 1-2 additional bonuses - a repeated bonus whenever the new roll had the same type (8 November 2026).
	for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; i++)
		pDS->ClearAttribute(i);

	int n = MIN(basic_apply_num, vec_basic_applys.size());
	for (int i = 0; i < n; i++)
	{
		const SApply& basic_apply = vec_basic_applys[i];
		WORD bType = basic_apply.apply_type; // MT2009_PLUS_WIDE_ATTR_V1
		short sValue = (short)(ceil((float)basic_apply.apply_value * fWeight - 0.01f));

		pDS->SetForceAttribute(i, bType, sValue);
	}

	BYTE additional_attr_num''' % M

OLD_PUT_ADD = '''		for (int i = 0; i < additional_attr_num; i++)
		{
			int r = random_set[i];
			const SApply& additional_attr = vec_addtional_applys[r];
			WORD bType = additional_attr.apply_type; // MT2009_PLUS_WIDE_ATTR_V1
			short sValue = (short)(ceil((float)additional_attr.apply_value * fWeight - 0.01f));

			pDS->SetForceAttribute(DRAGON_SOUL_ADDITIONAL_ATTR_START_IDX + i, bType, sValue);
		}
'''

NEW_PUT_ADD = '''		// %s (guard): no additional type equal to a basic one or to an earlier additional one (a table
		// listing a type twice, a bad index) - re-picked from the types left, logged; none left = the slot stays empty.
		std::vector<WORD> vecUsed;
		for (int i = 0; i < DRAGON_SOUL_ADDITIONAL_ATTR_START_IDX; i++)
			if (pDS->GetAttributeType(i))
				vecUsed.push_back(pDS->GetAttributeType(i));
		int slot = DRAGON_SOUL_ADDITIONAL_ATTR_START_IDX;
		for (int i = 0; i < additional_attr_num && slot < ITEM_ATTRIBUTE_MAX_NUM; i++)
		{
			int r = random_set[i];
			if (r < 0 || r >= (int) vec_addtional_applys.size() || POINT_NONE == vec_addtional_applys[r].apply_type
					|| std::find(vecUsed.begin(), vecUsed.end(), vec_addtional_applys[r].apply_type) != vecUsed.end())
			{
				const int r2 = DSPickUnusedAdditional(vec_addtional_applys, vecUsed);
				sys_err("[DS_ATTR] PutAttributes vnum=%%u id=%%u: additional #%%d (index %%d, type %%d) repeats a bonus - re-picked index %%d",
					pDS->GetVnum(), pDS->GetID(), i, r,
					(r >= 0 && r < (int) vec_addtional_applys.size()) ? (int) vec_addtional_applys[r].apply_type : -1, r2);
				if (r2 < 0)
					break;
				r = r2;
			}
			const SApply& additional_attr = vec_addtional_applys[r];
			WORD bType = additional_attr.apply_type; // MT2009_PLUS_WIDE_ATTR_V1
			short sValue = (short)(ceil((float)additional_attr.apply_value * fWeight - 0.01f));

			pDS->SetForceAttribute(slot++, bType, sValue);
			vecUsed.push_back(bType);
		}
''' % M

OLD_REPAIR_END = '''	return PutAttributes(pItem);
}
'''

NEW_REPAIR_END = '''	return PutAttributes(pItem);
}

// %s (repair): a stone loaded with an additional bonus repeating a basic or an earlier additional one (the
// stale 6th slot of a reroll before this fix) - that one is rerolled to a type the stone has not got, weighted by the
// prob of the stone's own table (DSStoneTable), its value from the same table and weight as a roll's. The first of
// the repeated ones stays, the other bonuses are not touched; no type left = the slot is emptied. True when changed.
// Called from the item load (input_db.cpp ItemLoad, char.cpp safebox) before the stone is worn.
bool DSManager::RepairDuplicateAttributes(LPITEM pDS)
{
	if (NULL == pDS || !pDS->IsDragonSoul() || NULL == m_pTable)
		return false;

	std::vector<WORD> vecUsed;
	std::vector<int> vecDupSlots;
	for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; i++)
	{
		const WORD t = pDS->GetAttributeType(i);
		if (POINT_NONE == t)
			continue;
		if (i >= DRAGON_SOUL_ADDITIONAL_ATTR_START_IDX && std::find(vecUsed.begin(), vecUsed.end(), t) != vecUsed.end())
			vecDupSlots.push_back(i);
		else
			vecUsed.push_back(t);
	}
	if (vecDupSlots.empty())
		return false;

	BYTE ds_type, grade_idx, step_idx, strength_idx;
	GetDragonSoulInfo(pDS->GetVnum(), ds_type, grade_idx, step_idx, strength_idx);
	DragonSoulTable* pTable = DSStoneTable(m_pTable, pDS, ds_type, grade_idx);
	DragonSoulTable::TVecApplys vec_add;
	float fWeight = 0.f;
	if (!pTable->GetAdditionalApplys(ds_type, vec_add) || !pTable->GetWeight(ds_type, grade_idx, step_idx, strength_idx, fWeight))
	{
		sys_err("[DS_ATTR] RepairDuplicateAttributes vnum=%%u id=%%u: no table data for ds_type=%%d", pDS->GetVnum(), pDS->GetID(), ds_type);
		return false;
	}
	fWeight /= 100.f;

	for (size_t k = 0; k < vecDupSlots.size(); ++k)
	{
		const int slot = vecDupSlots[k];
		const WORD oldType = pDS->GetAttributeType(slot);
		const short oldValue = pDS->GetAttributeValue(slot);
		const int r = DSPickUnusedAdditional(vec_add, vecUsed);
		if (r < 0)
		{
			pDS->SetForceAttribute(slot, 0, 0);
			sys_log(0, "[DS_ATTR] RepairDuplicateAttributes vnum=%%u id=%%u slot %%d: repeated type %%d (%%d) emptied - no type left",
				pDS->GetVnum(), pDS->GetID(), slot, oldType, oldValue);
			continue;
		}
		const WORD bType = vec_add[r].apply_type;
		const short sValue = (short)(ceil((float)vec_add[r].apply_value * fWeight - 0.01f));
		pDS->SetForceAttribute(slot, bType, sValue);
		vecUsed.push_back(bType);
		sys_log(0, "[DS_ATTR] RepairDuplicateAttributes vnum=%%u id=%%u slot %%d: repeated type %%d (%%d) -> type %%d (%%d)",
			pDS->GetVnum(), pDS->GetID(), slot, oldType, oldValue, bType, sValue);
	}
	return true;
}
''' % M

EDITS = [
    E('DragonSoul.cpp', 'distinct set', OLD_DISTINCT, NEW_DISTINCT),
    E('DragonSoul.cpp', 'clear', OLD_PUT_BASIC, NEW_PUT_BASIC),
    E('DragonSoul.cpp', 'guard', OLD_PUT_ADD, NEW_PUT_ADD),
    E('DragonSoul.cpp', 'repair', OLD_REPAIR_END, NEW_REPAIR_END),
    E('DragonSoul.h', 'repair declare',
      '\tbool\tRepairZeroAttributeItem(LPITEM pItem);\n',
      '\tbool\tRepairZeroAttributeItem(LPITEM pItem);\n'
      '\tbool\tRepairDuplicateAttributes(LPITEM pDS);\t// %s (repair declare)\n' % M),
    # the login: before the stone is worn (no bonus applied yet), saved once the load lets it save
    E('input_db.cpp', 'repair load',
      '\t\titem->SetSkipSave(true);\n\t\titem->SetSockets(p->alSockets);\n\t\titem->SetAttributes(p->aAttr);\n',
      '\t\titem->SetSkipSave(true);\n\t\titem->SetSockets(p->alSockets);\n\t\titem->SetAttributes(p->aAttr);\n'
      '\t\t// %s (repair load): a Dragon Stone with a repeated additional bonus gets it rerolled, before it is\n'
      '\t\t// worn (DragonSoul.cpp RepairDuplicateAttributes); switch: event flag m2_ds_dup_repair_off 1\n'
      '\t\tconst bool bMt2009DsDupFixed = item->IsDragonSoul()\n'
      '\t\t\t\t&& 0 == quest::CQuestManager::instance().GetEventFlag("m2_ds_dup_repair_off")\n'
      '\t\t\t\t&& DSManager::instance().RepairDuplicateAttributes(item);\n' % M),
    E('input_db.cpp', 'repair save',
      '\t\titem->SetSkipSave(false);\n\t}\n\n\titertype(v) it = v.begin();\n',
      '\t\titem->SetSkipSave(false);\n'
      '\t\tif (bMt2009DsDupFixed)\n\t\t\titem->Save();\t// %s (repair save)\n'
      '\t}\n\n\titertype(v) it = v.begin();\n' % M),
    E('char.cpp', 'repair safebox',
      '\t\t\titem->SetSkipSave(true);\n\t\t\titem->SetSockets(pItems->alSockets);\n\t\t\titem->SetAttributes(pItems->aAttr);\n'
      '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\t\t\titem->SetTransmutation(pItems->dwTransmutation); // MT2009_PLUS_CHANGE_LOOK_V1 (load safebox)\n',
      '\t\t\titem->SetSkipSave(true);\n\t\t\titem->SetSockets(pItems->alSockets);\n\t\t\titem->SetAttributes(pItems->aAttr);\n'
      '\t\t\t// %s (repair safebox): as the login\'s (input_db.cpp ItemLoad)\n'
      '\t\t\tconst bool bMt2009DsDupFixed = item->IsDragonSoul()\n'
      '\t\t\t\t\t&& 0 == quest::CQuestManager::instance().GetEventFlag("m2_ds_dup_repair_off")\n'
      '\t\t\t\t\t&& DSManager::instance().RepairDuplicateAttributes(item);\n'
      '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\t\t\titem->SetTransmutation(pItems->dwTransmutation); // MT2009_PLUS_CHANGE_LOOK_V1 (load safebox)\n' % M),
    E('char.cpp', 'repair safebox save',
      '\t\t\t\titem->OnAfterCreatedItem(); // @fixme306\n\t\t\t\titem->SetSkipSave(false);\n',
      '\t\t\t\titem->OnAfterCreatedItem(); // @fixme306\n\t\t\t\titem->SetSkipSave(false);\n'
      '\t\t\t\tif (bMt2009DsDupFixed)\n\t\t\t\t\titem->Save();\t// %s (repair safebox save)\n' % M),
]


def main():
    json.dump(EDITS, open(os.path.join(HERE, 'edits.json'), 'w'), indent=1)
    print('edits.json: %d edit(s)' % len(EDITS))
    if len(sys.argv) > 1:
        bad = 0
        for e in EDITS:
            text = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1').replace('\r\n', '\n')
            if e['marker'] in text:
                print('  %s: already applied' % e['marker'])
            elif text.count(e['old']) != 1:
                print('  %s: code found %d time(s) in %s' % (e['marker'], text.count(e['old']), e['file']))
                bad += 1
            else:
                print('  %s: ok' % e['marker'])
        sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
