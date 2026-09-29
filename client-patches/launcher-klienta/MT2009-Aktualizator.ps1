param(
    # Only define the functions and stop before the window: used by the tests
    # (dot-source with -TylkoFunkcje) and by nobody else.
    [switch]$TylkoFunkcje
)

# MT2009 PLUS - aktualizator klienta.
#
# A small program that lives in the game client folder, next to
# metin2client.exe: it checks the MT2009 PLUS update manifest, downloads the
# client update zip, verifies its SHA-256, applies it over the folder and
# starts the game. It also writes coop.cfg / coop2.cfg, the two online server
# slots the client lists besides localhost. It never touches a server.
#
# Windows PowerShell 5.1 + WinForms, started by MT2009-Aktualizator.bat. The
# logic above "OKNO" does not use WinForms, so it can be tested on its own.
#
# The launcher ships inside the client update zip, so an update replaces this
# very file while it runs. That is safe: PowerShell has read the whole script
# before the first line runs, the background picture is read into memory (not
# kept open) and the .bat has already ended (it uses "start").

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$script:AktVersion = '1.0.0'
$script:ManifestUrl = 'https://raw.githubusercontent.com/zaxerrrr-dot/mt2009-sp-plus/main/update-manifest-mt2009.json'
# The small files of the published client with their SHA-256 (made by
# dodaj-do-paczki.py with each client release). Hashing them at start tells
# whether this folder is that client, even with no CLIENT_VERSION.
$script:FileListUrl = 'https://raw.githubusercontent.com/zaxerrrr-dot/mt2009-sp-plus/main/client-files.json'
# The installed client version, one line. The launcher writes it after an
# update; the client update zip carries it as well, so a zip unpacked by hand
# leaves the right value behind.
$script:VersionFileName = 'CLIENT_VERSION'
$script:StagingName = 'MT2009-Aktualizator.tmp'
$script:LogName = 'MT2009-Aktualizator.log'
$script:LauncherFilePrefix = 'MT2009-Aktualizator.'
$script:Sep = [IO.Path]::DirectorySeparatorChar

# The player's own files. An update zip never overwrites them; it may only
# create one that is not there yet.
$script:KeepIfPresentFiles = @('coop.cfg', 'coop2.cfg', 'game1.cfg', 'metin2.cfg', 'config.cfg', 'syserr.txt', 'log.txt')
$script:KeepIfPresentDirs = @('UserData', 'screenshot', 'mark')
# Never written from a zip at all.
$script:NeverWrite = @($script:StagingName, $script:LogName)

$script:CancelRequested = $false

# --------------------------------------------------------------- general

function Write-AktLog {
    param([string]$Root, [string]$Text)
    if (-not $Root) { return }
    try {
        $path = Join-Path $Root $script:LogName
        if ((Test-Path -LiteralPath $path -PathType Leaf) -and (Get-Item -LiteralPath $path).Length -gt 512KB) {
            Remove-Item -LiteralPath $path -Force
        }
        $line = ('{0}  {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Text)
        [IO.File]::AppendAllText($path, $line + "`r`n", (New-Object Text.UTF8Encoding($false)))
    }
    catch { }
}

function Enable-AktTls12 {
    # Windows PowerShell 5.1 on an older Windows still starts with TLS 1.0,
    # which GitHub refuses.
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    }
    catch { }
}

function Format-AktSize {
    param([double]$Bytes)
    if ($Bytes -ge 1GB) { return ('{0:N2} GB' -f ($Bytes / 1GB)) }
    if ($Bytes -ge 1MB) { return ('{0:N1} MB' -f ($Bytes / 1MB)) }
    if ($Bytes -ge 1KB) { return ('{0:N0} KB' -f ($Bytes / 1KB)) }
    return ('{0:N0} B' -f $Bytes)
}

function Test-AktClientFolder {
    # The launcher belongs next to metin2client.exe. A folder with the packs
    # but no exe (an antivirus took it) is still a client the update repairs.
    param([Parameter(Mandatory = $true)][string]$Root)
    if (Test-Path -LiteralPath (Join-Path $Root 'metin2client.exe') -PathType Leaf) { return $true }
    return (Test-Path -LiteralPath (Join-Path $Root 'pack') -PathType Container)
}

# ---------------------------------------------------------------- errors

function Test-AktErrorCode {
    param($ErrorRecord, [int[]]$Codes)
    $exception = $ErrorRecord.Exception
    while ($exception) {
        if ($Codes -contains $exception.HResult) { return $true }
        $exception = $exception.InnerException
    }
    return $false
}

function Test-AktAntivirusError {
    # ERROR_VIRUS_INFECTED / ERROR_VIRUS_DELETED, as the existing launcher.
    param($ErrorRecord)
    if (Test-AktErrorCode $ErrorRecord @(-2147024671, -2147024670)) { return $true }
    return ([string]$ErrorRecord.Exception.Message -match 'wirus|virus')
}

function Test-AktInUseError {
    # ERROR_SHARING_VIOLATION / ERROR_LOCK_VIOLATION.
    param($ErrorRecord)
    return (Test-AktErrorCode $ErrorRecord @(-2147024864, -2147024863))
}

function Test-AktAccessDeniedError {
    param($ErrorRecord)
    $exception = $ErrorRecord.Exception
    while ($exception) {
        if ($exception -is [UnauthorizedAccessException]) { return $true }
        if ($exception.HResult -eq -2147024891) { return $true }
        $exception = $exception.InnerException
    }
    return $false
}

function Test-AktDiskFullError {
    # ERROR_DISK_FULL / ERROR_HANDLE_DISK_FULL.
    param($ErrorRecord)
    return (Test-AktErrorCode $ErrorRecord @(-2147024784, -2147024857))
}

function Get-AktErrorMessage {
    # The .NET sentence without PowerShell's 'Exception calling "Move" with
    # "2" argument(s):' wrapper around it.
    param($ErrorRecord)
    $exception = $ErrorRecord.Exception
    while ($exception -is [Management.Automation.MethodInvocationException] -and $exception.InnerException) {
        $exception = $exception.InnerException
    }
    return [string]$exception.Message
}

function Get-AktFileErrorText {
    # One Polish sentence for what went wrong with one file. "Nothing was
    # changed" is only true before or after a complete rollback, which is how
    # every caller uses it.
    param($ErrorRecord, [string]$File)
    $what = if ($File) { " ($File)" } else { '' }
    if (Test-AktAntivirusError $ErrorRecord) {
        return ("Antywirus zablokował plik$what. To fałszywy alarm - dodaj folder klienta do wyjątków " +
            '(Zabezpieczenia Windows > Ochrona przed wirusami i zagrożeniami > Zarządzaj ustawieniami > Wykluczenia) i spróbuj ponownie.')
    }
    if (Test-AktInUseError $ErrorRecord) {
        return "Plik$what jest używany przez inny program. Zamknij grę (sprawdź też w Menedżerze zadań, czy metin2client.exe nie został w tle) i spróbuj ponownie."
    }
    if (Test-AktDiskFullError $ErrorRecord) {
        return "Brak miejsca na dysku$what. Zwolnij miejsce i spróbuj ponownie."
    }
    if (Test-AktAccessDeniedError $ErrorRecord) {
        return ("Brak prawa zapisu$what. Możliwe przyczyny: klient leży w Program Files (przenieś go np. do C:\Gry\Metin2), " +
            'włączona Ochrona folderów przed ransomware w Zabezpieczeniach Windows albo gra jest uruchomiona.')
    }
    return ((Get-AktErrorMessage $ErrorRecord) + $what)
}

# -------------------------------------------------------------- manifest

function ConvertFrom-AktManifestText {
    param([AllowEmptyString()][string]$Text, [string]$Origin = 'manifest')
    # A byte order mark is not JSON and Windows PowerShell refuses it.
    $clean = [string]$Text
    if ($clean.Length -gt 0 -and [int]$clean[0] -eq 0xFEFF) { $clean = $clean.Substring(1) }
    $clean = $clean.Trim()
    if (-not $clean) { throw "Kanał aktualizacji ($Origin) zwrócił pustą odpowiedź." }
    try { $parsed = $clean | ConvertFrom-Json }
    catch { throw "Kanał aktualizacji ($Origin) zwrócił plik, którego nie da się odczytać: $($_.Exception.Message)" }
    if ($null -eq $parsed -or $parsed -is [string] -or $parsed -isnot [psobject]) {
        throw "Kanał aktualizacji ($Origin) zwrócił coś, co nie jest manifestem."
    }
    return $parsed
}

