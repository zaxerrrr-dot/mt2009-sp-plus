# MT2009_PLUS_RIPOSTY_V1: Riposty i Dopalacze - the passive 7th and 8th skills (server-patches/riposty/README.md).
# The client's part: every riposte (221-228) and boost (236-243) has a hidden slot of its own (slot = vnum, RegisterSlots
# from playersettingmodule.RegisterSkill), where the exe's RecvSkillLevelNew puts its level; the skill window shows the
# riposte a character knows in the active page's place 8 (slot 8, its grades in 28 / 48 - beside the 9th skill) and the
# boost in the support grid's last cell (112) - uicharacter asks SourceSlot() which hidden slot a shown place reads.
# The exe empties place 8 on every skill packet (SetSkill(8, 0)) - nothing of ours is there, so nothing to restore.
# The tooltip (uitooltip.SkillToolTip.SetSkillNew): the level (1-19, M1-M10, G1-G10, P), the wiki's per cent now and at
# the next level (GF's power table: riposte 24*k, boost 16*k - the server's riposty::Percent), how it grows.
import player

RIPOSTE_FIRST, RIPOSTE_LAST = 221, 228
BOOST_FIRST, BOOST_LAST = 236, 243
RIPOSTE_PLACE = 8	# the active page's place 8 (Skill_Active_Slot 8/28/48)
BOOST_PLACE = 112	# Skill_ETC_Slot's last cell
MAX_LEVEL = 40

# GF's skill power of a level 0-40 (the server's riposty.cpp s_aiPower)
POWER = (
	0,
	5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40,
	50, 52, 54, 56, 58, 60, 63, 66, 69, 72,
	82, 85, 88, 91, 94, 98, 102, 106, 110, 115,
	125,
)

# the attack skill of each (the vnums' order) and the class / path whose boost it is
SKILL_NAMES = ("Wir Miecza", "Zasadzka", "Uderzenie Palcem", "Strzelaj\xb9cy Smok", "Duchowe Uderzenie",
	"Ognista Strza\xb3a", "Mroczne Uderzenie", "Przywo\xb3anie B\xb3yskawicy")
SKILL_FROM = ("Wiru Miecza", "Zasadzki", "Uderzenia Palcem", "Strzelaj\xb9cego Smoka", "Duchowego Uderzenia",
	"Ognistej Strza\xb3y", "Mrocznego Uderzenia", "Przywo\xb3ania B\xb3yskawicy")
BOOST_CLASS = ("Wojownik (Body)", "Ninja (Dagger)", "Sura (Bro\xf1)", "Szaman (Smok)", "Wojownik (Mental)",
	"Ninja (\xa3uk)", "Sura (Czarna Magia)", "Szaman (Leczenie)")

TEXT_LEVEL = "Poziom umiej\xeatno\x9cci: %s"
TEXT_NEXT = "Nast\xeapny poziom: %s"
TEXT_RIPOSTE = "Obra\xbfenia od %s -%s%%"
TEXT_BOOST = "Obra\xbfenia %s +%s%%"
TEXT_TOP = "Najwy\xbfszy poziom."
TEXT_ONE = "Mo\xbfna zna\xe6 tylko jedn\xb9 ripost\xea."
TEXT_CLASS = "Dopalacz klasy: %s."
TEXT_GROW_1 = "Do M1: punkty umiej\xeatno\x9cci lub ksi\xeagi (bez gwarancji)."
TEXT_GROW_M = "Od M1 do G1: ksi\xeagi."
TEXT_GROW_G = "Od G1 do P: Kamie\xf1 Duchowy+."
TEXT_RESET = "Zw\xf3j Zmiany Treningu usuwa ripost\xea i dopalacz."


def IsRiposte(skillIndex):
	return RIPOSTE_FIRST <= skillIndex <= RIPOSTE_LAST


def IsBoost(skillIndex):
	return BOOST_FIRST <= skillIndex <= BOOST_LAST


def IsPassive(skillIndex):
	return IsRiposte(skillIndex) or IsBoost(skillIndex)


