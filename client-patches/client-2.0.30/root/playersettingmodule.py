import chr
import chrmgr
import skill
import net
import item
import player
import effect
import constInfo
import localeInfo
import app

import appPlayerSettingsModule
import riposty # MT2009_PLUS_RIPOSTY_V1

JOB_WARRIOR = 0
JOB_ASSASSIN = 1
JOB_SURA = 2
JOB_SHAMAN = 3

RACE_WARRIOR_M = 0
RACE_ASSASSIN_W = 1
RACE_SURA_M = 2
RACE_SHAMAN_W = 3
RACE_WARRIOR_W = 4
RACE_ASSASSIN_M = 5
RACE_SURA_W = 6
RACE_SHAMAN_M = 7

PASSIVE_GUILD_SKILL_INDEX_LIST = (151,)
ACTIVE_GUILD_SKILL_INDEX_LIST = (152, 153, 154, 155, 156, 157,)

NEW_678TH_SKILL_ENABLE = 0
SKILL_INDEX_DICT = []


def DefineSkillIndexDict():
	global SKILL_INDEX_DICT
	SKILL_INDEX_DICT = {
		# MT2009_PLUS_SKILL9_V1: the 9th skill of Yohara (176-182) in the 7th place (slot 7): Trzesienie, Swiatlo Gwiazd /
		# Strzal Wichury, Piekielny Cios / Fala Smierci, Meteor / Tarcza Eteru. MT2009_PLUS_SKILL_WINDOW_V1: the skill page
		# shows it in the left column's 5th row (place 9, grades 29/49 - riposty.SourceSlot), as the global client does.
		# MT2009_PLUS_PRECISION_SKILL_V1: "SUPPORT" 11th = slot 111 - the passive skill Precyzja (246, precisionskill.py).
		JOB_WARRIOR: {
			1: (1, 2, 3, 4, 5, 0, 176, 0, 137, 0, 138, 0, 139, 0,),
			2: (16, 17, 18, 19, 20, 0, 176, 0, 137, 0, 138, 0, 139, 0,),
			"SUPPORT": (122, 123, 121, 124, 132, 129, 0, 0, 130, 131, 246,),
		},
		JOB_ASSASSIN: {
			1: (31, 32, 33, 34, 35, 0, 177, 0, 137, 0, 138, 0, 139, 0, 140,),
			2: (46, 47, 48, 49, 50, 0, 178, 0, 137, 0, 138, 0, 139, 0, 140,),
			"SUPPORT": (122, 123, 121, 124, 132, 129, 0, 0, 130, 131, 246,),
		},
		JOB_SURA: {
			1: (61, 62, 63, 64, 65, 66, 179, 0, 137, 0, 138, 0, 139, 0,),
			2: (76, 77, 78, 79, 80, 81, 180, 0, 137, 0, 138, 0, 139, 0,),
			"SUPPORT": (122, 123, 121, 124, 132, 129, 0, 0, 130, 131, 246,),
		},
		JOB_SHAMAN: {
			1: (91, 92, 93, 94, 95, 96, 181, 0, 137, 0, 138, 0, 139, 0,),
			2: (106, 107, 108, 109, 110, 111, 182, 0, 137, 0, 138, 0, 139, 0,),
			"SUPPORT": (122, 123, 121, 124, 132, 129, 0, 0, 130, 131, 246,),
		},
	}
	# MT2009_PLUS_ADDEQ_V1: "SUPPORT" 12th = slot 112 - Zmiana strony ekwipunku (200, uiaddeq.py), with the exe that
	# sends it (app.ENABLE_MT2009_ADDEQ)
	if __import__("uiaddeq").IsSkillSupported():
		for job in SKILL_INDEX_DICT.keys():
			SKILL_INDEX_DICT[job]["SUPPORT"] = SKILL_INDEX_DICT[job]["SUPPORT"] + (200,)


