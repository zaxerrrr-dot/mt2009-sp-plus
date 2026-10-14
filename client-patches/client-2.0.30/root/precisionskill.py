# MT2009_PLUS_PRECISION_SKILL_V1: the passive skill Precyzja (skill 246, server-patches/precyzja/README.md) - its place
# in the skill window's support tab (playersettingmodule SKILL_INDEX_DICT "SUPPORT", slot 111) and its tooltip
# (uitooltip.SkillToolTip.SetSkillNew): the level (1-19, M1-M10, G1-G10, P), the bonus now and at the next level -
# the pl-wiki's table, the same as the server's (playerbot_champion.cpp s_aPrecisionBonus) - and how it grows
# (Ksiega Precyzji 50325, from Champion level 1). The bonus itself comes with POINT_HIT_PCT (sungmastate.py).
import player

SKILL_INDEX = 246
MAX_LEVEL = 40

# level 0-40: the bonus to Precyzja (pl-wiki "Precyzja", "Wartosc bonusu")
BONUS = (
	0,
	0, 0, 1, 1, 1, 2, 2, 2, 3, 3,
	4, 4, 4, 4, 5, 5, 5, 6, 6,
	8, 8, 8, 9, 9, 9, 10, 10, 11, 11,
	13, 13, 14, 14, 15, 16, 16, 17, 18, 18,
	20,
)

TEXT_LEVEL = "Poziom umiej\xeatno\x9cci: %s"
TEXT_NEXT = "Nast\xeapny poziom: %s"
TEXT_BONUS = "Precyzja +%d"
TEXT_TOP = "Najwy\xbfszy poziom."
TEXT_BOOK = "Rozwijana Ksi\xeag\xb9 Precyzji (od 0 do P)."
TEXT_CHAMPION = "Wymaga 1. Poziomu Czempiona."


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


def Bonus(level):
	return BONUS[max(0, min(level, MAX_LEVEL))]


def _IsChampion():
	try:
		return player.GetStatus(player.CONQUEROR_LEVEL) >= 1
	except:
		return True


def AppendToolTip(tip, skillIndex, skillGrade, skillLevel):
	if tip.SKILL_TOOL_TIP_WIDTH != tip.toolTipWidth:
		tip.toolTipWidth = tip.SKILL_TOOL_TIP_WIDTH
		tip.ResizeToolTip()

	tip.AppendDefaultData(skillIndex)

	level = RealLevel(skillGrade, skillLevel)
	tip.AppendSpace(5)
	tip.AppendTextLine(TEXT_LEVEL % LevelName(level), tip.NORMAL_COLOR)
	if level > 0:
		tip.AppendTextLine(TEXT_BONUS % Bonus(level), tip.POSITIVE_COLOR)

	if level >= MAX_LEVEL:
		tip.AppendTextLine(TEXT_TOP, tip.NORMAL_COLOR)
		return

	tip.AppendSpace(5)
	tip.AppendTextLine(TEXT_NEXT % LevelName(level + 1), tip.DISABLE_COLOR)
	tip.AppendTextLine(TEXT_BONUS % Bonus(level + 1), tip.DISABLE_COLOR)

	tip.AppendSpace(5)
	tip.AppendTextLine(TEXT_BOOK, tip.CONDITION_COLOR)
	if not _IsChampion():
		tip.AppendTextLine(TEXT_CHAMPION, tip.NEGATIVE_COLOR)
