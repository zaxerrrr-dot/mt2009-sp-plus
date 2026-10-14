# -*- coding: utf-8 -*-
"""MT2009_PLUS_SKILL9_TALENT_V1: where Mikstura Talentu (50527, G1 -> P of the 9th skills) drops - the pl-wiki's
list (Mikstura_Talentu: Metins Swiadomosci / Szacunku / Uwaznosci / Jin, every boss of the New Continent, the
monsters of the 1st level of Swiatynia Wezy, the non-boss monsters of Tajemnicza Instancja, Wawoz Polnocnego Wiatru
and Rozpadlina Dusz). The Yohara drop generators (tools/yohara_items/gen_yitems*.py, tools/yohara_maps3/gen_yitems3.py,
tools/yohara_maps4/gen_ymaps4.py, tools/yohara_dung4/gen_yitems_d4.py) pass their groups through with_talent(): a
group of a monster below that has no 50527 row yet gets one. Percents as the rows the second batch already had (a
"drop" percent P is P/400 a kill at mob_item 100): a boss 3, a Metin 2, a monster 0.02 (1 in 20 000 kills) - nothing
raised for the test server's drop event. The chests (B. Smocza Skrz. lekka / ciezka 70411/70412, Skarb Wezy 70429)
and Wieza Sung Mahi's rewards (wieza_sung_mahi.quest, every fifth floor) have it already; Nagroda Dongan /
Nagroda Swiatyni Wezy (83110/83113, the official mission chains' reward chests) are not in our world.
"""

TALENT = 50527
NAME = 'Mikstura Talentu'
BOSS, METIN, MOB = 3, 2, 0.02

_BOSSES = (6691, 6692, 6698, 6699, 6705, 6706, 6716, 6717,          # Opuszczona Twierdza, Dongan
           6723, 6724, 6730, 6731, 6763, 6764, 6880, 6881,          # Seoganland, Namgan, Przelecz Yilad
           6744, 6756, 6790, 6791, 6870, 6871,                      # Swiatynia Wezy, Glebie, Tajemnicza Instancja
           6775, 6776, 6887, 6888, 6782, 6783, 6894, 6895, 6789, 6797,  # Wawoz, Rozpadlina, Schronienie, Zejscie
           6804, 6805, 6814, 6815, 6819, 6820)                      # Jaskinie Gnolli
_METINS = (8063, 8064, 8065, 8067)                                  # Szacunku, Uwaznosci, Jin, Swiadomosc
_MOBS = (6745, 6746, 6747, 6748, 6749, 6758, 6759, 6760, 6761, 6762,    # 1. poziom Swiatyni Wezy (390)
         6875, 6876, 6877, 6878, 6879,
         6860, 6861, 6862, 6863, 6864, 6865, 6866, 6867, 6868, 6869,    # Tajemnicza Instancja (396)
         6770, 6771, 6772, 6773, 6774, 6882, 6883, 6884, 6885, 6886,    # Wawoz Polnocnego Wiatru (388)
         6777, 6778, 6779, 6780, 6781, 6889, 6890, 6891, 6892, 6893)    # Rozpadlina Dusz (389)

PCT = dict([(v, BOSS) for v in _BOSSES] + [(v, METIN) for v in _METINS] + [(v, MOB) for v in _MOBS])
assert len(PCT) == len(_BOSSES) + len(_METINS) + len(_MOBS)


def with_talent(groups, named=False):
    """(vnum, name, rows) -> the same with (50527, 1, pct[, name]) after the rows of a listed monster without it."""
    out = []
    for v, nm, rows in groups:
        if v in PCT and not any(r[0] == TALENT for r in rows):
            rows = list(rows) + [(TALENT, 1, PCT[v], NAME) if named else (TALENT, 1, PCT[v])]
        out.append((v, nm, rows))
    return out
