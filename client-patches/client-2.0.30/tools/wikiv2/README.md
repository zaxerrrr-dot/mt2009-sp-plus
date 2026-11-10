# Encyklopedia w grze (MT2009_PLUS_WIKI_V1) i podgląd modelu w opisie przedmiotu (MT2009_PLUS_TOOLTIP_MODEL_PREVIEW_V1)

Wiki z paczki Valiant2 (wygląd, obrazki, układ okna) przebudowana pod nasz klient i nasze dane serwera.

## Części

| Gdzie | Co |
|---|---|
| `client-patches/exe/UserInterface/Mt2009Wiki.cpp` | moduł `wikipedia` (exe): czyta `locale/common/wiki/*.txt`, indeksy przedmiot -> potwory / skrzynie / receptury / sklepy / ulepszenia, wyszukiwarka |
| `client-patches/exe/UserInterface/Mt2009WikiModel.cpp` | moduł `renderTarget` (exe): podglądy 3D (wiki i opis przedmiotu) na naszej ścieżce render target (hook `UI::CRenderTarget`), wiele widoków, efekty (błysk +7.., tabela błysków) |
| `client-patches/exe/{EterLib,EffectLib,GameLib}/...` | `RENDER_TARGET_INDEX_MT2009_FREE` + `RemoveRenderTargetTexture`, `CEffectManager::Mt2009RenderOne`, `CActorInstance::Mt2009RenderAttachingEffects` |
| `root/uiwiki.py` | okno (z `tools/wikiv2/src/uiwiki.py` - źródło UTF-8; `escape_cp1250.py` robi z niego plik ASCII z kodami CP1250) |
| `root/tooltipmodel.py` | podgląd modelu obok opisu przedmiotu (własna rasa i płeć gracza), Shift+H |
| `root/{game,keybind,uiinventory,uitarget,uitooltip,uiopcjedodatkowe}.py` | haki: klawisz `/` (akcja `wiki`), Shift+H (`wiki_item`), przycisk „Encyklopedia” na pasku przy ekwipunku (zamiast „Drop wiki”), (i) przy celu, opcja „Wyłącz podgląd modelu w opisie przedmiotu” |
| `wikiv2/d_/ymir work/ui/game/wiki/` | obrazki Valiant2 (bannery po polsku) - `make_wiki_images.py` |
| `wikiv2/locale/common/wiki/{items,mobs,chests,crafting}.txt` | dane - **GENEROWANE** przez `gen_wiki_data.py` z tabel serwera testowego |
| `build_wikiv2_pack.py` | nowa paczka klienta `wikiv2` (obrazki + dane), linia w `Index` na końcu |

## Regeneracja danych (każde wydanie)

Na vps1, przy działającym `mt2009plustest-game` i `mt2009plustest-db`:

```
python3 client-patches/client-2.0.30/tools/wikiv2/gen_wiki_data.py          # zapisuje 4 pliki
python3 client-patches/client-2.0.30/tools/wikiv2/gen_wiki_data.py --check  # sprawdza, czy są aktualne
```

Szanse: za jedno zabójstwo, dla gracza na poziomie potwora, bazowy item rate 100%, bez premium/rękawic/eventów
(port `ITEM_MANAGER::GetDropWikiRows` / `GetDropWikiChests` z drzewa testowego) - opis w nagłówku skryptu.

## Budowa klienta (clientY.sh)

Po ostatnim kroku paczek (przed pętlą weryfikacji):

```
S_wikiv2_pack() { docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/wikiv2/build_wikiv2_pack.py $C/azbase $C/out/pack; }; step wikiv2_pack $C/wikiv2.json S_wikiv2_pack
```

Pliki root idą jak zawsze przez build57 (repo `client-2.0.30/root`). Exe: nowe (zmiany w `client-patches/exe`).
