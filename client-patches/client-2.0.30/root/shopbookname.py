# MT2009_PLUS_SHOP_BOOK_NOTIFICATION_V1 (2026-10-15, Autor: Vekirion), client side: the skill of a sold /
# offered / auctioned skill book in the offline shop's history (offlineshophistory.py)
# and notifications (uiikashop.py). The server keeps it in the notification's "who"
# as "#S<skill>" (db, ClientManagerIkarusShop.cpp, Mt2009PlusBookWho).
# Python 2.7 as the client has it.
BOOK_WHO_MARK = "#S"


def SplitBookWho(who):
	"""'<name>#S<skill>' -> ('<name>', skill); anything else -> (who, 0)."""
	try:
		who = str(who)
	except Exception:
		return who, 0
	pos = who.rfind(BOOK_WHO_MARK)
	if pos < 0:
		return who, 0
	try:
		skillVnum = int(who[pos + len(BOOK_WHO_MARK):])
	except ValueError:
		return who, 0
	return who[:pos], skillVnum


def BookItemName(itemName, skillVnum):
	"""'<skill> - <book>' for a known skill, otherwise the item's own name."""
	if skillVnum <= 0:
		return itemName
	try:
		import uiauctionhouse
		if skillVnum not in uiauctionhouse.SKILL_IDS:
			return itemName		# skill.GetSkillName of an unknown number breaks the interpreter
	except Exception:
		return itemName
	try:
		import skill
		skillName = skill.GetSkillName(skillVnum)
	except Exception:
		skillName = ""
	if skillName:
		return "%s - %s" % (skillName, itemName)
	return itemName


def NotificationItemName(what, who):
	"""(item name, who without the marker) of a shop notification."""
	who, skillVnum = SplitBookWho(who)
	if not what:
		return "", who
	try:
		import item
		item.SelectItem(what)
		itemName = item.GetItemName()
	except Exception:
		return "", who
	return BookItemName(itemName, skillVnum), who
