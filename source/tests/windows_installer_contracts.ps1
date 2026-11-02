param(
  [Parameter(Mandatory=$true)][string]$InstallerPath,
  [Parameter(Mandatory=$true)][string]$WorkRoot
)
$ErrorActionPreference = 'Stop'
$raw = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $InstallerPath)).Replace("`r`n", "`n")
$marker = "`n:::BOMAI_PS_PAYLOAD_20261030`n"
$offset = $raw.IndexOf($marker)
if ($offset -lt 0) { throw 'Installer payload marker missing' }
$source = $raw.Substring($offset + $marker.Length)
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseInput($source, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ('Installer parser errors: ' + ($errors.Message -join '; ')) }
$testDir = Join-Path ([IO.Path]::GetFullPath($WorkRoot)) ('bomai path with spaces ' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testDir | Out-Null

# Execute only the credential-state helper, never the installer itself.
$helper = @($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Initialize-FirstLogin'}, $true))
if ($helper.Count -ne 1) { throw 'Initial-login helper missing or ambiguous' }
Invoke-Expression $helper[0].Extent.Text

# FIX 20261101 owner-report: bare drive-letter input must auto-append \BOMAI.
$normHelper = @($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Get-NormalizedRoot'}, $true))
if ($normHelper.Count -ne 1) { throw 'Root normalization helper missing or ambiguous' }
Invoke-Expression $normHelper[0].Extent.Text
$normCases = @(
  @{ in='D:\';      want='D:\BOMAI' },
  @{ in='D:\\';     want='D:\BOMAI' },
  @{ in='d:';       want='D:\BOMAI' },
  @{ in='D:/';      want='D:\BOMAI' },
  @{ in='D:\BOMAI'; want='D:\BOMAI' },
  @{ in='E:\My Apps'; want='E:\My Apps' },
  @{ in='  E:\BOMAI  '; want='E:\BOMAI' },
  @{ in='';         want='' },
  @{ in='\\server\share'; want='\\server\share' }
)
foreach ($case in $normCases) {
  $got = Get-NormalizedRoot $case.in
  if ($got -cne $case.want) { throw ('Get-NormalizedRoot "' + $case.in + '" returned "' + $got + '", expected "' + $case.want + '"') }
}
$installRootBodies = @($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Test-InstallRoot'}, $true))
if ($installRootBodies.Count -lt 1) { throw 'Test-InstallRoot missing' }
foreach ($body in $installRootBodies) {
  if ($body.Extent.Text -notmatch 'Get-NormalizedRoot\s+\$path') { throw 'A Test-InstallRoot definition does not normalize its input path' }
  if ($body.Extent.Text -notmatch 'if \(-not \(Test-Path -LiteralPath \$full\)\)') { throw 'A Test-InstallRoot definition still creates directories unconditionally (drive-root New-Item crash)' }
}
if ($source -notmatch '\$BOMAI_ROOT\s+= Get-NormalizedRoot \$BOMAI_ROOT') { throw 'Console root env override is not normalized' }

$loginPath = Join-Path $testDir 'first-login.json'
$fresh = Initialize-FirstLogin $loginPath $true
if ($fresh.managed_account -ne $true) { throw 'Fresh account ownership not recorded before boot' }
$initialPassword = $fresh.password
$retry = Initialize-FirstLogin $loginPath $false
if ($retry.managed_account -ne $true -or $retry.password -cne $initialPassword) { throw 'Retry lost initial-login ownership or rotated password' }
$legacyPath = Join-Path $testDir 'legacy-login.json'
@{email='existing@example.invalid';password='fixture-password'} | ConvertTo-Json | Set-Content -LiteralPath $legacyPath -Encoding UTF8
$legacy = Initialize-FirstLogin $legacyPath $false
if ($legacy.managed_account -ne $false -or $legacy.password -cne 'fixture-password') { throw 'Legacy credentials incorrectly claimed or replaced' }
$existingPath = Join-Path $testDir 'existing-account.json'
$existing = Initialize-FirstLogin $existingPath $false
if ($existing.managed_account -ne $false) { throw 'Existing database incorrectly claimed as a new account' }
if ($source -notmatch 'loginFile=\$\(if \(\$initialLogin\.managed_account -eq \$true\)') { throw 'Completion does not use persisted ownership' }

# Obtain the exact argument expressions from both installer and generated launcher.
$launchers = @($ast.FindAll({param($n) $n -is [Management.Automation.Language.AssignmentStatementAst] -and $n.Left.Extent.Text -eq '$launcherTpl'}, $true))
if ($launchers.Count -ne 1) { throw 'Launcher template missing or ambiguous' }
$launcherString = $launchers[0].Right.Find({param($n) $n -is [Management.Automation.Language.StringConstantExpressionAst]}, $true)
if (-not $launcherString) { throw 'Launcher literal not found' }
$launcherText = $launcherString.Value
$launcherAst = [Management.Automation.Language.Parser]::ParseInput($launcherText, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'Generated launcher parser errors' }
$commands = @($ast.FindAll({param($n) $n -is [Management.Automation.Language.CommandAst] -and $n.GetCommandName() -eq 'Start-Process' -and $n.Extent.Text -match "'-File'"}, $true))
$commands += @($launcherAst.FindAll({param($n) $n -is [Management.Automation.Language.CommandAst] -and $n.GetCommandName() -eq 'Start-Process' -and $n.Extent.Text -match "'-File'"}, $true))
if ($commands.Count -ne 8) { throw ('Expected eight PowerShell launch paths, found ' + $commands.Count) }
$rel = $testDir; $script:REL_DIR = $testDir
$startOwui = Join-Path $testDir 'start-owui.ps1'; $so0w = $startOwui
$startSx = Join-Path $testDir 'start-searxng.ps1'; $sx0 = $startSx; $sx = $startSx
$probeSource = "Add-Content -LiteralPath (Join-Path `$PSScriptRoot 'executed.txt') -Value 'executed' -Encoding ASCII"
foreach ($probe in @($startOwui, $startSx, (Join-Path $testDir 'Start-BOM-AI.ps1'))) { Set-Content -LiteralPath $probe -Value $probeSource -Encoding UTF8 }
$results = @()
for ($i=0; $i -lt $commands.Count; $i++) {
  $elements = $commands[$i].CommandElements
  $argIndex = -1
  for ($j=0; $j -lt $elements.Count; $j++) { if ($elements[$j] -is [Management.Automation.Language.CommandParameterAst] -and $elements[$j].ParameterName -eq 'ArgumentList') { $argIndex=$j+1; break } }
  if ($argIndex -lt 0) { throw 'ArgumentList not found' }
  [string[]]$nativeArgs = & ([scriptblock]::Create($elements[$argIndex].Extent.Text))
  $stdout = Join-Path $testDir ('launch-' + $i + '.stdout')
  $stderr = Join-Path $testDir ('launch-' + $i + '.stderr')
  $process = Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList $nativeArgs -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
  if ($process.ExitCode -ne 0) { throw ('Native PowerShell path-with-spaces launch failed at case ' + $i + ': ' + (Get-Content -LiteralPath $stderr -Raw)) }
  $results += @{case=$i;exit_code=$process.ExitCode}
}
$executed = @(Get-Content -LiteralPath (Join-Path $testDir 'executed.txt')).Count
if ($executed -ne 8) { throw ('Expected eight executed child scripts, found ' + $executed) }
@{
  powershell=$PSVersionTable.PSVersion.ToString()
  installer_sha256=(Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256).Hash
  parser_errors=0
  path_with_spaces_native_launches=$results
  executed_child_count=$executed
  initial_login_fresh=$true
  initial_login_retry_preserves_credentials=$true
  legacy_account_not_claimed=$true
  existing_database_not_claimed=$true
  drive_letter_normalization=$true
  test_directory=$testDir
  limitation='Tests argument dispatch and credential-state contracts; does not perform a full installation in a spaced path or drive the GUI.'
} | ConvertTo-Json -Depth 5
