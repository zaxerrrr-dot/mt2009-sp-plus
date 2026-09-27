[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# A Cor Draconis of a real player in the bot's own party may be picked up by
# the bot (server-patches/corpartypickup, README.md): the companion collects
# its owner's drop through the party branch of CHARACTER::PickupItem, which
# hands the item straight to the owner, and the blanket "no Cor for a bot"
# refused it ("Towarzysz nie podnosi Corow", 27 September). Same edit and
# marker as apply_corpartypickup.py (the Linux/VPS twin). A file without the
# expected code throws and nothing is written.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku char_item.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_COR_PARTY_PICKUP_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$nl = if ($text.Contains("`r`n")) { "`r`n" } else { "`n" }
$old = (@(
    "`tif (item->GetVnum() == 50255 &&",
    "`t`tGetDesc() &&",
    "`t`tGetDesc()->IsBot())",
    "`t{",
    "`t`tsys_log(0, `"[DS_COR_DROP] pickup blocked: bot pid=%u name=%s tried to pick up Cor Draconis id=%u`",",
    "`t`t`tGetPlayerID(), GetName(), item->GetID());",
    "`t`treturn false;",
    "`t}"
) -join $nl) + $nl
$new = (@(
    "`t//",
    "`t// MT2009_PLUS_COR_PARTY_PICKUP_V1: except a Cor that is a real player's of",
    "`t// the bot's own party - the companion collecting its owner's drop, a bot",
    "`t// invited into a player's party. The party branch below hands such an",
    "`t// item straight to its owner, so the bot never holds it (`"Towarzysz nie",
    "`t// podnosi Corow`", 27 September). Only an owned Cor: an ownerless one would",
    "`t// go to whichever member the party branch finds last, a bot as likely.",
    "`tif (item->GetVnum() == 50255 &&",
    "`t`tGetDesc() &&",
    "`t`tGetDesc()->IsBot())",
    "`t{",
    "`t`tLPCHARACTER corOwner = NULL;",
    "`t`tif (!item->IsOwnership(this) && GetParty() &&",
    "`t`t`t!IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_DROP))",
    "`t`t{",
    "`t`t`tNPartyPickupDistribute::FFindOwnership findOwner(item);",
    "`t`t`tGetParty()->ForEachOnlineMember(findOwner);",
    "`t`t`tcorOwner = findOwner.owner;",
    "`t`t}",
    "`t`tif (!corOwner || corOwner == this || !corOwner->GetDesc() || corOwner->GetDesc()->IsBot())",
    "`t`t{",
    "`t`t`tsys_log(0, `"[DS_COR_DROP] pickup blocked: bot pid=%u name=%s tried to pick up Cor Draconis id=%u`",",
    "`t`t`t`tGetPlayerID(), GetName(), item->GetID());",
    "`t`t`treturn false;",
    "`t`t}",
    "`t`tsys_log(0, `"[DS_COR_DROP] party pickup: bot pid=%u name=%s picks up Cor Draconis id=%u for %s`",",
    "`t`t`tGetPlayerID(), GetName(), item->GetID(), corOwner->GetName());",
    "`t}"
) -join $nl) + $nl
$first = $text.IndexOf($old, [StringComparison]::Ordinal)
if ($first -lt 0 -or $text.IndexOf($old, $first + 1, [StringComparison]::Ordinal) -ge 0) {
    throw 'Nie mozna zastosowac poprawki Cor Draconis dla Towarzysza: nie znaleziono oczekiwanego kodu w char_item.cpp.'
}
$text = $text.Substring(0, $first) + $new + $text.Substring($first + $old.Length)
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
