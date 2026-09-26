# Juki konne na wierzchowcach

Klient blokował wybór przedmiotu z juków (sloty 180–224), jeżeli klasyczny
koń nie był przywołany. Przez to nie dało się przeciągać przedmiotów z juków
podczas jazdy na wierzchowcu użytym z pieczęci, mimo że serwer tę operację
obsługuje.

Patch rozszerza warunek dostępu do juków. Są one dostępne, gdy postać ma konia
co najmniej na poziomie 1 oraz ma przywołanego klasycznego konia albo jedzie na
wierzchowcu. Nie zmienia zasad dla postaci bez konia ani dla gry pieszo.

Zmiana dotyczy tylko `root/uiinventory.py`; po niej trzeba ponownie spakować
`root.data` i `root.index`.
