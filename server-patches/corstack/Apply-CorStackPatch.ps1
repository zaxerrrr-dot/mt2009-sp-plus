[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# Cor Draconis boxes stack in CHARACTER::MoveItem (server-patches/corstack,
# README.md) even where the server proto carries ANTI_STACK. Same replacements
# and marker as apply_corstack.py (the Linux/VPS twin). A file without the
# expected code throws and nothing is written; only the blocks change, in the
# file's own line ending.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku char_item.cpp: $SourceFile" }
$marker = 'IsStackableCorDraconisVnum'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$crlf = $text.Contains("`r`n")
$pairs = @(
    @("enum {ITEM_BROKEN_METIN_VNUM = 28960};`n`n", "enum {ITEM_BROKEN_METIN_VNUM = 28960};`n`n// MT2009 Plus: Cor Draconis items from the newer client data must remain`n// stackable even when the legacy server proto still carries ANTI_STACK.`nstatic bool IsStackableCorDraconisVnum(DWORD vnum)`n{`n`tswitch (vnum)`n`t{`n`t`tcase 50252: case 50255: case 50256: case 50257: case 50258: case 50259: case 50260:`n`t`tcase 51501: case 51502: case 51503: case 51504: case 51505: case 51506: case 51507: case 51508: case 51509: case 51510:`n`t`tcase 51541: case 51548: case 51549: case 51562: case 51569: case 51576: case 51583: case 51590: case 51597:`n`t`tcase 51604: case 51611: case 51618: case 51625: case 51632: case 76040:`n`t`t`treturn true;`n`t}`n`treturn false;`n}`n`n"),
    @("`tconst bool bDSMoveTrace = bDSMoveTraceSrc || item->IsDragonSoul() || item->GetType() == ITEM_SPECIAL_DS;`n", "`tconst bool bDSMoveTrace = bDSMoveTraceSrc || item->IsDragonSoul() || item->GetType() == ITEM_SPECIAL_DS;`n`tconst bool bForceCorStack = IsStackableCorDraconisVnum(item->GetVnum());`n"),
    @("`t`tif ((item2 = GetItem(DestCell)) && item != item2 && item2->IsStackable() &&`n`t`t`t`t!IS_SET(item2->GetAntiFlag(), ITEM_ANTIFLAG_STACK) &&`n", "`t`tif ((item2 = GetItem(DestCell)) && item != item2 && (item2->IsStackable() || bForceCorStack) &&`n`t`t`t`t(!IS_SET(item2->GetAntiFlag(), ITEM_ANTIFLAG_STACK) || bForceCorStack) &&`n"),
    @("`t`tif (count == 0 || count >= item->GetCount() || !item->IsStackable() || IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_STACK))`n", "`t`tif (count == 0 || count >= item->GetCount() ||`n`t`t`t`t(!item->IsStackable() && !bForceCorStack) ||`n`t`t`t`t(IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_STACK) && !bForceCorStack))`n")
)
foreach ($pair in $pairs) {
    $old = $pair[0]; $new = $pair[1]
    if ($crlf) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
    if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
        throw 'Nie mozna zastosowac poprawki stackowania Corow: nie znaleziono oczekiwanego kodu w char_item.cpp.'
    }
    $index = $text.IndexOf($old, [StringComparison]::Ordinal)
    $text = $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length)
}
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