def RegisterSlots():
	for v in range(RIPOSTE_FIRST, RIPOSTE_LAST + 1) + range(BOOST_FIRST, BOOST_LAST + 1):
		player.SetSkill(v, v)


def _Known(first, last):
	for v in xrange(first, last + 1):
		try:
			if player.GetSkillGrade(v) > 0 or player.GetSkillLevel(v) > 0:
				return v
		except:
			return 0
	return 0


def SourceSlot(slotIndex):
	# the hidden slot a shown place reads (place 8: the known riposte, 112: the known boost); the place itself if none
	if slotIndex == RIPOSTE_PLACE:
		return _Known(RIPOSTE_FIRST, RIPOSTE_LAST) or slotIndex
	if slotIndex == BOOST_PLACE:
		return _Known(BOOST_FIRST, BOOST_LAST) or slotIndex
	return slotIndex


def RealLevel(grade, level):
	# player.GetSkillLevel of a slot counts within the grade (SetSkillLevel_ in the exe): M1 = grade 1 level 1
	if grade == 1:
		return 19 + level
	if grade == 2:
		return 29 + level
	if grade >= 3:
		return MAX_LEVEL
	return max(0, min(level, MAX_LEVEL))


def LevelName(level):
	if level >= 40:
		return "P"
	if level >= 30:
		return "G%d" % (level - 29)
	if level >= 20:
		return "M%d" % (level - 19)
	return str(level)


def Percent(skillIndex, level):
	k = POWER[max(0, min(level, MAX_LEVEL))] / 100.0
	if IsBoost(skillIndex):
		return 16.0 * k
	return 24.0 * k


def PercentText(skillIndex, level):
	return ("%.1f" % Percent(skillIndex, level)).replace(".0", "").replace(".", ",")


def _EffectLine(skillIndex, level):
	if IsBoost(skillIndex):
		return TEXT_BOOST % (SKILL_FROM[skillIndex - BOOST_FIRST], PercentText(skillIndex, level))
	return TEXT_RIPOSTE % (SKILL_FROM[skillIndex - RIPOSTE_FIRST], PercentText(skillIndex, level))


def AppendToolTip(tip, skillIndex, skillGrade, skillLevel):
	if tip.SKILL_TOOL_TIP_WIDTH != tip.toolTipWidth:
		tip.toolTipWidth = tip.SKILL_TOOL_TIP_WIDTH
		tip.ResizeToolTip()

	tip.AppendDefaultData(skillIndex)

	level = RealLevel(skillGrade, skillLevel)
	tip.AppendSpace(5)
	if IsBoost(skillIndex):
		tip.AppendTextLine(TEXT_CLASS % BOOST_CLASS[skillIndex - BOOST_FIRST], tip.CONDITION_COLOR)
	else:
		tip.AppendTextLine(TEXT_ONE, tip.CONDITION_COLOR)

	tip.AppendSpace(5)
	tip.AppendTextLine(TEXT_LEVEL % LevelName(level), tip.NORMAL_COLOR)
	if level > 0:
		tip.AppendTextLine(_EffectLine(skillIndex, level), tip.POSITIVE_COLOR)

	if level >= MAX_LEVEL:
		tip.AppendTextLine(TEXT_TOP, tip.NORMAL_COLOR)
	else:
		tip.AppendSpace(5)
		tip.AppendTextLine(TEXT_NEXT % LevelName(level + 1), tip.DISABLE_COLOR)
		tip.AppendTextLine(_EffectLine(skillIndex, level + 1), tip.DISABLE_COLOR)

	tip.AppendSpace(5)
	if level < 20:
		tip.AppendTextLine(TEXT_GROW_1, tip.CONDITION_COLOR)
	elif level < 30:
		tip.AppendTextLine(TEXT_GROW_M, tip.CONDITION_COLOR)
	elif level < MAX_LEVEL:
		tip.AppendTextLine(TEXT_GROW_G, tip.CONDITION_COLOR)
	tip.AppendTextLine(TEXT_RESET, tip.DISABLE_COLOR)
