# Translating the bots' chat lines (MT2009 PLUS game server)

The server runs hundreds of "player bots" that chat like real players of an
old-school Korean-style MMORPG (Polish community): whispers to players,
shout channel, trade chat ("S>" = selling, "K>"/"B>" = buying), guild chat,
party/dungeon calls, a companion bot that answers its owner's commands, etc.
All their lines are written in Polish WITHOUT diacritics (ASCII Polish:
"Jestem w Dolinie Orkow" = "Jestem w Dolinie Orków").

At runtime the finished Polish line is matched against these templates and the
translation is sent instead, so every catalog line needs its own translation.

## Input / output format

Each staging file `<lang>_NNN.tsv` has one row per line, 4 columns separated
by a real TAB:

    id <TAB> Polish source <TAB> English reference <TAB> target

- Fill ONLY column 4 (the target) with your translation. Leave id, Polish and
  English exactly as they are (byte for byte), keep the row order and count.
- The English column is a finished translation of the same line: use it to
  understand the Polish, but translate the meaning into natural chat in your
  language, not word by word from the English. It may be empty.
- UTF-8, no TAB and no line break inside the target, at most ~120 characters.
- Write the real letters of your language (ä ö ü ß, é è à ç, ñ, ç ğ ı ş, ă â î ș ț,
  č ř š ž ě ů, ő ű, Greek script). Never write escape sequences like `\xE9`.
- `-` as the target = the line is not text (a code word, a key): use it only
  when the English column is `-` too or the line obviously is no text.

## Slots (must survive exactly)

- `$NAME`-style tokens (`$MAPIN`, `$WEAPON`, `$PLAYER`, `$GOLD`, `$LVL`...) and
  `{1}`, `{2}`... are values filled in at runtime. Every slot of the Polish must
  appear in the translation, written exactly the same (case, braces). You may
  move them to where the target grammar wants them. Never invent a slot.
- The values are translated on their own before they are put in, so assume a
  slot holds a phrase in YOUR language. Important ones:
  - `$MAPIN`, `$MAPINSHORT`, `$WASAT`, `$SHOPAT` = "in <place>" INCLUDING the
    preposition (Polish "w Joan") -> write "$MAPIN" alone, not "in $MAPIN".
  - `$DEST` = "to <place>" including the preposition.
  - `$MAPNAME`, `$VIL` = bare place name. `$TARGET`, `$HUNT`, `$FAMILY` = monster(s).
  - `$WEAPON`, `$ARMOR`, `$ITEM`, `$GOAL`, `$BIO`, `$OBJ` = an item or a thing.
  - `$PLAYER` = the player spoken to, `$NAME` = the bot, `$LEADER` = a name.
  - `$GOLD`, `$GOALPRICE`, `$UNIT`, prices = amounts like "1.5kk" (kk = million yang).
  - `$LVL`, `$HP`, `$CH`, `$N`, numbers. `$CLASS` = class name, `$EMPIRE` = kingdom.
  - `{n}` = printf values: names, numbers, or whole sub-phrases; read the line
    to guess. `{1}{2}` side by side are two values glued together.
- Lines that are only a fragment ("na CH", ", do tego oslona na", "w Yongan",
  "do Doliny Orkow") are pieces glued into bigger lines - translate them as the
  same kind of piece ("on CH", ", plus a shield for", "in Yongan", "to Orc Valley").
  Place phrases: "w X"/"na X" -> "in X"/"at X"; "do X" -> "to X"; bare name -> name.

## Style - the most important part

