[CmdletBinding()]
param(
    # The engine's game/src folder (linux-port/docker/game/src/server/game/src).
    [Parameter(Mandatory = $true)][string]$SourceDir
)

# Target Drop Info and the private shop search (server-patches/shopsearchplus,
# README.md): copies src/shop_search_plus.h/.cpp next to the engine sources and
# hooks them into packet.h, packet_info.cpp, input_main.cpp and char_item.cpp.
# Same files, replacements and marker as apply_shopsearchplus.py (the Linux/VPS
# twin). A file without the expected code throws before anything is written;
# each hook keeps its file's line ending.

$ErrorActionPreference = 'Stop'
$marker = 'MT2009_PLUS_SHOP_SEARCH_PLUS_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$hooks = [ordered]@{
    'packet.h' = @(
        @("`tHEADER_CG_STATE_CHECKER`t`t`t= 206,`n", "`tHEADER_CG_STATE_CHECKER`t`t`t= 206,`n`t// MT2009_PLUS_SHOP_SEARCH_PLUS_V1 (server-patches/shopsearchplus)`n`tHEADER_CG_TARGET_DROP`t`t`t= 151,`n`tHEADER_CG_PRIVATE_SHOP_SEARCH`t= 216,`n`tHEADER_CG_PRIVATE_SHOP_SEARCH_CLOSE`t= 217,`n`tHEADER_CG_PRIVATE_SHOP_SEARCH_BUY_ITEM`t= 218,`n"),
        @("`tHEADER_GC_RESPOND_CHANNELSTATUS`t`t`t`t= 210,`n", "`tHEADER_GC_RESPOND_CHANNELSTATUS`t`t`t`t= 210,`n`t// MT2009_PLUS_SHOP_SEARCH_PLUS_V1 (server-patches/shopsearchplus)`n`tHEADER_GC_TARGET_DROP`t`t`t`t`t`t= 160,`n`tHEADER_GC_PRIVATE_SHOP_SEARCH`t`t`t`t= 216,`n`tHEADER_GC_PRIVATE_SHOP_SEARCH_OPEN`t`t`t= 217,`n`tHEADER_GC_PRIVATE_SHOP_SEARCH_MARK`t`t`t= 218,`n")
    )
    'packet_info.cpp' = @(
        @("#include `"packet_info.h`"`n", "#include `"packet_info.h`"`n#include `"shop_search_plus.h`" // MT2009_PLUS_SHOP_SEARCH_PLUS_V1`n"),
        @("`tSet(HEADER_CG_STATE_CHECKER, sizeof(BYTE), `"ServerStateCheck`", false);`n", "`tSet(HEADER_CG_STATE_CHECKER, sizeof(BYTE), `"ServerStateCheck`", false);`n`t// MT2009_PLUS_SHOP_SEARCH_PLUS_V1 (server-patches/shopsearchplus)`n`tSet(HEADER_CG_TARGET_DROP, sizeof(TPacketCGTargetDrop), `"TargetDrop`", false);`n`tSet(HEADER_CG_PRIVATE_SHOP_SEARCH, sizeof(TPacketCGPrivateShopSearch), `"PrivateShopSearch`", false);`n`tSet(HEADER_CG_PRIVATE_SHOP_SEARCH_CLOSE, sizeof(TPacketCGPrivateShopSearchClose), `"PrivateShopSearchClose`", false);`n`tSet(HEADER_CG_PRIVATE_SHOP_SEARCH_BUY_ITEM, sizeof(TPacketCGPrivateShopSearchBuyItem), `"PrivateShopSearchBuyItem`", false);`n")
    )
    'input_main.cpp' = @(
        @("#include `"input.h`"`n", "#include `"input.h`"`n#include `"shop_search_plus.h`" // MT2009_PLUS_SHOP_SEARCH_PLUS_V1`n"),
        @("#ifdef ENABLE_IKASHOP_RENEWAL`n`t`tcase HEADER_CG_NEW_OFFLINESHOP:`n", "`t`t// MT2009_PLUS_SHOP_SEARCH_PLUS_V1 (server-patches/shopsearchplus)`n`t`tcase HEADER_CG_TARGET_DROP:`n`t`t`tshop_search_plus::RecvTargetDrop(ch);`n`t`t`tbreak;`n`t`tcase HEADER_CG_PRIVATE_SHOP_SEARCH:`n`t`t`tshop_search_plus::RecvSearch(ch, c_pData);`n`t`t`tbreak;`n`t`tcase HEADER_CG_PRIVATE_SHOP_SEARCH_CLOSE:`n`t`t`tshop_search_plus::RecvClose(ch);`n`t`t`tbreak;`n`t`tcase HEADER_CG_PRIVATE_SHOP_SEARCH_BUY_ITEM:`n`t`t`tshop_search_plus::RecvBuy(ch, c_pData);`n`t`t`tbreak;`n#ifdef ENABLE_IKASHOP_RENEWAL`n`t`tcase HEADER_CG_NEW_OFFLINESHOP:`n")
    )
    'char_item.cpp' = @(
        @("#include `"PetSystem.h`"`n", "#include `"PetSystem.h`"`n#include `"shop_search_plus.h`" // MT2009_PLUS_SHOP_SEARCH_PLUS_V1`n"),
        @("`t`t`t`t`t`t`tcase UNIQUE_ITEM_CAPE_OF_COURAGE:`n", "`t`t`t`t`t`t`t// MT2009_PLUS_SHOP_SEARCH_PLUS_V1: Lupa / Lupa Handlarza open the shop search.`n`t`t`t`t`t`t`tcase SHOP_SEARCH_LOOKING_GLASS:`n`t`t`t`t`t`t`tcase SHOP_SEARCH_TRADING_GLASS:`n`t`t`t`t`t`t`t`tshop_search_plus::UseGlass(this, item);`n`t`t`t`t`t`t`t`tbreak;`n`n`t`t`t`t`t`t`tcase UNIQUE_ITEM_CAPE_OF_COURAGE:`n")
    )
}
$texts = [ordered]@{}
foreach ($name in $hooks.Keys) {
    $path = Join-Path $SourceDir $name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Brak pliku $name w $SourceDir" }
    $text = [IO.File]::ReadAllText($path, $latin1)
    if ($text.Contains($marker)) { continue }
    foreach ($pair in $hooks[$name]) {
        $done = $false
        foreach ($variant in @(@($pair[0].Replace("`n", "`r`n"), $pair[1].Replace("`n", "`r`n")), @($pair[0], $pair[1]))) {
            if (([regex]::Matches($text, [regex]::Escape($variant[0]))).Count -eq 1) {
                $index = $text.IndexOf($variant[0], [StringComparison]::Ordinal)
                $text = $text.Substring(0, $index) + $variant[1] + $text.Substring($index + $variant[0].Length)
                $done = $true
                break
            }
        }
        if (-not $done) { throw "Nie mozna zastosowac poprawki wyszukiwarki sklepow: nie znaleziono oczekiwanego kodu w $name." }
    }
    $texts[$path] = $text
}
foreach ($file in @('shop_search_plus.h', 'shop_search_plus.cpp')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "src/$file") -Destination (Join-Path $SourceDir $file) -Force
}
foreach ($path in $texts.Keys) { [IO.File]::WriteAllText($path, $texts[$path], $latin1) }
return [pscustomobject]@{ Changed = ($texts.Count -gt 0) }
