[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# A Cor Draconis picked up or given joins the stack in the bag
# (server-patches/corautostack, README.md): CHARACTER::AutoStackItem and
# AutoStackItemProto (char_item.cpp) skip ANTI_STACK / no STACKABLE for the
# Cor vnums, as MoveItem already does (server-patches/corstack, needed first).
# Same replacements and marker as apply_corautostack.py (the Linux/VPS twin).
# A file without the expected code throws and nothing is written.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku char_item.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_COR_AUTOSTACK_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
if (-not $text.Contains('IsStackableCorDraconisVnum')) { throw 'Najpierw poprawka server-patches/corstack.' }
$pairs = @(
    "`tif (p->dwFlags & ITEM_FLAG_STACKABLE && p->bType != ITEM_BLEND)`n", "`t// MT2009_PLUS_COR_AUTOSTACK_V1 (server-patches/corautostack): a Cor Draconis`n`t// joins the stack its owner carries whatever the proto says, as a drag does`n`t// (IsStackableCorDraconisVnum, server-patches/corstack).`n`tif (((p->dwFlags & ITEM_FLAG_STACKABLE) || IsStackableCorDraconisVnum(dwItemVnum)) && p->bType != ITEM_BLEND)`n",
    "`tif (item->IsStackable() && !IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_STACK))`n`t{`n`t`tauto bCount = item->GetCount();`n", "`t// MT2009_PLUS_COR_AUTOSTACK_V1: a Cor Draconis picked up or given joins the`n`t// stack already in the bag, even where the proto has ANTI_STACK or lacks`n`t// STACKABLE - the pickup put every Cor in a stack of its own.`n`tif ((item->IsStackable() && !IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_STACK)) ||`n`t`t`tIsStackableCorDraconisVnum(item->GetVnum()))`n`t{`n`t`tauto bCount = item->GetCount();`n"
)
$crlf = $text.Contains("`r`n")
for ($i = 0; $i -lt $pairs.Count; $i += 2) {
    $old = $pairs[$i]; $new = $pairs[$i + 1]
    if ($crlf) { $old = $old.Replace("`n", "`r`n"); $new = $new.Replace("`n", "`r`n") }
    if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) {
        throw 'Nie mozna zastosowac poprawki laczenia Corow przy podnoszeniu: nie znaleziono oczekiwanego kodu w char_item.cpp.'
    }
    $index = $text.IndexOf($old, [StringComparison]::Ordinal)
    $text = $text.Substring(0, $index) + $new + $text.Substring($index + $old.Length)
}
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