These are players chatting, not a UI. Keep the register of each line:
- casual Polish ("siema", "xd", "spoko", "nwm", lowercase, no full stop) ->
  casual target-language gamer chat with natural slang and abbreviations
  (EN: "yo", "lol", "np", "ty", "idk", "brb", "gz", "wts/wtb", "pm me", "lf party").
  NOT stiff textbook sentences. Keep smileys (:D :P xD :( ) as they are.
- Keep lowercase if the Polish is lowercase; keep the punctuation habit.
- Keep length roughly similar (chat line limit ~ 120 bytes).
- Proper notices/messages (e.g. "[Legenda] ...", companion instructions,
  "Podaj kwote, np. 500000 albo 1.5kk.") -> clear, correct, friendly sentences.
- Jokes: translate into a joke that works in the target language (keep the idea).
- Swearing: keep it mild, same strength at most.

## Game terms (use the usual names players of this game use in your language)

yang (money; "kk" = million, "kkk" = billion: keep kk/kkk), exp / expic = exp /
grind, lvl, metki / Metiny / Kamien Metin = Metin stones / Metins, boss, drop,
mob(y) = mob(s), pt / party = party, gildia = guild, wojna gildii = guild war,
stragan = shop/stall (private shop), sklep = shop, pw = PM, CH1 = CH1 (channel),
Smocze Monety (SM) = Dragon Coins (DC), Itemshop = item shop, Biolog =
Biologist, Kowal = Blacksmith, Stajenny = Stable Boy, Magazynier = Storekeeper,
Rybak = Fisherman, Handlarz = merchant / General Store, Towarzysz = Companion,
Ksiega Umiejetnosci (KU) = Skill Book, Kamien Duszy = Soul Stone, Zwoj
Blogoslawienstwa = Blessing Scroll, ulepszanie u kowala = upgrading at the
blacksmith (+0..+9), bonusy = bonuses (attributes), srednie (obrażenia) =
average damage, body / mental = Body / Mental (warrior builds).
Classes: Wojownik/woj = Warrior, Ninja = Ninja, Sura = Sura, Szaman = Shaman.
Kingdoms: Shinsoo (red), Chunjo (yellow), Jinno (blue). Villages and many maps
keep their names: Yongan, Jayang, Joan, Pyungmoo, Bokjung, Chunjo, Imha,
Bakra, Waryong, Seungryong, Yongbi, Sohan, Doyyumhwaji...
Places (EN): Dolina Orkow = Orc Valley, Gora Sohan = Mount Sohan, Pustynia
Yongbi = Yongbi Desert, Ognista Ziemia = Fireland (Doyyumhwaji), Las Duchow =
Ghost Forest, Czerwony Las = Red Forest, Wieza Demonow = Demon Tower, Lochy
Pajakow / Jaskinia Pajakow = Spider Dungeon, Grota Wygnancow = Grotto of Exile,
Ziemia Gigantow = Land of Giants, Swiatynia Hwang = Hwang Temple, Lochy Malp =
Monkey Dungeon, Pole Bitwy = battlefield, Smocza Grota = Dragon's Lair.
Never write "Metin2", "Gameforge" or "official".

## Lines that are not speech

Some catalog lines are keywords, labels or already English ("full bag", "an
add stone"). Translate them anyway as short labels (an already-English line is
copied unchanged in an English file). Only if a line is clearly a code
identifier / not text at all, put `-` as its translation.

## Never

- Never write "Metin2", "Gameforge", "official" (or "offiziell", "officiel",
  "ufficiale", "oficial", "resmi", "oficiální", "hivatalos", "επίσημο" ...),
  "Ameria" or "metin2alerts" - the import rejects such a row.
- Never translate `/towarzysz ...` commands, `/` commands or words inside
  quotes that a player has to type ("napisz \"chodz\"" -> write "come": the
  bots understand the English, German... words of input_<lang>.tsv; when in
  doubt keep the quoted Polish word).
- Never change, add or drop a `$SLOT` or `{n}`.

## Per language

- en: yo, lol, np, ty, idk, brb, gz, wts/wtb, pm me, lf party; Orc Valley, Mount Sohan,
  Yongbi Desert, Fireland, Ghost Forest, Red Forest, Demon Tower, Spider Dungeon.
- de: jo, moin, kk, lol, gz, vk = verkaufe, pn, lvl, Grp; Orktal, Berg Sohan, Yongbi-Wüste,
  Feuerland, Geisterwald, Roter Wald, Dämonenturm, Spinnendungeon; Schmied, Biologe,
  Stalljunge, Metinsteine, Fertigkeitsbuch, Seelenstein, Segensschriftrolle, Drachenmünzen;
  Krieger, Ninja, Sura, Schamane.
- tr: slm, naber, abi, kanka, satılık / alınır, pm, tşk, gz, kasmak = grind (casual lines may be
  ASCII Turkish as players type); Ork Vadisi, Sohan Dağı, Yongbi Çölü, Ateş Diyarı,
  Hayalet Ormanı, Kızıl Orman, Şeytan Kulesi, Örümcek Zindanı; demirci, biyolog, seyis,
  Metin taşları, Beceri Kitabı, Ruh Taşı, Kutsama Kağıdı, Ejderha Parası; Savaşçı, Ninja,
  Sura, Şaman.
- ro: salut, ce faci, vând / cumpăr, pm, lvl; Valea Orcilor, Muntele Sohan, Turnul Demonilor;
  fierar, biolog, pietre Metin.
- es: holi, q tal, vendo / compro, md, xd; Valle de los Orcos, Monte Sohan, Desierto de Yongbi,
  Torre Demoníaca; herrero, biólogo, piedras Metin.
- it: ciao, raga, vendo / compro, pm, xD; Valle degli Orchi, Monte Sohan, Deserto di Yongbi,
  Torre dei Demoni; fabbro, biologo, pietre Metin.
- fr: slt, cc, mdr, jsp, mp, vends / achète, gg; Vallée des Orcs, Mont Sohan, Désert de Yongbi,
  Terre de Feu, Forêt des Fantômes, Forêt Rouge, Tour des Démons, Donjon des Araignées;
  forgeron, biologiste, pierres Metin, livre de compétence.
- pt: olá, vendo / compro, pm, xD (European / neutral Portuguese); Vale dos Orcs, Monte Sohan,
  Torre dos Demónios; ferreiro, biólogo, pedras Metin.
- cz: čau, prodám / koupím, pm, lvl; Údolí orků, hora Sohan, Démonská věž; kovář, biolog,
  Metin kameny.
- hu: szia, eladó / veszek, pm; Ork-völgy, Sohan-hegy, Démontorony; kovács, biológus, Metin kövek.
- gr: Greek script, casual: γεια, τι λέει, πουλάω / αγοράζω, pm; Κοιλάδα των Ορκ,
  Πύργος των Δαιμόνων; σιδεράς, βιολόγος, πέτρες Metin.
- "Where are you from" style answers name a city / country of that language, not Poland.
