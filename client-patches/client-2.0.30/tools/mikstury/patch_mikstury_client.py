# -*- coding: utf-8 -*-
# MT2009_PLUS_BIOLOG_ELIKSIR_V1 / MT2009_PLUS_MIKSTURY_WYCOFANE_V1 (the owner, 3 November 2026) - the client's item
# descriptions (locale/pl/itemdesc.txt of the "dbdata" pack) of the Biologist's / skill books' helpers as the server now
# has them (linux-port/docker/game/quest/m2_mikstury.lua, quest eliksir_poszukiwacza; keep the texts equal to
# linux-port/docker/itemshop/app/shop3/include/db/client_itemdesc.json):
#   71035 / 76020 / 39023  Eliksir Poszukiwacza - the pl-wiki's "Opis" and what it does here: the next research hand-in
#                          at Chaegirab / Seon-Pyeong at 90% instead of 60%, not the Yohara missions
#   51782 / 51783 / 51785  Mikstura Geniuszu / Determinacji / Szybkiej Analizy - withdrawn (refused when used)
# The items themselves (item_proto, item_list, icons) are the client's own and stay as they are.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/mikstury/patch_mikstury_client.py <itemdesc.txt> [<out dir>]
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402

ELIXIR = (u'Poprawia jakość przedmiotów przeznaczonych do badań, co powoduje zwiększenie szansy na ich przyjęcie. '
	u'Następny przedmiot oddany do badań Biologowi Chaegirabowi lub Seonowi-Pyeongowi ma 90% szans na przyjęcie '
	u'zamiast 60%. Nie dotyczy misji na Yohara.')
WITHDRAWN = u'Mikstura wycofana - nie działa. Można ją sprzedać w sklepie NPC.'
ROWS = (
	(71035, u'Eliksir Poszukiwacza', ELIXIR),
	(76020, u'Eliksir Poszukiwacza', ELIXIR + u' Przedmiot ten jest niezdatny do handlu.'),
	(39023, u'Eliksir Poszukiwacza', ELIXIR + u' Przedmiot ten jest zdatny do handlu.'),
	(51782, u'Mikstura Geniuszu', WITHDRAWN),
	(51783, u'Mikstura Determinacji', WITHDRAWN),
	(51785, u'Mikstura Szybkiej Analizy', WITHDRAWN),
)


def desc_rows():
	return [u'%d\t%s\t%s' % r for r in ROWS]


def main():
	if len(sys.argv) not in (2, 3):
		raise SystemExit('usage: patch_mikstury_client.py <itemdesc.txt> [<out dir>]')
	desc_path = sys.argv[1]
	out_dir = sys.argv[2] if len(sys.argv) == 3 else None
	with open(desc_path, 'rb') as f:
		data, changed = base.set_rows(f.read(), desc_rows())
	target = os.path.join(out_dir, os.path.basename(desc_path)) if out_dir else desc_path
	if out_dir or changed:
		if out_dir and not os.path.isdir(out_dir):
			os.makedirs(out_dir)
		with open(target, 'wb') as f:
			f.write(data)
	print('%s: %d change(s)%s' % (os.path.basename(desc_path), changed, '' if target == desc_path else ' -> ' + target))


# the pack builder's jobs (build_mikstury_packs.py): an entry's name -> fn(bytes) -> (new bytes, changes)
JOBS = {'locale/pl/itemdesc.txt': lambda b: base.set_rows(b, desc_rows())}


if __name__ == '__main__':
	main()