def RegisterSkill(race, group, empire=0):
	DefineSkillIndexDict()

	job = chr.RaceToJob(race)

	# MT2009_PLUS_RIPOSTY_V1: every riposte / boost has a hidden slot (slot = vnum) where its level arrives (riposty.py)
	riposty.RegisterSlots()
	# MT2009_PLUS_BUFFI_V2: the buffi's skills 164-167 too - slot = vnum (uibuffi.py: its window and tooltip)
	__import__("uibuffi").RegisterSlots()

	## Character Skill
	if SKILL_INDEX_DICT.has_key(job):

		if SKILL_INDEX_DICT[job].has_key(group):

			activeSkillList = SKILL_INDEX_DICT[job][group]

			for i in xrange(len(activeSkillList)):
				skillIndex = activeSkillList[i]

				# MT2009_PLUS_SKILL9_V1: place 7 (index 6) is the 9th skill's; 8 stays empty.
				if (i != 6 and i != 7) or (i == 6 and skillIndex):
					player.SetSkill(i + 1, skillIndex)

			supportSkillList = SKILL_INDEX_DICT[job]["SUPPORT"]

			for i in xrange(len(supportSkillList)):
				player.SetSkill(i + 100 + 1, supportSkillList[i])

	## Language Skill
	if 0 != empire:
		languageSkillList = []
		for i in xrange(3):
			if (i + 1) != empire:
				languageSkillList.append(player.SKILL_INDEX_LANGUAGE1 + i)
		for i in xrange(len(languageSkillList)):
			player.SetSkill(107 + i, languageSkillList[i])

	## Guild Skill
	for i in xrange(len(PASSIVE_GUILD_SKILL_INDEX_LIST)):
		player.SetSkill(200 + i, PASSIVE_GUILD_SKILL_INDEX_LIST[i])

	for i in xrange(len(ACTIVE_GUILD_SKILL_INDEX_LIST)):
		player.SetSkill(210 + i, ACTIVE_GUILD_SKILL_INDEX_LIST[i])


def RestoreNinthSkillSlot():
	# MT2009_PLUS_SKILL9_V1 (fix 3.0 #1/#1b): the exe's RecvSkillLevelNew (every skill packet - a book read, a level up)
	# starts with player.SetSkill(7, 0) and SetSkill(8, 0) (the old 6th/7th skill places 112-119), so place 7 - our 9th
	# skill's - lost its skill index until the skill window re-registered it: the window and the quickslot bar showed it
	# empty. The level itself is kept (SetSkillLevel_ finds 176-182 -> 7 in the slot dict), so putting the index back
	# before the refresh is enough. Called by game.RefreshSkill (the exe's __RefreshSkillWindow) before the window/taskbar.
	try:
		group = net.GetMainActorSkillGroup()
		if not group:
			return
		if not SKILL_INDEX_DICT:
			DefineSkillIndexDict()
		skillList = SKILL_INDEX_DICT.get(chr.RaceToJob(net.GetMainActorRace()), {}).get(group)
		if not skillList or len(skillList) < 7 or not skillList[6]:
			return
		if player.GetSkillIndex(7) != skillList[6]:
			player.SetSkill(7, skillList[6])
	except:
		pass


def RegisterSkillAt(race, group, pos, num):
	DefineSkillIndexDict()

	job = chr.RaceToJob(race)
	tmp = list(SKILL_INDEX_DICT[job][group])
	tmp[pos] = num
	SKILL_INDEX_DICT[job][group] = tuple(tmp)
	player.SetSkill(pos + 1, num)


FACE_IMAGE_DICT = {
	RACE_WARRIOR_M: "d:/ymir work/ui/game/windows/face_warrior.sub",
	RACE_ASSASSIN_W: "d:/ymir work/ui/game/windows/face_assassin.sub",
	RACE_SURA_M: "d:/ymir work/ui/game/windows/face_sura.sub",
	RACE_SHAMAN_W: "d:/ymir work/ui/game/windows/face_shaman.sub",
}


def __InitData():
	appPlayerSettingsModule.InitData()


def __LoadGameSound():
	appPlayerSettingsModule.LoadGameSound()


def __LoadGameEffect():
	appPlayerSettingsModule.LoadGameEffect()


def __LoadGameWarrior():
	appPlayerSettingsModule.LoadGameWarrior()


def __LoadGameAssassin():
	appPlayerSettingsModule.LoadGameAssassin()


def __LoadGameSura():
	appPlayerSettingsModule.LoadGameSura()


def __LoadGameShaman():
	appPlayerSettingsModule.LoadGameShaman()


def __LoadGameSkill():
	appPlayerSettingsModule.LoadGameSkill()


