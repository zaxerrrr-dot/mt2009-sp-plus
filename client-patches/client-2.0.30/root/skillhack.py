# MT2009_PLUS_SKILL_HACK_V1: the skills of the other specialisation (server-patches/skillhack/README.md).
# The server says "SKILL2 1|0" at every login and when a GM / the panel switches it (game.py -> SetState). On, a
# character with a chosen path has its class's other path in the skill slots 61-66 (places 1-6 of the skill window's
# second tab) and the other 9th skill in 67 (place 9; the Warrior's Trzesienie 176 is one skill for both paths and
# stays in slot 7). Off (or an older server that never says it): those slots are emptied - the skills sleep.
# Exe: nothing - the skill slots go to 265 (SKILL_MAX_NUM), the vnum -> slot dictionary takes the last SetSkill, the
# quick slot keeps the slot number, every race has both paths' motions (they draw other players' characters).
import player
import net
import chr

SLOT_BASE = 60		# place n (1-6) of the second tab -> skill slot 60 + n
SLOT_FIRST = 61
SLOT_LAST = 67
NINTH_SLOT = 67		# the other path's 9th skill
NINTH_PLACE = 9		# its place (as riposty.NINTH_PLACE on the main tab)
EMPTY_SOURCE = 8	# a skill slot that is always empty (riposty.EMPTY_SOURCE)

JOB_WARRIOR = 0
JOB_ASSASSIN = 1
JOB_SURA = 2
JOB_SHAMAN = 3

# The paths' six places and their 9th skill, as playersettingmodule.SKILL_INDEX_DICT (0 = an empty place).
PATHS = {
	JOB_WARRIOR: {1: ((1, 2, 3, 4, 5, 0), 176), 2: ((16, 17, 18, 19, 20, 0), 176)},
	JOB_ASSASSIN: {1: ((31, 32, 33, 34, 35, 0), 177), 2: ((46, 47, 48, 49, 50, 0), 178)},
	JOB_SURA: {1: ((61, 62, 63, 64, 65, 66), 179), 2: ((76, 77, 78, 79, 80, 81), 180)},
	JOB_SHAMAN: {1: ((91, 92, 93, 94, 95, 96), 181), 2: ((106, 107, 108, 109, 110, 111), 182)},
}

STATE = {"on": 0}


def SetState(on):
	try:
		STATE["on"] = 1 if int(on) else 0
	except:
		STATE["on"] = 0


def IsOn():
	return STATE["on"] != 0


def MainGroup():
	try:
		return net.GetMainActorSkillGroup()
	except:
		return 0


def OtherGroup():
	group = MainGroup()
	if group in (1, 2):
		return 3 - group
	return 0


def _Job():
	try:
		return chr.RaceToJob(net.GetMainActorRace())
	except:
		return -1


def Applies():
	"""The second tab is there: switched on, a chosen path, one of the four classes."""
	return IsOn() and OtherGroup() != 0 and PATHS.has_key(_Job())


def OtherSkills():
	"""(the other path's six places, its 9th skill or 0) - ((), 0) without the second tab."""
	if not Applies():
		return ((), 0)
	job = _Job()
	group = MainGroup()
	skills, ninth = PATHS[job][3 - group]
	if ninth == PATHS[job][group][1]:
		ninth = 0
	return (skills, ninth)


def OtherGroupName(nameDict):
	"""The other path's own name from the window's SKILL_GROUP_NAME_DICT[job]."""
	return nameDict.get(OtherGroup(), "")


def RegisterSlots():
	# Called by playersettingmodule.RegisterSkill (and on the server's SKILL2) after the main path's registration.
	skills, ninth = OtherSkills()
	for i in xrange(6):
		slot = SLOT_FIRST + i
		vnum = 0
		if i < len(skills):
			vnum = skills[i]
		if vnum:
			player.SetSkill(slot, vnum)
		elif player.GetSkillIndex(slot):
			player.SetSkill(slot, 0)
	if ninth:
		player.SetSkill(NINTH_SLOT, ninth)
	elif player.GetSkillIndex(NINTH_SLOT):
		player.SetSkill(NINTH_SLOT, 0)


def IsForeignSlot(srcSlotIndex):
	return SLOT_FIRST <= srcSlotIndex <= SLOT_LAST


def SourceSlot(place):
	# The skill slot a place of the second tab reads: 1-6 -> 61-66, 9 -> 67, 7 / 8 (riposte, boost: the main path's
	# only) -> always empty.
	if 1 <= place <= 6:
		return SLOT_BASE + place
	if place == NINTH_PLACE:
		return NINTH_SLOT
	return EMPTY_SOURCE


def PlaceOfSource(srcSlotIndex):
	# The way back: 0 - not a slot of the second tab.
	if SLOT_FIRST <= srcSlotIndex <= SLOT_FIRST + 5:
		return srcSlotIndex - SLOT_BASE
	if srcSlotIndex == NINTH_SLOT:
		return NINTH_PLACE
	return 0
