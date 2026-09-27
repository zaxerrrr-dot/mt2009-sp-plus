[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# The pet stays when its owner dies (server-patches/petstaysondeath,
# README.md): CPetActor::Update unsummoned it the moment the owner died; now it
# waits by the body and follows again once the owner stands up. Same edit and
# marker as apply_petstaysondeath.py (the Linux/VPS twin). A file without the
# expected code throws and nothing is written.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku PetSystem.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_PET_STAYS_ON_DEATH_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$nl = if ($text.Contains("`r`n")) { "`r`n" } else { "`n" }
$old = (@(
    "`tif (m_pkOwner->IsDead() || (IsSummoned() && m_pkChar->IsDead())",
    "`t`t|| NULL == ITEM_MANAGER::instance().FindByVID(this->GetSummonItemVID())",
    "`t`t|| ITEM_MANAGER::instance().FindByVID(this->GetSummonItemVID())->GetOwner() != this->GetOwner()",
    "`t`t)",
    "`t{",
    "`t`tthis->Unsummon();",
    "`t`treturn true;",
    "`t}"
) -join $nl) + $nl
$new = (@(
    "`t// MT2009_PLUS_PET_STAYS_ON_DEATH_V1 (server-patches/petstaysondeath): the",
    "`t// owner's death no longer sends the pet away - it waits by the body and",
    "`t// follows again once the owner is back on its feet (`"po zginieciu pet jest",
    "`t// odwolywany, ma zostawac`", 27 September).",
    "`tif ((IsSummoned() && m_pkChar->IsDead())",
    "`t`t|| NULL == ITEM_MANAGER::instance().FindByVID(this->GetSummonItemVID())",
    "`t`t|| ITEM_MANAGER::instance().FindByVID(this->GetSummonItemVID())->GetOwner() != this->GetOwner()",
    "`t`t)",
    "`t{",
    "`t`tthis->Unsummon();",
    "`t`treturn true;",
    "`t}",
    "",
    "`tif (m_pkOwner->IsDead())",
    "`t`treturn true;"
) -join $nl) + $nl
$first = $text.IndexOf($old, [StringComparison]::Ordinal)
if ($first -lt 0 -or $text.IndexOf($old, $first + 1, [StringComparison]::Ordinal) -ge 0) {
    throw 'Nie mozna zastosowac poprawki peta: nie znaleziono oczekiwanego kodu w PetSystem.cpp.'
}
$text = $text.Substring(0, $first) + $new + $text.Substring($first + $old.Length)
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