# MT2009_PLUS_MOUNT_NAME_HEIGHT_V1 (Autor: Vekirion): the name over a rider stands at the rider's
# height + 10 + the mount's "base height" (exe, CInstanceBase::GetBaseHeight).
# The exe gives the plain horses (20101-20109, 20029, 20030) 100; any other
# mount gets its race height, and with no race height the exe measures the
# whole model once (wings, tails and effects included) and keeps that - a
# phoenix or a dragon put the name far above the rider. Every mount in
# npclist.txt (MOUNT_VNUM_RANGES) gets its race height here, before the exe
# measures anything; the exe never overwrites a race height once set.
# MOUNT_HEIGHTS sets one mount by its vnum when its class does not fit.
MOUNT_VNUM_RANGES = ((20110, 20125), (20149, 20151), (20201, 20299), (36000, 36999), (40000, 40999))
MOUNT_HEIGHT = 100.0		# as the plain horses
MOUNT_HEIGHT_LARGE = 140.0	# models whose saddle sits higher
MOUNT_LARGE_MODELS = ("mammoth", "dragon", "phoenix", "eagle", "drakkar", "camel", "sphinx",
	"volcano_beast", "cerberos", "dinosaur", "wagon", "ninetail")
MOUNT_HEIGHTS = {}	# vnum: height

def __SetMountHeights(lines):
	if not hasattr(chrmgr, "SetRaceHeight"):
		return
	for line in lines:
		tokens = line.strip().split("\t")
		if len(tokens) < 2:
			continue
		try:
			vnum = int(tokens[0])
		except ValueError:
			continue
		if vnum in MOUNT_HEIGHTS:
			height = MOUNT_HEIGHTS[vnum]
		elif [1 for low, high in MOUNT_VNUM_RANGES if low <= vnum <= high]:
			model = tokens[1].lower()
			if [1 for key in MOUNT_LARGE_MODELS if key in model]:
				height = MOUNT_HEIGHT_LARGE
			else:
				height = MOUNT_HEIGHT
		else:
			continue
		try:
			chrmgr.SetRaceHeight(vnum, float(height))
		except Exception:
			pass


def __LoadGameNPC():
	try:
		lines = open("gamedata/npclist.txt", "r").readlines()
	except IOError:
		import dbg
		dbg.LogBox("LoadLocaleError(%(srcFileName)s)" % locals())
		app.Abort()

	for line in lines:
		tokens = line[:-1].split("\t")
		if len(tokens) == 0 or not tokens[0]:
			continue

		try:
			vnum = int(tokens[0])

		except ValueError:
			import dbg
			dbg.LogBox("LoadGameNPC() - %s - line #%d: %s" % (tokens, lines.index(line), line))
			app.Abort()

		try:
			if vnum:
				chrmgr.RegisterRaceName(vnum, tokens[1].strip())
			else:
				chrmgr.RegisterRaceSrcName(tokens[1].strip(), tokens[2].strip())

		except IndexError:
			import dbg
			dbg.LogBox("LoadGameNPC() - %d, %s - line #%d: %s " % (vnum, tokens, lines.index(line), line))
			app.Abort()

	appPlayerSettingsModule.LoadNpcScale()
	appPlayerSettingsModule.LoadRaceHeight()
	__SetMountHeights(lines)  # MT2009_PLUS_MOUNT_NAME_HEIGHT_V1

def __PreloadGame():
	print "__PreloadGame"
	# playerRaces = [1, 2, 3, 4, 5, 6, 7]
	# for race in playerRaces:
	# 	print "pronto mordo"
	# 	chr.TestCreateInstance(100+race, race)
	# 	chr.DeleteInstance(100)

	# chr.CreateInstance(100)
	# chr.SelectInstance(100)
	# chr.SetRace(vnum)
	# chr.DeleteInstance(100)

