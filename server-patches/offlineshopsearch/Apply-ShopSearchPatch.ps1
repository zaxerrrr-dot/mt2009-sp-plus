[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) {
    throw "Brak pliku Ikarus shop manager: $SourceFile"
}

$original = [IO.File]::ReadAllText($SourceFile)
$hadCrlf = $original.Contains("`r`n")
$text = $original.Replace("`r`n", "`n")

function Replace-ShopSearchBlock {
    param(
        [Parameter(Mandatory = $true)][string]$Old,
        [Parameter(Mandatory = $true)][string]$New,
        [Parameter(Mandatory = $true)][string]$Name
    )
    if ($script:text.Contains($New)) { return }
    if (-not $script:text.Contains($Old)) {
        throw "Nie można zastosować poprawki wyszukiwarki sklepów ($Name): nie znaleziono oczekiwanego kodu."
    }
    $script:text = $script:text.Replace($Old, $New)
}

$old = @'
	static void PlayerBotSearchStalls(LPCHARACTER ch, DWORD category, const FILTERS& filters,
			std::vector<TSubPacketGCShopSearchItemShop>& foundShops)
'@
$new = @'
	static void PlayerBotSearchStalls(LPCHARACTER ch, DWORD category, const FILTERS& filters,
			std::vector<TSubPacketGCShopSearchItemShop>& foundShops,
			DWORD selectedVnum = 0, int selectedSocket0 = 0)
'@
Replace-ShopSearchBlock $old $new 'sygnatura straganów botów'

$old = @'
			CPlayerBotStallView view(keeper);
			if (!PlayerBotMatchShopCategory(category, &view, filters))
				continue;
'@
$new = @'
			CPlayerBotStallView view(keeper);
			// A picked icon searches for exactly one item; no selection keeps
			// the old whole-category behaviour.
			if (selectedVnum != 0 ? !view.HasItem(selectedVnum, selectedSocket0)
					: !PlayerBotMatchShopCategory(category, &view, filters))
				continue;
'@
Replace-ShopSearchBlock $old $new 'filtrowanie straganów botów'

$old = @'
		if (itemVnum >= SHOP_SEARCH_CATEGORY_MAX * SHOP_CATEGORY_MAX_SUB)
			return false;

		std::vector<TSubPacketGCShopSearchItemShop> foundShops{};
'@
$new = @'
		if (itemVnum >= SHOP_SEARCH_CATEGORY_MAX * SHOP_CATEGORY_MAX_SUB)
			return false;

		// MT2009_PLUS_SHOP_SEARCH_ITEM_V1
		// The category stays in itemVnum. A picked icon travels in socket0 as
		// vnum * 1000 + its socket0; zero means the complete category.
		DWORD selectedVnum = 0;
		int selectedSocket0 = 0;
		if (socket0 > 0)
		{
			selectedVnum = static_cast<DWORD>(socket0 / 1000);
			selectedSocket0 = socket0 % 1000;
			if (!ITEM_MANAGER::instance().GetTable(selectedVnum))
				return false;
		}

		std::vector<TSubPacketGCShopSearchItemShop> foundShops{};
'@
if ($text.Contains('selectedVnum = static_cast<DWORD>(socket0 / 1000);') -and
    $text.Contains('ITEM_MANAGER::instance().GetTable(selectedVnum)')) {
    if (-not $text.Contains('MT2009_PLUS_SHOP_SEARCH_ITEM_V1')) {
        $declaration = "`t`tDWORD selectedVnum = 0;"
        if (-not $text.Contains($declaration)) {
            throw 'Nie można oznaczyć istniejącego dekodowania wybranego przedmiotu.'
        }
        $text = $text.Replace($declaration,
            "`t`t// MT2009_PLUS_SHOP_SEARCH_ITEM_V1`n" + $declaration)
    }
}
else {
    Replace-ShopSearchBlock $old $new 'dekodowanie wybranego przedmiotu'
}

$old = @'
				if (!SearchItemsByCategory(itemVnum, shop))
				{
					continue;
				}
'@
$new = @'
				if (selectedVnum != 0 ? !shop->HasItem(selectedVnum, selectedSocket0)
						: !SearchItemsByCategory(itemVnum, shop))
				{
					continue;
				}
'@
Replace-ShopSearchBlock $old $new 'filtrowanie sklepów offline'

$old = 'PlayerBotSearchStalls(ch, itemVnum, m_shopSearchFilters, foundShops);'
$new = 'PlayerBotSearchStalls(ch, itemVnum, m_shopSearchFilters, foundShops, selectedVnum, selectedSocket0);'
Replace-ShopSearchBlock $old $new 'wywołanie wyszukiwania straganów'

foreach ($required in @(
    'MT2009_PLUS_SHOP_SEARCH_ITEM_V1',
    'DWORD selectedVnum = 0, int selectedSocket0 = 0',
    'shop->HasItem(selectedVnum, selectedSocket0)',
    'view.HasItem(selectedVnum, selectedSocket0)',
    'foundShops, selectedVnum, selectedSocket0)'
)) {
    if (-not $text.Contains($required)) {
        throw "Weryfikacja poprawki wyszukiwarki sklepów nie powiodła się: $required"
    }
}

if ($hadCrlf) { $text = $text.Replace("`n", "`r`n") }
$changed = $text -ne $original
if ($changed) {
    [IO.File]::WriteAllText($SourceFile, $text, [Text.UTF8Encoding]::new($false))
}

[pscustomobject]@{ Changed = $changed; SourceFile = $SourceFile }
