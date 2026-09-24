[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceFile
)

# Permanent mount seals (server-patches/mountpermanent, README.md): a seal
# without a real-time limit in its proto rides with no end instead of being
# reported as expired by CMountActor::Mount (MountSystem.cpp). Same
# replacement and marker as apply_mountpermanent.py (the Linux/VPS twin). A
# file without the expected code throws and nothing is written; only the
# block changes, in its own line ending.

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourceFile -PathType Leaf)) { throw "Brak pliku MountSystem.cpp: $SourceFile" }
$marker = 'MT2009_PLUS_MOUNT_PERMANENT_V1'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$text = [IO.File]::ReadAllText($SourceFile, $latin1)
if ($text.Contains($marker)) { return [pscustomobject]@{ Changed = $false } }
$old = "`tDWORD dwExpireAt = mountItem->GetSocket(0);`n`tDWORD dwNow = (DWORD)time(0);`n"
$new = "`t// MT2009_PLUS_MOUNT_PERMANENT_V1 (server-patches/mountpermanent): a seal whose`n`t// proto has no real-time limit (the blue and the war mounts, 71115-71128)`n`t// never gets an expiry in socket0. It is a permanent seal, not an expired`n`t// one: `"Ta pieczec wierzchowca juz wygasla`" on a brand new Dzik Wojenny.`n`tbool bTimedSeal = false;`n`tfor (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)`n`t{`n`t`tBYTE bLimit = mountItem->GetProto()->aLimits[i].bType;`n`t`tif (LIMIT_REAL_TIME == bLimit || LIMIT_REAL_TIME_START_FIRST_USE == bLimit)`n`t`t`tbTimedSeal = true;`n`t}`n`tif (!bTimedSeal)`n`t{`n`t`t*pDurationOut = INFINITE_AFFECT_DURATION;`n`t`treturn true;`n`t}`n`n`tDWORD dwExpireAt = mountItem->GetSocket(0);`n`tDWORD dwNow = (DWORD)time(0);`n"
$done = $false
foreach ($pair in @(@($old.Replace("`n", "`r`n"), $new.Replace("`n", "`r`n")), @($old, $new))) {
    if (([regex]::Matches($text, [regex]::Escape($pair[0]))).Count -eq 1) {
        $index = $text.IndexOf($pair[0], [StringComparison]::Ordinal)
        $text = $text.Substring(0, $index) + $pair[1] + $text.Substring($index + $pair[0].Length)
        $done = $true
        break
    }
}
if (-not $done) {
    throw 'Nie mozna zastosowac poprawki stalych pieczeci wierzchowca: nie znaleziono oczekiwanego kodu w MountSystem.cpp.'
}
[IO.File]::WriteAllText($SourceFile, $text, $latin1)
return [pscustomobject]@{ Changed = $true }