function Get-AktManifest {
    # A local file (tests) or the HTTPS address. For the repository's raw URL
    # the GitHub contents API is asked first: raw.githubusercontent.com caches
    # for five minutes and hands out the previous manifest after a release.
    param([Parameter(Mandatory = $true)][string]$Source, [int]$TimeoutSec = 20)

    if (Test-Path -LiteralPath $Source -PathType Leaf) {
        return ConvertFrom-AktManifestText -Text ([IO.File]::ReadAllText($Source, [Text.Encoding]::UTF8)) -Origin $Source
    }
    $uri = $null
    if (-not [Uri]::TryCreate($Source, [UriKind]::Absolute, [ref]$uri) -or $uri.Scheme -ne 'https') {
        throw 'Adres manifestu musi być adresem HTTPS.'
    }
    Enable-AktTls12
    $headers = @{ 'User-Agent' = 'MT2009-Aktualizator' }

    if ($uri.Host -eq 'raw.githubusercontent.com') {
        $parts = $uri.AbsolutePath.Trim('/') -split '/', 4
        if ($parts.Count -eq 4) {
            $api = 'https://api.github.com/repos/{0}/{1}/contents/{3}?ref={2}' -f $parts[0], $parts[1], $parts[2], $parts[3]
            try {
                $response = Invoke-WebRequest -Uri $api -UseBasicParsing -TimeoutSec ([Math]::Min($TimeoutSec, 10)) `
                    -Headers @{ Accept = 'application/vnd.github.raw+json'; 'User-Agent' = 'MT2009-Aktualizator' }
                # Windows PowerShell 5.1 returns this media type as byte[].
                $content = $response.Content
                $text = if ($content -is [byte[]]) { [Text.Encoding]::UTF8.GetString($content) } else { [string]$content }
                if ($text.TrimStart([char]0xFEFF, ' ', "`r", "`n", "`t").StartsWith('{')) {
                    return ConvertFrom-AktManifestText -Text $text -Origin 'api.github.com'
                }
            }
            catch { }
        }
    }

    try {
        $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec $TimeoutSec -Headers $headers
        $content = $response.Content
        $text = if ($content -is [byte[]]) { [Text.Encoding]::UTF8.GetString($content) } else { [string]$content }
        return ConvertFrom-AktManifestText -Text $text -Origin $uri.Host
    }
    catch {
        $status = 0
        try { if ($null -ne $_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode } } catch { }
        if ($status -eq 403 -or $status -eq 429) {
            throw 'GitHub chwilowo ogranicza liczbę zapytań z Twojego adresu IP. Spróbuj ponownie za kilkanaście minut - możesz grać bez aktualizacji.'
        }
        throw "Nie udało się sprawdzić aktualizacji. Sprawdź połączenie z internetem. Szczegóły: $($_.Exception.Message)"
    }
}

function Get-AktClientComponent {
    # The manifest's "client": version, url, sha256, size. $null when the
    # manifest has none (the channel between releases); a broken one throws.
    param([Parameter(Mandatory = $true)]$Manifest)
    $property = $Manifest.PSObject.Properties['client']
    if (-not $property -or $null -eq $property.Value) { return $null }
    $client = $property.Value

    $get = {
        param($Name)
        $p = $client.PSObject.Properties[$Name]
        if ($p -and $null -ne $p.Value) { return ([string]$p.Value).Trim() }
        return ''
    }
    $version = & $get 'version'
    $url = & $get 'url'
    $sha = (& $get 'sha256').ToUpperInvariant()
    $sizeText = & $get 'size'
    if (-not $version) { return $null }
    if ($version -notmatch '^[0-9A-Za-z._-]{1,32}$') { throw "Manifest podaje nieprawidłową wersję klienta: $version" }
    if ($sha -notmatch '^[A-F0-9]{64}$') { throw 'Manifest nie zawiera poprawnej sumy SHA-256 aktualizacji klienta.' }
    $isLocal = $url -and (Test-Path -LiteralPath $url -PathType Leaf)
    $uri = $null
    if (-not $isLocal -and (-not [Uri]::TryCreate($url, [UriKind]::Absolute, [ref]$uri) -or $uri.Scheme -ne 'https')) {
        throw 'Manifest nie zawiera poprawnego adresu HTTPS aktualizacji klienta.'
    }
    [long]$size = 0
    if ($sizeText -and -not [long]::TryParse($sizeText, [ref]$size)) { $size = 0 }

    $message = ''
    $statusProperty = $Manifest.PSObject.Properties['statusMessage']
    if ($statusProperty -and $statusProperty.Value) { $message = [string]$statusProperty.Value }

    return [pscustomobject]@{
        Version = $version
        Url = $url
        Sha256 = $sha
        Size = $size
        Message = $message
    }
}

# --------------------------------------------------------------- version

function Get-AktInstalledVersion {
    param([Parameter(Mandatory = $true)][string]$Root)
    $path = Join-Path $Root $script:VersionFileName
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return '' }
    try {
        $text = ([IO.File]::ReadAllText($path)).Trim().TrimStart([char]0xFEFF)
        $first = @($text -split "`r?`n")[0].Trim()
        if ($first -match '^[0-9A-Za-z._-]{1,32}$') { return $first }
    }
    catch { }
    return ''
}

function Set-AktInstalledVersion {
    param([Parameter(Mandatory = $true)][string]$Root, [Parameter(Mandatory = $true)][string]$Version)
    [IO.File]::WriteAllText((Join-Path $Root $script:VersionFileName), $Version + "`r`n", [Text.Encoding]::ASCII)
}

function Compare-AktVersion {
    # -1, 0 or 1. Dotted numbers compare as numbers (2.0.9 < 2.0.28); anything
    # else compares as text.
    param([string]$A, [string]$B)
    $va = $null; $vb = $null
    if ([Version]::TryParse($A, [ref]$va) -and [Version]::TryParse($B, [ref]$vb)) {
        return $va.CompareTo($vb)
    }
    return [Math]::Sign([string]::Compare($A, $B, [StringComparison]::OrdinalIgnoreCase))
}

function Test-AktUpdateNeeded {
    # An unknown installed version counts as old: better one download too many
    # than a client that cannot log in. A newer one installed (a test build)
    # is not "downgraded".
    param([AllowEmptyString()][string]$Installed, [AllowEmptyString()][string]$Available)
    if (-not $Available) { return $false }
    if (-not $Installed) { return $true }
    return ((Compare-AktVersion $Installed $Available) -lt 0)
}

# ------------------------------------------------------------ file list

function Get-AktClientFileList {
    # client-files.json, validated: {"version": "...", "files": [{path, size,
    # sha256}]}. Throws when missing or broken - the caller falls back to
    # comparing CLIENT_VERSION alone.
    param([Parameter(Mandatory = $true)][string]$Source)
    $list = Get-AktManifest -Source $Source -TimeoutSec 15
    $versionProperty = $list.PSObject.Properties['version']
    $filesProperty = $list.PSObject.Properties['files']
    if (-not $versionProperty -or -not $filesProperty) { throw 'Lista plików klienta nie ma pól version/files.' }
    $version = ([string]$versionProperty.Value).Trim()
    if ($version -notmatch '^[0-9A-Za-z._-]{1,32}$') { throw 'Lista plików klienta ma nieprawidłową wersję.' }
    $files = @()
    foreach ($entry in @($filesProperty.Value)) {
        if ($null -eq $entry) { continue }
        $path = [string]$entry.PSObject.Properties['path'].Value
        $sha = ([string]$entry.PSObject.Properties['sha256'].Value).ToUpperInvariant()
        [long]$size = -1
        if (-not [long]::TryParse([string]$entry.PSObject.Properties['size'].Value, [ref]$size)) { $size = -1 }
        if (-not $path -or $sha -notmatch '^[A-F0-9]{64}$' -or $size -lt 0) { throw "Lista plików klienta ma błędny wpis: $path" }
        $relative = Get-AktRelativeEntryPath -EntryName $path
        $files += [pscustomobject]@{ Path = $path; Relative = $relative; Size = $size; Sha256 = $sha }
    }
    if ($files.Count -eq 0) { throw 'Lista plików klienta jest pusta.' }
    return [pscustomobject]@{ Version = $version; Files = $files }
}

function Get-AktFileHashFast {
    param([Parameter(Mandatory = $true)][string]$Path)
    $sha = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
    try { return (([BitConverter]::ToString($sha.ComputeHash($stream))) -replace '-', '') }
    finally { $stream.Dispose(); $sha.Dispose() }
}

function Test-AktClientFiles {
    # Compares the listed files with the folder: size first, then SHA-256.
    # Returns the paths that are missing or different.
    param([Parameter(Mandatory = $true)][string]$Root, [Parameter(Mandatory = $true)]$FileList)
    $different = @()
    foreach ($file in $FileList.Files) {
        $local = Join-Path $Root $file.Relative
        $same = $false
        try {
            if (Test-Path -LiteralPath $local -PathType Leaf) {
                if ((Get-Item -LiteralPath $local -Force).Length -eq $file.Size) {
                    $same = ((Get-AktFileHashFast -Path $local) -eq $file.Sha256)
                }
            }
        }
        catch { $same = $false }
        if (-not $same) { $different += $file.Path }
    }
    return [pscustomobject]@{ Checked = @($FileList.Files).Count; Different = $different }
}

function Get-AktClientState {
    # Whether this folder needs the published client. With a file list of the
    # same version as the manifest, the files decide (and a matching folder
    # gets its CLIENT_VERSION written); otherwise CLIENT_VERSION alone does.
    # A newer CLIENT_VERSION (a test build) is left alone either way.
    param([Parameter(Mandatory = $true)][string]$Root, [Parameter(Mandatory = $true)]$Component, $FileList = $null)
    $installed = Get-AktInstalledVersion -Root $Root
    $state = [pscustomobject]@{
        Installed = $installed
        Available = $Component.Version
        UpdateNeeded = (Test-AktUpdateNeeded -Installed $installed -Available $Component.Version)
        ByFiles = $false
        Checked = 0
        Different = @()
        VersionWritten = $false
    }
    if ($null -eq $FileList -or $FileList.Version -ne $Component.Version) { return $state }
    if ($installed -and (Compare-AktVersion $installed $Component.Version) -gt 0) { return $state }
    $check = Test-AktClientFiles -Root $Root -FileList $FileList
    $state.ByFiles = $true
    $state.Checked = $check.Checked
    $state.Different = @($check.Different)
    if ($state.Different.Count -eq 0) {
        $state.UpdateNeeded = $false
        if ($installed -ne $Component.Version) {
            try {
                Set-AktInstalledVersion -Root $Root -Version $Component.Version
                $state.VersionWritten = $true
                Write-AktLog $Root "Pliki klienta zgodne z wydaniem $($Component.Version) - zapisano CLIENT_VERSION."
            }
            catch { }
            $state.Installed = $Component.Version
        }
    }
    else {
        $state.UpdateNeeded = $true
    }
    return $state
}