# GUILD_BUILDING
def LoadGuildBuildingList(filename):
	import uiGuild
	uiGuild.BUILDING_DATA_LIST = []

	handle = app.OpenTextFile(filename)
	count = app.GetTextFileLineCount(handle)
	for i in xrange(count):
		line = app.GetTextFileLine(handle, i)
		tokens = line.split("\t")

		TOKEN_VNUM = 0
		TOKEN_TYPE = 1
		TOKEN_NAME = 2
		TOKEN_LOCAL_NAME = 3
		NO_USE_TOKEN_SIZE_1 = 4
		NO_USE_TOKEN_SIZE_2 = 5
		NO_USE_TOKEN_SIZE_3 = 6
		NO_USE_TOKEN_SIZE_4 = 7
		TOKEN_X_ROT_LIMIT = 8
		TOKEN_Y_ROT_LIMIT = 9
		TOKEN_Z_ROT_LIMIT = 10
		TOKEN_PRICE = 11
		TOKEN_MATERIAL = 12
		TOKEN_NPC = 13
		TOKEN_GROUP = 14
		TOKEN_DEPEND_GROUP = 15
		TOKEN_ENABLE_FLAG = 16
		LIMIT_TOKEN_COUNT = 17

		if not tokens[TOKEN_VNUM].isdigit():
			continue

		if len(tokens) < LIMIT_TOKEN_COUNT:
			import dbg
			dbg.TraceError("Strange token count [%d/%d] [%s]" % (len(tokens), LIMIT_TOKEN_COUNT, line))
			continue

		ENABLE_FLAG_TYPE_NOT_USE = False
		ENABLE_FLAG_TYPE_USE = True
		ENABLE_FLAG_TYPE_USE_BUT_HIDE = 2

		if ENABLE_FLAG_TYPE_NOT_USE == int(tokens[TOKEN_ENABLE_FLAG]):
			continue

		vnum = int(tokens[TOKEN_VNUM])
		type = tokens[TOKEN_TYPE]
		name = tokens[TOKEN_NAME]
		localName = tokens[TOKEN_LOCAL_NAME]
		xRotLimit = int(tokens[TOKEN_X_ROT_LIMIT])
		yRotLimit = int(tokens[TOKEN_Y_ROT_LIMIT])
		zRotLimit = int(tokens[TOKEN_Z_ROT_LIMIT])
		price = tokens[TOKEN_PRICE]
		material = tokens[TOKEN_MATERIAL]

		folderName = ""
		if "HEADQUARTER" == type:
			folderName = "headquarter"
		elif "FACILITY" == type:
			folderName = "facility"
		elif "OBJECT" == type:
			folderName = "object"
		elif "WALL" == type:
			folderName = "fence"

		materialList = ["0", "0", "0"]
		if material:
			if material[0] == "\"":
				material = material[1:]
			if material[-1] == "\"":
				material = material[:-1]
			for one in material.split("/"):
				data = one.split(",")
				if 2 != len(data):
					continue
				itemID = int(data[0])
				count = data[1]

				if itemID == uiGuild.MATERIAL_STONE_ID:
					materialList[uiGuild.MATERIAL_STONE_INDEX] = count
				elif itemID == uiGuild.MATERIAL_LOG_ID:
					materialList[uiGuild.MATERIAL_LOG_INDEX] = count
				elif itemID == uiGuild.MATERIAL_PLYWOOD_ID:
					materialList[uiGuild.MATERIAL_PLYWOOD_INDEX] = count

		## GuildSymbol
		import chrmgr
		chrmgr.RegisterRaceSrcName(name, folderName)
		chrmgr.RegisterRaceName(vnum, name)

		appendingData = {"VNUM": vnum,
						 "TYPE": type,
						 "NAME": name,
						 "LOCAL_NAME": localName,
						 "X_ROT_LIMIT": xRotLimit,
						 "Y_ROT_LIMIT": yRotLimit,
						 "Z_ROT_LIMIT": zRotLimit,
						 "PRICE": price,
						 "MATERIAL": materialList,
						 "SHOW": True}

		if ENABLE_FLAG_TYPE_USE_BUT_HIDE == int(tokens[TOKEN_ENABLE_FLAG]):
			appendingData["SHOW"] = False

		uiGuild.BUILDING_DATA_LIST.append(appendingData)

	app.CloseTextFile(handle)


# END_OF_GUILD_BUILDING

loadGameDataDict = {
	"INIT": __InitData,
	"SOUND": __LoadGameSound,
	"EFFECT": __LoadGameEffect,
	"WARRIOR": __LoadGameWarrior,
	"ASSASSIN": __LoadGameAssassin,
	"SURA": __LoadGameSura,
	"SHAMAN": __LoadGameShaman,
	"SKILL": __LoadGameSkill,
	"NPC": __LoadGameNPC,
	"PRELOAD": __PreloadGame,
}


def LoadGameData(name):
	global loadGameDataDict

	load = loadGameDataDict.get(name, 0)
	if load:
		loadGameDataDict[name] = 0
		try:
			load()
		except:
			print name
			import exception
			exception.Abort("LoadGameData")
			raise
