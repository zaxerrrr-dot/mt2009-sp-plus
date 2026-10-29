# -*- coding: utf-8 -*-
"""MT2009_PLUS_ITEMSHOP_V3_V6: what happens to each row of the pl-wiki's "Item-Shop" list (wiki/Item-Shop.txt, rows in
the order tools/itemshop3/gen_global_catalog.py parses them - the key is the row number and the wiki's name, checked
on every run). The owner, 24.10.2026: add what the list has at its price (1 SM = 1 of their premium coin, SZ = their
marks), never change what our shop has (a different price goes to the sheet), list what our files lack, replace by
what we have where it is the same thing, skip the special offers (our flash offers stay as they are).

  ADD    the line(s) to add to the second shop: L(vnum, count, price, currency, category[, minutes, suffix]);
         currency 1 = Smocze Monety, 2 = Smocze Znaki; minutes = the duration this line gives (0 = the item's own);
         sub = the wiki item is not in our files, our item named there is the same thing ("Zastąpione")
  HAVE   our shop sells it already (in-game shop indexes): compared, a difference goes to "Różnice u nas";
         sub = under another name / another item of ours
  MISS   not in our files (or the item is there but nothing in the game uses it) -> "Brak w plikach"
  SKIP   not for this shop (special offers, another server's transfer, another currency)
Categories (gen_itemshop3_sql.py CATEGORIES): 2 Wyposażenie, 3 Uszlachetnianie, 4 VIPy, 8 Pety, 9 Mounty,
10 Małżeństwo, 11 Zwoje i księgi, 12 Smocze Znaki, 13 Kupony SM.
"""

D30, D15, D7 = 43200, 21600, 10080	# minutes


def L(vnum, count, price, cur, cat, minutes=0, suffix=''):
	return dict(vnum=vnum, count=count, price=price, cur=cur, cat=cat, minutes=minutes, suffix=suffix)


def ADD(*lines, sub=None, note=''):
	return dict(st='add', lines=list(lines), sub=sub, note=note)


def HAVE(*ours, sub=None, note=''):
	return dict(st='have', ours=list(ours), sub=sub, note=note)


def MISS(note):
	return dict(st='miss', note=note)


def SKIP(note):
	return dict(st='skip', note=note)


NO_MERC = 'System najemników - nie ma go na naszym serwerze.'
NO_HANDLER = 'Przedmiot jest w plikach, ale nic w grze go nie obsługuje (brak misji / kodu użycia).'
PET_GONE = 'Usunięte wcześniej z ItemShopu decyzją właściciela (owner_prices_pets) - nie dodaję ponownie.'