# ------------------------------------------------------------- processes

function Get-AktGameProcesses {
    # Programs started from the client folder, and every metin2client whose
    # path cannot be read (a game started as administrator): better to ask
    # once too often than to fail on a locked pack after the download.
    param([Parameter(Mandatory = $true)][string]$Root)
    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd($script:Sep) + $script:Sep
    $found = @()
    foreach ($process in @(Get-Process -ErrorAction SilentlyContinue)) {
        if ($process.Id -eq $PID) { continue }
        $path = $null
        try { $path = $process.Path } catch { }
        if ($path) {
            if ($path.StartsWith($rootFull, [StringComparison]::OrdinalIgnoreCase)) { $found += $process }
        }
        elseif ($process.ProcessName -like 'metin2client*') {
            $found += $process
        }
    }
    return $found
}

function Stop-AktGameProcesses {
    # Closes the game politely, then kills what is left after ten seconds.
    param([Parameter(Mandatory = $true)][string]$Root)
    foreach ($process in @(Get-AktGameProcesses -Root $Root)) {
        try { [void]$process.CloseMainWindow() } catch { }
    }
    $deadline = (Get-Date).AddSeconds(10)
    while ((Get-Date) -lt $deadline -and @(Get-AktGameProcesses -Root $Root).Count -gt 0) {
        Start-Sleep -Milliseconds 300
    }
    foreach ($process in @(Get-AktGameProcesses -Root $Root)) {
        try { $process.Kill(); [void]$process.WaitForExit(5000) } catch { }
    }
    return (@(Get-AktGameProcesses -Root $Root).Count -eq 0)
}

# -------------------------------------------------------------- download

function Receive-AktFile {
    # One attempt: streams the file to disk and computes its SHA-256 on the
    # way, so a 150 MB package is not read a second time. Returns the hash.
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [long]$ExpectedSize = 0,
        [scriptblock]$OnProgress = {}
    )
    $sha = [Security.Cryptography.SHA256]::Create()
    $response = $null; $inStream = $null; $output = $null
    try {
        [long]$total = 0
        if (Test-Path -LiteralPath $Source -PathType Leaf) {
            $inStream = [IO.File]::OpenRead($Source)
            $total = $inStream.Length
        }
        else {
            $request = [Net.HttpWebRequest]::Create($Source)
            $request.UserAgent = 'MT2009-Aktualizator'
            $request.AllowAutoRedirect = $true
            $request.Timeout = 30000
            $request.ReadWriteTimeout = 60000
            $response = $request.GetResponse()
            $total = $response.ContentLength
            $inStream = $response.GetResponseStream()
        }
        if ($total -le 0) { $total = $ExpectedSize }

        $output = [IO.File]::Open($Destination, [IO.FileMode]::Create, [IO.FileAccess]::Write, [IO.FileShare]::None)
        $buffer = New-Object byte[] 262144
        [long]$done = 0
        $tick = [Diagnostics.Stopwatch]::StartNew()
        while (($read = $inStream.Read($buffer, 0, $buffer.Length)) -gt 0) {
            $output.Write($buffer, 0, $read)
            [void]$sha.TransformBlock($buffer, 0, $read, $null, 0)
            $done += $read
            if ($tick.ElapsedMilliseconds -ge 120) {
                $null = & $OnProgress 'download' $done $total
                $tick.Restart()
                if ($script:CancelRequested) { throw 'Anulowano pobieranie.' }
            }
        }
        [void]$sha.TransformFinalBlock($buffer, 0, 0)
        $null = & $OnProgress 'download' $done $total
        return (([BitConverter]::ToString($sha.Hash)) -replace '-', '')
    }
    finally {
        if ($output) { $output.Dispose() }
        if ($inStream) { $inStream.Dispose() }
        if ($response) { $response.Close() }
        $sha.Dispose()
    }
}

function Invoke-AktDownload {
    # Three attempts, five seconds apart, as the full launcher: GitHub release
    # assets answer 500 or drop the connection now and then and serve the
    # same file a minute later. An antivirus block or a cancel is final.
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [long]$ExpectedSize = 0,
        [scriptblock]$OnProgress = {},
        [int]$Attempts = 3,
        [int]$RetryDelaySec = 5
    )
    Enable-AktTls12
    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try {
            return (Receive-AktFile -Source $Source -Destination $Destination -ExpectedSize $ExpectedSize -OnProgress $OnProgress)
        }
        catch {
            $failure = $_
            Remove-Item -LiteralPath $Destination -Force -ErrorAction SilentlyContinue
            if ($script:CancelRequested) { throw 'Anulowano pobieranie. Nic nie zostało zmienione.' }
            if (Test-AktAntivirusError $failure) { throw (Get-AktFileErrorText $failure 'pobierany plik') }
            if ($attempt -ge $Attempts) {
                throw ("Nie udało się pobrać aktualizacji (próby: $Attempts). Nic nie zostało zmienione. Szczegóły: " + (Get-AktErrorMessage $failure))
            }
            $null = & $OnProgress 'retry' $attempt $Attempts
            $wait = [Diagnostics.Stopwatch]::StartNew()
            while ($wait.Elapsed.TotalSeconds -lt $RetryDelaySec) {
                $null = & $OnProgress 'wait' $attempt $Attempts
                Start-Sleep -Milliseconds 100
                if ($script:CancelRequested) { throw 'Anulowano pobieranie. Nic nie zostało zmienione.' }
            }
        }
    }
}

# ----------------------------------------------------------- zip, apply

