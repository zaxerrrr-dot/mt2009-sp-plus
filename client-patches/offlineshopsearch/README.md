# Wyszukiwanie konkretnego przedmiotu w sklepach

`client-offlineshopsearch.patch` dodaje zaznaczenie ikony w oknie wyszukiwarki.
Zaznaczony przedmiot jest wyszukiwany po dokładnym `vnum` i `socket0`;
bez zaznaczenia pozostaje dotychczasowe wyszukiwanie całej kategorii.

Część serwerowa i pełna instrukcja znajdują się w
`server-patches/offlineshopsearch/`.