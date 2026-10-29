# MT2009_PLUS_QUICKSLOT_IMPROVE_V1 (the ENABLE_QUICKSLOT_IMPROVE package): the expanded quick slot bar's state per
# character - whether the bar is expanded and the active page - kept in quickslot/<name>.cfg ("<expanded> <page>").
# The package kept "expanded" in the exe (player.SetQuickSlotExpanded) and wrote the page with app.AtomicWriteFile;
# here both live in this module and in a plain file, so root needs nothing from the exe for them.
import os
import __builtin__

PAGE_COUNT = 4
CONFIG_DIR = 'quickslot'

_open = getattr(__builtin__, 'old_open', open)
_name = ''
_page = 0
_expanded = False


def _Path():
	safe = ''.join([c for c in _name if c.isalnum() or c in '_-'])
	if not safe:
		return ''
	return os.path.join(CONFIG_DIR, '%s.cfg' % safe)


def Activate(characterName):
	"""the character entering the game: its saved state (or a single bar, page 1)"""
	global _name, _page, _expanded
	_name = str(characterName or '')
	_page = 0
	_expanded = False
	path = _Path()
	if not path:
		return
	try:
		handle = _open(path, 'r')
		try:
			parts = handle.read(32).split()
		finally:
			handle.close()
		if len(parts) == 2:
			_expanded = parts[0] == '1'
			page = int(parts[1])
			if 0 <= page < PAGE_COUNT:
				_page = page
	except (IOError, OSError, ValueError):
		pass


def _Save():
	path = _Path()
	if not path:
		return
	try:
		if not os.path.isdir(CONFIG_DIR):
			os.makedirs(CONFIG_DIR)
		handle = _open(path, 'w')
		try:
			handle.write('%d %d\n' % (1 if _expanded else 0, _page))
		finally:
			handle.close()
	except (IOError, OSError):
		pass


def IsExpanded():
	return _expanded


def SetExpanded(expanded):
	global _expanded
	expanded = bool(expanded)
	if _expanded != expanded:
		_expanded = expanded
		_Save()


def GetPage():
	return _page


def SetPage(page):
	global _page
	if 0 <= page < PAGE_COUNT and _page != page:
		_page = page
		_Save()
