#!/usr/bin/env python3
"""Write input_<lang>.tsv for the languages other than English: the words a
player of that language whispers or shouts, put into the bots' Polish
(playerbot_i18n.h, RewritePlayerBotI18nInput). input_en.tsv is kept by hand
and is the fullest; these carry what a bot is asked most - greetings, where /
what / level, party and guild, the trade, the dungeon calls and the
companion's orders.

    gen_input.py            (re)writes linux-port/docker/game/playerbot_i18n/input_<lang>.tsv

Left column lowercase; the core folds marks (e = e, s = s), so either
spelling matches for the Latin scripts. "word*" = any word starting so.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'linux-port/docker/game/playerbot_i18n')

# Polish (what the bots read) -> the phrases per language.
ROWS = [
    # greetings and social
    ('czesc', {'de': 'hallo|hi leute|servus|moin', 'fr': 'bonjour|salut|coucou|bonsoir', 'es': 'hola|buenas|que tal',
               'it': 'ciao|salve|buongiorno|buonasera', 'pt': 'ola|oi|bom dia|boa tarde|boa noite',
               'tr': 'selam|merhaba|slm|selamlar|sa|selamun aleykum', 'ro': 'salut|buna|neata|buna ziua',
               'cz': 'ahoj|cau|nazdar|zdravim|dobry den', 'hu': 'szia|hello|helo|sziasztok|jo napot',
               'gr': 'γεια|γεια σου|γεια σας|καλημερα|geia|geia sou|kalimera'}),
    ('co tam', {'de': 'was geht|wie gehts|wie geht es dir|alles klar', 'fr': 'ca va|comment ca va|quoi de neuf|cv',
                'es': 'como estas|como vas|que pasa|como andas', 'it': 'come stai|come va|tutto bene',
                'pt': 'tudo bem|como vai|como estas|beleza|td bem', 'tr': 'naber|nasilsin|ne haber|nbr|iyimisin',
                'ro': 'ce faci|ce mai faci|cf|ce mai zici', 'cz': 'jak se mas|jak je|co delas noveho',
                'hu': 'mi ujsag|hogy vagy|mizu|hogy vagytok', 'gr': 'τι κανεις|τι λεει|ti kaneis|ti leei'}),
    ('nara', {'de': 'tschuss|bis dann|bis spater|ciao|bb', 'fr': 'au revoir|a plus|a+|bye|salut a plus',
              'es': 'adios|chao|hasta luego|nos vemos', 'it': 'arrivederci|a dopo|ci vediamo',
              'pt': 'tchau|adeus|ate logo|falou', 'tr': 'gorusuruz|bay bay|hosca kal|gorusmek uzere',
              'ro': 'pa|la revedere|pe curand|ne vedem', 'cz': 'cau cau|nashle|mej se|uvidime se',
              'hu': 'viszlat|szia szia|pa|majd talalkozunk', 'gr': 'αντιο|τα λεμε|bye|ta leme|antio'}),
    ('dzieki', {'de': 'danke|danke schon|dankeschon|thx', 'fr': 'merci|merci beaucoup|mrc', 'es': 'gracias|muchas gracias',
                'it': 'grazie|grazie mille', 'pt': 'obrigado|obrigada|valeu|vlw', 'tr': 'tesekkurler|tesekkur ederim|sagol|eyvallah|tsk',
                'ro': 'mersi|multumesc|ms', 'cz': 'diky|dekuji|dik', 'hu': 'koszi|koszonom|kosz',
                'gr': 'ευχαριστω|ευχαριστω πολυ|efxaristo|thanks'}),
    ('przepraszam', {'de': 'sorry|entschuldigung|tut mir leid|sry', 'fr': 'desole|pardon|dsl', 'es': 'perdon|lo siento|perdona',
                     'it': 'scusa|mi dispiace|scusami', 'pt': 'desculpa|desculpe|foi mal', 'tr': 'pardon|ozur dilerim|kusura bakma',
                     'ro': 'scuze|imi pare rau|scuzati', 'cz': 'promin|sorry|omlouvam se', 'hu': 'bocs|bocsanat|sajnalom',
                     'gr': 'συγγνωμη|signomi|sorry'}),
    ('tak', {'de': 'ja|jo|jap|klar', 'fr': 'oui|ouais|ouai|bien sur', 'es': 'si|claro|vale', 'it': 'si|certo|va bene',
             'pt': 'sim|claro|pode ser', 'tr': 'evet|tamam|olur|tabi|tabiki', 'ro': 'da|sigur|bine', 'cz': 'jo|ano|jasne',
             'hu': 'igen|persze|aha', 'gr': 'ναι|nai|βεβαια|ok'}),
    ('nie', {'de': 'nein|ne|nee|nicht', 'fr': 'non|nan|pas', 'es': 'no', 'it': 'no|non', 'pt': 'nao|nem', 'tr': 'hayir|yok|olmaz|yo',
             'ro': 'nu', 'cz': 'ne', 'hu': 'nem', 'gr': 'οχι|oxi|den'}),
    # questions
    ('gdzie jestes', {'de': 'wo bist du|wo bist', 'fr': 'ou es tu|t ou|tes ou|ou t es', 'es': 'donde estas', 'it': 'dove sei',
                      'pt': 'onde estas|onde voce esta|onde tu ta|cade voce', 'tr': 'nerdesin|neredesin|nerde',
                      'ro': 'unde esti|unde esti tu', 'cz': 'kde jsi|kde jses', 'hu': 'hol vagy',
                      'gr': 'που εισαι|pou eisai'}),
    ('gdzie', {'de': 'wo|wohin', 'fr': 'ou', 'es': 'donde|adonde', 'it': 'dove', 'pt': 'onde', 'tr': 'nerede|nereye|nereden',
               'ro': 'unde', 'cz': 'kde|kam', 'hu': 'hol|hova|hova mesz', 'gr': 'που|pou'}),
    ('co robisz', {'de': 'was machst du|was machst|wat machste', 'fr': 'tu fais quoi|que fais tu|tu fais koi|qu est ce que tu fais',
                   'es': 'que haces|q haces', 'it': 'che fai|cosa fai|che stai facendo', 'pt': 'o que fazes|o que voce faz|que fazes|oq ta fazendo',
                   'tr': 'ne yapiyorsun|napiyon|napiyorsun|n4pyon|ne yapiyon', 'ro': 'ce faci acum|ce faci aici',
                   'cz': 'co delas', 'hu': 'mit csinalsz|mit csinaltok', 'gr': 'τι κανεις τωρα|ti kaneis twra'}),
    ('co', {'de': 'was', 'fr': 'quoi|que|koi', 'es': 'que|q', 'it': 'cosa|che', 'pt': 'que|o que|oq', 'tr': 'ne', 'ro': 'ce', 'cz': 'co',
            'hu': 'mit|mi', 'gr': 'τι|ti'}),
    ('jak', {'de': 'wie', 'fr': 'comment', 'es': 'como', 'it': 'come', 'pt': 'como', 'tr': 'nasil', 'ro': 'cum', 'cz': 'jak',
             'hu': 'hogy|hogyan', 'gr': 'πως|pws'}),
    ('ile', {'de': 'wie viel|wieviel|wie viele', 'fr': 'combien', 'es': 'cuanto|cuantos|cuanta', 'it': 'quanto|quanti',
             'pt': 'quanto|quantos', 'tr': 'kac|kaca|ne kadar', 'ro': 'cat|cati|cate', 'cz': 'kolik', 'hu': 'mennyi|hany|mennyiert',
             'gr': 'ποσο|ποσα|poso'}),
    ('kto', {'de': 'wer', 'fr': 'qui', 'es': 'quien', 'it': 'chi', 'pt': 'quem', 'tr': 'kim', 'ro': 'cine', 'cz': 'kdo', 'hu': 'ki',
             'gr': 'ποιος|poios'}),
    ('dlaczego', {'de': 'warum|wieso|weshalb', 'fr': 'pourquoi', 'es': 'por que|porque', 'it': 'perche', 'pt': 'porque|por que',
                  'tr': 'neden|niye|nicin', 'ro': 'de ce', 'cz': 'proc', 'hu': 'miert', 'gr': 'γιατι|giati'}),
    ('kiedy', {'de': 'wann', 'fr': 'quand', 'es': 'cuando', 'it': 'quando', 'pt': 'quando', 'tr': 'ne zaman', 'ro': 'cand',
               'cz': 'kdy', 'hu': 'mikor', 'gr': 'ποτε|pote'}),
    ('jestes', {'de': 'bist du', 'fr': 'es tu|t es', 'es': 'eres|estas', 'it': 'sei', 'pt': 'es|estas|voce e', 'tr': 'misin|sen',
                'ro': 'esti', 'cz': 'jsi', 'hu': 'vagy', 'gr': 'εισαι|eisai'}),
    ('ty', {'de': 'du|dich|dir', 'fr': 'tu|toi|te', 'es': 'tu|te', 'it': 'tu|te|ti', 'pt': 'tu|voce|vc|te', 'tr': 'sen|seni|sana',
            'ro': 'tu|tine|te', 'cz': 'ty|tebe|te', 'hu': 'te|teged', 'gr': 'εσυ|εσενα|esy'}),
    ('masz', {'de': 'hast du|hast', 'fr': 'as tu|t as|tu as', 'es': 'tienes', 'it': 'hai', 'pt': 'tens|voce tem|tem',
              'tr': 'var mi|sende var mi|varmi', 'ro': 'ai', 'cz': 'mas', 'hu': 'van', 'gr': 'εχεις|exeis'}),
    ('poziom', {'de': 'level|stufe', 'fr': 'niveau|lvl', 'es': 'nivel', 'it': 'livello', 'pt': 'nivel', 'tr': 'seviye|level|lv',
                'ro': 'nivel|level', 'cz': 'level|uroven', 'hu': 'szint|level', 'gr': 'επιπεδο|level|lvl'}),
    ('jaki masz lvl', {'de': 'welches level', 'fr': 'quel niveau|quel lvl', 'es': 'que nivel', 'it': 'che livello',
                       'pt': 'que nivel', 'tr': 'kac level|kac lv|kac seviye', 'ro': 'ce level|ce nivel', 'cz': 'jaky level',
                       'hu': 'hanyas vagy|hanyas szint', 'gr': 'τι level|ti lvl'}),
    ('expisz', {'de': 'levelst|farmst|grindest', 'fr': 'tu xp|tu farm|tu up', 'es': 'subes nivel|farmeas', 'it': 'farmi|livelli',
                'pt': 'upando|farmando|upas', 'tr': 'kasiyor|kasiyorsun|exp kasiyon|kasmak', 'ro': 'faci exp|farmezi',
                'cz': 'levelujes|farmis', 'hu': 'farmolsz|szintezel', 'gr': 'φαρμαρεις|farmareis'}),
    ('moby', {'de': 'mobs|monster', 'fr': 'monstres|mobs', 'es': 'monstruos|mobs|bichos', 'it': 'mostri|mob', 'pt': 'monstros|mobs|bichos',
              'tr': 'yaratik|yaratiklar|mob|moblar', 'ro': 'monstri|mobi', 'cz': 'potvory|moby', 'hu': 'szornyek|mobok',
              'gr': 'τερατα|mobs'}),
    ('metiny', {'de': 'metins|metinsteine', 'fr': 'metins|pierres metin', 'es': 'metins|piedras metin', 'it': 'metin|pietre metin',
                'pt': 'metins|pedras metin', 'tr': 'metin|metin taslari|metinler', 'ro': 'metine|pietre metin',
                'cz': 'metiny|metin kameny', 'hu': 'metinek|metin kovek', 'gr': 'μετιν|metins'}),
    ('mapa', {'de': 'karte|map', 'fr': 'carte|map', 'es': 'mapa', 'it': 'mappa', 'pt': 'mapa', 'tr': 'harita', 'ro': 'harta',
              'cz': 'mapa', 'hu': 'terkep|map', 'gr': 'χαρτης|map'}),
    ('kon', {'de': 'pferd', 'fr': 'cheval', 'es': 'caballo', 'it': 'cavallo', 'pt': 'cavalo', 'tr': 'at', 'ro': 'cal', 'cz': 'kun',
             'hu': 'lo', 'gr': 'αλογο|alogo'}),
    ('bron', {'de': 'waffe', 'fr': 'arme', 'es': 'arma', 'it': 'arma', 'pt': 'arma', 'tr': 'silah', 'ro': 'arma', 'cz': 'zbran',
              'hu': 'fegyver', 'gr': 'οπλο|oplo'}),
    ('zbroja', {'de': 'rustung', 'fr': 'armure', 'es': 'armadura', 'it': 'armatura', 'pt': 'armadura', 'tr': 'zirh', 'ro': 'armura',
                'cz': 'zbroj', 'hu': 'pancel', 'gr': 'πανοπλια'}),
    ('kowal', {'de': 'schmied', 'fr': 'forgeron', 'es': 'herrero', 'it': 'fabbro', 'pt': 'ferreiro', 'tr': 'demirci', 'ro': 'fierar',
               'cz': 'kovar', 'hu': 'kovacs', 'gr': 'σιδηρουργος'}),
    ('yang', {'de': 'yang|geld', 'fr': 'yang|argent|thune', 'es': 'yang|dinero|pasta', 'it': 'yang|soldi', 'pt': 'yang|dinheiro|grana',
              'tr': 'yang|para', 'ro': 'yang|bani', 'cz': 'yang|penize|prachy', 'hu': 'yang|penz', 'gr': 'yang|λεφτα|lefta'}),
    ('pt', {'de': 'gruppe', 'fr': 'groupe', 'es': 'grupo', 'it': 'gruppo', 'pt': 'grupo', 'tr': 'grup|parti', 'ro': 'grup',
            'cz': 'skupina|parta', 'hu': 'csapat|parti', 'gr': 'ομαδα|party'}),
    ('gildia', {'de': 'gilde', 'fr': 'guilde', 'es': 'gremio|guild', 'it': 'gilda', 'pt': 'guilda|guild', 'tr': 'lonca|guild',
                'ro': 'breasla|guild', 'cz': 'guilda|cech', 'hu': 'ceh|guild', 'gr': 'συντεχνια|guild'}),
    ('dolacz', {'de': 'beitreten|komm mit|mitmachen', 'fr': 'rejoindre|rejoins', 'es': 'unete|unirse', 'it': 'unisciti|entra',
                'pt': 'entra|junta te|entrar', 'tr': 'katil|gel|katilmak', 'ro': 'alatura te|intra', 'cz': 'pridej se|pridat',
                'hu': 'csatlakozz|gyere', 'gr': 'ελα|μπες'}),
    ('zapros mnie', {'de': 'lad mich ein|einladen', 'fr': 'invite moi|inv moi', 'es': 'invitame|inv', 'it': 'invitami',
                     'pt': 'me convida|convida me|inv', 'tr': 'davet et|inv at|beni al', 'ro': 'invita ma|da mi inv',
                     'cz': 'pozvi me|pozvi mne', 'hu': 'hivj meg|invitalj', 'gr': 'καλεσε με|inv'}),
    ('pomoz mi', {'de': 'hilf mir|hilfe', 'fr': 'aide moi|aidez moi|help', 'es': 'ayudame|ayuda', 'it': 'aiutami|aiuto',
                  'pt': 'me ajuda|ajuda|socorro', 'tr': 'yardim et|yardim|yardim eder misin', 'ro': 'ajuta ma|ajutor',
                  'cz': 'pomoz mi|pomoc', 'hu': 'segits|segitseg', 'gr': 'βοηθεια|βοηθησε με|help'}),
    ('jestes botem', {'de': 'bist du ein bot|bist du bot', 'fr': 'tu es un bot|t es un bot', 'es': 'eres un bot|eres bot',
                      'it': 'sei un bot', 'pt': 'es um bot|voce e um bot|vc e bot', 'tr': 'bot musun|botmusun|sen bot musun',
                      'ro': 'esti bot|esti un bot', 'cz': 'jsi bot', 'hu': 'bot vagy', 'gr': 'εισαι bot|eisai bot'}),
    ('ile masz lat', {'de': 'wie alt bist du', 'fr': 'quel age as tu|t as quel age', 'es': 'cuantos anos tienes',
                      'it': 'quanti anni hai', 'pt': 'quantos anos tens|quantos anos voce tem', 'tr': 'kac yasindasin|yasin kac',
                      'ro': 'cati ani ai', 'cz': 'kolik ti je', 'hu': 'hany eves vagy', 'gr': 'ποσο χρονων εισαι'}),
    ('skad jestes', {'de': 'woher kommst du|woher bist du', 'fr': 'tu viens d ou|d ou tu viens', 'es': 'de donde eres',
                     'it': 'di dove sei', 'pt': 'de onde es|de onde voce e', 'tr': 'nerelisin', 'ro': 'de unde esti',
                     'cz': 'odkud jsi', 'hu': 'honnan vagy|hova valosi vagy', 'gr': 'απο που εισαι'}),
    ('lubisz', {'de': 'magst du|mag', 'fr': 'tu aimes|aimes', 'es': 'te gusta|gusta', 'it': 'ti piace|piace', 'pt': 'gostas|voce gosta|curte',
                'tr': 'sever misin|seviyor musun|seviyon', 'ro': 'iti place|place', 'cz': 'mas rad|libi se', 'hu': 'szereted|szeretsz',
                'gr': 'σου αρεσει|aresei'}),
    ('dropnelo', {'de': 'gedroppt', 'fr': 'drop|loot', 'es': 'dropeo|soltó', 'it': 'droppato', 'pt': 'dropou', 'tr': 'dustu|drop',
                  'ro': 'a picat|drop', 'cz': 'padlo', 'hu': 'esett|dropolt', 'gr': 'drop'}),
    ('gratulacje', {'de': 'gz|glückwunsch|gluckwunsch|gratuliere', 'fr': 'gg|felicitations|bravo', 'es': 'felicidades|enhorabuena|gz',
                    'it': 'complimenti|congratulazioni|gz', 'pt': 'parabens|gz', 'tr': 'tebrikler|helal|gz', 'ro': 'felicitari|bravo|gz',
                    'cz': 'gratuluju|gratulace|gz', 'hu': 'gratula|gratulalok|gz', 'gr': 'συγχαρητηρια|gz|bravo'}),
    ('zaraz wracam', {'de': 'bin gleich zuruck|gleich wieder da|bin gleich da', 'fr': 'je reviens|j reviens|brb', 'es': 'ahora vuelvo|ya vuelvo',
                      'it': 'torno subito', 'pt': 'ja volto|volto ja', 'tr': 'hemen geliyorum|birazdan gelirim|geliyorum',
                      'ro': 'revin imediat|revin', 'cz': 'hned jsem zpet', 'hu': 'mindjart jovok|mindjart jovok vissza', 'gr': 'επιστρεφω|brb'}),
    # trade
    ('sprzedam', {'de': 'verkaufe|vk|verkauf', 'fr': 'vends|vend|vente', 'es': 'vendo', 'it': 'vendo', 'pt': 'vendo', 'tr': 'satilik|satiyorum|satarim|sat',
                  'ro': 'vand|vinde', 'cz': 'prodam|prodavam', 'hu': 'eladom|elado|eladnam', 'gr': 'πουλαω|poulaw|wts'}),
    ('kupie', {'de': 'kaufe|suche|kaufe an', 'fr': 'achete|achat|cherche', 'es': 'compro|busco', 'it': 'compro|cerco', 'pt': 'compro|procuro',
               'tr': 'alinir|alirim|aliyorum|ariyorum', 'ro': 'cumpar|caut', 'cz': 'koupim|hledam', 'hu': 'veszek|keresek|vennek',
               'gr': 'αγοραζω|agorazw|wtb'}),
    ('ile kosztuje', {'de': 'was kostet|wie teuer|preis', 'fr': 'combien coute|quel prix|prix', 'es': 'cuanto cuesta|precio|cuanto vale',
                      'it': 'quanto costa|prezzo', 'pt': 'quanto custa|preco', 'tr': 'kac para|fiyat|fiyati ne|ne kadar',
                      'ro': 'cat costa|pret', 'cz': 'kolik stoji|cena', 'hu': 'mennyibe kerul|ar|mennyi az ara',
                      'gr': 'ποσο κανει|τιμη|poso kanei'}),
    ('pw', {'de': 'pn|pm|privat|fluster', 'fr': 'mp|pm', 'es': 'md|privado|pm', 'it': 'pm|privato', 'pt': 'pm|privado|pv',
            'tr': 'pm|ozel|fisilti', 'ro': 'pm|privat|pv', 'cz': 'pm|pis|soukrome', 'hu': 'pm|privat|priv', 'gr': 'pm|ιδιωτικα'}),
    ('biore', {'de': 'nehme ich|ich nehme|deal', 'fr': 'je prends|ok je prends|deal', 'es': 'lo compro|me lo quedo|trato',
               'it': 'lo prendo|affare', 'pt': 'eu fico|fechado|quero', 'tr': 'aliyorum|tamam aliyorum|anlastik',
               'ro': 'il iau|ma bag|deal', 'cz': 'beru|beru to', 'hu': 'megveszem|elviszem|all az alku', 'gr': 'το παιρνω|deal'}),
    ('taniej', {'de': 'billiger', 'fr': 'moins cher', 'es': 'mas barato', 'it': 'meno caro|piu economico', 'pt': 'mais barato',
                'tr': 'daha ucuz|indirim', 'ro': 'mai ieftin', 'cz': 'levneji', 'hu': 'olcsobban|olcsobb', 'gr': 'φθηνοτερα'}),
    # dungeon and group calls
    ('kto na', {'de': 'wer kommt mit|wer geht mit|wer will', 'fr': 'qui vient|qui veut|qui pour', 'es': 'quien viene|quien va',
                'it': 'chi viene|chi va', 'pt': 'quem vem|quem vai|bora', 'tr': 'kim geliyor|gelen var mi|kimler gelir',
                'ro': 'cine vine|cine merge', 'cz': 'kdo jde|kdo pujde', 'hu': 'ki jon|ki jonne', 'gr': 'ποιος ερχεται|ποιος παει'}),
    ('szukam ekipy', {'de': 'suche gruppe', 'fr': 'cherche groupe', 'es': 'busco grupo', 'it': 'cerco gruppo', 'pt': 'procuro grupo',
                      'tr': 'grup ariyorum|parti ariyorum', 'ro': 'caut grup|caut party', 'cz': 'hledam skupinu|hledam partu',
                      'hu': 'csapatot keresek|partit keresek', 'gr': 'ψαχνω ομαδα|lfg'}),
    ('wieza demonow', {'de': 'dämonenturm|damonenturm', 'fr': 'tour des demons', 'es': 'torre demoniaca|torre de los demonios',
                       'it': 'torre dei demoni', 'pt': 'torre demoniaca|torre dos demonios', 'tr': 'seytan kulesi|seytan kule',
                       'ro': 'turnul demonilor', 'cz': 'demonska vez|vez demonu', 'hu': 'demon torony|demontorony', 'gr': 'πυργος των δαιμονων'}),
    ('pajaki', {'de': 'spinnendungeon|spinnen', 'fr': 'donjon des araignees|araignees', 'es': 'mazmorra arana|aranas',
                'it': 'dungeon dei ragni|ragni', 'pt': 'masmorra das aranhas|aranhas', 'tr': 'orumcek zindani|orumcek',
                'ro': 'temnita paianjenilor|paianjeni', 'cz': 'pavouci dungeon|pavouci', 'hu': 'pokbarlang|pokok', 'gr': 'αραχνες'}),
    ('smok', {'de': 'drache', 'fr': 'dragon', 'es': 'dragon', 'it': 'drago', 'pt': 'dragao', 'tr': 'ejderha|ejder', 'ro': 'dragon|balaur',
              'cz': 'drak', 'hu': 'sarkany', 'gr': 'δρακος'}),
    ('ide', {'de': 'komme|bin dabei|ich komme', 'fr': 'je viens|j arrive|chaud', 'es': 'voy|me apunto|yo voy', 'it': 'vengo|ci sto|arrivo',
             'pt': 'eu vou|to indo|bora', 'tr': 'geliyorum|ben varim|varim', 'ro': 'vin|ma bag|merg', 'cz': 'jdu|jsem tam',
             'hu': 'megyek|jovok|benne vagyok', 'gr': 'ερχομαι|μεσα'}),
    # companion
    ('chodz', {'de': 'komm|folge mir|komm her', 'fr': 'viens|suis moi|viens ici', 'es': 'ven|sigueme|ven aqui', 'it': 'vieni|seguimi|vieni qui',
               'pt': 'vem|segue me|anda ca|vem ca', 'tr': 'gel|beni takip et|buraya gel', 'ro': 'vino|urmeaza ma|vino aici',
               'cz': 'pojd|pojd sem|nasleduj me', 'hu': 'gyere|kovess|gyere ide', 'gr': 'ελα|ακολουθησε με|ela'}),
    ('czekaj', {'de': 'warte|bleib|warte hier', 'fr': 'attends|reste|attends ici', 'es': 'espera|quedate', 'it': 'aspetta|resta|fermo',
                'pt': 'espera|fica|aguarda', 'tr': 'bekle|dur|burada bekle', 'ro': 'asteapta|stai', 'cz': 'cekej|pockej|zustan',
                'hu': 'varj|maradj', 'gr': 'περιμενε|μεινε'}),
    ('graj sam', {'de': 'spiel allein|geh spielen', 'fr': 'joue seul|va jouer', 'es': 'juega solo|ve a jugar', 'it': 'gioca da solo|vai a giocare',
                  'pt': 'joga sozinho|vai jogar', 'tr': 'tek oyna|git oyna|kendin oyna', 'ro': 'joaca singur|du te sa joci',
                  'cz': 'hraj sam|jdi hrat', 'hu': 'jatssz egyedul|menj jatszani', 'gr': 'παιξε μονος'}),
    ('zakupy', {'de': 'einkaufen|geh einkaufen', 'fr': 'courses|va acheter', 'es': 'compras|ve de compras', 'it': 'spesa|vai a comprare',
                'pt': 'compras|vai as compras', 'tr': 'alisveris|alisverise git', 'ro': 'cumparaturi', 'cz': 'nakup|jdi nakupovat',
                'hu': 'vasarlas|menj vasarolni', 'gr': 'ψωνια'}),
    ('sprzedaj zlom', {'de': 'verkauf den mull|verkaufe schrott', 'fr': 'vends les dechets|vends la camelote', 'es': 'vende la basura',
                       'it': 'vendi la roba|vendi spazzatura', 'pt': 'vende o lixo', 'tr': 'copleri sat|esyalari sat',
                       'ro': 'vinde gunoiul', 'cz': 'prodej haraburdi|prodej smeti', 'hu': 'add el a szemetet', 'gr': 'πουλα τα σκουπιδια'}),
    ('atakuj', {'de': 'angreifen|greif an', 'fr': 'attaque', 'es': 'ataca|atacar', 'it': 'attacca', 'pt': 'ataca|atacar', 'tr': 'saldir|vur',
                'ro': 'ataca', 'cz': 'utoc', 'hu': 'tamadj', 'gr': 'επιτεθου'}),
]

DETECT = {
    'de': 'ich du bist hast ist nicht und was wo wie warum wer danke bitte hallo jemand verkaufe kaufe suche gruppe gilde komm kommst mit mir dir ja nein gut schon auch noch',
    'fr': 'je tu es suis est pas et quoi ou comment pourquoi qui merci salut bonjour quelqu vends achete cherche groupe guilde viens avec moi toi oui non bien deja aussi',
    'es': 'yo tu eres estas soy hola gracias donde como porque quien alguien vendo compro busco grupo ven conmigo contigo si bien tambien todavia que haces',
    'it': 'io tu sei sono ciao grazie dove come perche chi qualcuno vendo compro cerco gruppo vieni con me te si bene anche ancora che fai',
    'pt': 'eu tu voce vc es sou ola oi obrigado obrigada onde como porque quem alguem vendo compro procuro grupo vem comigo contigo sim nao bem tambem ainda',
    'tr': 'ben sen sana bana var yok evet hayir merhaba selam tesekkurler nerede nasil neden kim satilik alinir grup gel benimle seninle iyi daha cok abi kanka naber',
    'ro': 'eu tu esti sunt salut buna mersi multumesc unde cum cine cineva vand cumpar caut grup vino cu mine tine da nu bine si inca ce faci',
    'cz': 'ja ty jsi jsem ahoj diky dekuji kde jak proc kdo nekdo prodam koupim hledam skupina pojd se mnou tebou ano ne dobre taky jeste co delas',
    'hu': 'en te vagy vagyok szia koszi koszonom hol hogy miert ki valaki eladom veszek keresek csapat gyere velem veled igen nem jo meg mit csinalsz',
    'gr': 'εγω εσυ εισαι ειμαι γεια ευχαριστω που πως γιατι ποιος καποιος πουλαω αγοραζω ψαχνω ομαδα ελα μαζι μου ναι οχι καλα και ακομα τι κανεις geia ti kaneis pou eisai',
}


def main():
    for lang in sorted(DETECT):
        path = os.path.join(OUT, 'input_%s.tsv' % lang)
        with open(path, 'w', encoding='utf-8', newline='\n') as fp:
            fp.write('# %s -> the bots\' Polish (playerbot_i18n.h). Generated by tools/playerbot_i18n/gen_input.py;\n' % lang)
            fp.write('# edit the script, not this file. "#@detect" = the words that say a line is in this language.\n')
            fp.write('#@detect\t%s\n' % DETECT[lang])
            for pl, per in ROWS:
                for phrase in per.get(lang, '').split('|'):
                    phrase = phrase.strip()
                    if phrase:
                        fp.write('%s\t%s\n' % (phrase, pl))
        print('wrote', os.path.basename(path))


if __name__ == '__main__':
    main()