# key: (row, wiki name) - the name is checked, so a changed wiki snapshot fails loudly instead of mismatching.
ROWS = {
	# --- Hity
	(3, 'Szkatuła na Biżuterię'): MISS('Losowy pierścień / amulet / lizak / mikstura - takiej szkatuły nie ma w naszych plikach.'),
	(4, 'Zwój Badacza'): MISS('Reset misji „Badanie Seona-Pyeonga” (92/94) - brak przedmiotu.'),
	(5, 'Zwój Zapomnienia'): MISS('Usuwa czas oczekiwania stajennego - brak przedmiotu.'),
	(6, 'Zdobna Skrzynia z Odłamkiem'): ADD(L(39068, 1, 12, 1, 3)),
	(7, 'Buty Wiatru'): HAVE(1, 5),
	(8, 'Szarfa Władcy (prosta)'): ADD(L(85001, 1, 49, 1, 2), sub=(85001, 'Szarfa Władcy +0'), note='Szarfa 1. stopnia (absorbuje 1% bonusów) - u nas nazwa „Szarfa Władcy +0”.'),
	(9, 'Średni Suplement'): ADD(L(72065, 1, 5, 1, 3)),
	(10, 'Duży Suplement'): ADD(L(72066, 1, 9, 1, 3)),
	(11, 'Silny Suplement'): ADD(L(72067, 1, 18, 1, 3)),
	(12, 'Błogosławieństwo (przedmiot)'): ADD(L(71052, 1, 129, 1, 3), sub=(71052, 'Błogosław. Przedmiotu'), note='Zmiana 6. i 7. bonusu - u nas nazwa skrócona.'),
	(13, 'Kompas Strażnika'): MISS('Kompas do strażników Świątyni Ochao - brak przedmiotu.'),
	(14, 'Magmowa Skrzynka Meley'): MISS('Pakiet Meley (wierzchowiec, Minidall, przepustki) - brak skrzynki.'),
	(15, 'Duża Magmowa Skrzynka Meley'): MISS('Większy pakiet Meley - brak skrzynki.'),
	(16, 'Boska Odżywka'): MISS('Wskrzesza zwierzaka (system zwierzaków poziomowanych) - brak przedmiotu.'),
	(17, 'Zwój Badacza'): MISS('Drugi wpis listy (379 SM) - brak przedmiotu.'),
	(18, 'Power Booster Pack'): MISS('Pakiet (Mroźny Rufus 30 dni + 10 Rad Pustelnika + 30 Zwojów Egzorcyzmu + 50 Eliksirów Poszukiwacza) - brak pakietu.'),
	(19, 'Znak Strażnika'): ADD(L(72328, 1, 69, 1, 11), note='Lista ma dwie ceny: 87 SM (Hity) i 69 SM (Przepustki) - przyjęta 69 SM.'),
	(20, 'Pergamin Sfer'): ADD(L(72329, 1, 29, 1, 11)),
	(21, 'Auto Łowy'): HAVE(6, note='U nas bilet na 8 godzin; na liście 7 dni (49 SM) i 14 dni (95 SM) - innego przedmiotu nie ma.'),
	(22, 'Zaczarowanie Przedmiotu+'): MISS('Zaczarowanie z podglądem nowych bonusów - brak przedmiotu.'),
	(23, 'Zmiana nazwy'): MISS('Zmiana imienia postaci - brak przedmiotu.'),
	(24, 'Klatka Transportowa'): HAVE(40928, sub=(55002, 'Transporter Peta'), note='U nas Transporter Peta (nowy system petów).'),
	(25, 'Szpula Kaszmiru'): MISS('Wygląd sklepu prywatnego (7 dni) - jest tylko Szpula Jedwabiu (dodana z wiersza „Szpula Jedwabiu”).'),
	(26, 'Skrzynia Ksiąg Zwierza'): MISS(PET_GONE + ' Odpowiednik: Skrzynia Ksiąg Peta (55009).'),
	(27, 'Odżywka'): MISS(PET_GONE + ' Odpowiednik: Smakołyk (55032).'),
	(28, 'Karta Resetu'): HAVE(617, sub=(72322, 'Karta Nowego Początku'), note='Cofnięcie misji kart potwora - u nas Karta Nowego Początku.'),
	(29, 'Karta Przetasowania'): HAVE(618, sub=(72323, 'Karta Nowego Układu'), note='Przetasowanie misji kart potwora - u nas Karta Nowego Układu.'),
	(30, 'Pergamin Nazwy Zwierzaka'): HAVE(40924, sub=(55008, 'Zwój Imienia Peta')),
	(31, 'Pierścień Tajemnic'): MISS('Blokuje zdobywanie PD na 15 dni - u nas jest Pierścień Anty-Exp (40002) w Wyposażeniu, inny przedmiot.'),
	(32, 'Średni Kupon Wpłaty'): MISS('Wpłata do gildii (medale męstwa) - brak przedmiotu.'),
	# --- Pakiety
	(33, 'Pakiet Przetrwania na Lodowej Ziemi'): MISS('Pakiet - brak.'),
	(34, 'Skrzynia Woj. M. Ciała (D)'): MISS('Skrzynia klasowa - brak.'),
	(35, 'Skrzynia Woj. M. Ciała (M)'): MISS('Skrzynia klasowa - brak.'),
	(36, 'Skrzynia Woj. M. Ducho. (D)'): MISS('Skrzynia klasowa - brak.'),
	(37, 'Skrzynia Woj. M. Ducho. (M)'): MISS('Skrzynia klasowa - brak.'),
	(38, 'Skrzynia Ninja M. Łuku (D)'): MISS('Skrzynia klasowa - brak.'),
	(39, 'Skrzynia Ninja M. Łuku (M)'): MISS('Skrzynia klasowa - brak.'),
	(40, 'Skrzynia Ninja M. Ostrza (D)'): MISS('Skrzynia klasowa - brak.'),
	(41, 'Skrzynia Ninja M. Ostrza (M)'): MISS('Skrzynia klasowa - brak.'),
	(42, 'Skrzynia Sura Broni (D)'): MISS('Skrzynia klasowa - brak.'),
	(43, 'Skrzynia Sura Broni (M)'): MISS('Skrzynia klasowa - brak.'),
	(44, 'Skrzynia Sura Magii (D)'): MISS('Skrzynia klasowa - brak.'),
	(45, 'Skrzynia Sura Magii (M)'): MISS('Skrzynia klasowa - brak.'),
	(46, 'Skrzynia Szam. M. Smoka (D)'): MISS('Skrzynia klasowa - brak.'),
	(47, 'Skrzynia Szam. M. Smoka (M)'): MISS('Skrzynia klasowa - brak.'),
	(48, 'Skrzynia Szam. M. Lecz. (D)'): MISS('Skrzynia klasowa - brak.'),
	(49, 'Skrzynia Szam. M. Lecz. (M)'): MISS('Skrzynia klasowa - brak.'),
	(50, 'Skrzynia Likanów (D)'): SKIP('Likan - nie ma tej klasy na naszym serwerze.'),
	(51, 'Skrzynia Likanów (M)'): SKIP('Likan - nie ma tej klasy na naszym serwerze.'),
	(52, 'Diamentowe Pudełko'): MISS('Pakiet 4 dopalaczy (30 dni) - brak.'),
	(53, 'Złote Pudełko'): MISS('Pakiet dopalaczy (15 dni) - brak.'),
	(54, 'Srebrne Pudełko'): MISS('Pakiet dopalaczy (3 dni) - brak.'),
	(55, 'Brązowe Pudełko'): MISS('Pakiet dopalaczy (1 dzień) - brak.'),
	(56, 'Ekonomiczna paczka dziesięciu Zwojów Egzorcyzmu'): ADD(L(71001, 10, 166, 1, 11, suffix='(Paczka 10)')),
	(57, 'Wzmocnienie Przedmiotu 3+1'): ADD(L(71085, 4, 299, 1, 11, suffix='(3+1)')),
	(58, 'Zaczarowanie Przedmiotu 3+1 Pakiet Oszczędny'): HAVE(608),
	(59, 'Pakiet Zwój Błogosławieństwa 2+1'): ADD(L(25041, 3, 720, 2, 12, suffix='(2+1)'), note='Lista: 1440 SZ (Pakiety) i 720 SZ (Przedmioty za Znaki) - przyjęte 720 SZ (wiersz „Pakiet Zwój Błogosławieństwa 2+1” niżej).'),
	(60, 'Pakiet Startowy Mały'): MISS('Pakiet - brak.'),
	(61, 'Pakiet Startowy Średni'): MISS('Pakiet - brak.'),
	(62, 'Pakiet Startowy Duży'): MISS('Pakiet - brak.'),
	(63, 'Pakiet Biologa'): MISS('Pakiet - brak.'),
	(64, 'Pudełko Premium'): MISS('Pakiet - brak.'),
	(65, 'Pakiet Przetrwania na Lodowej Ziemi'): MISS('Pakiet - brak.'),
	(66, 'Duża Magmowa Skrzynka Meley'): MISS('Pakiet - brak.'),
	(67, 'Magmowa Skrzynka Meley'): MISS('Pakiet - brak.'),
	(68, 'Power Booster Pack'): MISS('Pakiet - brak.'),
	(69, 'Azraeluś'): HAVE(40004, note='Pakiet z Azraelusiem (30 dni) za 299 SM - u nas sam pet Azraeluś (30 dni).'),
	# --- Kupony
	(70, 'Kupon SM (50)'): HAVE(901),
	# --- Ulepszenie konta (VIP: our in-game shop gives these as premium time - the 30/15/7-day lines added the same way)
	(99, 'Auto Łowy'): HAVE(6, note='U nas bilet na 8 godzin; na liście 7 dni (49 SM) i 14 dni (95 SM).'),
	(100, 'Powiększony Skład'): ADD(L(71009, 1, 45, 1, 4), note='Tylko wariant 30 dni (71009) - 15 i 7 dni nie ma, a czasu przedmiotu unikatowego sklep nie zmienia (serwer bierze go z item_proto).'),
	(101, 'Rękawica Złodzieja'): ADD(L(72111, 1, 89, 1, 4, D30, '(30 dni)'), L(72111, 1, 51, 1, 4, D15, '(15 dni)'), L(72111, 1, 32, 1, 4, D7, '(7 dni)'), note='Jak w sklepie w grze: czas premium na koncie (VIP), z czasem linii.'),
	(102, 'Trzecia Ręka'): ADD(L(72131, 1, 45, 1, 4, D30, '(30 dni)'), L(72131, 1, 24, 1, 4, D15, '(15 dni)'), L(72131, 1, 13, 1, 4, D7, '(7 dni)'), note='VIP (czas premium na koncie).'),
	(103, 'Pierścień Doświadczenia'): ADD(L(72101, 1, 199, 1, 4, D30, '(30 dni)'), L(72101, 1, 114, 1, 4, D15, '(15 dni)'), L(72101, 1, 61, 1, 4, D7, '(7 dni)'), note='VIP (czas premium na koncie).'),
	(104, 'Medal Szczęścia'): ADD(L(72121, 1, 86, 1, 4, D30, '(30 dni)'), L(72121, 1, 62, 1, 4, D15, '(15 dni)'), L(72121, 1, 36, 1, 4, D7, '(7 dni)'), sub=(72121, 'Szczęśliwa Moneta'), note='Więcej yang z potworów - u nas VIP „Szczęśliwa Moneta”.'),
	(105, 'Rybie Wnętrzności'): ADD(L(72141, 1, 42, 1, 4, D30, '(30 dni)'), L(72141, 1, 30, 1, 4, D15, '(15 dni)'), L(72141, 1, 18, 1, 4, D7, '(7 dni)'), note='VIP (czas premium na koncie).'),
	(106, 'Buff Premium SungMa'): MISS('+10 do woli SungMa - brak przedmiotu.'),
	# --- Ulepszenie postaci
	(107, 'Pakiet Dusz'): ADD(L(30263, 1, 100, 1, 2), note='MT2009_PLUS_RELIC_V1: po jednej Duszy Miecza / Ochrony / Ozdoby / Światła (ilość nie podana na wiki).'),
	(108, 'Dusza Światła'): ADD(L(30258, 1, 39, 1, 2), note='MT2009_PLUS_RELIC_V1: Bonus Reliktu.'),
	(109, 'Dusza Ozdoby'): ADD(L(30257, 1, 39, 1, 2), note='MT2009_PLUS_RELIC_V1: Bonus Reliktu.'),
	(110, 'Dusza Ochrony'): ADD(L(30256, 1, 39, 1, 2), note='MT2009_PLUS_RELIC_V1: Bonus Reliktu.'),
	(111, 'Dusza Miecza'): ADD(L(30255, 1, 39, 1, 2), note='MT2009_PLUS_RELIC_V1: Bonus Reliktu.'),
	(112, 'Losowe Pudełko Sklepiku Premium'): MISS('Losowy czas sklepiku premium - brak przedmiotu.'),
	(113, 'Eliksir Ochrony Żywiołów'): MISS('Brak przedmiotu.'),
	(114, 'Wino z Kwiatu Brzoskwini'): ADD(L(70020, 1, 3, 1, 2)),
	(115, 'Szkło Handlu'): MISS('Szukanie przedmiotu w pobliżu - brak przedmiotu.'),
	(116, 'Świadectwo Zmiany'): MISS('Brak przedmiotu.'),
	(117, 'Peleryna Męstwa'): HAVE(3),
	(118, 'Buty Wiatru'): HAVE(1, 5),
	(119, 'Szpula Jedwabiu'): ADD(L(71049, 1, 9, 1, 2)),
	(120, 'Pierścień Języka'): ADD(L(71007, 1, 49, 1, 2), L(71006, 1, 29, 1, 2), note='30 dni (71007) i 15 dni (71006); 7 dni - u nas Pierścień Języka 71005 (porównany niżej).'),
	(121, 'Szkło Intuicji'): HAVE(112, note='U nas Szkło Intuicji na 30 dni (72161); zwykłego (71113) nic w grze nie używa.'),
	(122, 'Eliksir Słońca (Ś)'): ADD(L(72724, 1, 15, 1, 2)),
	(123, 'Eliksir Księżyca (Ś)'): ADD(L(72728, 1, 11, 1, 2)),
	(124, 'Mikstura Szybkości'): ADD(L(71050, 1, 4, 1, 2)),
	(125, 'Mikstura Ataku +15'): ADD(L(71034, 1, 4, 1, 2)),
	(126, 'Mikstura Ataku +10'): ADD(L(71014, 1, 4, 1, 2)),
	(127, 'Mikstura Pośpiechu'): ADD(L(71101, 1, 24, 1, 2)),
	(128, 'Błogosławieństwo Życia'): ADD(L(71018, 1, 15, 1, 2)),
	(129, 'Błogosławieństwo Magii'): ADD(L(71019, 1, 15, 1, 2)),
	(130, 'Błogosławieństwo Smoka'): ADD(L(71020, 1, 20, 1, 2)),
	(131, 'Owoc Życia'): ADD(L(71107, 1, 129, 1, 2)),
	(132, 'Księga Lidera'): ADD(L(71012, 1, 29, 1, 2), sub=(71012, 'Książka Lidera'), note='U nas nazwa „Książka Lidera” (3 godziny).'),
	(133, 'Zwój Powrotu'): HAVE(605),
	(134, 'Wykrywacz Kamieni Metin'): HAVE(906, note='U nas linia 906 (1 szt.) jest poza zakresami okna w grze, więc obu sklepom niewidoczna.'),
	# --- Uszlachetnienie
	(135, 'Żółta Lśniąca Skrzynia z Odłamkiem'): MISS('Brak skrzyni.'),
	(136, 'Zielona Lśniąca Skrzynia z Odłamkiem'): MISS('Brak skrzyni.'),
	(137, 'Szara Lśniąca Skrzynia z Odłamkiem'): MISS('Brak skrzyni.'),
	(138, 'Ognista Runa Aury (10)'): ADD(L(49991, 1, 9, 1, 3)),
	(139, 'Ognista Runa Aury (50)'): ADD(L(49992, 1, 45, 1, 3)),
	(140, 'Ognista Runa Aury (100)'): ADD(L(49993, 1, 80, 1, 3)),
	(141, 'Lśniąca Sk. z Odłamkiem'): MISS('Brak skrzyni (39069 nie ma w item_proto).'),
	(142, 'Zdobna Skrz. z Odłamkiem'): ADD(L(39068, 1, 12, 1, 3), note='Ta sama linia co w „Hity”.'),
	(143, 'Błogosławieństwo'): ADD(L(71052, 1, 129, 1, 3), sub=(71052, 'Błogosław. Przedmiotu'), note='Ta sama linia co w „Hity”; ilości x5/x10/x25 to wielokrotność ceny - wybór ilości w oknie.'),
	(144, 'Silny Suplement'): ADD(L(72067, 1, 18, 1, 3), note='x5/x10/x25 = wielokrotność ceny.'),
	(145, 'Duży Suplement'): ADD(L(72066, 1, 9, 1, 3), note='x5/x10/x25 = wielokrotność ceny.'),
	(146, 'Średni Suplement'): ADD(L(72065, 1, 5, 1, 3), note='x5/x10/x25 = wielokrotność ceny.'),
	(147, 'Świadectwo Zmiany'): MISS('Brak przedmiotu.'),
	(148, 'Zaczarowanie Przedmiotu+'): MISS('Brak przedmiotu.'),
	(149, 'Cor Draconis (surowe)'): ADD(L(51501, 1, 10, 1, 3)),
	(150, 'Zielona Smocza Fasola'): MISS('Alchemia smoczych kamieni (fasola) - brak przedmiotu.'),
	(151, 'Kula Błogosławieństwa'): ADD(L(70024, 1, 50, 1, 3), sub=(70024, 'Marmur Błogosławieństwa'), note='Dodaje 5. bonus przedmiotowi z 4 - u nas Marmur Błogosławieństwa.'),
	(152, 'Zaczarowanie Przedmiotu'): HAVE(607),
	(153, 'Wzmocnienie Przedmiotu'): ADD(L(71085, 1, 99, 1, 11)),
	(154, 'Księga Obróbki Kamienia'): HAVE(604),
	(155, 'Kamień Kowala'): HAVE(452),
	(156, 'Magiczny Metal'): HAVE(451),
	(157, 'Zwój Korekcji'): HAVE(612),
	# --- Małżeństwo
	(158, 'Bransoleta Miłości'): HAVE(207),
	(159, 'Bransoleta Harmonii'): HAVE(209),
	(160, 'Naszyjnik Miłości'): HAVE(210),
	(161, 'Naszyjnik Harmonii'): HAVE(211),
	(162, 'Kolczyki Miłości'): HAVE(208),
	(163, 'Kolczyki Harmonii'): HAVE(206),
	(164, 'Pióro Ptaka Miłości'): HAVE(205, note='Na liście 30/15/7 dni; warianty czasowe (72010-72012) nie mają danych w kliencie.'),
	# --- Indywidualizacja
	(165, 'Złote Pud. Kart Potwora'): MISS('Losowa karta potwora - brak pudełka.'),
	(166, 'Srebrne Pu. Kart Potwora'): MISS('Losowa karta potwora - brak pudełka.'),
	(167, 'Nowa Wola (WIT)'): HAVE(623),
	(168, 'Nowa Wola (ODP)'): HAVE(624),
	(169, 'Nowa Wola (SIŁA)'): HAVE(622),
	(170, 'Nowa Wola (INT)'): HAVE(625),
	(171, 'Anulacja Transmutacji'): ADD(L(72325, 1, 9, 1, 11)),
	(172, 'Bilet Transmutacji'): HAVE(950, note='U nas linia 950 jest poza zakresami okna w grze (niewidoczna) - patrz poprzednie rundy.'),
	(173, 'Maska Uczuć'): ADD(L(71011, 1, 48, 1, 2), L(71033, 1, 26, 1, 2)),
	(174, 'Zwój Cofania Umiejętności'): MISS(NO_HANDLER + ' (50003)'),
	(175, 'Olejek Wygnania'): HAVE(611),
	(176, 'Zaklęcie Modyfikacji'): HAVE(601),
	(177, 'Zwój Zmiany Profesji'): MISS(NO_HANDLER + ' (71100)'),
	(178, 'Medal Smoka'): ADD(L(71004, 1, 3, 1, 11)),
	(179, 'Zwój Egzorcyzmu'): HAVE(606),
	(180, 'Zwój Powrotu Statusu'): HAVE(602),
	(181, 'Zwój Redystrybucji (SIŁ)'): HAVE(615),
	(182, 'Zwój Redystrybucji (ZRĘ)'): HAVE(616),
	(183, 'Zwój Redystrybucji (INT)'): HAVE(614),
	(184, 'Zwój Redystrybucji (WIT)'): HAVE(613),
	(185, 'Zwój Zmiany Treningu'): ADD(L(71000, 1, 49, 1, 11)),
	(186, 'Zmiana nazwy'): MISS('Zmiana imienia postaci - brak przedmiotu.'),
	(187, 'Rozszerzenie Ekwipunku'): MISS('Brak przedmiotu.'),
	(188, 'Reset Sklepu Gaya'): HAVE(620, note='Na liście też x5 95 / x10 190 / x20 380 / x50 950 SM - to 19 SM za sztukę przy 5 SM za 1 szt. (błąd listy?), nie dodaję.'),
	(189, 'Rozszerzenie Sklepu Gaya'): ADD(L(39064, 2, 30, 1, 11, suffix='(x2)'), L(39064, 4, 48, 1, 11, suffix='(x4)'), L(39064, 9, 72, 1, 11, suffix='(x9)'), note='1 szt. mamy (19 SM = lista); dodane paczki x2/x4/x9 z rabatem z listy.'),
	(190, 'Redukcja Wytrzymałości (30%)'): MISS(NO_MERC),
	(191, 'Ładowanie Wytrzymałości (100)'): MISS(NO_MERC),
	(192, 'Wzmocnienie Wytrzymałości (1000)'): MISS(NO_MERC),
	(193, 'Esencja Komendanta Legionu'): MISS(NO_MERC),
	(194, 'Pakiet Zadań Najemnika'): MISS(NO_MERC),
	(195, 'Ekspres. Leczenie Najem.'): MISS(NO_MERC),
	(196, 'Licencja Rozszerzenia'): MISS(NO_MERC),
	(197, 'Licencja Najemnika'): MISS(NO_MERC + ' (72740 jest w item_proto jako materiał, bez użycia)'),
	(198, 'Dodatkowa strona wyposażenia'): MISS('Druga strona wyposażenia - brak systemu.'),
	# --- Transfer serwerów
	(199, 'Bilet Podróżnika'): SKIP('Transfer na inny serwer - nie dotyczy.'),
	(200, 'Bilet Podróżnika (Česko)'): SKIP('Transfer na inny serwer - nie dotyczy.'),
	(201, 'Bilet Podróżnika (Magyarország)'): SKIP('Transfer na inny serwer - nie dotyczy.'),
	(202, 'Bilet Podróżnika (Țara Românească)'): SKIP('Transfer na inny serwer - nie dotyczy.'),
	(203, 'Bilet Podróżnika (România)'): SKIP('Transfer na inny serwer - nie dotyczy.'),
	# --- Przepustki
	(204, 'Sztandar Czaszki'): ADD(L(70401, 1, 50, 1, 11), L(70401, 25, 899, 1, 11, suffix='(Paczka 25)')),
	(205, 'Tajemniczy Bilet'): ADD(L(70408, 1, 29, 1, 11), L(70408, 20, 449, 1, 11, suffix='(Paczka 20)')),
	(206, 'Wejście do Świątyni Węży'): HAVE(626),
	(207, 'Książka Przebudzenia'): ADD(L(31146, 1, 29, 1, 11)),
	(208, 'Znak Strażnika'): ADD(L(72328, 1, 69, 1, 11)),
	(209, 'Pergamin Sfer'): ADD(L(72329, 1, 29, 1, 11)),
	(210, 'Zasuszona Głowa'): ADD(L(30319, 1, 10, 1, 11), note='Lista: 12 SM i 10 SM (dwa wiersze) - przyjęte 10 SM z wiersza z paczkami.'),
	(211, 'Zasuszona Głowa'): ADD(L(30319, 1, 10, 1, 11), L(30319, 5, 39, 1, 11, suffix='(Paczka 5)'), L(30319, 25, 169, 1, 11, suffix='(Paczka 25)')),
	(212, 'Przepustka'): HAVE(609, 610),
	(213, 'Krwisty Kamień'): ADD(L(30190, 1, 12, 1, 11)),
	(214, 'Przepustka (Meley)'): MISS('Wejście gildii do Schronienia Meley - brak przedmiotu.'),
	(215, 'Wstęp do Świątyni Smoka'): SKIP('Na liście za Tygrysie Monety (inna waluta, Sklep Tygrysi); przedmiotu też nie mamy.'),
	# --- Przedmioty za Znaki (SZ)
	(216, 'Eliksir: W. SungMa(SIŁA)'): MISS('Eliksir woli SungMa (+5 na 30 min) - brak przedmiotu (55063 „Jazda (W. SungMa. SIŁA)” to inny materiał).'),
	(217, 'Eliksir: W. SungMa (INT)'): MISS('Brak przedmiotu.'),
	(218, 'Eliksir: W. SungMa (ODP)'): MISS('Brak przedmiotu.'),
	(219, 'Eliksir: W. SungMa (WIT)'): MISS('Brak przedmiotu.'),
	(220, 'Peleryna Męstwa'): ADD(L(70138, 1, 9, 2, 12), L(70138, 50, 420, 2, 12, suffix='(Paczka 50)')),
	(221, 'Szkło Intuicji'): MISS(NO_HANDLER + ' (71113; u nas jest wariant 30 dni za SM)'),
	(222, 'Mikstura Szybkości'): ADD(L(71050, 1, 25, 2, 12)),
	(223, 'Mikstura Ataku +10'): ADD(L(71014, 1, 20, 2, 12)),
	(224, 'Mikstura Ataku +15'): ADD(L(71034, 1, 20, 2, 12)),
	(225, 'Zwój Powrotu'): ADD(L(22010, 1, 9, 2, 12)),
	(226, 'Medal Smoka'): ADD(L(71004, 1, 19, 2, 12)),
	(227, 'Pierścień Tajemnic'): MISS('Brak przedmiotu.'),
	(228, 'Błogosławieństwo Życia'): ADD(L(71018, 1, 95, 2, 12)),
	(229, 'Błogosławieństwo Magii'): ADD(L(71019, 1, 95, 2, 12)),
	(230, 'Błogosławieństwo Smoka'): ADD(L(71020, 1, 125, 2, 12)),
	(231, 'Szpula Kaszmiru'): MISS('Brak przedmiotu.'),
	(232, 'Odżywka'): MISS(PET_GONE),
	(233, 'Magiczny Metal'): HAVE(710),
	(234, 'Zwój Błogosławieństwa'): HAVE(701),
	(235, 'Rada Pustelnika'): HAVE(702),
	(236, 'Dłoń Krytyka'): HAVE(703),
	(237, 'Dłoń Przebicia'): HAVE(704),
	(238, 'Atak Boga Smoków'): HAVE(706),
	(239, 'Inteligencja Boga Smoków'): ADD(L(71029, 1, 75, 2, 12)),
	(240, 'Obrona Boga Smoków'): HAVE(708),
	(241, 'Życie Boga Smoków'): HAVE(705),
	(242, 'Magiczna Ruda Miedzi'): HAVE(709),
	(243, 'Olejek Piżmowy'): HAVE(713),
	(244, 'Pakiet Zwój Błogosławieństwa 2+1'): ADD(L(25041, 3, 720, 2, 12, suffix='(2+1)')),
	# --- Wierzchowce i Zwierzaki (the owner's fixed prices: pets 299 / with loot 699 / mounts 299, 30 days)
	(349, 'Azraeluś (pieczęć)'): HAVE(40004, note='Pet bez łupu: zasada 299 SM / 30 dni (lista: 30 dni 299 SM, 7 dni 99, 200 dni 799).'),
	(350, 'Blue Barry'): HAVE(50078, note='U nas wierzchowiec (30 dni); zasada 299 SM / 30 dni (lista: 3 dni 45 SM).'),
	(351, 'Boska Odżywka'): MISS('Brak przedmiotu.'),
	(352, 'Cukier dla Konia'): MISS(NO_HANDLER + ' (71110)'),
	(353, 'Duża Magmowa Skrzynka Meley'): MISS('Brak skrzynki.'),
	(354, 'Klatka Transportowa'): HAVE(40928, sub=(55002, 'Transporter Peta')),
	(355, 'Magmowa Skrzynka Meley'): MISS('Brak skrzynki.'),
	(356, 'Mega Przekąska'): MISS(NO_HANDLER + ' (38100-38102, tylko w ofercie Gai)'),
	(357, 'Muffin z Brązowymi Akcesoriami'): HAVE(50055, note='Wierzchowiec: zasada 299 SM / 30 dni (lista: 3 dni 45 SM).'),
	(358, 'Odżywka'): MISS(PET_GONE),
	(359, 'Pancerna Panda'): HAVE(50050, note='Wierzchowiec: zasada 299 SM / 30 dni (lista: 3 dni 35 SM).'),
	(360, 'Pergamin Nazwy Zwierzaka'): HAVE(40924, sub=(55008, 'Zwój Imienia Peta')),
	(361, 'Reverti Zwierza'): HAVE(40925, sub=(55033, 'Pet Reverti')),
	(362, 'Revertus Zwierza'): HAVE(40926, sub=(55034, 'Pet Revertus')),
	(363, 'Skrzynia Ksiąg Zwierza'): MISS(PET_GONE + ' Odpowiednik: Skrzynia Ksiąg Peta (55009).'),
	(364, 'Świadectwo Lwa'): MISS(NO_HANDLER + ' (52701)'),
	(365, 'Świadectwo Wilka'): MISS(NO_HANDLER + ' (52704)'),
	(366, 'Świadectwo Dzika'): MISS(NO_HANDLER + ' (52703)'),
	(367, 'Zestaw Opieki nad Koniem'): MISS('Pakiet - brak.'),
	# --- Wizerunki broni (the owner's rule: skins 299 SM / 30 days)
	(368, 'Ostrze Wodnika+'): HAVE(30012, note='Nakładka: zasada 299 SM / 30 dni (lista: 5 dni 39 SM).'),
	(369, 'Glewia Wodnika+'): HAVE(30015, note='Nakładka: zasada 299 SM / 30 dni (lista: 5 dni 39 SM).'),
	(370, 'Sztylet Wodnika+'): HAVE(30013, note='Nakładka: zasada 299 SM / 30 dni (lista: 5 dni 39 SM).'),
	(371, 'Łuk Wodnika+'): HAVE(30014, note='Nakładka: zasada 299 SM / 30 dni (lista: 5 dni 39 SM).'),
	(372, 'Dzwon Wodnika+'): HAVE(30016, note='Nakładka: zasada 299 SM / 30 dni (lista: 5 dni 39 SM).'),
	(373, 'Wachlarz Wodnika+'): HAVE(30017, note='Nakładka: zasada 299 SM / 30 dni (lista: 5 dni 39 SM).'),
	(374, 'Szpony Wodnika+'): SKIP('Likan - nie ma tej klasy na naszym serwerze.'),
}
# The special offers (rows 71-97) and the yang pack (98) are skipped as a section (gen_global_catalog.py SKIP_SECTIONS);
# the classic hairstyles (245-348) are matched by name there (HAIR rule).