function Get-AktRelativeEntryPath {
    # The zip entry as a path below the client folder, or an exception for
    # anything that would leave it (absolute paths, "..", drive letters).
    param([Parameter(Mandatory = $true)][string]$EntryName)
    $relative = $EntryName.Replace('\', '/').TrimStart('/')
    if (-not $relative) { return '' }
    $segments = $relative.Split('/')
    foreach ($segment in $segments) {
        if ($segment -eq '..' -or $segment -match ':') { throw "Niedozwolona ścieżka w paczce: $EntryName" }
    }
    return ($segments -join $script:Sep)
}

function Test-AktKeepIfPresent {
    param([Parameter(Mandatory = $true)][string]$Relative)
    $unified = $Relative.Replace('\', '/')
    if (-not $unified.Contains('/')) {
        foreach ($name in $script:KeepIfPresentFiles) {
            if ($unified.Equals($name, [StringComparison]::OrdinalIgnoreCase)) { return $true }
        }
    }
    foreach ($dir in $script:KeepIfPresentDirs) {
        if ($unified.StartsWith($dir + '/', [StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    return $false
}

function Test-AktNeverWrite {
    param([Parameter(Mandatory = $true)][string]$Relative)
    $first = $Relative.Replace('\', '/').Split('/')[0]
    foreach ($name in $script:NeverWrite) {
        if ($first.Equals($name, [StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    return $false
}

function Expand-AktZip {
    # Unpacks into the staging folder, entry by entry, so an antivirus block
    # names its file and the progress bar moves.
    param(
        [Parameter(Mandatory = $true)][string]$ArchivePath,
        [Parameter(Mandatory = $true)][string]$Destination,
        [scriptblock]$OnProgress = {}
    )
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    $root = [IO.Path]::GetFullPath($Destination).TrimEnd($script:Sep) + $script:Sep
    $archive = [IO.Compression.ZipFile]::OpenRead($ArchivePath)
    try {
        [long]$total = 0
        foreach ($entry in $archive.Entries) { $total += $entry.Length }
        [long]$done = 0
        $buffer = New-Object byte[] 262144
        $tick = [Diagnostics.Stopwatch]::StartNew()
        foreach ($entry in $archive.Entries) {
            $relative = Get-AktRelativeEntryPath -EntryName $entry.FullName
            if (-not $relative) { continue }
            $target = [IO.Path]::GetFullPath((Join-Path $root $relative))
            if (-not $target.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
                throw "Plik w paczce wychodzi poza folder klienta: $($entry.FullName)"
            }
            if (-not $entry.Name) {
                New-Item -ItemType Directory -Path $target -Force | Out-Null
                continue
            }
            New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
            $in = $entry.Open()
            try {
                try {
                    $out = [IO.File]::Open($target, [IO.FileMode]::Create, [IO.FileAccess]::Write, [IO.FileShare]::None)
                    try {
                        while (($read = $in.Read($buffer, 0, $buffer.Length)) -gt 0) {
                            $out.Write($buffer, 0, $read)
                            $done += $read
                            if ($tick.ElapsedMilliseconds -ge 120) {
                                $null = & $OnProgress 'extract' $done $total
                                $tick.Restart()
                            }
                        }
                    }
                    finally { $out.Dispose() }
                }
                catch { throw (Get-AktFileErrorText $_ $entry.FullName) }
            }
            finally { $in.Dispose() }
        }
        $null = & $OnProgress 'extract' $total $total
    }
    finally { $archive.Dispose() }
}

function Clear-AktStaging {
    # What an interrupted update left behind. The version file is written only
    # after a complete update, so a half-applied one is offered again and the
    # next run finishes it - the leftovers are not needed for that.
    param([Parameter(Mandatory = $true)][string]$Root)
    $staging = Join-Path $Root $script:StagingName
    if (Test-Path -LiteralPath $staging) {
        Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue
    }
    return (-not (Test-Path -LiteralPath $staging))
}

function Get-AktFreeSpace {
    param([Parameter(Mandatory = $true)][string]$Root)
    try {
        $drive = New-Object IO.DriveInfo ([IO.Path]::GetPathRoot([IO.Path]::GetFullPath($Root)))
        return [long]$drive.AvailableFreeSpace
    }
    catch { return [long]-1 }
}

function Install-AktClientUpdate {
    # The whole update: download into <client>\MT2009-Aktualizator.tmp, check
    # the size and SHA-256, unpack there, then move each file into place with
    # the old one moved aside first (same disk, so instant). Any failure
    # moves every replaced file back. The version file is written last.
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)]$Component,
        [scriptblock]$OnProgress = {},
        [int]$RetryDelaySec = 5
    )
    $root = [IO.Path]::GetFullPath($Root).TrimEnd($script:Sep)
    $script:CancelRequested = $false
    Write-AktLog $root "Aktualizacja do $($Component.Version): $($Component.Url)"

    [void](Clear-AktStaging -Root $root)
    $staging = Join-Path $root $script:StagingName
    try { New-Item -ItemType Directory -Path $staging -Force | Out-Null }
    catch { throw (Get-AktFileErrorText $_ $root) }

    try {
        # Disk space: the zip plus its unpacked copy, roughly 2.3x the zip.
        if ($Component.Size -gt 0) {
            $free = Get-AktFreeSpace -Root $root
            $need = [long]($Component.Size * 2.3) + 50MB
            if ($free -ge 0 -and $free -lt $need) {
                throw ("Za mało miejsca na dysku: potrzeba około {0}, wolne {1}. Zwolnij miejsce i spróbuj ponownie." -f (Format-AktSize $need), (Format-AktSize $free))
            }
        }

        $zip = Join-Path $staging 'aktualizacja.zip'
        $hash = Invoke-AktDownload -Source $Component.Url -Destination $zip -ExpectedSize $Component.Size `
            -OnProgress $OnProgress -RetryDelaySec $RetryDelaySec
        $null = & $OnProgress 'verify' 0 0
        $length = (Get-Item -LiteralPath $zip).Length
        if ($Component.Size -gt 0 -and $length -ne $Component.Size) {
            throw ("Pobrany plik ma zły rozmiar ({0} zamiast {1} bajtów) - połączenie zostało przerwane. Nic nie zostało zmienione, spróbuj ponownie." -f $length, $Component.Size)
        }
        if ($hash -ne $Component.Sha256) {
            throw "Suma kontrolna SHA-256 pobranego pliku się nie zgadza (oczekiwano $($Component.Sha256), jest $hash). Nic nie zostało zmienione, spróbuj ponownie."
        }
        Write-AktLog $root "Pobrano $length B, SHA-256 zgodne."

        $expanded = Join-Path $staging 'nowe'
        Expand-AktZip -ArchivePath $zip -Destination $expanded -OnProgress $OnProgress
        Remove-Item -LiteralPath $zip -Force

        $expandedRoot = [IO.Path]::GetFullPath($expanded).TrimEnd($script:Sep)
        $files = @(Get-ChildItem -LiteralPath $expandedRoot -Recurse -File -Force)
        if ($files.Count -eq 0) { throw 'Paczka aktualizacji jest pusta.' }

        $changes = New-Object System.Collections.ArrayList
        $kept = New-Object System.Collections.ArrayList
        $selfUpdated = $false
        foreach ($file in $files) {
            $relative = $file.FullName.Substring($expandedRoot.Length).TrimStart($script:Sep)
            if (Test-AktNeverWrite $relative) { continue }
            $destination = [IO.Path]::GetFullPath((Join-Path $root $relative))
            if (-not $destination.StartsWith($root + $script:Sep, [StringComparison]::OrdinalIgnoreCase)) {
                throw "Niedozwolona ścieżka w paczce: $relative"
            }
            $exists = Test-Path -LiteralPath $destination -PathType Leaf
            if ($exists -and (Test-AktKeepIfPresent $relative)) {
                [void]$kept.Add($relative)
                continue
            }
            if ($relative.StartsWith($script:LauncherFilePrefix, [StringComparison]::OrdinalIgnoreCase)) { $selfUpdated = $true }
            [void]$changes.Add([pscustomobject]@{
                Relative = $relative
                Source = $file.FullName
                Destination = $destination
                Backup = (Join-Path (Join-Path $staging 'kopia') $relative)
                Existed = $exists
            })
        }

        # The game may have been started while the package downloaded.
        $running = @(Get-AktGameProcesses -Root $root)
        if ($running.Count -gt 0) {
            throw ("Gra jest uruchomiona ({0}). Zamknij ją i kliknij Aktualizuj jeszcze raz - pobieranie trzeba będzie powtórzyć." -f (($running | ForEach-Object { $_.ProcessName } | Select-Object -Unique) -join ', '))
        }

        $applied = New-Object System.Collections.ArrayList
        $index = 0
        try {
            foreach ($change in $changes) {
                $index++
                $null = & $OnProgress 'apply' $index $changes.Count
                try {
                    New-Item -ItemType Directory -Path (Split-Path -Parent $change.Destination) -Force | Out-Null
                    if ($change.Existed) {
                        New-Item -ItemType Directory -Path (Split-Path -Parent $change.Backup) -Force | Out-Null
                        [IO.File]::Move($change.Destination, $change.Backup)
                    }
                    [void]$applied.Add($change)
                    [IO.File]::Move($change.Source, $change.Destination)
                }
                catch { throw (Get-AktFileErrorText $_ $change.Relative) }
            }
        }
        catch {
            $reason = $_
            Write-AktLog $root ("Błąd przy podmianie plików, wycofuję: " + $reason.Exception.Message)
            for ($i = $applied.Count - 1; $i -ge 0; $i--) {
                $change = $applied[$i]
                try {
                    if (Test-Path -LiteralPath $change.Destination -PathType Leaf) {
                        if ($change.Existed -and -not (Test-Path -LiteralPath $change.Backup -PathType Leaf)) { continue }
                        Remove-Item -LiteralPath $change.Destination -Force
                    }
                    if ($change.Existed -and (Test-Path -LiteralPath $change.Backup -PathType Leaf)) {
                        [IO.File]::Move($change.Backup, $change.Destination)
                    }
                }
                catch { Write-AktLog $root ("Nie udało się przywrócić " + $change.Relative + ": " + $_.Exception.Message) }
            }
            throw ([string]$reason.Exception.Message + ' Poprzednie pliki zostały przywrócone.')
        }

        Set-AktInstalledVersion -Root $root -Version $Component.Version
        Write-AktLog $root ("Zaktualizowano do {0}: plików {1}, pozostawione pliki gracza: {2}" -f $Component.Version, $changes.Count, ($(if ($kept.Count) { $kept -join ', ' } else { '-' })))
        return [pscustomobject]@{
            Version = $Component.Version
            Files = $changes.Count
            Kept = @($kept)
            SelfUpdated = $selfUpdated
            Sha256 = $hash
        }
    }
    finally {
        [void](Clear-AktStaging -Root $root)
    }
}

# ------------------------------------------------------ coop.cfg (serwery)

function Get-AktCoopPath {
    param([Parameter(Mandatory = $true)][string]$Root, [ValidateSet(1, 2)][int]$Slot)
    if ($Slot -eq 1) { return (Join-Path $Root 'coop.cfg') }
    return (Join-Path $Root 'coop2.cfg')
}

function ConvertTo-AktAsciiName {
    # Polish letters to their plain forms, other accents dropped, then plain
    # printable ASCII only - the client shows the name as bytes.
    param([AllowEmptyString()][string]$Text)
    $pairs = @(
        @(0x0105, 'a'), @(0x0104, 'A'), @(0x0107, 'c'), @(0x0106, 'C'), @(0x0119, 'e'), @(0x0118, 'E'),
        @(0x0142, 'l'), @(0x0141, 'L'), @(0x0144, 'n'), @(0x0143, 'N'), @(0x00F3, 'o'), @(0x00D3, 'O'),
        @(0x015B, 's'), @(0x015A, 'S'), @(0x017A, 'z'), @(0x0179, 'Z'), @(0x017C, 'z'), @(0x017B, 'Z')
    )
    foreach ($pair in $pairs) { $Text = $Text.Replace([string][char]$pair[0], $pair[1]) }
    $decomposed = $Text.Normalize([Text.NormalizationForm]::FormD)
    $builder = New-Object Text.StringBuilder
    foreach ($char in $decomposed.ToCharArray()) {
        if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($char) -eq [Globalization.UnicodeCategory]::NonSpacingMark) { continue }
        $code = [int]$char
        if ($code -ge 32 -and $code -le 126) { [void]$builder.Append($char) }
    }
    $name = $builder.ToString().Replace('=', '-').Trim()
    $name = [Text.RegularExpressions.Regex]::Replace($name, ' {2,}', ' ')
    if ($name.Length -gt 80) { $name = $name.Substring(0, 80).Trim() }
    return $name
}

function Test-AktCoopHost {
    # The client's own check (serverinfo.py __IsValidCoopHost).
    param([AllowEmptyString()][string]$HostName)
    if ([string]::IsNullOrWhiteSpace($HostName) -or $HostName.Length -gt 253) { return $false }
    if ($HostName -notmatch '^[A-Za-z0-9.-]+$') { return $false }
    if ($HostName -match '^[0-9.]+$') {
        $parts = $HostName.Split('.')
        if ($parts.Count -ne 4) { return $false }
        foreach ($part in $parts) {
            if ($part -notmatch '^\d{1,3}$' -or [int]$part -gt 255) { return $false }
        }
        return $true
    }
    foreach ($label in $HostName.Split('.')) {
        if ($label.Length -lt 1 -or $label.Length -gt 63 -or $label -notmatch '^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?$') { return $false }
    }
    return $true
}

function ConvertTo-AktCoopHost {
    # What people paste: "http://1.2.3.4/", " 1.2.3.4 ", a domain. Returns the
    # bare host or throws a sentence that says what to type.
    param([AllowEmptyString()][string]$Text)
    $value = ([string]$Text).Trim()
    if (-not $value) { throw 'Wpisz IP albo domenę serwera VPS.' }
    if ($value -match '^(?i)https?://') {
        $uri = $null
        if (-not [Uri]::TryCreate($value, [UriKind]::Absolute, [ref]$uri)) { throw 'Nieprawidłowe IP lub domena.' }
        if (-not $uri.IsDefaultPort -or ($uri.AbsolutePath -ne '/' -and $uri.AbsolutePath -ne '')) {
            throw 'Wpisz samo IP albo domenę - bez portu i ścieżki.'
        }
        $value = $uri.Host
    }
    $value = $value.TrimEnd('/')
    if ($value -match '^[^:]+:\d+$') { throw 'Wpisz samo IP, bez portu (porty są w polach poniżej).' }
    if (-not (Test-AktCoopHost $value)) {
        if ($value -match '^[0-9.]+$') { throw 'Nieprawidłowy adres IPv4 (cztery liczby 0-255 oddzielone kropkami, np. 203.0.113.10).' }
        throw 'Nieprawidłowe IP lub nazwa domeny (dozwolone: litery bez polskich znaków, cyfry, kropki i myślniki).'
    }
    return $value
}

function ConvertTo-AktPort {
    param([AllowEmptyString()][string]$Text, [string]$Label)
    $value = 0
    if (-not [int]::TryParse(([string]$Text).Trim(), [ref]$value) -or $value -lt 1 -or $value -gt 65535) {
        throw "$Label musi być liczbą od 1 do 65535."
    }
    return $value
}

function New-AktCoopConfig {
    # Validates everything and returns the file text (ASCII, CRLF) with the
    # values as they will be saved. Throws a Polish sentence on bad input.
    param(
        [AllowEmptyString()][string]$Name,
        [AllowEmptyString()][string]$HostName,
        [AllowEmptyString()][string]$Auth = '11000',
        [AllowEmptyString()][string]$Channel = '13000',
        [AllowEmptyString()][string]$Channels = '2'
    )
    if ([string]::IsNullOrWhiteSpace($Name)) { throw 'Wpisz nazwę serwera.' }
    $cleanName = ConvertTo-AktAsciiName $Name
    if (-not $cleanName) { throw 'Nazwa serwera nie zawiera żadnych obsługiwanych znaków (użyj liter, cyfr i spacji).' }
    $cleanHost = ConvertTo-AktCoopHost $HostName
    $authPort = ConvertTo-AktPort $Auth 'Port logowania'
    $channelPort = ConvertTo-AktPort $Channel 'Port kanału 1'
    $count = 0
    if (-not [int]::TryParse(([string]$Channels).Trim(), [ref]$count) -or $count -lt 1 -or $count -gt 2) {
        throw 'Liczba kanałów musi wynosić 1 albo 2.'
    }
    if ($channelPort + ($count - 1) * 10 -gt 65535) {
        throw ("Port kanału 2 wyniósłby {0} (kanał 1 + 10), a maksimum to 65535. Zmniejsz port kanału 1 albo wybierz 1 kanał." -f ($channelPort + 10))
    }
    $channelPorts = @($channelPort)
    if ($count -eq 2) { $channelPorts += ($channelPort + 10) }
    if ($channelPorts -contains $authPort) {
        throw ("Port logowania ({0}) nie może być taki sam jak port kanału ({1})." -f $authPort, ($channelPorts -join ' / '))
    }
    $text = @(
        '# MT2009 PLUS - serwer VPS (zapisane przez MT2009-Aktualizator)'
        ('name=' + $cleanName)
        ('host=' + $cleanHost)
        ('auth=' + $authPort)
        ('channel=' + $channelPort)
        ('channels=' + $count)
        ''
    ) -join "`r`n"
    return [pscustomobject]@{
        Name = $cleanName
        Host = $cleanHost
        Auth = $authPort
        Channel = $channelPort
        Channels = $count
        Text = $text
    }
}

function Read-AktCoopConfig {
    # $null when the slot is empty; Valid = $false when the file is there but
    # the client would ignore it. The same rules as serverinfo.py.
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $result = [pscustomobject]@{ Valid = $false; Name = ''; Host = ''; Auth = 11000; Channel = 13000; Channels = 2 }
    try {
        $bytes = [IO.File]::ReadAllBytes($Path)
        if ($bytes.Length -gt 8192) { return $result }
        $settings = @{}
        foreach ($raw in ([Text.Encoding]::GetEncoding(28591).GetString($bytes) -split "`r`n|`n|`r")) {
            $line = $raw.Trim()
            if (-not $line -or $line.StartsWith('#')) { continue }
            $at = $line.IndexOf('=')
            if ($at -lt 0) { return $result }
            $key = $line.Substring(0, $at).Trim().ToLowerInvariant()
            if (-not $key -or $settings.ContainsKey($key)) { return $result }
            $settings[$key] = $line.Substring($at + 1).Trim()
        }
        foreach ($key in @('name', 'host')) {
            if ($settings.ContainsKey($key)) { $result.$key = $settings[$key] }
        }
        foreach ($key in @('name', 'host', 'auth', 'channel', 'channels')) {
            if (-not $settings.ContainsKey($key) -or -not $settings[$key]) { return $result }
        }
        $auth = 0; $channel = 0; $channels = 0
        if (-not [int]::TryParse($settings['auth'], [ref]$auth) -or -not [int]::TryParse($settings['channel'], [ref]$channel) -or
            -not [int]::TryParse($settings['channels'], [ref]$channels)) { return $result }
        $result.Auth = $auth; $result.Channel = $channel; $result.Channels = $channels
        if (-not (Test-AktCoopHost $settings['host'])) { return $result }
        if ($auth -lt 1 -or $auth -gt 65535 -or $channel -lt 1 -or $channel -gt 65535) { return $result }
        if ($channels -lt 1 -or $channels -gt 2 -or $channel + ($channels - 1) * 10 -gt 65535) { return $result }
        $result.Valid = $true
    }
    catch { }
    return $result
}

function Save-AktCoopConfig {
    param([Parameter(Mandatory = $true)][string]$Root, [ValidateSet(1, 2)][int]$Slot, [Parameter(Mandatory = $true)]$Config)
    $path = Get-AktCoopPath -Root $Root -Slot $Slot
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        try { (Get-Item -LiteralPath $path -Force).Attributes = [IO.FileAttributes]::Normal } catch { }
    }
    [IO.File]::WriteAllText($path, $Config.Text, [Text.Encoding]::ASCII)
    Write-AktLog $Root ("Zapisano {0}: {1} {2} auth={3} channel={4} channels={5}" -f [IO.Path]::GetFileName($path), $Config.Name, $Config.Host, $Config.Auth, $Config.Channel, $Config.Channels)
    return $path
}

function Remove-AktCoopConfig {
    param([Parameter(Mandatory = $true)][string]$Root, [ValidateSet(1, 2)][int]$Slot)
    $path = Get-AktCoopPath -Root $Root -Slot $Slot
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        Remove-Item -LiteralPath $path -Force
        Write-AktLog $Root ("Usunięto " + [IO.Path]::GetFileName($path))
    }
}

if ($TylkoFunkcje) { return }

# ================================================================== OKNO

$script:Root = $PSScriptRoot
if (-not $script:Root) { $script:Root = Split-Path -Parent $MyInvocation.MyCommand.Path }
$script:Root = [IO.Path]::GetFullPath($script:Root).TrimEnd('\')

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[Windows.Forms.Application]::EnableVisualStyles()

$script:Title = 'MT2009 PLUS - aktualizator klienta'

function Show-AktMessage {
    param([string]$Text, [string]$Icon = 'Information', [string]$Buttons = 'OK')
    return [Windows.Forms.MessageBox]::Show($Text, $script:Title,
        [Windows.Forms.MessageBoxButtons]::$Buttons, [Windows.Forms.MessageBoxIcon]::$Icon)
}

# One window per client folder: two updaters moving the same files would
# break both updates.
$mutexName = 'Local\MT2009-Aktualizator-' + ([BitConverter]::ToString(
        [Security.Cryptography.SHA1]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($script:Root.ToLowerInvariant()))) -replace '-', '')
$createdNew = $false
$script:Mutex = [Threading.Mutex]::new($true, $mutexName, [ref]$createdNew)
if (-not $createdNew) {
    [void](Show-AktMessage 'Aktualizator jest już otwarty dla tego folderu klienta.' 'Warning')
    exit 0
}

if (-not (Test-AktClientFolder -Root $script:Root)) {
    [void](Show-AktMessage ("Aktualizator musi leżeć w folderze klienta gry, obok metin2client.exe.`r`n`r`nTeraz jest w:`r`n$($script:Root)`r`n`r`nSkopiuj pliki MT2009-Aktualizator.* do folderu klienta i uruchom go stamtąd.") 'Warning')
    exit 1
}

Write-AktLog $script:Root "Start aktualizatora $($script:AktVersion)"

# Colours and fonts.
$colorGold = [Drawing.Color]::FromArgb(232, 193, 112)
$colorText = [Drawing.Color]::FromArgb(240, 232, 220)
$colorDim = [Drawing.Color]::FromArgb(190, 178, 160)
$colorPanel = [Drawing.Color]::FromArgb(24, 17, 13)
$colorField = [Drawing.Color]::FromArgb(40, 30, 24)
$fontNormal = New-Object Drawing.Font('Segoe UI', 9.5)
$fontBold = New-Object Drawing.Font('Segoe UI', 11, [Drawing.FontStyle]::Bold)
$fontButton = New-Object Drawing.Font('Segoe UI', 10, [Drawing.FontStyle]::Bold)
$fontPlay = New-Object Drawing.Font('Segoe UI', 15, [Drawing.FontStyle]::Bold)
$fontSmall = New-Object Drawing.Font('Segoe UI', 8.5)

function New-AktButton {
    param([string]$Text, [int]$X, [int]$Y, [int]$W, [int]$H, [Drawing.Color]$Back, [Drawing.Color]$Fore, $Font)
    $button = New-Object Windows.Forms.Button
    $button.Text = $Text
    $button.SetBounds($X, $Y, $W, $H)
    $button.FlatStyle = [Windows.Forms.FlatStyle]::Flat
    $button.FlatAppearance.BorderColor = $colorGold
    $button.FlatAppearance.BorderSize = 1
    $button.BackColor = $Back
    $button.ForeColor = $Fore
    $button.Font = $Font
    $button.Cursor = [Windows.Forms.Cursors]::Hand
    $button.UseVisualStyleBackColor = $false
    return $button
}

function New-AktLabel {
    param([string]$Text, [int]$X, [int]$Y, [int]$W, [int]$H, $Font, [Drawing.Color]$Color)
    $label = New-Object Windows.Forms.Label
    $label.Text = $Text
    $label.SetBounds($X, $Y, $W, $H)
    $label.Font = $Font
    $label.ForeColor = $Color
    $label.BackColor = [Drawing.Color]::Transparent
    return $label
}

# ---------------------------------------------------------- main window

$form = New-Object Windows.Forms.Form
$form.Text = $script:Title
$form.ClientSize = New-Object Drawing.Size(880, 495)
$form.FormBorderStyle = [Windows.Forms.FormBorderStyle]::FixedSingle
$form.MaximizeBox = $false
$form.StartPosition = [Windows.Forms.FormStartPosition]::CenterScreen
$form.BackColor = [Drawing.Color]::FromArgb(18, 13, 11)
$form.AutoScaleDimensions = New-Object Drawing.SizeF(96, 96)
$form.AutoScaleMode = [Windows.Forms.AutoScaleMode]::Dpi
try {
    $exe = Join-Path $script:Root 'metin2client.exe'
    if (Test-Path -LiteralPath $exe -PathType Leaf) { $form.Icon = [Drawing.Icon]::ExtractAssociatedIcon($exe) }
}
catch { }

# The picture is read into memory (the file stays free for the update to
# replace) and, once the window has its final size on this screen's DPI,
# scaled once to it, so painting the transparent labels stays cheap.
$script:Picture = $null
$picturePath = Join-Path $script:Root 'MT2009-Aktualizator.jpg'
if (Test-Path -LiteralPath $picturePath -PathType Leaf) {
    try {
        $script:PictureStream = New-Object IO.MemoryStream(, [IO.File]::ReadAllBytes($picturePath))
        $script:Picture = [Drawing.Image]::FromStream($script:PictureStream)
        $form.BackgroundImage = $script:Picture
        $form.BackgroundImageLayout = [Windows.Forms.ImageLayout]::Stretch
    }
    catch { $script:Picture = $null }
}

function Set-AktBackground {
    if (-not $script:Picture) { return }
    try {
        $size = $form.ClientSize
        $scaled = New-Object Drawing.Bitmap($size.Width, $size.Height)
        $graphics = [Drawing.Graphics]::FromImage($scaled)
        $graphics.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.DrawImage($script:Picture, 0, 0, $size.Width, $size.Height)
        $graphics.Dispose()
        $form.BackgroundImageLayout = [Windows.Forms.ImageLayout]::None
        $form.BackgroundImage = $scaled
    }
    catch { }
}

# The state in one line at the top, over a dark strip: green up to date,
# yellow update available, red check failed.
$colorOk = [Drawing.Color]::FromArgb(120, 220, 120)
$colorWarn = [Drawing.Color]::FromArgb(255, 205, 80)
$colorBad = [Drawing.Color]::FromArgb(255, 120, 100)
$lblTop = New-AktLabel 'Sprawdzam, czy klient jest aktualny...' 0 0 880 36 (New-Object Drawing.Font('Segoe UI', 12, [Drawing.FontStyle]::Bold)) $colorDim
$lblTop.BackColor = [Drawing.Color]::FromArgb(185, 12, 8, 6)
$lblTop.TextAlign = [Drawing.ContentAlignment]::MiddleCenter

function Set-AktTop {
    param([string]$Text, [Drawing.Color]$Color)
    $lblTop.Text = $Text
    $lblTop.ForeColor = $Color
}

$lblStatus = New-AktLabel 'Sprawdzam aktualizacje...' 30 296 820 26 $fontBold $colorGold
$lblInfo = New-AktLabel '' 30 324 820 42 $fontNormal $colorText
$lblInfo.AutoEllipsis = $true
$progress = New-Object Windows.Forms.ProgressBar
$progress.SetBounds(30, 370, 820, 16)
$progress.Minimum = 0
$progress.Maximum = 1000
$progress.Visible = $false
$lblProgress = New-AktLabel '' 30 389 820 20 $fontSmall $colorDim

$btnServers = New-AktButton 'Dodaj własny serwer VPS' 30 424 230 48 $colorPanel $colorText $fontButton
$btnUpdate = New-AktButton 'Aktualizuj' 470 424 180 48 $colorPanel $colorText $fontButton
$btnPlay = New-AktButton 'GRAJ' 670 424 180 48 ([Drawing.Color]::FromArgb(150, 28, 20)) ([Drawing.Color]::White) $fontPlay
$btnUpdate.Enabled = $false
$lblFooter = New-AktLabel ("Aktualizator $($script:AktVersion)  |  $($script:Root)") 30 474 820 18 $fontSmall $colorDim
$lblFooter.AutoEllipsis = $true

$form.Controls.AddRange(@($lblTop, $lblStatus, $lblInfo, $progress, $lblProgress, $btnServers, $btnUpdate, $btnPlay, $lblFooter))

$script:Component = $null
$script:UpdateAvailable = $false
$script:Busy = $false
$script:Downloading = $false
$script:ManifestFailed = $false
$script:FileList = $null
$script:ClientState = $null

function Invoke-AktSafe {
    # Every click handler goes through here: an exception thrown out of a
    # WinForms event would end the whole window without a word.
    param([scriptblock]$Action)
    try { & $Action }
    catch {
        Write-AktLog $script:Root ("Błąd: " + $_.Exception.Message)
        [void](Show-AktMessage $_.Exception.Message 'Error')
    }
}

function Update-AktView {
    $installed = Get-AktInstalledVersion -Root $script:Root
    $installedText = if ($installed) { $installed } else { 'nieznana' }
    $btnUpdate.Text = 'Aktualizuj'
    if ($script:ManifestFailed) {
        Set-AktTop "Nie udało się sprawdzić aktualizacji (Twój klient: $installedText)" $colorBad
        $btnUpdate.Text = 'Sprawdź ponownie'
        $btnUpdate.Enabled = $true
        return
    }
    if (-not $script:Component) {
        Set-AktTop "Twój klient: $installedText" $colorDim
        $lblStatus.Text = "Twój klient: $installedText"
        $lblInfo.Text = 'Kanał aktualizacji nie podaje teraz wersji klienta. Możesz grać.'
        $btnUpdate.Text = 'Sprawdź ponownie'
        $btnUpdate.Enabled = $true
        $script:UpdateAvailable = $false
        return
    }
    $state = $script:ClientState
    if ($null -eq $state) { $state = Get-AktClientState -Root $script:Root -Component $script:Component }
    $installed = $state.Installed
    $installedText = if ($installed) { $installed } else { 'nieznana' }
    $script:UpdateAvailable = $state.UpdateNeeded
    $version = $script:Component.Version
    $sizeText = if ($script:Component.Size -gt 0) { ' (' + (Format-AktSize $script:Component.Size) + ')' } else { '' }
    if ($script:UpdateAvailable) {
        Set-AktTop "Dostępna aktualizacja klienta $version" $colorWarn
        $lblStatus.Text = "Dostępna aktualizacja klienta: $version$sizeText"
        if ($state.ByFiles) {
            $detail = "Różni się lub brakuje plików klienta: $($state.Different.Count) z $($state.Checked)"
            if ($installed) { $detail += " (Twój klient: $installed)" }
            $lblInfo.Text = "$detail. Kliknij Aktualizuj albo od razu GRAJ - zapytam, czy zaktualizować.`r`n$($script:Component.Message)"
        }
        elseif ($installed) {
            $lblInfo.Text = "Twój klient: $installed. Kliknij Aktualizuj albo od razu GRAJ - zapytam, czy zaktualizować.`r`n$($script:Component.Message)"
        }
        else {
            $lblStatus.Text = "Najnowszy klient: $version$sizeText - wersja Twojego nieznana"
            $lblInfo.Text = "Nie wiadomo, którą wersję klienta masz. Zalecana aktualizacja - ustawienia i serwery zostaną.`r`n$($script:Component.Message)"
        }
        $btnUpdate.Enabled = $true
        $btnUpdate.BackColor = [Drawing.Color]::FromArgb(120, 84, 20)
    }
    else {
        Set-AktTop "Klient aktualny ($installedText)" $colorOk
        $lblStatus.Text = "Klient jest aktualny ($installedText)"
        $lblInfo.Text = if ($state.ByFiles) { "Sprawdzono pliki klienta ($($state.Checked)) - zgodne z wydaniem $version.`r`n$($script:Component.Message)" } else { $script:Component.Message }
        $btnUpdate.Text = 'Aktualny'
        $btnUpdate.Enabled = $false
        $btnUpdate.BackColor = $colorPanel
    }
}

function Update-AktClientState {
    # Hashes the listed files (a fraction of a second: the exe and the
    # .index files) and decides. No list, or a list of another version: the
    # CLIENT_VERSION comparison, as before.
    $script:ClientState = $null
    if (-not $script:Component) { return }
    $lblStatus.Text = 'Sprawdzam pliki klienta...'
    [Windows.Forms.Application]::DoEvents()
    try { $script:ClientState = Get-AktClientState -Root $script:Root -Component $script:Component -FileList $script:FileList }
    catch {
        Write-AktLog $script:Root ("Sprawdzanie plików: " + $_.Exception.Message)
        $script:ClientState = Get-AktClientState -Root $script:Root -Component $script:Component
    }
}

function Invoke-AktCheck {
    $script:ManifestFailed = $false
    $lblStatus.Text = 'Sprawdzam aktualizacje...'
    Set-AktTop 'Sprawdzam, czy klient jest aktualny...' $colorDim
    $lblInfo.Text = ''
    $btnUpdate.Enabled = $false
    $form.Cursor = [Windows.Forms.Cursors]::WaitCursor
    [Windows.Forms.Application]::DoEvents()
    try {
        $manifest = Get-AktManifest -Source $script:ManifestUrl
        $script:Component = Get-AktClientComponent -Manifest $manifest
        $script:FileList = $null
        if ($script:Component) {
            try { $script:FileList = Get-AktClientFileList -Source $script:FileListUrl }
            catch { Write-AktLog $script:Root ("Lista plików klienta niedostępna: " + $_.Exception.Message) }
        }
        Update-AktClientState
        Update-AktView
    }
    catch {
        $script:ManifestFailed = $true
        $script:Component = $null
        $script:ClientState = $null
        $installed = Get-AktInstalledVersion -Root $script:Root
        $lblStatus.Text = 'Nie udało się sprawdzić aktualizacji'
        $lblInfo.Text = $_.Exception.Message + $(if ($installed) { " Twój klient: $installed." } else { '' })
        Write-AktLog $script:Root ("Manifest: " + $_.Exception.Message)
        Update-AktView
    }
    finally { $form.Cursor = [Windows.Forms.Cursors]::Default }
}

$script:ProgressStarted = $null
$onProgress = {
    param($Stage, $Done, $Total)
    switch ($Stage) {
        'download' {
            if ($Total -gt 0) { $progress.Value = [int][Math]::Min(1000, [Math]::Max(0, $Done * 1000 / $Total)) }
            $elapsed = ([DateTime]::Now - $script:ProgressStarted).TotalSeconds
            $speed = if ($elapsed -gt 0.5) { ' - ' + (Format-AktSize ($Done / $elapsed)) + '/s' } else { '' }
            $totalText = if ($Total -gt 0) { ' / ' + (Format-AktSize $Total) } else { '' }
            $lblProgress.Text = 'Pobieranie: ' + (Format-AktSize $Done) + $totalText + $speed
        }
        'retry' {
            $lblProgress.Text = "Pobieranie przerwane (próba $Done z $Total) - ponawiam za chwilę..."
            $script:ProgressStarted = [DateTime]::Now
        }
        'wait' { }
        'verify' {
            $script:Downloading = $false
            $btnUpdate.Enabled = $false
            $lblProgress.Text = 'Sprawdzanie sumy kontrolnej SHA-256...'
        }
        'extract' {
            $script:Downloading = $false
            $btnUpdate.Enabled = $false
            if ($Total -gt 0) { $progress.Value = [int][Math]::Min(1000, $Done * 1000 / $Total) }
            $lblProgress.Text = 'Rozpakowywanie: ' + (Format-AktSize $Done) + ' / ' + (Format-AktSize $Total)
        }
        'apply' {
            if ($Total -gt 0) { $progress.Value = [int][Math]::Min(1000, $Done * 1000 / $Total) }
            $lblProgress.Text = "Instalowanie plików: $Done / $Total"
        }
    }
    [Windows.Forms.Application]::DoEvents()
}

function Invoke-AktUpdate {
    # Returns $true when the client is up to date afterwards.
    if (-not $script:Component) { return $false }

    $running = @(Get-AktGameProcesses -Root $script:Root)
    if ($running.Count -gt 0) {
        $answer = Show-AktMessage ("Gra jest uruchomiona. Aby zaktualizować klienta, trzeba ją zamknąć.`r`n`r`nZamknąć grę teraz?") 'Question' 'YesNo'
        if ($answer -ne [Windows.Forms.DialogResult]::Yes) { return $false }
        if (-not (Stop-AktGameProcesses -Root $script:Root)) {
            [void](Show-AktMessage 'Nie udało się zamknąć gry. Zamknij ją sam (sprawdź też Menedżer zadań) i spróbuj ponownie.' 'Warning')
            return $false
        }
    }

    $script:Busy = $true
    $script:Downloading = $true
    $script:CancelRequested = $false
    $script:ProgressStarted = [DateTime]::Now
    $btnPlay.Enabled = $false
    $btnServers.Enabled = $false
    $btnUpdate.Text = 'Anuluj'
    $btnUpdate.Enabled = $true
    $progress.Value = 0
    $progress.Visible = $true
    $lblStatus.Text = "Aktualizuję klienta do wersji $($script:Component.Version)..."
    $lblProgress.Text = 'Łączenie...'
    [Windows.Forms.Application]::DoEvents()
    try {
        $result = Install-AktClientUpdate -Root $script:Root -Component $script:Component -OnProgress $onProgress
        $progress.Value = 1000
        $lblProgress.Text = "Zainstalowano plików: $($result.Files)."
        if ($result.Kept.Count -gt 0) { $lblProgress.Text += ' Twoje ustawienia i serwery zostały bez zmian.' }
        if ($result.SelfUpdated) { $lblProgress.Text += ' Nowa wersja aktualizatora uruchomi się przy następnym starcie.' }
        Update-AktClientState
        Update-AktView
        $lblStatus.Text = "Klient zaktualizowany do wersji $($result.Version)"
        return $true
    }
    catch {
        $message = $_.Exception.Message
        Write-AktLog $script:Root ("Aktualizacja nieudana: " + $message)
        $progress.Visible = $false
        $lblProgress.Text = ''
        Update-AktView
        if (-not $script:CancelRequested) { [void](Show-AktMessage $message 'Error') }
        else { $lblProgress.Text = 'Anulowano pobieranie. Nic nie zostało zmienione.' }
        return $false
    }
    finally {
        $script:Busy = $false
        $script:Downloading = $false
        $btnPlay.Enabled = $true
        $btnServers.Enabled = $true
    }
}

function Start-AktGame {
    $exe = Join-Path $script:Root 'metin2client.exe'
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
        [void](Show-AktMessage 'Brak pliku metin2client.exe w folderze klienta (mógł go usunąć antywirus). Kliknij Aktualizuj, aby go przywrócić, i dodaj folder klienta do wyjątków antywirusa.' 'Warning')
        return
    }
    Write-AktLog $script:Root 'Uruchamiam grę.'
    # The client reads coop.cfg and its packs relative to the working folder.
    Start-Process -FilePath $exe -WorkingDirectory $script:Root
    $form.Close()
}

$btnPlay.Add_Click({
        Invoke-AktSafe {
            if ($script:Busy) { return }
            if ($script:UpdateAvailable -and $script:Component) {
                $answer = Show-AktMessage ("Dostępna jest aktualizacja klienta $($script:Component.Version). Zaktualizować przed grą?`r`n`r`nTak - zaktualizuj i uruchom grę`r`nNie - graj bez aktualizacji") 'Question' 'YesNoCancel'
                if ($answer -eq [Windows.Forms.DialogResult]::Cancel) { return }
                if ($answer -eq [Windows.Forms.DialogResult]::Yes) {
                    if (-not (Invoke-AktUpdate)) { return }
                }
            }
            Start-AktGame
        }
    })

$btnUpdate.Add_Click({
        Invoke-AktSafe {
            if ($script:Downloading) {
                $script:CancelRequested = $true
                $lblProgress.Text = 'Anulowanie...'
                return
            }
            if ($script:Busy) { return }
            if ($script:ManifestFailed -or -not $script:Component) { Invoke-AktCheck; return }
            [void](Invoke-AktUpdate)
        }
    })

$form.Add_FormClosing({
        param($formSender, $e)
        if (-not $script:Busy) { return }
        if ($script:Downloading) {
            $answer = Show-AktMessage 'Trwa pobieranie aktualizacji. Przerwać je?' 'Question' 'YesNo'
            if ($answer -eq [Windows.Forms.DialogResult]::Yes) { $script:CancelRequested = $true }
        }
        else {
            [void](Show-AktMessage 'Trwa instalowanie plików - poczekaj kilka sekund, aż się skończy.' 'Information')
        }
        $e.Cancel = $true
    })

$form.Add_Shown({
        Invoke-AktSafe {
            Set-AktBackground
            [Windows.Forms.Application]::DoEvents()
            if (-not (Clear-AktStaging -Root $script:Root)) {
                Write-AktLog $script:Root 'Nie udało się usunąć pozostałości po poprzedniej aktualizacji.'
            }
            Invoke-AktCheck
        }
    })

# ------------------------------------------------------ server dialog

function Show-AktServerDialog {
    $dialog = New-Object Windows.Forms.Form
    $dialog.Text = 'Dodaj własny serwer VPS'
    $dialog.ClientSize = New-Object Drawing.Size(500, 440)
    $dialog.FormBorderStyle = [Windows.Forms.FormBorderStyle]::FixedDialog
    $dialog.MaximizeBox = $false
    $dialog.MinimizeBox = $false
    $dialog.StartPosition = [Windows.Forms.FormStartPosition]::CenterParent
    $dialog.BackColor = $colorPanel
    $dialog.ForeColor = $colorText
    $dialog.Font = $fontNormal
    $dialog.AutoScaleDimensions = New-Object Drawing.SizeF(96, 96)
    $dialog.AutoScaleMode = [Windows.Forms.AutoScaleMode]::Dpi

    $intro = New-AktLabel ('Serwer pojawi się na liście serwerów w grze jako "Online: <nazwa>". ' +
        'Zwykle wystarczy wpisać nazwę i IP - porty zmieniaj tylko wtedy, gdy właściciel serwera poda inne.') 16 12 468 40 $fontNormal $colorDim

    $group = New-Object Windows.Forms.GroupBox
    $group.Text = 'Miejsce na liście'
    $group.ForeColor = $colorGold
    $group.SetBounds(16, 58, 468, 76)
    $radio1 = New-Object Windows.Forms.RadioButton
    $radio1.SetBounds(12, 20, 450, 24)
    $radio1.ForeColor = $colorText
    $radio2 = New-Object Windows.Forms.RadioButton
    $radio2.SetBounds(12, 46, 450, 24)
    $radio2.ForeColor = $colorText
    $group.Controls.AddRange(@($radio1, $radio2))

    $makeField = {
        param([string]$Caption, [int]$Y, [int]$Width)
        $label = New-AktLabel $Caption 16 ($Y + 3) 170 22 $fontNormal $colorText
        $box = New-Object Windows.Forms.TextBox
        $box.SetBounds(190, $Y, $Width, 24)
        $box.BackColor = $colorField
        $box.ForeColor = $colorText
        $box.BorderStyle = [Windows.Forms.BorderStyle]::FixedSingle
        $dialog.Controls.AddRange(@($label, $box))
        return $box
    }
    $txtName = & $makeField 'Nazwa serwera *' 148 294
    $txtName.MaxLength = 80
    $txtHost = & $makeField 'IP lub domena VPS *' 180 294
    $txtHost.MaxLength = 253
    $txtAuth = & $makeField 'Port logowania' 222 90
    $txtChannel = & $makeField 'Port kanału 1 (CH1)' 254 90
    $lblChannels = New-AktLabel 'Liczba kanałów' 16 289 170 22 $fontNormal $colorText
    $cmbChannels = New-Object Windows.Forms.ComboBox
    $cmbChannels.DropDownStyle = [Windows.Forms.ComboBoxStyle]::DropDownList
    $cmbChannels.SetBounds(190, 286, 90, 24)
    [void]$cmbChannels.Items.AddRange(@('1', '2'))
    $cmbChannels.BackColor = $colorField
    $cmbChannels.ForeColor = $colorText
    $hint = New-AktLabel 'Domyślnie: logowanie 11000, CH1 13000, CH2 13010 (kanał 1 + 10).' 16 318 468 20 $fontSmall $colorDim

    $btnSave = New-AktButton 'Zapisz' 16 380 150 42 ([Drawing.Color]::FromArgb(150, 28, 20)) ([Drawing.Color]::White) $fontButton
    $btnRemove = New-AktButton 'Usuń z tego miejsca' 176 380 170 42 $colorPanel $colorText $fontButton
    $btnClose = New-AktButton 'Zamknij' 356 380 128 42 $colorPanel $colorText $fontButton
    $dialog.Controls.AddRange(@($intro, $group, $lblChannels, $cmbChannels, $hint, $btnSave, $btnRemove, $btnClose))
    $dialog.CancelButton = $btnClose

    $describe = {
        param([int]$Slot)
        $file = [IO.Path]::GetFileName((Get-AktCoopPath -Root $script:Root -Slot $Slot))
        $config = Read-AktCoopConfig -Path (Get-AktCoopPath -Root $script:Root -Slot $Slot)
        if ($null -eq $config) { return "Miejsce $Slot ($file): puste" }
        if (-not $config.Valid) { return "Miejsce $Slot ($file): plik uszkodzony - gra go pomija" }
        return ("Miejsce {0} ({1}): {2} - {3}" -f $Slot, $file, $config.Name, $config.Host)
    }
    $refresh = {
        $radio1.Text = & $describe 1
        $radio2.Text = & $describe 2
    }
    $load = {
        $slot = if ($radio2.Checked) { 2 } else { 1 }
        $config = Read-AktCoopConfig -Path (Get-AktCoopPath -Root $script:Root -Slot $slot)
        if ($null -eq $config) {
            $txtName.Text = ''; $txtHost.Text = ''
            $txtAuth.Text = '11000'; $txtChannel.Text = '13000'; $cmbChannels.SelectedItem = '2'
        }
        else {
            $txtName.Text = $config.Name; $txtHost.Text = $config.Host
            $txtAuth.Text = [string]$config.Auth; $txtChannel.Text = [string]$config.Channel
            $cmbChannels.SelectedItem = $(if ($config.Channels -eq 1) { '1' } else { '2' })
        }
        $btnRemove.Enabled = ($null -ne $config)
    }

    & $refresh
    # The first empty slot, so adding a second server does not replace the first.
    if ($null -ne (Read-AktCoopConfig -Path (Get-AktCoopPath -Root $script:Root -Slot 1)) -and
        $null -eq (Read-AktCoopConfig -Path (Get-AktCoopPath -Root $script:Root -Slot 2))) { $radio2.Checked = $true }
    else { $radio1.Checked = $true }
    & $load
    $radio1.Add_CheckedChanged({ if ($radio1.Checked) { Invoke-AktSafe { & $load } } })
    $radio2.Add_CheckedChanged({ if ($radio2.Checked) { Invoke-AktSafe { & $load } } })

    $btnSave.Add_Click({
            Invoke-AktSafe {
                $slot = if ($radio2.Checked) { 2 } else { 1 }
                $config = New-AktCoopConfig -Name $txtName.Text -HostName $txtHost.Text -Auth $txtAuth.Text `
                    -Channel $txtChannel.Text -Channels ([string]$cmbChannels.SelectedItem)
                $existing = Read-AktCoopConfig -Path (Get-AktCoopPath -Root $script:Root -Slot $slot)
                if ($existing -and $existing.Valid -and ($existing.Host -ne $config.Host -or $existing.Name -ne $config.Name)) {
                    $answer = Show-AktMessage ("W miejscu $slot jest już serwer `"$($existing.Name)`" ($($existing.Host)). Zastąpić go?") 'Question' 'YesNo'
                    if ($answer -ne [Windows.Forms.DialogResult]::Yes) { return }
                }
                [void](Save-AktCoopConfig -Root $script:Root -Slot $slot -Config $config)
                & $refresh
                & $load
                $channelsText = if ($config.Channels -eq 2) { 'CH1 i CH2' } else { 'CH1' }
                $running = if (@(Get-AktGameProcesses -Root $script:Root).Count -gt 0) { "`r`n`r`nGra jest uruchomiona - serwer pojawi się po jej ponownym uruchomieniu." } else { '' }
                [void](Show-AktMessage ("Zapisano.`r`n`r`nW grze wybierz serwer `"Online: $($config.Name)`" ($channelsText).$running") 'Information')
            }
        })
    $btnRemove.Add_Click({
            Invoke-AktSafe {
                $slot = if ($radio2.Checked) { 2 } else { 1 }
                $answer = Show-AktMessage "Usunąć serwer z miejsca $slot?" 'Question' 'YesNo'
                if ($answer -ne [Windows.Forms.DialogResult]::Yes) { return }
                Remove-AktCoopConfig -Root $script:Root -Slot $slot
                & $refresh
                & $load
            }
        })
    $btnClose.Add_Click({ $dialog.Close() })

    [void]$dialog.ShowDialog($form)
    $dialog.Dispose()
}

$btnServers.Add_Click({ Invoke-AktSafe { if (-not $script:Busy) { Show-AktServerDialog } } })

try {
    [void]$form.ShowDialog()
}
catch {
    Write-AktLog $script:Root ("Błąd okna: " + $_.Exception.Message)
    [void](Show-AktMessage ("Aktualizator zakończył się błędem:`r`n" + $_.Exception.Message) 'Error')
}
finally {
    $form.Dispose()
    try { $script:Mutex.ReleaseMutex() } catch { }
}
