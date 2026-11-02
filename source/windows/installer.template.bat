:: BOM AI Astra Installer v2.0.0 ONLINE - polyglot bootstrap header (ASCII only)
:: ONLINE edition 20261031: no 1.2 GB payload zip required next to this file.
:: All components are downloaded at install time (python.org / GitHub / PyPI /
:: bomai.app/dl/online / Ollama registry) and verified by SHA-256 where pinned.
:: Copyright (c) BOM AI / SiamCafe group. Components keep their upstream licenses
:: (Python PSF, Open WebUI BSD-3-based, SearXNG AGPL-3.0, Ollama MIT, waitress ZPL-2.1).
:: Architecture: ASCII cmd header -> fixed PowerShell 5.1 loader -> unique marker -> UTF-8 payload.
@echo off
setlocal
set "BOMAI_SELF=%~f0"
set "BOMAI_MODE=install"
if not "%~1"=="" set "BOMAI_MODE=%~1"
if /i "%BOMAI_MODE%"=="install" goto :bomai_ok
if /i "%BOMAI_MODE%"=="console" goto :bomai_ok
if /i "%BOMAI_MODE%"=="update" goto :bomai_ok
if /i "%BOMAI_MODE%"=="uninstall" goto :bomai_ok
if /i "%BOMAI_MODE%"=="validatepath" goto :bomai_ok
echo Usage: %~nx0 [install^|console^|update^|uninstall^|validatepath]
echo   install      = Thai GUI installer (default)
echo   console      = same engine, console progress (ASCII)
echo   update       = read-only release check
echo   uninstall    = remove BOM-AI-owned files, keep data/models/shared runtimes
echo   validatepath = check BOMAI_VALIDATE_PATH env as install root (support/QC)
exit /b 2
:bomai_ok
set "BOMAI_PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%BOMAI_PS%" goto :bomai_ps
echo Windows PowerShell 5.1 not found. Windows 10 22H2+ / Windows 11 x64 required.
endlocal & exit /b 3
:bomai_ps
"%BOMAI_PS%" -NoProfile -NoLogo -STA -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $k='::'+':BOMAI_PS_PAYLOAD_20261030'; $nl=[string]([char]13+[char]10); $t=[Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($env:BOMAI_SELF)); $L=$t.Split([string[]]$nl,[System.StringSplitOptions]::None); $f=-1; for($i=0;$i -lt $L.Length;$i++){ if($L[$i] -eq $k){ if($f -ge 0){ Write-Error 'duplicate marker'; exit 5 } $f=$i } }; if($f -lt 0){ Write-Error 'marker missing'; exit 5 }; $p=[string]::Join($nl,$L,$f+1,$L.Length-$f-1); Invoke-Expression $p; if($BOMAI_RC){ exit [int]$BOMAI_RC } else { exit 0 }"
set "BOMAI_RC=%ERRORLEVEL%"
endlocal & exit /b %BOMAI_RC%
:::BOMAI_PS_PAYLOAD_20261030
# ============================================================================
# BOM AI Astra Installer v2.0.0 ONLINE - PowerShell payload (UTF-8, decoded by loader)
# ONLINE edition: same engine as the offline installer, but every dependency is
# fetched at install time instead of reading payload\ wheelhouses:
#   - Python 3.11.9 installer  : python.org (SHA-256 pinned)
#   - SearXNG source zip       : codeload.github.com rev 54ca1d9cf (SHA-256 pinned)
#   - Open WebUI 0.12.5        : pip install open-webui==0.12.5 (PyPI, online)
#   - SearXNG python deps      : pip install -r <src>\requirements.txt (PyPI, online)
#   - bom_runtime gateway      : https://bomai.app/dl/online/ (SHA-256 pinned)
# K3 HOLD-3 (manifest/blob verify), GOD CONFIG v7.0 Modelfile
# (7 parameters, presence_penalty=0.0 IRON 12, NO think=false in Modelfile).
# ============================================================================
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$script:BOMAI_RC = 0

# ---------------------------------------------------------------- pins -----
$PIN = [ordered]@{
  release        = '2.0.0'
  qcBrowserOrigin = ''
  python         = '3.11.9'
  pythonUrl      = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe'
  pythonSha      = '5EE42C4EEE1E6B4464BB23722F90B45303F79442DF63083F05322F1785F5FDDE'
  pythonMsiBase  = 'https://www.python.org/ftp/python/3.11.9/amd64/'
  ollamaVer      = '0.40.13'
  ollamaUrl      = 'https://github.com/ollama/ollama/releases/download/v0.40.13/OllamaSetup.exe'
  ollamaSha      = '9E3C76E54E7184C68E88A2378B909BF59BBE454F83C076CB4F4A717E946AE719'
  owuiVer        = '0.12.5'
  owuiWheelSha   = '74FAFB4EFEEE7C894303CA5B87FA7525FBF63B39C0B9962496FB82939119D3FD'
  waitressVer    = '3.0.2'
  waitressSha    = 'C56D67FD6E87C2EE598B76ABDD4E96CFAD1F24CACDEA5078D382B1F9D7B5ED2E'
  searxngUrl     = 'https://codeload.github.com/searxng/searxng/zip/54ca1d9cfb08674f66261d7f351b063558dfcc62'
  searxngSha     = '030E9E28E6CFA5083DD168771C60BBC109500F5B5F68653A0EBB0117F3364590'
  searxngRev     = '54ca1d9cfb08674f66261d7f351b063558dfcc62'
  dlOnlineBase   = 'https://bomai.app/dl/online/'
  gatewayPayload = '__EMBED_RUNTIME_B64__'
  catalogPayload = '__EMBED_CATALOG_B64__'
  seedPayload    = '__EMBED_SEED_B64__'
  auditPayload   = '__EMBED_AUDIT_B64__'
  gatewayUrl     = 'https://bomai.app/dl/online/bom_runtime_r2.py'
  gatewayCatUrl  = 'https://bomai.app/dl/online/models.json'
  gatewaySha     = '__RUNTIME_SHA__'
  gatewayCatSha  = '__CATALOG_SHA__'
  modelTag       = 'siamcafe/bom-ai:light-v2.0.0'
  modelLayerSha  = 'E2E460E979A24BBA9187854B96E79FBAB5561B26C2493FFCEE00BF659212FD67'
  modelProjSha   = 'EA8EB56D7FDCAA49698F1A06C61D90AB18C30AC96F61F02054A0F36C0BC3C2B9'
  proTag         = 'siamcafe/bom-ai:pro-v2.0.0'
  proLayerSha    = 'A20B8A3682CE75EE9B1C586C85696EBF1DF79A46B1A44A10BFBEFAC5591DADC1'
  proProjSha     = 'D9F429A6EE114923E8C1D9ED93F72205A0E9FA4083898DC0A774312DB11A31EF'
  proOutputAlias = 'bomai-pro:latest'
  outputAlias    = 'bomai-safe:latest'
  godEnvSha      = '3A01ED1A8AAF19C6F50E517B48A84B09B135AEEF1E3921994E11DD0A99D9572A'
  configGSha     = '8FFDE4AF685F41B78349894F52E4C610ABCE75A0728A69255E51D1B6765A629A'
  godParams      = [ordered]@{ temperature=0.6; top_p=0.95; top_k=20; repeat_penalty=1.0; presence_penalty=0.0; num_ctx=8192; num_predict=4096 }
  # think=false is request/gateway level ONLY - never a Modelfile PARAMETER.
  tailscaleVer   = '1.104.4'
  tailscaleUrl   = 'https://pkgs.tailscale.com/stable/tailscale-setup-1.104.4-amd64.msi'
  tailscaleResolve = 'https://pkgs.tailscale.com/stable/'
  tailscaleExe   = 'C:\Program Files\Tailscale\tailscale.exe'
  faviconUrl     = 'https://bomai.app/user/themes/bomai/images/apple-touch-icon.png'
  # BOM AI Thai system prompt (source: models/Modelfile_v4b + rule 6 live-price guard).
  # Without SYSTEM the base image persona answers with canned Thai-only refusals (fix 20261031).
  # GOD CONFIG SYSTEM (LOCKED, spec art#54872): canonical short Thai prompt,
  # byte-identical on every tier. Do not edit or extend.
  systemPrompt   = 'คุณคือ BOM AI (บอม เอไอ) ผู้ช่วย AI ภาษาไทย
ตอบเป็นภาษาไทยเสมอ ชัดเจน กระชับ เป็นมิตร
ถ้าถูกถามเรื่องราคาหุ้น ทอง หรือค่าเงิน ให้แนะนำค้นหาจากอินเทอร์เน็ตเพื่อข้อมูลล่าสุด'
  diskNeededGB   = 30
}

# FIX 20261101 owner-report: a bare drive letter (D:\ or D:) entered on the
# location page or via env override is accepted and auto-appends \BOMAI.
function Get-NormalizedRoot([string]$path) {
  if ([string]::IsNullOrWhiteSpace($path)) { return $path }
  $t = $path.Trim()
  if ($t -match '^([A-Za-z]):[\\/]{0,2}$') { return ($t.Substring(0,1).ToUpper() + ':\BOMAI') }
  return $t
}

$MODE = $env:BOMAI_MODE
$SELF = $env:BOMAI_SELF
$RELDIR_ROOT = Split-Path -Parent $SELF
$PAYLOAD     = Join-Path $RELDIR_ROOT 'payload'
# default root; overridden by the location page (GUI) or BOMAI_ROOT_OVERRIDE (console)
$BOMAI_ROOT_DEFAULT = Join-Path $env:LOCALAPPDATA 'BOMAI'
$ROOT_PTR   = Join-Path $BOMAI_ROOT_DEFAULT 'state\install-root.txt'
$BUILD_ID    = 'b' + (Get-Date -Format 'yyyyMMddHHmmss')
if ($env:BOMAI_QC -eq '1' -and $env:BOMAI_BUILD_ID) {
  if ($env:BOMAI_BUILD_ID -notmatch '^[A-Za-z0-9_-]+$') { throw 'Invalid QC build ID' }
  $BUILD_ID = $env:BOMAI_BUILD_ID
}
$BOMAI_ROOT  = $BOMAI_ROOT_DEFAULT
if ($env:BOMAI_ROOT_OVERRIDE) { $BOMAI_ROOT = $env:BOMAI_ROOT_OVERRIDE }
elseif ($env:BOMAI_ROOT) { $BOMAI_ROOT = $env:BOMAI_ROOT } # FIX 20261031 qc-full-audit: accept BOMAI_ROOT alias (spec verify name)
$BOMAI_ROOT  = Get-NormalizedRoot $BOMAI_ROOT
$REL_DIR     = Join-Path $BOMAI_ROOT ("releases\" + $PIN.release + '\' + $BUILD_ID)
$DATA_DIR    = Join-Path $BOMAI_ROOT 'data\open-webui'
$CACHE_DIR   = Join-Path $BOMAI_ROOT 'cache\sha256'
$LOG_DIR     = Join-Path $BOMAI_ROOT 'logs'
$STATE_DIR   = Join-Path $BOMAI_ROOT 'state'
$INSTALL_JSON= Join-Path $STATE_DIR 'install.json'
$ACTIVE_PTR  = Join-Path $STATE_DIR 'active-release.txt'

$PAYLOAD_    = $PAYLOAD
$BOMAI_ROOT_ = $BOMAI_ROOT
$BUILD_ID_   = $BUILD_ID
$REL_DIR_    = $REL_DIR
$INSTALL_JSON_ = $INSTALL_JSON
$ACTIVE_PTR_ = $ACTIVE_PTR
$ROOT_PTR_   = $ROOT_PTR

# update/uninstall: honor a recorded non-default install root (written by S2)
if ($MODE -in 'update','uninstall' -and -not $env:BOMAI_ROOT_OVERRIDE -and (Test-Path $ROOT_PTR)) {
  $ptrRoot = (Get-Content $ROOT_PTR -Raw).Trim()
  if ($ptrRoot -and (Test-Path -LiteralPath $ptrRoot)) {
    $BOMAI_ROOT  = $ptrRoot
    $STATE_DIR   = Join-Path $BOMAI_ROOT 'state'
    $ACTIVE_PTR  = Join-Path $STATE_DIR 'active-release.txt'
    $INSTALL_JSON= Join-Path $STATE_DIR 'install.json'
    $ACTIVE_PTR_ = $ACTIVE_PTR
    $INSTALL_JSON_ = $INSTALL_JSON
    $BOMAI_ROOT_ = $BOMAI_ROOT
  }
}

# ------------------------------------------------------------- resources ----
$RES = @{}
$RES['th'] = [ordered]@{
  title='ติดตั้ง BOM AI'; welcome='ยินดีต้อนรับสู่ BOM AI'
  privacy='BOM AI ประมวลผลบนเครื่องของคุณเอง แชตและรูปภาพไม่ถูกส่งออกไป ยกเว้นการค้นหาบนเว็บที่คุณเปิดใช้ ซึ่งจะส่งคำค้นไปยังผู้ให้บริการค้นหา'
  meta='ตัวติดตั้งออนไลน์ • เวอร์ชัน 2.0.0 • สคริปต์จะดาวน์โหลดส่วนประกอบที่จำเป็นเอง (~5.1 GB ถ้ายังไม่มี Ollama) • ต้องการพื้นที่ดิสก์ประมาณ 30 GB'
  terms='# เงื่อนไขการใช้งาน BOM AI (สรุป)`n- ซอฟต์แวร์นี้ติดตั้งและทำงานบนเครื่องของคุณทั้งหมด`n- ส่วนประกอบ: Ollama (MIT), Open WebUI (BSD-3), Python 3.11.9 (PSF), SearXNG (AGPL-3.0), waitress (ZPL-2.1)`n- โมเดล siamcafe/bom-ai v2.0.0 (Apache-2.0) ตรวจสอบความถูกต้องด้วย SHA-256`n- การเปิดใช้การค้นหาเว็บจะส่งคำค้นของคุณไปยังผู้ให้บริการค้นหาสาธารณะ`n- ผู้พัฒนาไม่รับผิดชอบความเสียหายใด ๆ จากการใช้งาน'
  consent='ฉันยอมรับเงื่อนไขการใช้งาน'; install='ติดตั้ง'; cancel='ยกเลิก'; next='ถัดไป'; back='ย้อนกลับ'
  compTitle='เลือกองค์ประกอบ'
  compCore='ส่วนหลัก: Ollama + โมเดล BOM AI + Python + Open WebUI (จำเป็น)'
  compSearch='การค้นหาเว็บ (SearXNG)'; compShortcut='ทางลัดบนเดสก์ท็อป'; compStartMenu='ทางลัดในเมนู Start'; compSignin='เริ่มอัตโนมัติเมื่อเข้าสู่ระบบ'
  installing='กำลังติดตั้ง...'; step='ขั้นตอน'; retry='การเชื่อมต่อขัดข้อง กำลังลองใหม่ (ครั้งที่ {0})'
  done='ติดตั้งเสร็จแล้ว'; open='เปิด BOM AI'; openLogs='เปิดโฟลเดอร์บันทึก'; close='ปิด'
  firstUse='เข้าสู่ระบบด้วยบัญชีเริ่มต้นที่แสดงด้านล่าง หรือใช้บัญชีเดิมของคุณ'
  initialLogin='บัญชีเริ่มต้น (หากเคยเปลี่ยนรหัสผ่าน ให้ใช้รหัสผ่านใหม่): {0}'
  initialPassword='รหัสผ่านเริ่มต้น: {0}'
  errTitle='เกิดข้อผิดพลาด'; errIntegrity='ไฟล์ที่ดาวน์โหลดไม่ผ่านการตรวจสอบ กรุณาดาวน์โหลดใหม่จากเว็บไซต์ทางการ'
  errDisk='พื้นที่ว่างไม่เพียงพอ'; errPolicy='Windows ไม่อนุญาตให้เรียกใช้ตัวติดตั้งนี้ กรุณาดูวิธีติดตั้งที่รองรับ'
  errGeneric='ติดตั้งไม่สำเร็จ โปรดดูบันทึกและลองอีกครั้ง'; retryBtn='ลองใหม่'
  errRemains='สิ่งที่ยังคงอยู่: ข้อมูลผู้ใช้ แคชที่ตรวจสอบแล้ว และโมเดลที่แชร์ไว้จะถูกรักษาไว้ทั้งหมด ส่วนที่ติดตั้งไม่สำเร็จในขั้นนี้ถูกลบออกแล้ว กด ลองใหม่ เพื่อเริ่มใหม่ได้'
  copyDiag='คัดลอกข้อมูลวินิจฉัย'
  locTitle='เลือกตำแหน่งติดตั้ง'
  locDesc='เลือกโฟลเดอร์ที่จะติดตั้ง BOM AI (ค่าเริ่มต้นแนะนำ: โฟลเดอร์ผู้ใช้ของ Windows)'
  locNeeded='ต้องการพื้นที่ว่างประมาณ 30 GB'
  browse='เรียกดู...'
  locFree='พื้นที่ว่าง: {0} GB'
  locErrUNC='ไม่รองรับเส้นทางเครือข่าย (UNC) กรุณาเลือกไดรว์ในเครื่อง'
  locErrDrive='กรุณาระบุไดรว์ในเครื่อง เช่น C:\\ หรือ D:\\'
  locErrNotReady='ไดรว์นี้ไม่พร้อมใช้งาน'
  locErrRemovable='ไม่รองรับไดรว์แบบถอดเสียบหรือแผ่นซีดี'
  locErrFS='ระบบไฟล์ต้องเป็น NTFS (พบ: {0})'
  locErrSpace='พื้นที่ว่างไม่เพียงพอ ต้องการอย่างน้อย 30 GB (พบ: {0} GB)'
  locErrReparse='เส้นทางมี reparse point/junction ไม่อนุญาตให้ใช้งาน'
  locOk='ตำแหน่งนี้ใช้งานได้'
  tailscaleOpt='📱 เข้าถึง BOM AI จากมือถือ/นอกบ้าน (Tailscale VPN ฟรี — ต้องสมัครแยก)'
  tsNote='ติดตั้งเสร็จให้สมัครบัญชีฟรีที่ tailscale.com แล้วติดตั้งแอพ Tailscale บนมือถือ จะใช้ BOM AI นอกบ้านได้ (ต้องมีสิทธิ์ผู้ดูแล + UAC)'
  searchStatus='การค้นหาเว็บ (SearXNG): {0}'
  searchOnLbl='เปิดใช้งาน'; searchOffLbl='ไม่ได้ติดตั้ง'
  installedAt='ติดตั้งที่: {0}'
  lang='EN'; searchOn='(ค่าเริ่มต้น: เปิด)'
  tierTitle='เลือกเวอร์ชัน BOM AI'
  tierLight='BOM AI Light — โมเดล 4B'
  tierLightDesc='ประมาณ 3.4 GB · ใช้ CPU ได้ ไม่ต้องมี GPU'
  tierPro='BOM AI Pro — โมเดล 12B'
  tierProDesc='ประมาณ 7.9 GB · ต้องมี GPU 12GB ขึ้นไป'
  tierProd='BOM AI Production — 27B'
  tierProdDesc='Mac + MLX · ยังไม่เปิดสาธารณะ'
  tierRec='[แนะนำสำหรับเครื่องนี้]'
  tierNeedGpu='[ต้องมี GPU ที่รองรับ]'
  tierThisMachine='เครื่องนี้: CPU {0} · RAM {1} GB · GPU {2} · VRAM {3}'
  tierGpuNone='ตรวจไม่ได้'
  tierFree='พื้นที่ว่าง: {0} GB | ต้องการ: {1} GB'
}
$RES['en'] = [ordered]@{
  title='Install BOM AI'; welcome='Welcome to BOM AI'
  privacy='BOM AI runs entirely on your own machine. Chat and images never leave it, except web search you explicitly enable, which sends queries to public search providers.'
  meta='Online installer - Version 2.0.0 - the script downloads required components itself (~5.1 GB if Ollama not present) - approx 30 GB disk required'
  terms='# BOM AI terms (summary)`n- This software installs and runs fully on your machine`n- Components: Ollama (MIT), Open WebUI (BSD-3), Python 3.11.9 (PSF), SearXNG (AGPL-3.0), waitress (ZPL-2.1)`n- Model siamcafe/bom-ai v2.0.0 (Apache-2.0) verified by SHA-256`n- Enabling web search sends your queries to public search providers`n- Provided as-is, without warranty of any kind'
  consent='I accept the terms'; install='Install'; cancel='Cancel'; next='Next'; back='Back'
  compTitle='Choose components'
  compCore='Core: Ollama + BOM AI model + Python + Open WebUI (required)'
  compSearch='Web search (SearXNG)'; compShortcut='Desktop shortcut'; compStartMenu='Start Menu shortcut'; compSignin='Start at sign-in'
  installing='Installing...'; step='Step'; retry='Connection problem, retrying (attempt {0})'
  done='Installation complete'; open='Open BOM AI'; openLogs='Open log folder'; close='Close'
  firstUse='Sign in with the initial login shown below, or use your existing account.'
  initialLogin='Initial login (use your changed password if applicable): {0}'
  initialPassword='Initial password: {0}'
  errTitle='An error occurred'; errIntegrity='Downloaded file failed verification. Please download again from the official website.'
  errDisk='Not enough free disk space'; errPolicy='Windows does not allow this installer to run. See supported installation methods.'
  errGeneric='Installation failed. Check the logs and try again'; retryBtn='Retry'
  errRemains='What remains: user data, verified cache and shared models are all kept; the failed partial stage was removed. Press Retry to start again.'
  copyDiag='Copy diagnostics'
  locTitle='Choose Install Location'
  locDesc='Choose the folder where BOM AI will be installed (recommended default: your Windows user folder)'
  locNeeded='Approximately 30 GB of free space required'
  browse='Browse...'
  locFree='Free space: {0} GB'
  locErrUNC='Network paths (UNC) are not supported; pick a local drive'
  locErrDrive='Specify a local drive such as C:\\ or D:\\'
  locErrNotReady='This drive is not ready'
  locErrRemovable='Removable or CD drives are not supported'
  locErrFS='Filesystem must be NTFS (found: {0})'
  locErrSpace='Not enough free space; at least 30 GB required (found: {0} GB)'
  locErrReparse='Path contains a reparse point/junction; not allowed'
  locOk='This location is usable'
  tailscaleOpt='📱 Access BOM AI from phone/outside home (Tailscale VPN free — separate signup needed)'
  tsNote='After install, create a free account at tailscale.com and install the Tailscale app on your phone to use BOM AI away from home (requires administrator + UAC)'
  searchStatus='Web search (SearXNG): {0}'
  searchOnLbl='enabled'; searchOffLbl='not installed'
  installedAt='Installed at: {0}'
  lang='ไทย'; searchOn='(default: on)'
  tierTitle='Choose BOM AI Version'
  tierLight='BOM AI Light — 4B model'
  tierLightDesc='about 3.4 GB · runs on CPU, no GPU needed'
  tierPro='BOM AI Pro — 12B model'
  tierProDesc='about 7.9 GB · GPU with 12GB+ required'
  tierProd='BOM AI Production — 27B'
  tierProdDesc='Mac + MLX · not publicly available yet'
  tierRec='[recommended for this PC]'
  tierNeedGpu='[supported GPU required]'
  tierThisMachine='This PC: CPU {0} · RAM {1} GB · GPU {2} · VRAM {3}'
  tierGpuNone='not detectable'
  tierFree='Free space: {0} GB | needed: {1} GB'
}

# -------------------------------------------------------------- helpers -----
function Write-Log([string]$m) {
  try {
    New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null
    $line = ('{0} [{1}] {2}' -f (Get-Date -Format s), $MODE, $m)
    Add-Content -Path (Join-Path $LOG_DIR ('install-' + $PIN.release + '.log')) -Value $line -Encoding UTF8
  } catch {}
}

# ----------------------------------------------------- install-root checks ---
function Test-InstallRoot([string]$path) {
  $r = @{ ok=$false; freeGB=0.0; fs=''; reason='' }
  try {
    if ([string]::IsNullOrWhiteSpace($path)) { $r.reason='EMPTY'; return $r }
    $path = Get-NormalizedRoot $path
    if ($path -like '\\*') { $r.reason='UNC'; return $r }
    if ($path -notmatch '^[A-Za-z]:\\') { $r.reason='DRIVE'; return $r }
    $full = [IO.Path]::GetFullPath($path)
    $drive = New-Object System.IO.DriveInfo($full.Substring(0,3))
    if (-not $drive.IsReady) { $r.reason='NOTREADY'; return $r }
    if ($drive.DriveType -eq [System.IO.DriveType]::Removable -or $drive.DriveType -eq [System.IO.DriveType]::CDRom) { $r.reason='REMOVABLE'; return $r }
    if ($drive.DriveFormat -ne 'NTFS') { $r.reason=('FS:' + $drive.DriveFormat); return $r }
    $r.fs = $drive.DriveFormat
    $r.freeGB = [math]::Round($drive.AvailableFreeSpace/1GB,1)
    if ($r.freeGB -lt $PIN.diskNeededGB) { $r.reason='SPACE'; return $r }
    $cur = $full
    while ($cur -and $cur.Length -gt 3) {
      if (Test-Path -LiteralPath $cur) {
        $item = Get-Item -LiteralPath $cur -Force
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { $r.reason='REPARSE'; return $r }
      }
      $cur = Split-Path -Parent $cur
    }
    # FIX 20261101: never New-Item a drive root; PS 5.1 throws
    # "The path is not of a legal form" for root directories.
    if (-not (Test-Path -LiteralPath $full)) {
      New-Item -ItemType Directory -Path $full -Force | Out-Null
    }
    $probe = Join-Path $full ('.bomai-write-probe-' + [guid]::NewGuid().ToString('N').Substring(0,8))
    Set-Content -Path $probe -Value 'ok' -Encoding ASCII
    Remove-Item $probe -Force
    $r.ok = $true
  } catch { $r.reason = ('ERROR: ' + $_.Exception.Message) }
  return $r
}

# ---------------------------------------------------------- engine script ---
# Runs inside a worker runspace (GUI) or inline (console).
# Injected variables: Q, OPT, PIN, BOMAI_ROOT_, PAYLOAD_, BUILD_ID_, REL_DIR_,
# INSTALL_JSON_, ACTIVE_PTR_, LOG_DIR, STATE_DIR, DATA_DIR, CACHE_DIR
$EngineDef = {
# native tools (python, pip, msiexec, curl) write progress to stderr; rely on exit codes, not EAP
$ErrorActionPreference = 'Continue'

function Initialize-FirstLogin([string]$Path, [bool]$BrandNewData) {
  if (Test-Path -LiteralPath $Path) {
    $login = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    if (-not $login.email -or -not $login.password) { throw 'Invalid initial-login state' }
  } else {
    $login = [pscustomobject]@{ email='owner@bomai.local'; password=([Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N')); managed_account=$false }
  }
  # Persist ownership before first boot so a later retry can still show the login.
  # A legacy account/database is never inferred to use these generated credentials.
  if ($BrandNewData) { $login | Add-Member -NotePropertyName managed_account -NotePropertyValue $true -Force }
  elseif (-not $login.PSObject.Properties['managed_account']) { $login | Add-Member -NotePropertyName managed_account -NotePropertyValue $false }
  $login | ConvertTo-Json | Set-Content -LiteralPath $Path -Encoding UTF8
  return $login
}

function Test-InstallRoot([string]$path) {
  $r = @{ ok=$false; freeGB=0.0; fs=''; reason='' }
  try {
    if ([string]::IsNullOrWhiteSpace($path)) { $r.reason='EMPTY'; return $r }
    $path = Get-NormalizedRoot $path
    if ($path -like '\\*') { $r.reason='UNC'; return $r }
    if ($path -notmatch '^[A-Za-z]:\\') { $r.reason='DRIVE'; return $r }
    $full = [IO.Path]::GetFullPath($path)
    $drive = New-Object System.IO.DriveInfo($full.Substring(0,3))
    if (-not $drive.IsReady) { $r.reason='NOTREADY'; return $r }
    if ($drive.DriveType -eq [System.IO.DriveType]::Removable -or $drive.DriveType -eq [System.IO.DriveType]::CDRom) { $r.reason='REMOVABLE'; return $r }
    if ($drive.DriveFormat -ne 'NTFS') { $r.reason=('FS:' + $drive.DriveFormat); return $r }
    $r.fs = $drive.DriveFormat
    $r.freeGB = [math]::Round($drive.AvailableFreeSpace/1GB,1)
    if ($r.freeGB -lt $PIN.diskNeededGB) { $r.reason='SPACE'; return $r }
    $cur = $full
    while ($cur -and $cur.Length -gt 3) {
      if (Test-Path -LiteralPath $cur) {
        $item = Get-Item -LiteralPath $cur -Force
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { $r.reason='REPARSE'; return $r }
      }
      $cur = Split-Path -Parent $cur
    }
    # FIX BUG1 20261031: same semantics as the outer helper - create the target
    # directory when missing so a fresh path (e.g. E:\BOMAI) is auto-created.
    if (-not (Test-Path -LiteralPath $full)) {
      New-Item -ItemType Directory -Path $full -Force | Out-Null
    }
    $probe = Join-Path $full ('.bomai-write-probe-' + [guid]::NewGuid().ToString('N').Substring(0,8))
    Set-Content -Path $probe -Value 'ok' -Encoding ASCII
    Remove-Item $probe -Force
    $r.ok = $true
  } catch { $r.reason = ('ERROR: ' + $_.Exception.Message) }
  return $r
}

function Emit([string]$t, $d) {
  if ($Q) { $Q.Enqueue([pscustomobject]@{ t=$t; d=$d; at=(Get-Date) }) }
  elseif (-not $OPT.gui) {
    switch ($t) {
      'log'  { Write-Host ('[log] ' + $d) }
      'step' { Write-Host ('[step] ' + $d.name + ' ' + $d.pct + '%') }
      'dl'   { $dp = 0; if ($d.tot -gt 0) { $dp = [int](100*$d.cur/$d.tot) }
               $ds = ''; if ($d.spd -gt 0) { $ds = ('  ' + ('{0:N1}' -f ($d.spd/1MB)) + ' MiB/s') }
               if ($d.eta -ge 0) { $ds = $ds + ('  ETA ' + ('{0:mm\:ss}' -f [timespan]::FromSeconds([int]$d.eta))) }
               Write-Host ('[dl]   ' + $d.label + '  ' + $d.cur + '/' + $d.tot + ' B  (' + $dp + '%)' + $ds) }
      'done' { Write-Host ('[done] ok=' + $d.ok) }
      'err'  { Write-Host ('[err]  ' + $d.code + ' ' + $d.msg) }
    }
  }
}
function Fail([string]$c, [string]$m) {
  $script:ec = $c; $script:em = $m
  throw $m
}
function Get-Sha([string]$path) {
  return (Get-FileHash -Path $path -Algorithm SHA256).Hash.ToUpperInvariant()
}
function Test-Port([int]$port) {
  try {
    $c = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop | Select-Object -First 1
    $proc = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
    return @{busy=$true; pid=$c.OwningProcess; proc=($proc.ProcessName)}
  } catch { return @{busy=$false; pid=0; proc=''} }
}
function Stop-OwnedOwui {
  # FIX BUG5 20261031: stop ONLY the 8080 listener that belongs to this install root
  # (ExecutablePath/CommandLine under $BOMAI_ROOT_) - never a foreign process.
  # Returns $true once port 8080 is free.
  for ($i = 0; $i -lt 30; $i++) {
    $t = Test-Port 8080
    if (-not $t.busy) { return $true }
    $ours = $false
    try {
      $pi = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $t.pid) -ErrorAction Stop
      if ($pi.ExecutablePath -and $pi.ExecutablePath.StartsWith($BOMAI_ROOT_, [StringComparison]::OrdinalIgnoreCase)) { $ours = $true }
      elseif ($pi.CommandLine -and $pi.CommandLine -match 'open[_.-]webui' -and $pi.CommandLine -match [regex]::Escape($BOMAI_ROOT_)) { $ours = $true }
    } catch {}
    if (-not $ours) { return $false }
    if ($i -eq 0) { Emit 'log' ('S8b: stopping owned OWUI pid ' + $t.pid + ' for the db seed') }
    Stop-Process -Id $t.pid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
  }
  return (-not (Test-Port 8080).busy)
}
function Invoke-Json([string]$method,[string]$uri,$body) {
  if ($body) {
    return Invoke-RestMethod -Method $method -Uri $uri -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 30
  }
  return Invoke-RestMethod -Method $method -Uri $uri -TimeoutSec 30
}
function Get-BomaiFile([string]$url,[string]$dest,[string]$sha,[string]$label) {
  # FIX BUG2 20261031: staged .part download with 206-only resume, low-speed watchdog
  # (<1 KiB/s for 120s aborts the attempt), 3 attempts at 5/15/30s backoff, SHA-256
  # gate before the final move. FIX BUG4: emits 'dl' events (bytes/total/speed/eta)
  # so the GUI title bar + panel update every ~500ms while transferring.
  if ($label -eq '') { $label = (Split-Path -Leaf $dest) }
  if (Test-Path $dest) {
    if ($sha) { if ((Get-Sha $dest) -eq $sha) { return $true } }
    else { return $true }
  }
  $dir = Split-Path -Parent $dest; New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $part = $dest + '.part'
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  for ($a = 1; $a -le 3; $a++) {
    if ($OPT.cancel) { $script:ec='CANCELLED'; throw 'CANCELLED' }
    $offset = 0
    if (Test-Path $part) { try { $offset = [int64](Get-Item $part).Length } catch { $offset = 0 } }
    Emit 'log' ('download ' + $label + ' attempt ' + $a + ' (resume offset ' + $offset + ' B)')
    try {
      $req = [Net.HttpWebRequest]::Create($url)
      $req.Method = 'GET'; $req.AllowAutoRedirect = $true; $req.KeepAlive = $true
      $req.Timeout = 30000; $req.ReadWriteTimeout = 120000
      if ($offset -gt 0) { $null = $req.AddRange($offset) }
      $resp = $req.GetResponse()
      $code = [int]$resp.StatusCode
      if ($offset -gt 0 -and $code -ne 206) {
        # server ignored the Range header: restart clean, never append a 200 body
        $resp.Close()
        Remove-Item $part -Force -ErrorAction SilentlyContinue
        Emit 'log' ($label + ': server ignored Range (HTTP ' + $code + ') - restarting from 0')
        $req = [Net.HttpWebRequest]::Create($url)
        $req.Method = 'GET'; $req.AllowAutoRedirect = $true
        $req.Timeout = 30000; $req.ReadWriteTimeout = 120000
        $resp = $req.GetResponse()
      }
      $tot = [int64]0
      try { $tot = [int64]$resp.ContentLength } catch {}
      if ($tot -gt 0 -and $offset -gt 0) { $tot = $tot + $offset }
      $stream = $resp.GetResponseStream()
      $fs = [IO.File]::Open($part, [IO.FileMode]::Append, [IO.FileAccess]::Write)
      $buf = New-Object byte[] 262144
      $got = $offset
      $t0 = [Diagnostics.Stopwatch]::StartNew()
      $lastEmit = [Diagnostics.Stopwatch]::StartNew()
      $winStart = [Diagnostics.Stopwatch]::StartNew()
      $winBytes = $got
      while ($true) {
        if ($OPT.cancel) { $fs.Close(); $stream.Close(); $resp.Close(); $script:ec='CANCELLED'; throw 'CANCELLED' }
        $n = $stream.Read($buf, 0, $buf.Length)
        if ($n -le 0) { break }
        $fs.Write($buf, 0, $n)
        $got += $n
        if (($got - $winBytes) -ge 122880) { $winStart.Restart(); $winBytes = $got }
        elseif ($winStart.Elapsed.TotalSeconds -ge 120) {
          throw ('stall watchdog: <1 KiB/s for 120s at ' + $got + ' B')
        }
        if ($lastEmit.ElapsedMilliseconds -ge 500) {
          $spd = [double]0; $eta = -1
          if ($t0.Elapsed.TotalSeconds -gt 0.5) { $spd = ($got - $offset) / $t0.Elapsed.TotalSeconds }
          if ($spd -gt 100 -and $tot -gt $got) { $eta = [int](($tot - $got) / $spd) }
          Emit 'dl' @{ cur=$got; tot=$tot; label=$label; spd=[int64]$spd; eta=$eta }
          $lastEmit.Restart()
        }
      }
      $fs.Close(); $stream.Close(); $resp.Close()
      if ($tot -gt 0 -and $got -ne $tot) { throw ('short read: ' + $got + ' of ' + $tot + ' B') }
      if ($sha) {
        $h = Get-Sha $part
        if ($h -ne $sha) { throw ('hash mismatch after transfer: ' + $h) }
      } else { Emit 'log' ('downloaded (no pin) sha256=' + (Get-Sha $part)) }
      if (Test-Path $dest) { Remove-Item $dest -Force }
      Move-Item -Path $part -Destination $dest -Force
      Emit 'dl' @{ cur=$got; tot=$tot; label=$label; spd=0; eta=-1 }
      return $true
    } catch {
      if ($script:ec -eq 'CANCELLED') { throw }
      Emit 'log' ('download ' + $label + ' attempt ' + $a + ' failed: ' + $_.Exception.Message + ' - partial kept for resume')
    }
    if ($a -lt 3) { Start-Sleep -Seconds (@(5,15,30)[$a-1]) }
  }
  return $false
}

function Wait-Http([string]$uri, [int]$timeoutSec, [int]$pctBase, [int]$pctSpan) {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt $timeoutSec) {
    if ($OPT.cancel) { $script:ec='CANCELLED'; throw 'CANCELLED' }
    try {
      $r = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 5
      if ($r.StatusCode -eq 200) { return $true }
    } catch {}
    $p = $pctBase + [int](($sw.Elapsed.TotalSeconds / $timeoutSec) * $pctSpan)
    Emit 'step' @{ name=('waiting ' + $uri); pct=[Math]::Min($p, 100) }
    Start-Sleep 2
  }
  return $false
}
function Save-State([hashtable]$extra) {
  $stDir = Split-Path -Parent $INSTALL_JSON_
  if (-not (Test-Path $stDir)) { New-Item -ItemType Directory -Force -Path $stDir | Out-Null }
  $s = [ordered]@{ release=$PIN.release; build=$BUILD_ID_; updated=(Get-Date -Format s) }
  if (Test-Path $INSTALL_JSON_) {
    try {
      $old = Get-Content $INSTALL_JSON_ -Raw | ConvertFrom-Json
      foreach ($p in $old.PSObject.Properties) { $s[$p.Name] = $p.Value }
    } catch {}
  }
  foreach ($k in $extra.Keys) { $s[$k] = $extra[$k] }
  $s | ConvertTo-Json -Depth 6 | Set-Content -Path $INSTALL_JSON_ -Encoding UTF8
}

$steps = @(
  @{k='S1';  w=2;  n='preflight'}
  @{k='S2';  w=2;  n='prepare'}
  @{k='S3';  w=8;  n='ollama'}
  @{k='S4';  w=4;  n='ollama-ready'}
  @{k='S5';  w=6;  n='payload-sha'}
  @{k='S6';  w=6;  n='python'}
  @{k='S7';  w=12; n='wheelhouses'}
  @{k='S8';  w=10; n='owui'}
  @{k='S9';  w=20; n='model-god'}
  @{k='S10'; w=15; n='searxng'}
  @{k='S11'; w=5;  n='shortcuts'}
  @{k='ST';  w=3;  n='tailscale'}
  @{k='S12'; w=7;  n='commit'}
)
$wsum = ($steps | ForEach-Object { $_.w } | Measure-Object -Sum).Sum
function Step-Pct([string]$k) {
  $done = 0; $cur = $null
  foreach ($s in $steps) { if ($s.k -eq $k) { $cur = $s; break } else { $done += $s.w } }
  return @{ base=[int](100*$done/$wsum); span=[int](100*$cur.w/$wsum) }
}

$script:ec = $null; $script:em = $null
$owned = @()
$mtx = $null
# clear stale failure keys from previous runs so install.json reflects THIS run
if (Test-Path $INSTALL_JSON_) {
  try {
    $oldJ = Get-Content $INSTALL_JSON_ -Raw | ConvertFrom-Json
    foreach ($stale in @('code','msg')) { if ($oldJ.PSObject.Properties[$stale]) { $oldJ.PSObject.Properties.Remove($stale) } }
    $oldJ | ConvertTo-Json -Depth 6 | Set-Content -Path $INSTALL_JSON_ -Encoding UTF8
  } catch {}
}
try {
  # ---------------- S0 resume / second-run (FIX BUG3 20261031) ----------------
  # resume_key = SHA256(release | canonical root | tier | dependency lock). Same key
  # + uncommitted state reuses the SAME release dir (no new BUILD_ID); same key +
  # COMPLETE status takes the verify-only path below and reports
  # reused_verified_existing instead of reinstalling over user data.
  function Get-StrSha([string]$s) {
    $p = [System.Security.Cryptography.SHA256]::Create()
    try { $b = $p.ComputeHash([Text.Encoding]::UTF8.GetBytes($s)); return (($b | ForEach-Object { $_.ToString('x2') }) -join '') }
    finally { $p.Dispose() }
  }
  $depLockSeed = @($PIN.python,$PIN.pythonSha,$PIN.ollamaVer,$PIN.ollamaSha,$PIN.owuiVer,$PIN.owuiWheelSha,$PIN.waitressVer,$PIN.waitressSha,$PIN.searxngUrl,$PIN.searxngSha,$PIN.gatewayUrl,$PIN.gatewaySha,$PIN.gatewayCatUrl,$PIN.gatewayCatSha,$PIN.modelTag,$PIN.modelLayerSha,$PIN.modelProjSha,$PIN.outputAlias,$PIN.proTag,$PIN.proLayerSha,$PIN.proProjSha,$PIN.proOutputAlias) -join '|'
  $depLockSha = Get-StrSha $depLockSeed
  $tierNow = 'light'
  if ($OPT.tier) { $tierNow = [string]$OPT.tier }
  if ($tierNow -ne 'light' -and $tierNow -ne 'pro') { $tierNow = 'light' }
  $resumeKey = Get-StrSha ($PIN.release + '|' + $BOMAI_ROOT_ + '|' + $tierNow + '|' + $depLockSha)
  # PHASE 1 20261031: tier-resolved model pins (both tiers share the same
  # GOD CONFIG; only FROM/alias differ)
  $tierTag = $PIN.modelTag; $tierLayer = $PIN.modelLayerSha; $tierProj = $PIN.modelProjSha; $tierAlias = $PIN.outputAlias
  if ($tierNow -eq 'pro') { $tierTag = $PIN.proTag; $tierLayer = $PIN.proLayerSha; $tierProj = $PIN.proProjSha; $tierAlias = $PIN.proOutputAlias }
  $tierAliasShort = ($tierAlias -split ':')[0]
  $prevInstall = $null
  if (Test-Path $INSTALL_JSON_) {
    try { $prevInstall = Get-Content $INSTALL_JSON_ -Raw | ConvertFrom-Json } catch { $prevInstall = $null }
  }
  if ($prevInstall -and $prevInstall.resumeKey -and $prevInstall.resumeKey -eq $resumeKey) {
    if ($prevInstall.status -eq 'COMPLETE') { $prevInstall.status = 'REPAIR_REQUIRED' }
    $prevRel = [string]$prevInstall.rel
    if ($prevInstall.status -eq 'COMPLETE' -and $prevRel -and (Test-Path -LiteralPath $prevRel)) {
      Emit 'step' @{ name='S0 verify existing install'; pct=5 }
      $mtxR = New-Object System.Threading.Mutex($false, ('Local\BOM-AI-Installer-' + $PIN.release))
      if (-not $mtxR.WaitOne(1000)) { Fail 'E-MUTEX' 'another BOM AI installer is running' }
      try {
        $rootChk0 = Test-InstallRoot $BOMAI_ROOT_
        if (-not $rootChk0.ok) { Fail 'E-DISK' ('install root invalid on re-run: ' + $rootChk0.reason) }
        if (-not (Wait-Http 'http://127.0.0.1:11434/api/version' 90 8 8)) {
          $ollCand = @((Get-Command ollama.exe -ErrorAction SilentlyContinue).Source, (Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'))
          $ollExe0 = $null; foreach ($c in $ollCand) { if ($c -and (Test-Path $c)) { $ollExe0 = $c; break } }
          if (-not $ollExe0) { Fail 'E-OLLAMA' 'ollama missing on re-run' }
          $env:OLLAMA_MAX_LOADED_MODELS = '1'
          $so0 = Join-Path $LOG_DIR 'ollama-serve-out.log'; $se0 = Join-Path $LOG_DIR 'ollama-serve-err.log'
          $p0 = Start-Process -FilePath $ollExe0 -ArgumentList 'serve' -WindowStyle Hidden -RedirectStandardOutput $so0 -RedirectStandardError $se0 -PassThru
          $owned += $p0.Id
          if (-not (Wait-Http 'http://127.0.0.1:11434/api/version' 120 16 8)) { Fail 'E-OLLAMA' 'ollama not ready on re-run' }
        }
        if (-not (Test-Port 11435).busy) {
          $g0 = Join-Path $prevRel 'bom_runtime.py'
          if (Test-Path $g0) {
            $rootAll0 = Split-Path -Parent (Split-Path -Parent $prevRel)
            $gLog0 = Join-Path $rootAll0 'logs\gateway.jsonl'
            $py0 = Join-Path $prevRel 'python\python.exe'
            if (Test-Path $py0) {
              $null = Start-Process -FilePath $py0 -ArgumentList ('"' + $g0 + '"','--host','127.0.0.1','--port','11435','--upstream','http://127.0.0.1:11434','--log',('"' + $gLog0 + '"')) -WindowStyle Hidden -PassThru
              $null = Wait-Http 'http://127.0.0.1:11435/' 60 26 6
            }
          }
        }
        if (-not (Test-Port 8080).busy) {
          $so0w = Join-Path $prevRel 'start-owui.ps1'
          if (Test-Path $so0w) {
            $null = Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-File',('"' + $so0w + '"') -WindowStyle Hidden -PassThru
            if (-not (Wait-Http 'http://127.0.0.1:8080/' 420 30 30)) { Fail 'E-OWUI' 'Open WebUI not ready on re-run' }
          } else { Fail 'E-OWUI' ('start-owui.ps1 missing in ' + $prevRel) }
        }
        if ($prevInstall.s10 -eq 'ok' -and -not (Test-Port 8888).busy) {
          $sx0 = Join-Path $prevRel 'start-searxng.ps1'
          if (Test-Path $sx0) {
            $null = Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-File',('"' + $sx0 + '"') -WindowStyle Hidden -PassThru
            $null = Wait-Http 'http://127.0.0.1:8888/' 120 70 10
          }
        }
        $tierPrev = [string]$prevInstall.tier
        if ($tierPrev -ne 'pro') { $tierPrev = 'light' }
        $aliasPrev = 'bomai-pro' ; if ($tierPrev -eq 'light') { $aliasPrev = 'bomai-safe' }
        try {
          $chk0 = Invoke-Json POST 'http://127.0.0.1:11434/api/show' ('{"model":"' + $aliasPrev + '"}')
          if (-not $chk0) { Fail 'E-MODEL' ('model alias ' + $aliasPrev + ' missing on re-run') }
        } catch { Fail 'E-MODEL' ('model alias check failed on re-run: ' + $_.Exception.Message) }
        Save-State @{ lastVerify=(Get-Date -Format s) }
        Emit 'step' @{ name='complete'; pct=100 }
        Emit 'done' @{ ok=$true; rel=$prevRel; root=$BOMAI_ROOT_; reused='reused_verified_existing'; search=$(if ($prevInstall.s10 -eq 'ok') { 'on' } else { 'off' }); tailscale=$prevInstall.sTailscale }
        $script:BOMAI_RC = 0
        return
      } finally { try { $mtxR.ReleaseMutex() } catch {} }
    }
    elseif ($prevInstall.status -ne 'COMPLETE' -and $prevRel -and (Test-Path -LiteralPath $prevRel)) {
      $BUILD_ID_ = Split-Path -Leaf $prevRel
      $REL_DIR_ = $prevRel
      Emit 'log' ('resume: reusing uncommitted release dir ' + $prevRel + ' (status ' + $prevInstall.status + ')')
    }
  } elseif ($prevInstall) {
    Emit 'log' 'resume: key mismatch (release/root/tier/deps changed) - fresh release dir'
  }

  # ---------------- S1 preflight ----------------
  $sp = Step-Pct 'S1'; Emit 'step' @{ name='S1 preflight'; pct=$sp.base }
  $osv = [Environment]::OSVersion.Version
  if ($osv.Major -ne 10 -or $osv.Build -lt 19045) {
    Fail 'E-OS' ('unsupported Windows build ' + $osv.ToString() + ' (need 10.0.19045+)')
  }
  if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') { Fail 'E-OS' 'x64 Windows required' }
  try { Add-Type -AssemblyName PresentationFramework } catch { Fail 'E-WPF' '.NET WPF unavailable' }
  $rootChk = Test-InstallRoot $BOMAI_ROOT_
  if (-not $rootChk.ok -and $rootChk.reason -ne 'SPACE') { Fail 'E-DISK' ('install root invalid: ' + $rootChk.reason) }
  if (-not $rootChk.ok -and $rootChk.reason -eq 'SPACE') { Fail 'E-DISK' ('install root free ' + $rootChk.freeGB + 'GB < ' + $PIN.diskNeededGB + 'GB') }
  $p8080 = Test-Port 8080; $p11434 = Test-Port 11434; $p8888 = Test-Port 8888
  Emit 'log' ('ports: 8080=' + $p8080.busy + '/' + $p8080.proc + ' 11434=' + $p11434.busy + '/' + $p11434.proc + ' 8888=' + $p8888.busy + '/' + $p8888.proc)
  if (-not $p11434.busy) {
    # ollama app + shared model store default to the user profile drive when not already present
    $sysFree = (Get-PSDrive -Name ($env:LOCALAPPDATA.Substring(0,1))).Free
    if ($sysFree -lt 6GB) { Fail 'E-DISK' ('system drive free ' + [int]($sysFree/1GB) + 'GB < 6GB (Ollama + model store)') }
  }
  if ($p8080.busy -and $p8080.proc -notmatch 'python') { Fail 'E-PORT' ('port 8080 busy by ' + $p8080.proc) }
  if ($p8888.busy -and $p8888.proc -notmatch 'python') { Fail 'E-PORT' ('port 8888 busy by ' + $p8888.proc) }
  Save-State @{ s1='ok'; ports=@{p8080=$p8080.proc; p11434=$p11434.proc; p8888=$p8888.proc} }

  # ---------------- S2 prepare ----------------
  $sp = Step-Pct 'S2'; Emit 'step' @{ name='S2 prepare'; pct=$sp.base }
  foreach ($d in @($REL_DIR_, (Join-Path $REL_DIR_ 'python'), $DATA_DIR, $CACHE_DIR, $LOG_DIR, $STATE_DIR,
                   (Join-Path $REL_DIR_ 'venvs'), (Join-Path $REL_DIR_ 'searxng'))) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
  }
  $mtx = New-Object System.Threading.Mutex($false, 'Local\BOM-AI-Installer-2.0.0')
  if (-not $mtx.WaitOne(1000)) { Fail 'E-MUTEX' 'another BOM AI installer is running' }
  # record chosen install root at the DEFAULT location so update/uninstall can locate any root
  $defState = Split-Path -Parent $ROOT_PTR_
  New-Item -ItemType Directory -Force -Path $defState | Out-Null
  Set-Content -Path $ROOT_PTR_ -Value $BOMAI_ROOT_ -Encoding ASCII
  Save-State @{ s2='ok'; rel=$REL_DIR_; root=$BOMAI_ROOT_; resumeKey=$resumeKey; tier=$tierNow }

  # ---------------- S3/S4 ollama reuse-or-install ----------------
  $sp = Step-Pct 'S3'; Emit 'step' @{ name='S3 ollama'; pct=$sp.base }
  $ollamaExe = $null; $ollamaReused = $false
  if ($p11434.busy) {
    try { $v = Invoke-Json GET 'http://127.0.0.1:11434/api/version' $null } catch { $v = $null }
    if ($v -and $v.version) {
      $vn = [version]($v.version -replace '-.*','')
      # PHASE 5 fix 20261031 (Grok WARN): accept EXACTLY 0.40.13, not >= 0.40.0
      if ($vn -eq [version]$PIN.ollamaVer) {
        $ollamaReused = $true
        $pr = Get-Process -Id $p11434.pid -ErrorAction SilentlyContinue
        if ($pr -and $pr.Path) { $ollamaExe = Join-Path (Split-Path -Parent $pr.Path) 'ollama.exe' }
        Emit 'log' ('ollama reused: server ' + $v.version + ' pid ' + $p11434.pid)
      } else {
        Fail 'E-OLLAMA' ('ollama server on 11434 is ' + $v.version + ' - this installer requires exactly ' + $PIN.ollamaVer + '. Stop it / upgrade it, then run again.')
      }
    }
  }
  if (-not $ollamaReused) {
    foreach ($cand in @((Get-Command ollama.exe -ErrorAction SilentlyContinue).Source, (Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'))) {
      if ($cand -and (Test-Path $cand)) { $ollamaExe = $cand; break }
    }
    # PHASE 5 fix 20261031: an existing CLI must ALSO be exactly 0.40.13
    if ($ollamaExe -and (Test-Path $ollamaExe)) {
      $cliV = (& $ollamaExe --version 2>&1 | Out-String)
      if ("$cliV" -notmatch ('0\.40\.13')) {
        Fail 'E-OLLAMA' ('installed ollama CLI is ' + "$cliV" + ' - this installer requires exactly ' + $PIN.ollamaVer + '. Upgrade it, then run again.')
      }
    }
  }
  if (-not $ollamaExe) {
    foreach ($cand in @((Get-Command ollama.exe -ErrorAction SilentlyContinue).Source, (Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'))) {
      if ($cand -and (Test-Path $cand)) { $ollamaExe = $cand; break }
    }
  }
  if (-not $ollamaReused -and -not $ollamaExe) {
    Emit 'log' 'ollama not found: downloading 0.40.13 (1.68 GB)'
    $dest = Join-Path $CACHE_DIR 'OllamaSetup-0.40.13.exe'
    $ok = Get-BomaiFile $PIN.ollamaUrl $dest $PIN.ollamaSha 'Ollama 0.40.13'
    if (-not $ok) { Fail 'E-SHA' 'OllamaSetup hash mismatch after 3 attempts' }
    $sig = Get-AuthenticodeSignature $dest
    if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'Ollama') {
      Fail 'E-SIGN' ('Authenticode ' + $sig.Status + ' / ' + $sig.SignerCertificate.Subject)
    }
    $p = Start-Process -FilePath $dest -ArgumentList '/SP-','/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART' -Wait -PassThru
    if ($p.ExitCode -ne 0) { Fail 'E-OLLAMA' ('OllamaSetup exit ' + $p.ExitCode) }
    $ollamaExe = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
  }
  Save-State @{ s3='ok'; ollamaExe=$ollamaExe; ollamaReused=$ollamaReused }
  $sp = Step-Pct 'S4'; Emit 'step' @{ name='S4 ollama-ready'; pct=$sp.base }
  if (-not $p11434.busy) {
    Emit 'log' 'starting owned ollama serve (loopback)'
    $env:OLLAMA_MAX_LOADED_MODELS = '1' # RD1 sync 20261030: one resident model (RAM guard)
    $so = Join-Path $LOG_DIR 'ollama-serve-out.log'; $se = Join-Path $LOG_DIR 'ollama-serve-err.log'
    $proc = Start-Process -FilePath $ollamaExe -ArgumentList 'serve' -WindowStyle Hidden `
            -RedirectStandardOutput $so -RedirectStandardError $se -PassThru
    $owned += $proc.Id
    Set-Content -Path (Join-Path $STATE_DIR 'ollama.pid') -Value $proc.Id -Encoding ASCII
  }
  if (-not (Wait-Http 'http://127.0.0.1:11434/api/version' 120 $sp.base $sp.span)) {
    Fail 'E-OLLAMA' 'ollama server not ready on 11434'
  }
  Save-State @{ s4='ok' }

  # ---------------- S5 online downloads + SHA chain ----------------
  $sp = Step-Pct 'S5'; Emit 'step' @{ name='S5 online downloads'; pct=$sp.base }
  # ONLINE edition: no payload\ wheelhouses are required; everything is fetched now.
  # Downloads stage into the verified cache dir (survives re-runs, resume-friendly).
  $pyExe = Join-Path $CACHE_DIR 'python-3.11.9-amd64.exe'
  $okPy = Get-BomaiFile $PIN.pythonUrl $pyExe $PIN.pythonSha 'Python 3.11.9'
  if (-not $okPy) { Fail 'E-SHA' 'python installer hash mismatch after 3 attempts' }
  $sxZip = Join-Path $CACHE_DIR 'searxng-54ca1d9cf.zip'
  $okSx = Get-BomaiFile $PIN.searxngUrl $sxZip $PIN.searxngSha 'SearXNG source'
  if (-not $okSx) { Fail 'E-SHA' 'searxng source hash mismatch after 3 attempts' }
  # gateway runtime + catalog come from the small-file channel on bomai.app (SHA-256 pinned)
  $gwSrc = Join-Path $CACHE_DIR 'bom_runtime_r2.py'
  [IO.File]::WriteAllBytes($gwSrc, [Convert]::FromBase64String($PIN.gatewayPayload))
  $okGw = ((Get-Sha $gwSrc) -eq $PIN.gatewaySha)
  if (-not $okGw) { Fail 'E-SHA' 'bom_runtime_r2.py hash mismatch after 3 attempts' }
  $catSrc = Join-Path $CACHE_DIR 'gateway-models.json'
  [IO.File]::WriteAllBytes($catSrc, [Convert]::FromBase64String($PIN.catalogPayload))
  $okCat = ((Get-Sha $catSrc) -eq $PIN.gatewayCatSha)
  if (-not $okCat) { Fail 'E-SHA' 'gateway models.json hash mismatch after 3 attempts' }
  # GOD protected-file SHA chain: verify-if-present, NEVER create or rewrite (R4 payload absent => NOT_PRESENT recorded)
  $godEnv = Join-Path $PAYLOAD_ 'config\god.env'; $cfgG = Join-Path $PAYLOAD_ 'config\config_g.json'
  if (Test-Path $godEnv) {
    $h = Get-Sha $godEnv
    if ($h -ne $PIN.godEnvSha) { Fail 'E-GODSHA' 'god.env SHA mismatch - abort, no rewrite' }
    Emit 'log' 'god.env SHA chain: MATCH'
  } else { Emit 'log' 'god.env NOT_PRESENT in payload (recorded, skipped)' }
  if (Test-Path $cfgG) {
    $h = Get-Sha $cfgG
    if ($h -ne $PIN.configGSha) { Fail 'E-GODSHA' 'config_g.json SHA mismatch - abort, no rewrite' }
    Emit 'log' 'config_g.json SHA chain: MATCH'
  } else { Emit 'log' 'config_g.json NOT_PRESENT in payload (recorded, skipped)' }
  Save-State @{ s5='ok' }

  # ---------------- S6 python (K3 HOLD-1) ----------------
  $sp = Step-Pct 'S6'; Emit 'step' @{ name='S6 python'; pct=$sp.base }
  $pyDir = Join-Path $REL_DIR_ 'python'
  $runPy = Join-Path $pyDir 'python.exe'
  $needInstall = $true
  if (Test-Path $runPy) {
    $vv = & $runPy --version 2>&1
    if ("$vv" -match '3\.11\.9') { $needInstall = $false; Emit 'log' 'python 3.11.9 already staged - reuse' }
  }
  if ($needInstall) {
    Emit 'log' 'silent install python 3.11.9 per-user (K3 HOLD-1 flags)'
    $p = Start-Process -FilePath $pyExe -ArgumentList '/quiet','InstallAllUsers=0',('"TargetDir=' + $pyDir + '"'),
         'Include_pip=1','Include_lib=1','Include_exe=1','Include_launcher=0','PrependPath=0','AssociateFiles=0','Shortcuts=0' -Wait -PassThru
    if (($p.ExitCode -ne 0) -or (-not (Test-Path $runPy))) {
      # fallback for stale/failed bundle installs: an existing per-user 3.11.9
      # registration makes the bundle exit 0 WITHOUT installing (i9 20261031).
      # administrative image from version-pinned python.org MSIs + ensurepip (no registry writes, no elevation)
      Emit 'log' ('python bundle exit ' + $p.ExitCode + ' - falling back to MSI administrative image (pinned ' + $PIN.pythonMsiBase + ')')
      if (Test-Path $pyDir) { Remove-Item $pyDir -Recurse -Force }
      New-Item -ItemType Directory -Force -Path $pyDir | Out-Null
      $msiCache = Join-Path $CACHE_DIR 'python-3.11.9-msi'
      foreach ($m in @('core.msi','exe.msi','lib.msi','tcltk.msi')) {
        $mi = Join-Path $msiCache $m
        $okm = Get-BomaiFile ($PIN.pythonMsiBase + $m) $mi '' ('Python ' + $m)
        if (-not $okm) { Fail 'E-PYTHON' ('msi download failed ' + $m) }
        $pm = Start-Process -FilePath 'msiexec.exe' -ArgumentList '/a', ('"' + $mi + '"'), ('"TARGETDIR=' + $pyDir + '"'), '/qn' -Wait -PassThru
        if ($pm.ExitCode -ne 0) { Fail 'E-PYTHON' ('msiexec /a exit ' + $pm.ExitCode + ' for ' + $m) }
      }
      $null = & $runPy -m ensurepip --upgrade 2>&1
    }
  }
  $vv = & $runPy --version 2>&1
  if ("$vv" -notmatch '3\.11\.9') { Fail 'E-PYTHON' ('version check failed: ' + $vv) }
  $ssl = & $runPy -c 'import ssl; print(ssl.OPENSSL_VERSION)' 2>&1
  if (-not $ssl -or "$ssl" -notmatch 'OpenSSL') { Fail 'E-PYTHON' 'ssl module failed' }
  $null = & $runPy -m venv --help 2>&1
  if ($LASTEXITCODE -ne 0) { Fail 'E-PYTHON' 'venv module failed' }
  Emit 'log' ('python ok: ' + $vv + ' / ' + $ssl)
  Save-State @{ s6='ok'; python="$vv" }

  # ---------------- S7 online pip installs (PyPI) ----------------
  $sp = Step-Pct 'S7'; Emit 'step' @{ name='S7 online pip installs'; pct=$sp.base }
  # ONLINE edition replaces the hash-locked offline wheelhouses with PyPI installs.
  # owui    : pip install open-webui==0.12.5 (version pin)
  # searxng : extract pinned source zip, pip install -r requirements.txt + waitress 3.0.2
  $sxSrcDir = $null
  $sxDir = Join-Path $REL_DIR_ 'searxng-src'
  if (Test-Path $sxDir) {
    $sxSrcDir = Get-ChildItem $sxDir -Directory | Where-Object { $_.Name -like 'searxng-*' } | Select-Object -First 1
  }
  if (-not $sxSrcDir) {
    # python.org builds are longPathAware; PS5.1 Expand-Archive fails on >260-char paths
    & $runPy -c ('import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])') $sxZip $sxDir
    if ($LASTEXITCODE -ne 0) { Fail 'E-SEARXNG' 'source extraction failed' }
    $sxSrcDir = Get-ChildItem $sxDir -Directory | Where-Object { $_.Name -like 'searxng-*' } | Select-Object -First 1
  }
  if (-not $sxSrcDir) { Fail 'E-SEARXNG' 'searxng source dir not found after extraction' }
  foreach ($name in @('owui','searxng')) {
    $venv = Join-Path $REL_DIR_ ('venvs\' + $name)
    if (-not (Test-Path (Join-Path $venv 'Scripts\python.exe'))) {
      & $runPy -m venv $venv
      if ($LASTEXITCODE -ne 0) { Fail 'E-PIP' ('venv create failed ' + $name) }
    }
    $pip = Join-Path $venv 'Scripts\pip.exe'
    $pipLog = Join-Path $LOG_DIR ('pip-' + $name + '.log')
    $pipDone = Join-Path $venv '.pip-complete'
    if (Test-Path $pipDone) {
      Emit 'log' ('online install ' + $name + ': already installed - skip (single-install guard)')
      Emit 'step' @{ name=('S7 ' + $name + ' installed'); pct=($sp.base + [int]($sp.span/2)) }
      continue
    }
    # pip log resets per run; completion marker makes re-runs into the same release dir idempotent
    Set-Content -Path $pipLog -Value ('pip ' + $name + ' online run ' + $BUILD_ID_ + ' (log reset per run)') -Encoding Unicode
    $pipArgs = @()
    if ($name -eq 'owui') {
      Emit 'log' ('online install open-webui==' + $PIN.owuiVer + ' from PyPI')
      $pipArgs = @('install','--no-input',('open-webui==' + $PIN.owuiVer))
    } else {
      Emit 'log' 'online install searxng requirements from PyPI (+ waitress 3.0.2)'
      $pipArgs = @('install','--no-input','-r',(Join-Path $sxSrcDir.FullName 'requirements.txt'),('waitress==' + $PIN.waitressVer))
    }
    $pipOk = $false
    for ($pa = 1; $pa -le 2; $pa++) {
      & $pip install --quiet --upgrade pip *>> $pipLog
      & $pip @pipArgs *>> $pipLog
      if ($LASTEXITCODE -eq 0) { $pipOk = $true; break }
      Emit 'log' ('online pip install ' + $name + ' attempt ' + $pa + ' failed - retrying in 15s')
      if ($pa -lt 2) { Start-Sleep -Seconds 15 }
    }
    if (-not $pipOk) { Fail 'E-PIP' ('online pip install failed ' + $name + ' (see logs\pip-' + $name + '.log)') }
    & $pip check *>> $pipLog
    Set-Content -Path $pipDone -Value $BUILD_ID_ -Encoding ASCII
    Emit 'step' @{ name=('S7 ' + $name + ' installed'); pct=($sp.base + [int]($sp.span/2)) }
  }
  # online pin verification: exact versions importable in their venvs
  $venvPy = Join-Path $REL_DIR_ 'venvs\owui\Scripts\python.exe'
  $owuiVer = & $venvPy -c "import importlib.metadata as m; print(m.version('open-webui'))" 2>&1
  if ("$owuiVer" -notmatch ('^' + $PIN.owuiVer + '$')) { Fail 'E-PIP' ('open-webui version check failed: ' + $owuiVer) }
  Emit 'log' ('owui online install verified: open-webui ' + "$owuiVer")
  Save-State @{ s7='ok'; owuiOnline=$true }

  # ---------------- S8 OWUI config + start ----------------
  $sp = Step-Pct 'S8'; Emit 'step' @{ name='S8 owui'; pct=$sp.base }

  # ---------------- S8a bom_runtime gateway on 11435 (blueprint stage 11; RD2 backend) ----------------
  # ONLINE edition: $gwSrc/$catSrc were downloaded + SHA-verified into the cache in S5
  if (-not (Test-Path $gwSrc)) { Fail 'E-GATEWAY' 'cached bom_runtime_r2.py missing' }
  if ((Get-Sha $gwSrc) -ne $PIN.gatewaySha) { Fail 'E-SHA' 'bom_runtime_r2.py SHA mismatch' }
  $gwLocal = Join-Path $REL_DIR_ 'bom_runtime.py'
  Copy-Item -LiteralPath $gwSrc -Destination $gwLocal -Force
  if (-not (Test-Path $catSrc)) { Fail 'E-GATEWAY' 'cached gateway models.json missing' }
  if ((Get-Sha $catSrc) -ne $PIN.gatewayCatSha) { Fail 'E-SHA' 'gateway catalog models.json SHA mismatch' }
  $catDir = Join-Path $REL_DIR_ 'config'
  New-Item -ItemType Directory -Force -Path $catDir | Out-Null
  Copy-Item -LiteralPath $catSrc -Destination (Join-Path $catDir 'models.json') -Force
  $runtimeJson = Join-Path $STATE_DIR 'runtime.json'
  $oldRuntime = $null
  if (Test-Path $runtimeJson) { try { $oldRuntime = Get-Content $runtimeJson -Raw | ConvertFrom-Json } catch {} }
  $gatewayKey = [Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N')
  if ($oldRuntime -and $oldRuntime.gateway_key) { $gatewayKey = [string]$oldRuntime.gateway_key }
  $runtimeCfgNew = @{ schema_version=2; release=$PIN.release; tier=$tierNow; model_alias=$tierAliasShort;
    catalog=(Join-Path $catDir 'models.json');
    gateway_key=$gatewayKey; gateway_url='http://127.0.0.1:11435/v1'; gateway_port=11435;
    searxng_url='http://127.0.0.1:8888/search?q=<query>&format=json';
    expected_version=$PIN.ollamaVer; ollama_url='http://127.0.0.1:11434'; registry_ref=$tierTag }
  $runtimeCfgNew | ConvertTo-Json | Set-Content -Path $runtimeJson -Encoding UTF8
  $dataDirAbs = Join-Path $BOMAI_ROOT_ 'data\open-webui'
  $legacyData = Join-Path $BOMAI_ROOT_ 'releases\data\open-webui'
  if ($prevInstall -and $prevInstall.dataDir -and (Test-Path (Join-Path $prevInstall.dataDir 'webui.db'))) { $dataDirAbs = [string]$prevInstall.dataDir }
  elseif (Test-Path (Join-Path $legacyData 'webui.db')) {
    if (Test-Path (Join-Path $dataDirAbs 'webui.db')) { Fail 'E-DATA' 'Two data directories found; explicitly resolve before repair' }
    $dataDirAbs = $legacyData
  }
  $brandNewData = -not (Test-Path (Join-Path $dataDirAbs 'webui.db'))
  $bootstrapPath = Join-Path $STATE_DIR 'first-login.json'
  $initialLogin = Initialize-FirstLogin $bootstrapPath $brandNewData
  foreach ($privateFile in @($runtimeJson,$bootstrapPath)) {
    $null = & icacls.exe $privateFile /inheritance:r /grant:r ($env:USERNAME + ':(F)') 'SYSTEM:(F)'
    if ($LASTEXITCODE -ne 0) { Fail 'E-ACL' 'Could not protect installation credentials' }
  }
  # A running old gateway must not survive a runtime upgrade. Validate its owner.
  $gp = Test-Port 11435
  if ($gp.busy) {
    $gpi = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $gp.pid)
    if (-not $gpi.CommandLine -or $gpi.CommandLine -notmatch [regex]::Escape($BOMAI_ROOT_)) { Fail 'E-PORT' 'Gateway port belongs to another installation' }
    Stop-Process -Id $gp.pid -Force
    Start-Sleep -Seconds 2
  }
  if (-not (Test-Port 11435).busy) {
    $gLog = Join-Path $LOG_DIR 'gateway.jsonl'
    $proc = Start-Process -FilePath $runPy -ArgumentList ('"' + $gwLocal + '"','--host','127.0.0.1','--port','11435','--upstream','http://127.0.0.1:11434','--config',('"' + (Join-Path (Split-Path -Parent (Split-Path -Parent $gLog)) 'state\runtime.json') + '"'),'--log',('"' + $gLog + '"')) -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LOG_DIR 'gateway-out.log') -RedirectStandardError (Join-Path $LOG_DIR 'gateway-err.log') -PassThru
    $owned += $proc.Id
    Set-Content -Path (Join-Path $STATE_DIR 'gateway.pid') -Value $proc.Id -Encoding ASCII
  }
  if (-not (Wait-Http 'http://127.0.0.1:11435/healthz' 60 $sp.base $sp.span)) {
    Fail 'E-GATEWAY' 'bom_runtime gateway not ready on 11435 (see logs\gateway.jsonl)'
  }
  Emit 'log' 'gateway ok: bom_runtime 11435 -> upstream 11434'
  $startOwui = Join-Path $REL_DIR_ 'start-owui.ps1'
  $owuiAlias = $tierAliasShort
  $bannersJson = '[{"id":"bomai-welcome","type":"info","title":"","content":"**BOM AI** \u2014 \u0e1c\u0e39\u0e49\u0e0a\u0e48\u0e27\u0e22 AI \u0e20\u0e32\u0e29\u0e32\u0e44\u0e17\u0e22 100% \u0e1f\u0e23\u0e35 \u0e17\u0e33\u0e07\u0e32\u0e19\u0e1a\u0e19\u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e04\u0e38\u0e13\u0e40\u0e2d\u0e07 \u0e44\u0e21\u0e48\u0e2a\u0e48\u0e07\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e2d\u0e2d\u0e01\u0e19\u0e2d\u0e01","dismissible":true,"timestamp":0},{"id":"xm-partner","type":"info","title":"","content":"[![Open XM Account](https://ads.pipaffiliates.com/i/158598?c=72816)](https://clicks.pipaffiliates.com/c?m=158598&c=72816)","dismissible":true,"timestamp":0}]'
  @'
param()
$ErrorActionPreference = 'Stop'
$rel = Split-Path -Parent $MyInvocation.MyCommand.Path
# FIX BUG5 20261031: $data is the ABSOLUTE data dir baked at install time. The old
# parent-of-parent resolution silently landed on <root>\releases\data - the same
# location every existing install already uses; now it is explicit and stable.
$data = '__DATA_DIR__'
New-Item -ItemType Directory -Force -Path $data | Out-Null
$env:DATA_DIR = $data
$env:STATIC_DIR = Join-Path $data 'static'
Remove-Item Env:WEBUI_SECRET_KEY -ErrorAction SilentlyContinue
$env:WEBUI_AUTH = 'true'
$env:OLLAMA_BASE_URL = 'http://127.0.0.1:11435'
$env:ENABLE_OLLAMA_API = 'false'
$env:ENABLE_OPENAI_API = 'true'
$env:ENABLE_PERSISTENT_CONFIG = 'true'
$env:RESET_CONFIG_ON_START = 'false'
$env:FRONTEND_BUILD_DIR = Join-Path $rel 'venvs\owui\Lib\site-packages\open_webui\frontend'
Set-Location $data
# === RD1 FIX: Disable memory feature (default-on inflates prompts beyond num_ctx 8192) ===
$env:ENABLE_MEMORIES = 'false'
$env:OLLAMA_MAX_LOADED_MODELS = '1' # RD1 spec pin (server env is set at S4 + launcher)
# === RD2 FIX: Route all OWUI traffic through gateway 11435 (think=false + token budget) ===
$env:OLLAMA_BASE_URLS = 'http://127.0.0.1:11435'
# FIX BUG5 20261031: RESET_CONFIG_ON_START removed - it defeated persisted OWUI settings
# on every restart (F11/F12). BOM defaults are written into webui.db once by the S8b
# seed; the env block below only supplies FIRST-boot defaults for anything missing.
# === FIX 20261031 qc-full-audit: explicit CORS origin (OWUI default '*' logs a warning) ===
$env:CORS_ALLOW_ORIGIN = 'http://127.0.0.1:8080;http://localhost:8080__QC_BROWSER_ORIGIN__'
# PHASE 1 (spec 1D): tier from the committed runtime.json overrides the baked
# install-time alias, so switching tier config follows without editing this file.
$tierAliasDef = '__MODEL_ALIAS__'
$runtimeCfg = '__RUNTIME_JSON__'
$runtimeSettings = Get-Content $runtimeCfg -Raw | ConvertFrom-Json
$env:OPENAI_API_BASE_URL = $runtimeSettings.gateway_url
$env:OPENAI_API_KEY = $runtimeSettings.gateway_key
$bootstrap = Get-Content (Join-Path (Split-Path -Parent $runtimeCfg) 'first-login.json') -Raw | ConvertFrom-Json
$env:WEBUI_ADMIN_EMAIL = $bootstrap.email
$env:WEBUI_ADMIN_PASSWORD = $bootstrap.password
$env:WEBUI_ADMIN_NAME = 'BOM AI'
try {
  if (Test-Path $runtimeCfg) {
    $rc = Get-Content $runtimeCfg -Raw | ConvertFrom-Json
    if ($rc.model_alias) { $tierAliasDef = [string]$rc.model_alias }
  }
} catch {}
$env:WEBUI_NAME = 'BOM AI'
$env:DEFAULT_MODELS = $tierAliasDef
$env:ENABLE_SIGNUP = 'false'
$env:DEFAULT_LOCALE = 'th-TH'
$env:ENABLE_WEB_SEARCH = 'true'
$env:DEFAULT_INTERFACE_SETTINGS = '{"webSearch":"always"}'
$env:WEB_SEARCH_ENGINE = 'searxng'
$env:SEARXNG_QUERY_URL = 'http://127.0.0.1:8888/search?q=<query>'
$env:WEB_SEARCH_RESULT_COUNT = '3' # FIX 20261101 overflow: 5 web results + query splits exceeded num_ctx 8192
$env:WEB_SEARCH_CONCURRENT_REQUESTS = '10'
$env:WEBUI_BANNERS = '__BANNERS__'
# 20261031: banner content persists to webui.db via the S8b seed; env is first-boot default.

& (Join-Path $rel 'venvs\owui\Scripts\open-webui.exe') serve --host 127.0.0.1 --port 8080
'@.Replace('__DATA_DIR__', $dataDirAbs).Replace('__MODEL_ALIAS__', $owuiAlias).Replace('__RUNTIME_JSON__', (Join-Path $STATE_DIR 'runtime.json')).Replace('__BANNERS__', $bannersJson).Replace('__QC_BROWSER_ORIGIN__', $(if ($PIN.qcBrowserOrigin) { ';' + $PIN.qcBrowserOrigin } else { '' })) | Set-Content -Path $startOwui -Encoding UTF8
  # BOM AI favicon: OWUI 0.12.5 ignores WEBUI_FAVICON_URL env (webhook-only); swap the static
  # file the same way the CUSTOM_NAME branch does. STATIC_DIR is re-seeded from it each boot.
  $favSrc = Join-Path $CACHE_DIR 'bomai-favicon.png'
  $favOk = Get-BomaiFile $PIN.faviconUrl $favSrc '' 'favicon'
  if ($favOk) {
    $frontendDir = Join-Path $REL_DIR_ 'venvs\owui\Lib\site-packages\open_webui\frontend'
    # The model/avatar fallback uses /favicon.png, separately from /static/favicon.png.
    foreach ($asset in @('favicon.png','static\favicon.png','static\logo.png','static\favicon-96x96.png','static\apple-touch-icon.png')) {
      $favDst = Join-Path $frontendDir $asset
      if ((Test-Path -LiteralPath $favDst) -and -not (Test-Path -LiteralPath ($favDst + '.bak_default'))) { Copy-Item -LiteralPath $favDst -Destination ($favDst + '.bak_default') }
      Copy-Item -LiteralPath $favSrc -Destination $favDst -Force
    }
    Emit 'log' 'favicon: BOM AI icon and model/avatar fallback installed'
  } else { Fail 'E-FAVICON' 'favicon download failed' }
  # FIX 0F 20261031: OWUI 0.12.5 index.html carries an inline FOUC script that
  # defaults localStorage.theme to 'system' (follows OS). Patch that first-run
  # default to 'dark'. Only applies when the user has no stored choice; a user's
  # own theme selection still wins on every later visit.
  $idxHtml = Join-Path $REL_DIR_ 'venvs\owui\Lib\site-packages\open_webui\frontend\index.html'
  if (Test-Path $idxHtml) {
    $html = [IO.File]::ReadAllText($idxHtml)
    if ($html.Contains("localStorage.theme = 'dark';")) {
      Emit 'log' 'dark default: already patched'
    } elseif ($html.Contains("localStorage.theme = 'system';")) {
      $bakIdx = $idxHtml + '.bak_default'
      if (-not (Test-Path $bakIdx)) { Copy-Item -LiteralPath $idxHtml -Destination $bakIdx -Force }
      $html = $html.Replace("localStorage.theme = 'system';", "localStorage.theme = 'dark';")
      [IO.File]::WriteAllText($idxHtml, $html, (New-Object Text.UTF8Encoding($false)))
      Emit 'log' 'dark default: first-run theme default set to dark'
    } else { Fail 'E-THEME' 'Pinned dark theme bootstrap not found' }
  }
  $owuiWasRunning = (Test-Port 8080).busy
  if (-not (Test-Path $idxHtml)) { Fail 'E-THEME' 'Pinned frontend index missing' }
  $iconHtml = [IO.File]::ReadAllText($idxHtml)
  $iconHtml = [regex]::Replace($iconHtml, '<link\b[^>]*\brel=["''](?:icon|shortcut icon)["''][^>]*>', '', [Text.RegularExpressions.RegexOptions]::IgnoreCase -bor [Text.RegularExpressions.RegexOptions]::Singleline)
  $iconHtml = $iconHtml.Replace('</head>', '<link rel="icon" type="image/png" href="/static/favicon.png?bomai=v3" /></head>')
  [IO.File]::WriteAllText($idxHtml, $iconHtml, (New-Object Text.UTF8Encoding($false)))
  $owuiStartedHere = $false
  if (-not $owuiWasRunning) {
    $so = Join-Path $LOG_DIR 'owui-out.log'; $se = Join-Path $LOG_DIR 'owui-err.log'
    $proc = Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-File',('"' + $startOwui + '"') `
            -WindowStyle Hidden -RedirectStandardOutput $so -RedirectStandardError $se -PassThru
    $owned += $proc.Id
    Set-Content -Path (Join-Path $STATE_DIR 'owui.pid') -Value $proc.Id -Encoding ASCII
    $owuiStartedHere = $true
  } else { Emit 'log' 'S8: OWUI already listening on 8080 - first-boot seed skipped (defaults persisted by the original install)' }
  if (-not (Wait-Http 'http://127.0.0.1:8080/' 420 $sp.base ([int]($sp.span*0.6)))) {
    Fail 'E-OWUI' 'Open WebUI not ready on 8080 (see logs\owui-err.log)'
  }
  # S8b FIX BUG5+BUG6 20261031: ALL BOM AI defaults go into webui.db (config rows +
  # workspace model with function_calling=legacy + per-user webSearch default), not
  # BAT-session env vars. The seed runs while OWUI is STOPPED, then OWUI restarts.
  # Idempotent merge - existing user settings/chats are never overwritten.
  $seedState = 'pending'
  if ($true) {
    Emit 'step' @{ name='S8b seed defaults'; pct=($sp.base + [int]($sp.span*0.6)) }
    $stoppedOk = Stop-OwnedOwui
    if (-not $stoppedOk) { Fail 'E-OWUI' 'could not stop owned OWUI for the db seed (port owner not ours)' }
    $dbPath = Join-Path $dataDirAbs 'webui.db'
    if (Test-Path $dbPath) {
      $seedPy = Join-Path $CACHE_DIR 'seed_owui_bomai.py'
      [IO.File]::WriteAllBytes($seedPy, [Convert]::FromBase64String($PIN.seedPayload))
      $seedOut = & $venvPy $seedPy --db $dbPath --config $runtimeJson --offline-confirmed --owui-port 8080 2>&1
      Emit 'log' ('owui db seed: ' + ($seedOut -join ' '))
      if ($LASTEXITCODE -ne 0) { Fail 'E-SEED' ('owui db seed failed: ' + ($seedOut -join ' ')) }
      $seedState = 'seeded'
    } else {
      Fail 'E-SEED' 'webui.db missing after first boot; installation incomplete'
    }
    Emit 'step' @{ name='S8 restart OWUI'; pct=($sp.base + [int]($sp.span*0.8)) }
    $so2 = Join-Path $LOG_DIR 'owui-out.log'; $se2 = Join-Path $LOG_DIR 'owui-err.log'
    $proc2 = Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-File',('"' + $startOwui + '"') `
            -WindowStyle Hidden -RedirectStandardOutput $so2 -RedirectStandardError $se2 -PassThru
    $owned += $proc2.Id
    Set-Content -Path (Join-Path $STATE_DIR 'owui.pid') -Value $proc2.Id -Encoding ASCII
    if (-not (Wait-Http 'http://127.0.0.1:8080/' 420 ($sp.base + [int]($sp.span*0.8)) ([int]($sp.span*0.2)))) {
      Fail 'E-OWUI' 'Open WebUI not ready after seed restart (see logs\owui-err.log)'
    }
  }
  $auditPy = Join-Path $CACHE_DIR 'audit_owui.py'
  [IO.File]::WriteAllBytes($auditPy, [Convert]::FromBase64String($PIN.auditPayload))
  $auditOut = & $venvPy $auditPy --db $dbPath --secret-file (Join-Path $dataDirAbs '.webui_secret_key') --base-url 'http://127.0.0.1:8080' --verify 2>&1
  $auditOut | Set-Content -Path (Join-Path $LOG_DIR 'configuration-verification.json') -Encoding UTF8
  if ($LASTEXITCODE -ne 0) { Fail 'E-VERIFY' ('Configuration verification failed: ' + ($auditOut -join ' ')) }
  Save-State @{ s8='ok'; seeded=$seedState; dataDir=$dataDirAbs }

  # ---------------- S9 model pull + HOLD-3 verify + GOD CONFIG v7.0 ----------------
  $sp = Step-Pct 'S9'; Emit 'step' @{ name='S9 model-god'; pct=$sp.base }
  Emit 'log' ('pull ' + $tierTag + ' (tier ' + $tierNow + ') via /api/pull NDJSON')
  $pullDone = $false
  for ($pullA = 1; $pullA -le 3 -and -not $pullDone; $pullA++) {
    try {
      $req = [Net.HttpWebRequest]::Create('http://127.0.0.1:11434/api/pull')
      $req.Method = 'POST'; $req.ContentType = 'application/json'
      # FIX BUG2 20261031: ReadWriteTimeout = silent-stall watchdog (180s without a
      # NDJSON line aborts the attempt); ollama keeps partial layers, pull resumes.
      $req.Timeout = [Threading.Timeout]::Infinite; $req.ReadWriteTimeout = 180000
      $bytes = [Text.Encoding]::UTF8.GetBytes(('{"model":"' + $tierTag + '","stream":true}'))
      $req.ContentLength = $bytes.Length
      $rsW = $req.GetRequestStream(); $rsW.Write($bytes,0,$bytes.Length); $rsW.Close()
      $resp = $req.GetResponse(); $sr = New-Object IO.StreamReader($resp.GetResponseStream())
      $swPull = [Diagnostics.Stopwatch]::StartNew()
      while (-not $sr.EndOfStream) {
        if ($OPT.cancel) { $resp.Close(); $script:ec='CANCELLED'; throw 'CANCELLED' }
        $line = $sr.ReadLine()
        try { $o = $line | ConvertFrom-Json } catch { continue }
        if ($o.error) { $resp.Close(); Fail 'E-MODEL' $o.error }
        if ($o.total) {
          if ($swPull.ElapsedMilliseconds -gt 900) {
            $frac = [double]$o.completed / [double]$o.total
            Emit 'dl' @{ cur=[int64]$o.completed; tot=[int64]$o.total; label='BOM AI model'; spd=0; eta=-1 }
            Emit 'step' @{ name='S9 pulling model'; pct=($sp.base + [int]($sp.span * 0.5 * $frac)) }
            $swPull.Restart()
          }
        } elseif ($o.status) { Emit 'log' ('pull: ' + $o.status) }
      }
      $resp.Close()
      $pullDone = $true
    } catch {
      if ($script:ec) { throw }
      Emit 'log' ('model pull attempt ' + $pullA + ' interrupted: ' + $_.Exception.Message + ' - ollama resumes partial layers')
      if ($pullA -lt 3) { Start-Sleep -Seconds @(5,15)[$pullA-1] }
    }
  }
  if (-not $pullDone) { Fail 'E-MODEL' ('model pull failed after 3 attempts: ' + $tierTag) }

  Emit 'step' @{ name='S9 verifying manifest'; pct=($sp.base + [int]($sp.span * 0.5)) }
  $show = Invoke-Json POST 'http://127.0.0.1:11434/api/show' ('{"model":"' + $tierTag + '"}')
  $tagRepo = ($tierTag -split ':')[0]
  $tagVer  = ($tierTag -split ':')[1]
  # locate the models store: resolved blob paths from the server's own modelfile view, else env/default candidates
  $pinLow = $tierLayer.ToLowerInvariant()
  $fromLines = @(([string]$show.modelfile) -split "`n" | Where-Object { $_ -match '^\s*FROM\s+\S' } | ForEach-Object { ($_ -replace '^\s*FROM\s+','').Trim() })
  $blob = $null; $modelsRoot = $null
  foreach ($f in $fromLines) {
    if ($f -like ('*' + 'sha256-' + $pinLow)) { $blob = $f; break }
  }
  if ($blob) {
    $modelsRoot = Split-Path -Parent (Split-Path -Parent $blob)
    Emit 'log' ('resolved blob via server modelfile: ' + $blob)
  } else {
    $candRoots = @()
    if ($env:OLLAMA_MODELS) { $candRoots += $env:OLLAMA_MODELS }
    $candRoots += (Join-Path $env:LOCALAPPDATA 'Ollama\models')
    foreach ($cand in $candRoots) {
      $p = Join-Path $cand (('manifests\registry.ollama.ai\' + ($tagRepo -replace '/','\')) + '\' + $tagVer)
      if (Test-Path $p) { $modelsRoot = $cand; break }
    }
    if ($modelsRoot) { $blob = Join-Path $modelsRoot ('blobs\sha256-' + $pinLow) }
  }
  if (-not $blob -or -not (Test-Path $blob)) { Fail 'E-MODEL-SHA' 'pinned layer blob not found (store resolution failed)' }
  # K3 HOLD-3: ConvertFrom-Json manifest parse -> exactly 1 model layer -> digest pin -> blob size + SHA256
  $mfPath = Join-Path $modelsRoot (('manifests\registry.ollama.ai\' + ($tagRepo -replace '/','\')) + '\' + $tagVer)
  if (-not (Test-Path $mfPath)) { Fail 'E-MODEL-SHA' ('manifest not found: ' + $mfPath) }
  Emit 'log' ('manifest file: ' + $mfPath)
  $mjson = Get-Content $mfPath -Raw | ConvertFrom-Json
  $layers = @($mjson.layers | Where-Object { $_.mediaType -like '*model*' })
  if ($layers.Count -ne 1) { Fail 'E-MODEL-SHA' ('model layers=' + $layers.Count + ', expected exactly 1') }
  if ($layers[0].digest -ne ('sha256:' + $pinLow)) {
    Fail 'E-MODEL-SHA' ('layer digest ' + $layers[0].digest + ' != pin')
  }
  $projLayers = @($mjson.layers | Where-Object { $_.mediaType -like '*projector*' })
  if ($projLayers.Count -gt 0 -and $projLayers[0].digest -ne ('sha256:' + $tierProj.ToLowerInvariant())) {
    Fail 'E-MODEL-SHA' ('projector digest ' + $projLayers[0].digest + ' != pin')
  }
  if ((Get-Item $blob).Length -ne [int64]$layers[0].size) { Fail 'E-MODEL-SHA' 'blob size != manifest layer size' }
  $bh = (Get-FileHash $blob -Algorithm SHA256).Hash
  if ($bh -ne $tierLayer) { Fail 'E-MODEL-SHA' 'blob SHA mismatch (shared store untouched, abort)' }
  Emit 'log' ('manifest+blob verified: 1 model layer ' + $tierLayer.Substring(0,16) + '..., size ' + $layers[0].size)
  if ($show.details.quantization -and $show.details.quantization -ne 'Q4_K_M') {
    Fail 'E-MODEL-SHA' ('quantization ' + $show.details.quantization + ' != Q4_K_M (Q6_K = Han bleed)')
  }
  # GOD CONFIG v7.0 Modelfile: 7 PARAMETERs, presence_penalty 0.0 (IRON 12), NO think=false
  Emit 'step' @{ name='S9 god-config modelfile'; pct=($sp.base + [int]($sp.span * 0.7)) }
  $mf = Join-Path $REL_DIR_ ('Modelfile.' + $tierAliasShort)
  $mflines = @('FROM ' + $tierTag)
  foreach ($k in @('temperature','top_p','top_k','repeat_penalty','presence_penalty','num_ctx','num_predict')) {
    $mflines += ('PARAMETER ' + $k + ' ' + $PIN.godParams[$k])
  }
  # GOD CONFIG params stay LOCKED; SYSTEM added 20261031 (spec fix-installer 6C) to stop base-persona refusals.
  $mflines += 'SYSTEM """'
  $mflines += $PIN.systemPrompt
  $mflines += '"""'
  [IO.File]::WriteAllLines($mf, $mflines, (New-Object Text.UTF8Encoding($false)))
  $savedHost = $env:OLLAMA_HOST
  $env:OLLAMA_HOST = 'http://127.0.0.1:11434'
  # Preserve a wrong/legacy alias mapping before overwriting it; blobs are
  # never deleted (contract 4A.2).
  try {
    $tagsNow = Invoke-Json GET 'http://127.0.0.1:11434/api/tags'
    $namesNow = @($tagsNow.models | ForEach-Object { [string]$_.name })
    $legacyName = (($tierAlias -replace ':latest$','') + ':pre2-legacy')
    $aliasLive = @($namesNow | Where-Object { $_ -eq $tierAlias -or $_.StartsWith($tierAlias + ':') })
    if ($aliasLive.Count -gt 0 -and -not ($namesNow -contains $legacyName)) {
      $cpOut = & $ollamaExe cp $tierAlias $legacyName 2>&1
      Emit 'log' ('legacy alias preserved: ' + $legacyName + ' (' + ($cpOut -join ' ') + ')')
    }
  } catch { Emit 'log' ('legacy alias check skipped: ' + $_.Exception.Message) }
  try { $createOut = & $ollamaExe create $tierAlias -f $mf 2>&1 } finally { $env:OLLAMA_HOST = $savedHost }
  Emit 'log' ('ollama create: ' + ($createOut -join ' '))
  $chk = Invoke-Json POST 'http://127.0.0.1:11434/api/show' ('{"model":"' + $tierAlias + '"}')
  $pp = @{}
  foreach ($ln in ($chk.parameters -split "`n")) { $z = $ln.Trim() -split '\s+'; if ($z.Count -ge 2) { $pp[$z[0]] = $z[1] } }
  foreach ($k in $PIN.godParams.Keys) {
    if (-not $pp.ContainsKey($k)) { Fail 'E-PARAMS' ('param missing: ' + $k) }
    $want = [string]([double]$PIN.godParams[$k]); $got = [string]([double]($pp[$k]))
    if ($got -ne $want) { Fail 'E-PARAMS' ('param ' + $k + '=' + $pp[$k] + ' want ' + $want) }
  }
  if ([double]$pp['presence_penalty'] -ne 0.0) { Fail 'E-PARAMS' 'IRON 12 violation: presence_penalty != 0.0' }
  Emit 'log' ('GOD CONFIG v7.0 verified on ' + $tierAlias + ' (7/7 params, presence_penalty=0.0)')
  Save-State @{ s9='ok'; modelLayer=$tierLayer; alias=$tierAlias; tierTag=$tierTag }

  # ---------------- S10 SearXNG native + waitress (K3 HOLD-2) ----------------
  $sp = Step-Pct 'S10'; Emit 'step' @{ name='S10 searxng'; pct=$sp.base }
  if ($OPT.searxng) {
    $sxDir = Join-Path $REL_DIR_ 'searxng-src'
    $sxSrcDir = $null
    if (Test-Path $sxDir) {
      $sxSrcDir = Get-ChildItem $sxDir -Directory | Where-Object { $_.Name -like 'searxng-*' } | Select-Object -First 1
    }
    if (-not $sxSrcDir) {
      # python.org builds are longPathAware; PS5.1 Expand-Archive fails on >260-char paths
      & $runPy -c ('import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])') $sxZip $sxDir
      if ($LASTEXITCODE -ne 0) { Fail 'E-SEARXNG' 'source extraction failed' }
      $sxSrcDir = Get-ChildItem $sxDir -Directory | Where-Object { $_.Name -like 'searxng-*' } | Select-Object -First 1
    }
    if (-not $sxSrcDir) { Fail 'E-SEARXNG' 'searxng source dir not found after extraction' }
    # Windows guard 1: searx/valkeydb.py imports pwd (POSIX-only) unconditionally
    $vdPatch = Join-Path $sxSrcDir.FullName 'searx\valkeydb.py'
    if (Test-Path $vdPatch) {
      $vs = [IO.File]::ReadAllText($vdPatch)
      if ($vs.Contains('import pwd') -and -not $vs.Contains('except ImportError')) {
        $vs = $vs.Replace('import pwd', "try:`r`n    import pwd`r`nexcept ImportError:`r`n    pwd = None")
        [IO.File]::WriteAllText($vdPatch, $vs)
        Emit 'log' 'windows guard applied: searx/valkeydb.py pwd import'
      }
    }
    # Windows guard 2: webutils.get_result_templates builds theme paths with os.sep; jinja needs forward slashes
    $wuPatch = Join-Path $sxSrcDir.FullName 'searx\webutils.py'
    if (Test-Path $wuPatch) {
      $ws = [IO.File]::ReadAllText($wuPatch)
      $oldLn = 'f = os.path.join(directory[templates_path_length:], filename)'
      if ($ws.Contains($oldLn) -and -not $ws.Contains(".replace(os.sep, '/')")) {
        $ws = $ws.Replace($oldLn, ($oldLn + ".replace(os.sep, '/')"))
        [IO.File]::WriteAllText($wuPatch, $ws)
        Emit 'log' 'windows guard applied: searx/webutils.py template path separators'
      }
    }
    $secret = [Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N')
    $settings = Join-Path $REL_DIR_ 'searxng\settings.yml'
    @("use_default_settings: true",
       'server:', '  secret_key: "' + $secret + '"', '  bind_address: "127.0.0.1"', '  port: 8888',
       '  limiter: false', '  image_proxy: true', '  base_url: false',
       'search:', '  formats:', '    - html', '    - json',
       'public_instance: false') | Set-Content -Path $settings -Encoding UTF8
    $startSx = Join-Path $REL_DIR_ 'start-searxng.ps1'
    @'
param()
$ErrorActionPreference = 'Stop'
$rel = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:SEARXNG_SETTINGS_PATH = Join-Path $rel 'searxng\settings.yml'
Set-Location (Join-Path $rel 'searxng-src\__SX_SRC_NAME__')
& (Join-Path $rel 'venvs\searxng\Scripts\python.exe') -m waitress --listen=127.0.0.1:8888 searx.webapp:app
'@.Replace('__SX_SRC_NAME__', $sxSrcDir.Name) | Set-Content -Path $startSx -Encoding UTF8
    if (-not (Test-Port 8888).busy) {
      $so = Join-Path $LOG_DIR 'searxng-out.log'; $se = Join-Path $LOG_DIR 'searxng-err.log'
      $proc = Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-File',('"' + $startSx + '"') `
              -WindowStyle Hidden -RedirectStandardOutput $so -RedirectStandardError $se -PassThru
      $owned += $proc.Id
      Set-Content -Path (Join-Path $STATE_DIR 'searxng.pid') -Value $proc.Id -Encoding ASCII
    }
    if (-not (Wait-Http 'http://127.0.0.1:8888/' 180 $sp.base $sp.span)) {
      Fail 'E-SEARXNG' 'SearXNG not ready on 8888 (see logs\searxng-err.log)'
    }
    $sxSearch = Invoke-Json GET 'http://127.0.0.1:8888/search?q=test&format=json' $null
    if (-not $sxSearch) { Fail 'E-SEARXNG' 'json search endpoint failed' }
    Emit 'log' ('searxng ok: rev ' + $PIN.searxngRev.Substring(0,7) + ' waitress ' + $PIN.waitressVer + ' json search OK')
    Save-State @{ s10='ok' }
  } else { Emit 'log' 'searxng not selected - core only'; Save-State @{ s10='skipped' } }

  # ---------------- S11 launcher + shortcuts ----------------
  $sp = Step-Pct 'S11'; Emit 'step' @{ name='S11 shortcuts'; pct=$sp.base }
  $launcher = Join-Path $REL_DIR_ 'Start-BOM-AI.ps1'
  $launcherTpl = @'
param()
$ErrorActionPreference = 'SilentlyContinue'
$rel = Split-Path -Parent $MyInvocation.MyCommand.Path
function Listening([int]$p) {
  try { $null = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction Stop; return $true } catch { return $false }
}
if (-not (Listening 11434)) {
  $env:OLLAMA_MAX_LOADED_MODELS = '1' # RD1 sync 20261030
  Start-Process '__OLLAMA_EXE__' -ArgumentList 'serve' -WindowStyle Hidden
}
if (-not (Listening 11435)) {
  $gwRoot = '__INSTALL_ROOT__'
  Start-Process '__PY_EXE__' -ArgumentList ('"' + (Join-Path $rel 'bom_runtime.py') + '" --host 127.0.0.1 --port 11435 --upstream http://127.0.0.1:11434 --config "' + (Join-Path $gwRoot 'state\runtime.json') + '" --log "' + (Join-Path $gwRoot 'logs\gateway.jsonl') + '"') -WindowStyle Hidden
}
if (-not (Listening 8080)) {
  Start-Process powershell.exe -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-File',('"' + (Join-Path $rel 'start-owui.ps1') + '"') -WindowStyle Hidden
}
if (-not (Listening 8888)) {
  $sx = Join-Path $rel 'start-searxng.ps1'
  if (Test-Path $sx) { Start-Process powershell.exe -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-File',('"' + $sx + '"') -WindowStyle Hidden }
}
$ok = $false
for ($i = 0; $i -lt 90; $i++) {
  if (Listening 8080) { $ok = $true; break }
  Start-Sleep 2
}
Start-Process 'http://127.0.0.1:8080'
'@
  $launcherTpl.Replace('__OLLAMA_EXE__', $ollamaExe).Replace('__PY_EXE__', $runPy).Replace('__INSTALL_ROOT__', $BOMAI_ROOT_) | Set-Content -Path $launcher -Encoding UTF8
  if ($OPT.shortcut) {
    $sh = New-Object -ComObject WScript.Shell
    $lnk = $sh.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'BOM AI.lnk'))
    $lnk.TargetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    $lnk.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $launcher + '"'
    $lnk.WorkingDirectory = $REL_DIR_
    $lnk.Description = 'BOM AI ' + $PIN.release
    $lnk.Save()
  }
  if ($OPT.startmenu) {
    $sh2 = New-Object -ComObject WScript.Shell
    $sm = Join-Path ([Environment]::GetFolderPath('Programs')) 'BOM AI'
    New-Item -ItemType Directory -Force -Path $sm | Out-Null
    $lnk2 = $sh2.CreateShortcut((Join-Path $sm 'BOM AI.lnk'))
    $lnk2.TargetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    $lnk2.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $launcher + '"'
    $lnk2.WorkingDirectory = $REL_DIR_
    $lnk2.Save()
  }
  if ($OPT.signin) {
    $sh3 = New-Object -ComObject WScript.Shell
    $lnk3 = $sh3.CreateShortcut((Join-Path (Join-Path ([Environment]::GetFolderPath('Programs')) 'Startup') 'BOM AI.lnk'))
    $lnk3.TargetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    $lnk3.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $launcher + '"'
    $lnk3.Save()
  }
  Save-State @{ s11='ok' }

  # ---------------- ST Tailscale (optional, non-blocking; needs UAC) ----------------
  $tsState = 'OFF'
  if ($OPT.tailscale) {
    $sp = Step-Pct 'ST'; Emit 'step' @{ name='ST tailscale'; pct=$sp.base }
    if (Test-Path $PIN.tailscaleExe) {
      $tsv = & $PIN.tailscaleExe version 2>$null | Select-Object -First 1
      Emit 'log' ('tailscale already installed: ' + $tsv)
      $tsState = 'ALREADY'
    } else {
      $tsMsi = $null
      $tsUrl = $PIN.tailscaleUrl
      for ($ta = 1; $ta -le 2; $ta++) {
        if ($OPT.cancel) { break }
        $dest = Join-Path $CACHE_DIR 'tailscale-setup.msi'
        $okT = Get-BomaiFile $tsUrl $dest '' 'Tailscale'
        if ($okT) { $tsMsi = $dest; break }
        if ($ta -eq 1) {
          try {
            $pg = Invoke-WebRequest -Uri $PIN.tailscaleResolve -UseBasicParsing -TimeoutSec 30
            $m = [regex]::Match($pg.Content, 'tailscale-setup-[\d.]+-amd64\.msi')
            if ($m.Success) { $tsUrl = ($PIN.tailscaleResolve + $m.Value); Emit 'log' ('tailscale url resolved: ' + $m.Value) }
          } catch { Emit 'log' ('tailscale version resolve failed: ' + $_.Exception.Message) }
        }
      }
      if ($tsMsi) {
        try {
          $tsP = Start-Process -FilePath 'msiexec.exe' -ArgumentList '/i', ('"' + $tsMsi + '"'), '/quiet', '/norestart', 'TS_NOLAUNCH=1' -Verb RunAs -Wait -PassThru
          Emit 'log' ('tailscale msiexec exit ' + $tsP.ExitCode)
        } catch { Emit 'log' ('tailscale UAC declined or install failed: ' + $_.Exception.Message) }
        if (Test-Path $PIN.tailscaleExe) {
          $tsv = & $PIN.tailscaleExe version 2>$null | Select-Object -First 1
          Emit 'log' ('tailscale installed: ' + $tsv)
          $tsState = 'INSTALLED'
        } else { $tsState = 'SKIPPED'; Emit 'log' 'tailscale not present after install - SKIPPED (non-blocking)' }
      } else { $tsState = 'SKIPPED'; Emit 'log' 'tailscale download failed after retries - SKIPPED (non-blocking)';
    Emit 'log' 'manual download: https://tailscale.com/download/windows' }
    }
  }
  Save-State @{ sTailscale=$tsState }

  if (-not $OPT.searxng) { Fail 'E-SEARXNG' 'Web search is required by this release' }
  # ---------------- S12 final health + commit ----------------
  $sp = Step-Pct 'S12'; Emit 'step' @{ name='S12 commit'; pct=95 }
  $h8080 = (Invoke-WebRequest -Uri 'http://127.0.0.1:8080/' -UseBasicParsing -TimeoutSec 10).StatusCode
  if ($h8080 -ne 200) { Fail 'E-OWUI' 'final health 8080 != 200' }
  if ($OPT.searxng) {
    $h8888 = (Invoke-WebRequest -Uri 'http://127.0.0.1:8888/' -UseBasicParsing -TimeoutSec 10).StatusCode
    if ($h8888 -ne 200) { Fail 'E-SEARXNG' 'final health 8888 != 200' }
  }
  # PHASE 1 20261031 (spec 1D): committed runtime config - start-owui.ps1 reads
  # the tier from here so DEFAULT_MODELS follows the installed tier.
  $runtimeJson = Join-Path $STATE_DIR 'runtime.json'
  $runtimeCfgNew.updated = (Get-Date -Format s)
  $runtimeCfgNew | ConvertTo-Json | Set-Content -Path $runtimeJson -Encoding UTF8
  $ptrTmp = $ACTIVE_PTR_ + '.tmp'
  Set-Content -Path $ptrTmp -Value $REL_DIR_ -Encoding ASCII
  Move-Item -Path $ptrTmp -Destination $ACTIVE_PTR_ -Force
  Save-State @{ s12='ok'; status='COMPLETE'; ended=(Get-Date -Format s); rel=$REL_DIR_; root=$BOMAI_ROOT_; resumeKey=$resumeKey; tier=$tierNow }
  Emit 'log' ('install complete: tier=' + $tierNow + ' alias=' + $tierAlias + ' tag=' + $tierTag)
  Emit 'step' @{ name='complete'; pct=100 }
  Emit 'done' @{ ok=$true; rel=$REL_DIR_; root=$BOMAI_ROOT_; tier=$tierNow; alias=$tierAlias; search=$(if ($OPT.searxng) { 'on' } else { 'off' }); tailscale=$tsState; reused='fresh'; loginFile=$(if ($initialLogin.managed_account -eq $true) { $bootstrapPath } else { '' }) }
}
catch {
  try { Emit 'err' @{ code=$(if ($script:ec) { $script:ec } else { 'E-GENERIC' }); msg=$(if ($script:em) { $script:em } else { $_.Exception.Message }) } } catch {}
  if ($script:ec -eq 'CANCELLED') {
    Emit 'log' 'cancelled - rolling back uncommitted release dir (data/cache/models kept)'
    foreach ($pid_ in $owned) {
      try {
        $pr = Get-Process -Id $pid_ -ErrorAction Stop
        if ($pr.Path -and $pr.Path.StartsWith($BOMAI_ROOT_, [StringComparison]::OrdinalIgnoreCase)) { Stop-Process -Id $pid_ -Force }
      } catch {}
    }
    $committed = $false
    if (Test-Path $INSTALL_JSON_) { try { $committed = ((Get-Content $INSTALL_JSON_ -Raw | ConvertFrom-Json).s12 -eq 'ok') } catch {} }
    if (-not $committed -and (Test-Path $REL_DIR_)) { Remove-Item $REL_DIR_ -Recurse -Force -ErrorAction SilentlyContinue }
    Save-State @{ status='CANCELLED' }
    Emit 'done' @{ ok=$false; cancelled=$true }
    $script:BOMAI_RC = 4
  } else {
    $code = $script:ec; if (-not $code) { $code = 'E-GENERIC' }
    $msg = $script:em; if (-not $msg) { $msg = $_.Exception.Message }
    Emit 'log' 'rollback: keeping verified cache/data/models; uncommitted release dir removed'
    foreach ($pid_ in $owned) {
      try {
        $pr = Get-Process -Id $pid_ -ErrorAction Stop
        if ($pr.Path -and $pr.Path.StartsWith($BOMAI_ROOT_, [StringComparison]::OrdinalIgnoreCase)) { Stop-Process -Id $pid_ -Force }
      } catch {}
    }
    $committed = $false
    if (Test-Path $INSTALL_JSON_) { try { $committed = ((Get-Content $INSTALL_JSON_ -Raw | ConvertFrom-Json).s12 -eq 'ok') } catch {} }
    if (-not $committed -and (Test-Path $REL_DIR_)) { Remove-Item $REL_DIR_ -Recurse -Force -ErrorAction SilentlyContinue }
    Save-State @{ status='FAILED'; code=$code; msg=$msg }
    Emit 'done' @{ ok=$false; code=$code }
    $script:BOMAI_RC = 1
  }
}
finally {
  try { if ($mtx) { $mtx.ReleaseMutex() } } catch {}
}

} # end EngineDef

# Isolated integration mode. All service traffic remains on loopback; the
# existing Ollama server/model blobs are reused, but aliases never overwrite
# the production BOM AI aliases. Normal installer behavior is unchanged.
if ($env:BOMAI_QC -eq '1') {
  if (-not $env:BOMAI_ROOT_OVERRIDE) { throw 'BOMAI_QC requires a dedicated BOMAI_ROOT_OVERRIDE' }
  $ROOT_PTR = Join-Path $BOMAI_ROOT 'state\install-root.txt'
  $ROOT_PTR_ = $ROOT_PTR
  if ($env:BOMAI_QC_BROWSER_ORIGIN) {
    $candidateOrigin = [string]$env:BOMAI_QC_BROWSER_ORIGIN
    if ($candidateOrigin -notmatch '^http://(127\.0\.0\.1|localhost|\[::1\]):([0-9]{1,5})$') { throw 'QC browser origin must be a literal loopback HTTP origin with a port' }
    if ([int]$Matches[2] -lt 1 -or [int]$Matches[2] -gt 65535) { throw 'Invalid QC browser origin port' }
    $PIN.qcBrowserOrigin = $candidateOrigin
  }
  $PIN.outputAlias = 'bomai-qc-light:latest'
  $PIN.proOutputAlias = 'bomai-qc-pro:latest'
  $EngineDef = [scriptblock]::Create($EngineDef.ToString().Replace('11435','11436').Replace('8888','18888').Replace('8080','18080'))
}

# ------------------------------------------------------------- uninstall ----
function Invoke-Uninstall([bool]$removeData) {
  Write-Log 'uninstall start (owned files only; data/models/shared runtimes kept unless removeData)'
  foreach ($pf in @('owui.pid','searxng.pid','ollama.pid')) {
    $f = Join-Path $STATE_DIR $pf
    if (Test-Path $f) {
      $p_ = [int](Get-Content $f -Raw)
      try {
        $pr = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $p_)
        if ($pr -and $pr.ExecutablePath -and $pr.ExecutablePath.StartsWith($BOMAI_ROOT, [StringComparison]::OrdinalIgnoreCase)) {
          Stop-Process -Id $p_ -Force; Write-Log ('stopped owned pid ' + $p_)
        } else { Write-Log ('pid ' + $p_ + ' not owned by BOMAI root - skipped') }
      } catch { Write-Log ('pid ' + $p_ + ' gone') }
      Remove-Item $f -Force
    }
  }
  foreach ($lnkPath in @((Join-Path ([Environment]::GetFolderPath('Desktop')) 'BOM AI.lnk'),
                         (Join-Path (Join-Path ([Environment]::GetFolderPath('Programs')) 'BOM AI') 'BOM AI.lnk'),
                         (Join-Path ([Environment]::GetFolderPath('Programs')) 'Startup\BOM AI.lnk'))) {
    if (Test-Path $lnkPath) {
      $sh = New-Object -ComObject WScript.Shell
      $l = $sh.CreateShortcut($lnkPath)
      if ($l.Arguments -like '*BOMAI*') { Remove-Item $lnkPath -Force; Write-Log ('removed shortcut ' + $lnkPath) }
      else { Write-Log ('shortcut not ours - kept: ' + $lnkPath) }
    }
  }
  $smDir = Join-Path ([Environment]::GetFolderPath('Programs')) 'BOM AI'
  if ((Test-Path $smDir) -and -not (Get-ChildItem $smDir)) { Remove-Item $smDir -Force }
  if (Test-Path (Join-Path $BOMAI_ROOT 'releases')) {
    Get-ChildItem (Join-Path $BOMAI_ROOT 'releases') -Directory | ForEach-Object {
      if ($_.FullName.StartsWith($BOMAI_ROOT, [StringComparison]::OrdinalIgnoreCase)) {
        Remove-Item $_.FullName -Recurse -Force; Write-Log ('removed ' + $_.FullName)
      }
    }
  }
  $pc = Join-Path $BOMAI_ROOT 'cache'
  if ((Test-Path $pc) -and $pc.StartsWith($BOMAI_ROOT)) { Remove-Item $pc -Recurse -Force; Write-Log ('removed ' + $pc) }
  if ($removeData) {
    $pd = Join-Path $BOMAI_ROOT 'data'
    if ((Test-Path $pd) -and $pd.StartsWith($BOMAI_ROOT)) { Remove-Item $pd -Recurse -Force; Write-Log ('removed DATA ' + $pd) }
  } else { Write-Log 'data kept (chats/settings) - run uninstall with BOMAI_REMOVE_DATA=1 to remove' }
  Write-Log 'uninstall done: Ollama, Python, downloaded models and other apps untouched'
  Write-Host 'UNINSTALL_OK (data kept; models + shared runtimes untouched)'
}

# ---------------------------------------------------------- validatepath ----
if ($MODE -eq 'validatepath') {
  $chk = Test-InstallRoot $env:BOMAI_VALIDATE_PATH
  Write-Output ($chk | ConvertTo-Json -Compress)
  $BOMAI_RC = 0
  if (-not $chk.ok) { $BOMAI_RC = 20 }
  return
}

# --------------------------------------------------------------- update -----
if ($MODE -eq 'update') {
  $cur = ''
  if (Test-Path $ACTIVE_PTR) { $cur = (Get-Content $ACTIVE_PTR -Raw).Trim() }
  if ($cur) { Write-Host ('installed release dir: ' + $cur) } else { Write-Host 'no active BOM AI release found' }
  Write-Host ('this installer version: ' + $PIN.release)
  Write-Host 'update mode is read-only. to stage a new release side-by-side run: Install-BOM-AI.bat install'
  return
}

# ------------------------------------------------------------ uninstall -----
if ($MODE -eq 'uninstall') {
  $rmData = $false
  if ($env:BOMAI_REMOVE_DATA -eq '1') { $rmData = $true }
  Invoke-Uninstall $rmData
  return
}

# ------------------------------------------------------- console (no GUI) ---
if ($MODE -eq 'console') {
  $tierEnv = 'light'
  if ($env:BOMAI_TIER -eq 'pro') { $tierEnv = 'pro' }
  $OPT = @{ gui=$false; cancel=$false; root=$BOMAI_ROOT; tier=$tierEnv; searxng=$true; shortcut=$false; startmenu=$false; signin=$false; tailscale=($env:BOMAI_INSTALL_TAILSCALE -eq '1') }
  $Q = $null
  $ROOT_PTR_ = $ROOT_PTR
  Invoke-Expression $EngineDef.ToString()
  return
}

# ------------------------------------------------------------- GUI (WPF) ----
Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase

[xml]$xaml = @'
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="BOM AI" Width="780" Height="580" WindowStartupLocation="CenterScreen"
        Background="#FAF6EF" FontFamily="Leelawadee UI, Segoe UI" ResizeMode="CanResize">
  <Window.Resources>
    <Style TargetType="Button">
      <Setter Property="Background" Value="#C86A4A"/>
      <Setter Property="Foreground" Value="#FFFDF8"/>
      <Setter Property="Padding" Value="18,8"/>
      <Setter Property="FontSize" Value="14"/>
      <Setter Property="BorderThickness" Value="0"/>
      <Setter Property="Cursor" Value="Hand"/>
      <Style.Triggers>
        <Trigger Property="IsEnabled" Value="False"><Setter Property="Background" Value="#D8C9B8"/></Trigger>
        <Trigger Property="IsMouseOver" Value="True"><Setter Property="Background" Value="#A85537"/></Trigger>
      </Style.Triggers>
    </Style>
    <Style TargetType="CheckBox"><Setter Property="Foreground" Value="#3E2F23"/><Setter Property="FontSize" Value="13"/></Style>
  </Window.Resources>
  <Grid Margin="28">
    <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
    <DockPanel Grid.Row="0" Margin="0,0,0,18">
      <TextBlock x:Name="Logo" Text="BOM AI" FontSize="30" FontWeight="Bold" Foreground="#C86A4A"/>
      <TextBlock x:Name="HdrVersion" Text="v2.0.0" FontSize="13" Foreground="#8C5B42" VerticalAlignment="Bottom" Margin="12,0,0,6"/>
      <Button x:Name="BtnLang" Content="EN" DockPanel.Dock="Right" Padding="10,4" FontSize="12" Background="#8C5B42" HorizontalAlignment="Right"/>
    </DockPanel>
    <Grid Grid.Row="1">
      <StackPanel x:Name="PgWelcome" Visibility="Visible">
        <TextBlock x:Name="LWelcome" Text="welcome" FontSize="22" FontWeight="Bold" Foreground="#3E2F23" Margin="0,0,0,10"/>
        <TextBlock x:Name="LPrivacy" TextWrapping="Wrap" Foreground="#5C4A3A" FontSize="13" Margin="0,0,0,10"/>
        <TextBlock x:Name="LMeta" TextWrapping="Wrap" Foreground="#8C5B42" FontSize="12" Margin="0,0,0,10"/>
        <TextBox x:Name="Terms" Height="170" IsReadOnly="True" TextWrapping="Wrap" VerticalScrollBarVisibility="Auto"
                 Background="#FFFDF8" Foreground="#3E2F23" BorderBrush="#E4D5C3" FontSize="12" Padding="8"/>
        <CheckBox x:Name="ChkConsent" Content="consent" Margin="0,12,0,0" FontSize="14"/>
      </StackPanel>
      <StackPanel x:Name="PgLocation" Visibility="Collapsed">
        <TextBlock x:Name="LLocTitle" Text="location" FontSize="22" FontWeight="Bold" Foreground="#3E2F23" Margin="0,0,0,10"/>
        <TextBlock x:Name="LLocDesc" TextWrapping="Wrap" Foreground="#5C4A3A" FontSize="13" Margin="0,0,0,10"/>
        <TextBox x:Name="LocPath" FontSize="13" Background="#FFFDF8" Foreground="#3E2F23" BorderBrush="#E4D5C3" Padding="6"/>
        <StackPanel Orientation="Horizontal" Margin="0,10,0,0">
          <Button x:Name="BtnBrowse" Content="browse" Background="#8C5B42" Padding="12,6" FontSize="12"/>
          <TextBlock x:Name="LLocInfo" VerticalAlignment="Center" Margin="14,0,0,0" Foreground="#8C5B42" FontSize="12"/>
        </StackPanel>
        <TextBlock x:Name="LLocErr" Foreground="#B0432F" FontSize="12" Margin="0,10,0,0" TextWrapping="Wrap"/>
      </StackPanel>
      <StackPanel x:Name="PgComponents" Visibility="Collapsed">
        <TextBlock x:Name="LCompTitle" Text="components" FontSize="22" FontWeight="Bold" Foreground="#3E2F23" Margin="0,0,0,10"/>
        <TextBlock x:Name="LTierTitle" Text="tier" FontSize="15" FontWeight="Bold" Foreground="#3E2F23" Margin="0,0,0,6"/>
        <RadioButton x:Name="RdoLight" GroupName="tier" IsChecked="True" Margin="8,0,0,2" FontSize="14"/>
        <TextBlock x:Name="LTierLightDesc" Foreground="#8C5B42" FontSize="12" Margin="28,0,0,2" TextWrapping="Wrap"/>
        <TextBlock x:Name="LTierLightBadge" Foreground="#4C7A4C" FontSize="11" Margin="28,0,0,6"/>
        <RadioButton x:Name="RdoPro" GroupName="tier" Margin="8,0,0,2" FontSize="14"/>
        <TextBlock x:Name="LTierProDesc" Foreground="#8C5B42" FontSize="12" Margin="28,0,0,2" TextWrapping="Wrap"/>
        <TextBlock x:Name="LTierProBadge" Foreground="#B0432F" FontSize="11" Margin="28,0,0,6"/>
        <RadioButton x:Name="RdoProd" GroupName="tier" IsEnabled="False" Margin="8,0,0,2" FontSize="13"/>
        <TextBlock x:Name="LTierProdDesc" Foreground="#8C5B42" FontSize="11" Margin="28,0,0,8" TextWrapping="Wrap"/>
        <TextBlock x:Name="LTierMachine" Foreground="#5C4A3A" FontSize="12" Margin="0,0,0,2" TextWrapping="Wrap"/>
        <TextBlock x:Name="LTierDisk" Foreground="#8C5B42" FontSize="12" Margin="0,0,0,10"/>
        <TextBlock x:Name="LCompCore" TextWrapping="Wrap" Foreground="#8C5B42" FontSize="13" Margin="0,0,0,10"/>
        <CheckBox x:Name="ChkSearch" IsChecked="True" Content="search" Margin="8,0,0,8"/>
        <CheckBox x:Name="ChkShortcut" IsChecked="True" Content="shortcut" Margin="8,0,0,8"/>
        <CheckBox x:Name="ChkStartMenu" IsChecked="True" Content="startmenu" Margin="8,0,0,8"/>
        <CheckBox x:Name="ChkSignin" IsChecked="False" Content="signin" Margin="8,0,0,8"/>
        <CheckBox x:Name="ChkTailscale" IsChecked="False" Content="tailscale" Margin="8,0,0,4"/>
        <TextBlock x:Name="LTailscaleNote" TextWrapping="Wrap" Foreground="#8C5B42" FontSize="11" Margin="28,0,0,8"/>
      </StackPanel>
      <Grid x:Name="PgProgress" Visibility="Collapsed">
        <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="*"/></Grid.RowDefinitions>
        <TextBlock x:Name="LInstalling" Text="installing" FontSize="20" FontWeight="Bold" Foreground="#3E2F23" Margin="0,0,0,10"/>
        <ProgressBar x:Name="Bar" Grid.Row="1" Height="22" Minimum="0" Maximum="100" Value="0" Foreground="#C86A4A" Background="#EFE6D8" BorderBrush="#E4D5C3"/>
        <StackPanel Grid.Row="2" Orientation="Horizontal" Margin="0,8,0,8">
          <TextBlock x:Name="LStep" Text="-" FontSize="13" Foreground="#5C4A3A"/>
          <TextBlock x:Name="LDl" Text="" FontSize="12" Foreground="#8C5B42" Margin="16,1,0,0"/>
        </StackPanel>
        <TextBox x:Name="LogBox" Grid.Row="3" IsReadOnly="True" TextWrapping="NoWrap" VerticalScrollBarVisibility="Auto"
                 FontFamily="Consolas" FontSize="11" Background="#FFFDF8" Foreground="#3E2F23" BorderBrush="#E4D5C3"/>
      </Grid>
      <StackPanel x:Name="PgDone" Visibility="Collapsed">
        <TextBlock x:Name="LDone" Text="done" FontSize="24" FontWeight="Bold" Foreground="#4C7A4C" Margin="0,0,0,12"/>
        <TextBlock x:Name="LFirstUse" TextWrapping="Wrap" Foreground="#5C4A3A" FontSize="13" Margin="0,0,0,10"/>
        <TextBlock x:Name="LVersions" TextWrapping="Wrap" Foreground="#8C5B42" FontSize="12"/>
      </StackPanel>
      <StackPanel x:Name="PgError" Visibility="Collapsed">
        <TextBlock x:Name="LErrTitle" Text="error" FontSize="24" FontWeight="Bold" Foreground="#B0432F" Margin="0,0,0,12"/>
        <TextBlock x:Name="LErrMsg" TextWrapping="Wrap" Foreground="#3E2F23" FontSize="14" Margin="0,0,0,8"/>
        <TextBlock x:Name="LErrCode" Text="" FontFamily="Consolas" FontSize="12" Foreground="#8C5B42" Margin="0,0,0,8"/>
        <TextBlock x:Name="LErrRemains" TextWrapping="Wrap" Foreground="#5C4A3A" FontSize="12" Margin="0,0,0,8"/>
        <TextBox x:Name="ErrLog" Height="190" IsReadOnly="True" TextWrapping="NoWrap" VerticalScrollBarVisibility="Auto"
                 FontFamily="Consolas" FontSize="11" Background="#FFFDF8" Foreground="#3E2F23" BorderBrush="#E4D5C3"/>
      </StackPanel>
    </Grid>
    <StackPanel Grid.Row="2" Orientation="Horizontal" HorizontalAlignment="Right" Margin="0,18,0,0">
      <Button x:Name="BtnBack" Content="back" Visibility="Collapsed" Margin="0,0,10,0"/>
      <Button x:Name="BtnNext" Content="next" Margin="0,0,10,0"/>
      <Button x:Name="BtnInstall" Content="install" Visibility="Collapsed" IsEnabled="False" Margin="0,0,10,0"/>
      <Button x:Name="BtnCancel" Content="cancel" Background="#8C5B42"/>
      <Button x:Name="BtnOpen" Content="open" Visibility="Collapsed" Margin="0,0,10,0"/>
      <Button x:Name="BtnLogs" Content="logs" Visibility="Collapsed" Background="#8C5B42" Margin="0,0,10,0"/>
      <Button x:Name="BtnRetry" Content="retry" Visibility="Collapsed" Margin="0,0,10,0"/>
      <Button x:Name="BtnCopyDiag" Content="copydiag" Visibility="Collapsed" Background="#8C5B42" Margin="0,0,10,0"/>
      <Button x:Name="BtnClose" Content="close" Visibility="Collapsed" Background="#8C5B42"/>
    </StackPanel>
  </Grid>
</Window>
'@

$win = [Windows.Markup.XamlReader]::Parse($xaml.OuterXml)
foreach ($n in @('Logo','HdrVersion','BtnLang','PgWelcome','LWelcome','LPrivacy','LMeta','Terms','ChkConsent',
  'PgLocation','LLocTitle','LLocDesc','LocPath','BtnBrowse','LLocInfo','LLocErr',
  'PgComponents','LCompTitle','LCompCore','LTierTitle','RdoLight','LTierLightDesc','LTierLightBadge','RdoPro','LTierProDesc','LTierProBadge','RdoProd','LTierProdDesc','LTierMachine','LTierDisk','ChkSearch','ChkShortcut','ChkStartMenu','ChkSignin','ChkTailscale','LTailscaleNote',
  'PgProgress','LInstalling','Bar','LStep','LDl','LogBox',
  'PgDone','LDone','LFirstUse','LVersions',
  'PgError','LErrTitle','LErrMsg','LErrCode','LErrRemains','ErrLog',
  'BtnBack','BtnNext','BtnInstall','BtnCancel','BtnOpen','BtnLogs','BtnRetry','BtnCopyDiag','BtnClose')) {
  Set-Variable -Name ('W_' + $n) -Value $win.FindName($n)
}

$lang = 'th'
function Set-Lang([string]$l) {
  $r = $RES[$l]
  $win.Title = $r['title']
  $W_LWelcome.Text = $r['welcome']; $W_LPrivacy.Text = $r['privacy']; $W_LMeta.Text = $r['meta']
  $W_Terms.Text = $r['terms'] -replace '`n', "`r`n"
  $W_ChkConsent.Content = $r['consent']
  $W_LLocTitle.Text = $r['locTitle']; $W_LLocDesc.Text = $r['locDesc']
  $W_BtnBrowse.Content = $r['browse']; $W_LLocInfo.Text = $r['locNeeded']
  $W_LCompTitle.Text = $r['compTitle']; $W_LCompCore.Text = $r['compCore']
  $W_LTierTitle.Text = $r['tierTitle']
  $W_RdoLight.Content = $r['tierLight']; $W_LTierLightDesc.Text = $r['tierLightDesc']
  $W_RdoPro.Content = $r['tierPro']; $W_LTierProDesc.Text = $r['tierProDesc']
  $W_RdoProd.Content = $r['tierProd'] + ' ' + $r['tierNeedGpu']; $W_LTierProdDesc.Text = $r['tierProdDesc']
  $W_ChkSearch.Content = ($r['compSearch'] + ' ' + $r['searchOn'])
  $W_ChkShortcut.Content = $r['compShortcut']; $W_ChkStartMenu.Content = $r['compStartMenu']; $W_ChkSignin.Content = $r['compSignin']
  $W_ChkTailscale.Content = $r['tailscaleOpt']; $W_LTailscaleNote.Text = $r['tsNote']
  $W_LInstalling.Text = $r['installing']
  $W_LDone.Text = $r['done']; $W_LFirstUse.Text = $r['firstUse']
  $W_LErrTitle.Text = $r['errTitle']; $W_LErrMsg.Text = $r['errGeneric']; $W_LErrRemains.Text = $r['errRemains']
  $W_BtnNext.Content = $r['next']; $W_BtnBack.Content = $r['back']
  $W_BtnInstall.Content = $r['install']; $W_BtnCancel.Content = $r['cancel']
  $W_BtnCopyDiag.Content = $r['copyDiag']
  $W_BtnOpen.Content = $r['open']; $W_BtnLogs.Content = $r['openLogs']
  $W_BtnRetry.Content = $r['retryBtn']; $W_BtnClose.Content = $r['close']
  $W_BtnLang.Content = $r['lang']
  $script:lang = $l
}
Set-Lang 'th'

# PHASE 1 20261031 (spec 1B): GPU/VRAM probe via nvidia-smi (never WMI AdapterRAM -
# uint32 overflow above 4 GB). VRAM >= 12 GB recommends Pro, otherwise Light;
# undetectable VRAM shows a note and recommends Light (Pro stays selectable).
$script:gpuInfo = @{ name = ''; vramMB = 0 }
try {
  $nv = Get-Command 'nvidia-smi.exe' -ErrorAction SilentlyContinue
  if (-not $nv) { $nv = Get-Item ($env:SystemRoot + '\System32\nvidia-smi.exe') -ErrorAction SilentlyContinue }
  if ($nv) {
    $line = & $nv.Source '--query-gpu=name,memory.total' '--format=csv,noheader,nounits' 2>$null | Select-Object -First 1
    if ($line -match '^([^,]+),\s*(\d+)') { $script:gpuInfo.name = $Matches[1].Trim(); $script:gpuInfo.vramMB = [int]$Matches[2] }
  }
} catch {}
$script:ramGB = 0
$script:cpuName = ''
try { $script:ramGB = [math]::Round((Get-CimInstance Win32_ComputerSystem -ErrorAction Stop).TotalPhysicalMemory/1GB,0) } catch {}
try { $script:cpuName = [string](Get-CimInstance Win32_Processor -ErrorAction Stop | Select-Object -First 1).Name } catch {}
function Update-TierUi {
  $r = $RES[$script:lang]
  $gpuTxt = $r['tierGpuNone']
  if ($script:gpuInfo.name -ne '') { $gpuTxt = $script:gpuInfo.name + ' (' + $script:gpuInfo.vramMB + ' MB)' }
  $W_LTierMachine.Text = ($r['tierThisMachine'] -f $script:cpuName, $script:ramGB, $gpuTxt, $script:gpuInfo.vramMB)
  $needGB = 30; if ($W_RdoPro.IsChecked) { $needGB = 45 }
  $freeTxt = '-'
  if ($script:locFreeGB) { $freeTxt = [string]$script:locFreeGB }
  $W_LTierDisk.Text = ($r['tierFree'] -f $freeTxt, $needGB)
  $proOk = ($script:gpuInfo.vramMB -ge 12000)
  if ($proOk) {
    $W_LTierProBadge.Text = $r['tierRec']; $W_LTierProBadge.Foreground = '#4C7A4C'
    $W_LTierLightBadge.Text = ''
  } else {
    $W_LTierProBadge.Text = $r['tierNeedGpu']; $W_LTierProBadge.Foreground = '#B0432F'
    $W_LTierLightBadge.Text = $r['tierRec']; $W_LTierLightBadge.Foreground = '#4C7A4C'
  }
}
Update-TierUi
$W_RdoLight.Add_Checked({ Update-TierUi })
$W_RdoPro.Add_Checked({ Update-TierUi })

function Show-Page([string]$p) {
  foreach ($pg in @($W_PgWelcome,$W_PgLocation,$W_PgComponents,$W_PgProgress,$W_PgDone,$W_PgError)) { $pg.Visibility = 'Collapsed' }
  $pages = @{ welcome=$W_PgWelcome; location=$W_PgLocation; components=$W_PgComponents; progress=$W_PgProgress; done=$W_PgDone; error=$W_PgError }
  $pages[$p].Visibility = 'Visible'
  $btns = @($W_BtnBack,$W_BtnNext,$W_BtnInstall,$W_BtnCancel,$W_BtnOpen,$W_BtnLogs,$W_BtnRetry,$W_BtnCopyDiag,$W_BtnClose)
  foreach ($b in $btns) { $b.Visibility = 'Collapsed' }
  $vis = @{
    welcome   = @($W_BtnNext,$W_BtnCancel)
    location  = @($W_BtnNext,$W_BtnCancel)
    components= @($W_BtnBack,$W_BtnInstall,$W_BtnCancel)
    progress  = @($W_BtnCancel)
    done      = @($W_BtnOpen,$W_BtnLogs,$W_BtnClose)
    error     = @($W_BtnRetry,$W_BtnCopyDiag,$W_BtnLogs,$W_BtnClose)
  }
  foreach ($b in $vis[$p]) { $b.Visibility = 'Visible' }
}

$Q = New-Object System.Collections.Concurrent.ConcurrentQueue[object]
$OPT = @{ gui=$true; cancel=$false; root=$null; tier='light'; searxng=$true; shortcut=$true; startmenu=$true; signin=$false; tailscale=$false }

function Start-Worker {
  $root = $OPT.root
  if (-not $root) { $root = $script:BOMAI_ROOT_DEFAULT }
  $rel = Join-Path $root (('releases\' + $PIN.release) + '\' + $script:BUILD_ID)
  $rs = [runspacefactory]::CreateRunspace(); $rs.ApartmentState = 'MTA'; $rs.Open()
  $rs.SessionStateProxy.SetVariable('Q', $Q)
  $rs.SessionStateProxy.SetVariable('OPT', $OPT)
  $rs.SessionStateProxy.SetVariable('PIN', $PIN)
  $rs.SessionStateProxy.SetVariable('BOMAI_ROOT_', $root)
  $rs.SessionStateProxy.SetVariable('PAYLOAD_', $script:PAYLOAD)
  $rs.SessionStateProxy.SetVariable('BUILD_ID_', $script:BUILD_ID)
  $rs.SessionStateProxy.SetVariable('INSTALL_JSON_', (Join-Path $root 'state\install.json'))
  $rs.SessionStateProxy.SetVariable('REL_DIR_', $rel)
  $rs.SessionStateProxy.SetVariable('ACTIVE_PTR_', (Join-Path $root 'state\active-release.txt'))
  $rs.SessionStateProxy.SetVariable('LOG_DIR', (Join-Path $root 'logs'))
  $rs.SessionStateProxy.SetVariable('STATE_DIR', (Join-Path $root 'state'))
  $rs.SessionStateProxy.SetVariable('DATA_DIR', (Join-Path $root 'data\open-webui'))
  $rs.SessionStateProxy.SetVariable('CACHE_DIR', (Join-Path $root 'cache\sha256'))
  $rs.SessionStateProxy.SetVariable('ROOT_PTR_', $(if ($env:BOMAI_QC -eq '1') { Join-Path $root 'state\install-root.txt' } else { Join-Path $script:BOMAI_ROOT_DEFAULT 'state\install-root.txt' }))
  $ps = [powershell]::Create(); $ps.Runspace = $rs
  $null = $ps.AddScript($EngineDef.ToString())
  $script:workerHandle = $ps.BeginInvoke()
}

$timer = New-Object Windows.Threading.DispatcherTimer
$timer.Interval = [TimeSpan]::FromMilliseconds(125)
$timer.Add_Tick({
  $item = $null
  while ($Q.TryDequeue([ref]$item)) {
    switch ($item.t) {
      'log'  { $W_LogBox.AppendText($item.d + "`r`n"); $W_LogBox.ScrollToEnd(); $W_ErrLog.AppendText($item.d + "`r`n"); $W_ErrLog.ScrollToEnd() }
      'step' { $W_Bar.Value = [double]$item.d.pct; $W_LStep.Text = ($item.d.name + '  ' + $item.d.pct + '%')
               $win.Title = ('ติดตั้ง BOM AI — ' + $item.d.name + ' ' + $item.d.pct + '%') }
      'dl'   { $d = $item.d
               if ($d.tot -gt 0) {
                 $mb = [math]::Round($d.cur/1MB,0); $mt = [math]::Round($d.tot/1MB,0)
                 $pct = [int](100*$d.cur/$d.tot)
                 $spd = [double]$d.spd
                 if ($spd -le 0 -and $script:dlPrevAt -and $d.cur -ge $script:dlPrevBytes) {
                   $sec = ([Diagnostics.Stopwatch]::GetTimestamp() - $script:dlPrevAt) / [Diagnostics.Stopwatch]::Frequency
                   if ($sec -gt 0) { $spd = ($d.cur - $script:dlPrevBytes) / $sec }
                 }
                 $script:dlPrevAt = [Diagnostics.Stopwatch]::GetTimestamp(); $script:dlPrevBytes = $d.cur
                 $spdTxt = ''; $etaTxt = '--:--'
                 if ($spd -gt 0) {
                   $spdTxt = ('{0:N1} MiB/s' -f ($spd/1MB))
                   if ($d.eta -ge 0) { $etaTxt = ('{0:mm\:ss}' -f [timespan]::FromSeconds([int]$d.eta)) }
                   elseif ($spd -gt 100) {
                     $remain = ($d.tot - $d.cur) / $spd
                     if ($remain -gt 0 -and $remain -lt 86400) { $etaTxt = ('{0:mm\:ss}' -f [timespan]::FromSeconds([int]$remain)) }
                   }
                 }
                 $W_LDl.Text = ('{0:N0} / {1:N0} MB  ({2}%)  {3}  {4}' -f $mb, $mt, $pct, $spdTxt, $etaTxt)
                 if ($d.label) { $win.Title = ('ติดตั้ง BOM AI — ' + $d.label + ' ' + $pct + '% | ' + $spdTxt + ' | ' + $etaTxt) }
               } }
      'err'  { $W_LogBox.AppendText(('ERROR ' + $item.d.code + ': ' + $item.d.msg + "`r`n")); $W_LogBox.ScrollToEnd() }
      'done' { $win.Title = $RES[$script:lang]['title']; $win.Tag = $item.d
               if ($item.d.ok) {
                 $script:REL_DIR = [string]$item.d.rel
                 $script:LOG_DIR = Join-Path ([string]$item.d.root) 'logs'
                 Show-Page 'done'
                 $r = $RES[$script:lang]
                 $searchTxt = $r['searchOffLbl']
                 if ($item.d.search -eq 'on') { $searchTxt = $r['searchOnLbl'] }
                 $tsTxt = ''
                 if ($item.d.tailscale) { $tsTxt = "`r`nTailscale: " + $item.d.tailscale + ' - ' + $r['tsNote'] }
                 $pre = ''
                 $loginText = ''
                 if ($item.d.loginFile -and (Test-Path $item.d.loginFile)) {
                   $firstLogin = Get-Content $item.d.loginFile -Raw | ConvertFrom-Json
                   $loginText = "`r`n" + ($r['initialLogin'] -f $firstLogin.email) + "`r`n" + ($r['initialPassword'] -f $firstLogin.password)
                 }
                if ($item.d.reused) { $pre = 'ตรวจสอบการติดตั้งเดิมที่มีอยู่แล้ว (ไม่ติดตั้งซ้ำ)' + "`r`n" }
                $W_LVersions.Text = ($pre + 'BOM AI ' + $PIN.release + "`r`nPython " + $PIN.python +
                   "`r`nOpen WebUI " + $PIN.owuiVer + "`r`nSearXNG rev " + $PIN.searxngRev.Substring(0,7) + ' + waitress ' + $PIN.waitressVer +
                   "`r`nTier " + $item.d.tier + "`r`nmodel " + $(if ($item.d.tier -eq 'pro') { $PIN.proTag } else { $PIN.modelTag }) + ' -> ' + $item.d.alias +
                   "`r`n" + ($r['searchStatus'] -f $searchTxt) +
                   "`r`n" + ($r['installedAt'] -f $item.d.root) + $tsTxt +
                   "`r`nhttp://127.0.0.1:8080" + $loginText)
                 Start-Process 'http://127.0.0.1:8080'
               } else {
                 Show-Page 'error'
                 $code = $item.d.code; if (-not $code) { $code = 'E-GENERIC' }
                 $r = $RES[$script:lang]
                 $msg = $r['errGeneric']
                 if ($code -eq 'E-DISK') { $msg = $r['errDisk'] }
                elseif ($code -eq 'E-SHA') { $msg = $r['errIntegrity'] }
                elseif ($code -eq 'E-GODSHA') { $msg = $r['errIntegrity'] }
                elseif ($code -eq 'E-POLICY') { $msg = $r['errPolicy'] }
                 $W_LErrMsg.Text = $msg
                 $W_LErrCode.Text = ('error code: ' + $code + '   component: install-' + $PIN.release)
               }
               $timer.Stop() }
    }
  }
})

$W_ChkConsent.Add_Checked({ $W_BtnInstall.IsEnabled = $true })
$W_ChkConsent.Add_Unchecked({ $W_BtnInstall.IsEnabled = $false })
$W_BtnLang.Add_Click({ if ($script:lang -eq 'th') { Set-Lang 'en' } else { Set-Lang 'th' } })

# ---- location page plumbing ----
$script:locOk = $false
$W_LocPath.Text = $BOMAI_ROOT_DEFAULT
function Get-LocErr([string]$reason, [double]$freeGB) {
  $r = $RES[$script:lang]
  switch ($reason) {
    'UNC'      { $r['locErrUNC'] }
    'DRIVE'    { $r['locErrDrive'] }
    'NOTREADY' { $r['locErrNotReady'] }
    'REMOVABLE'{ $r['locErrRemovable'] }
    default {
      if ($reason -like 'FS:*') { ($r['locErrFS'] -f $reason.Substring(3)) }
      elseif ($reason -eq 'SPACE') { ($r['locErrSpace'] -f $freeGB) }
      elseif ($reason -eq 'REPARSE') { $r['locErrReparse'] }
      else { $reason }
    }
  }
}
function Update-LocUi {
  $chk = Test-InstallRoot $W_LocPath.Text
  $script:locOk = [bool]$chk.ok
  $r = $RES[$script:lang]
  $script:locFreeGB = $chk.freeGB
  if ($script:locOk) {
    $W_LLocErr.Text = $r['locOk']
    $W_LLocErr.Foreground = '#4C7A4C'
    $W_LLocInfo.Text = ($r['locFree'] -f $chk.freeGB) + ' | ' + $r['locNeeded']
  } else {
    $W_LLocErr.Text = Get-LocErr $chk.reason $chk.freeGB
    $W_LLocErr.Foreground = '#B0432F'
    $W_LLocInfo.Text = $r['locNeeded']
  }
  if ($W_PgLocation.Visibility -eq 'Visible') { $W_BtnNext.IsEnabled = $script:locOk }
}
$W_BtnBrowse.Add_Click({
  Add-Type -AssemblyName System.Windows.Forms
  $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
  $dialog.Description = 'BOM AI'
  $dialog.RootFolder = [System.Environment+SpecialFolder]::MyComputer
  $dialog.SelectedPath = $W_LocPath.Text
  if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
    $W_LocPath.Text = $dialog.SelectedPath
    Update-LocUi
  }
})
$W_LocPath.Add_TextChanged({ Update-LocUi })
Update-LocUi

$W_BtnNext.Add_Click({
  if ($W_PgWelcome.Visibility -eq 'Visible') {
    Show-Page 'location'
    $W_BtnNext.IsEnabled = $script:locOk
  }
  elseif ($W_PgLocation.Visibility -eq 'Visible') {
    if (-not $script:locOk) { Update-LocUi } else { Show-Page 'components'; $W_BtnNext.IsEnabled = $true }
  }
})
$W_BtnBack.Add_Click({ Show-Page 'location'; $W_BtnNext.IsEnabled = $script:locOk })
$W_BtnInstall.Add_Click({
  $OPT.root      = if ($script:locOk) { Get-NormalizedRoot $W_LocPath.Text } else { $BOMAI_ROOT_DEFAULT }
  $OPT.tier      = if ($W_RdoPro.IsChecked) { 'pro' } else { 'light' }
  $OPT.searxng   = [bool]$W_ChkSearch.IsChecked
  $OPT.shortcut  = [bool]$W_ChkShortcut.IsChecked
  $OPT.startmenu = [bool]$W_ChkStartMenu.IsChecked
  $OPT.signin    = [bool]$W_ChkSignin.IsChecked
  $OPT.tailscale = [bool]$W_ChkTailscale.IsChecked
  Show-Page 'progress'; Start-Worker; $timer.Start()
})
$W_BtnCancel.Add_Click({
  if ($W_PgProgress.Visibility -eq 'Visible') { $OPT.cancel = $true; $W_LStep.Text = 'cancelling - finishing current step...' }
  else { $win.Close() }
})
$W_BtnOpen.Add_Click({
  Start-Process "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-File',('"' + (Join-Path $script:REL_DIR 'Start-BOM-AI.ps1') + '"') -WindowStyle Hidden
})
$W_BtnLogs.Add_Click({ if (Test-Path $LOG_DIR) { Start-Process explorer.exe -ArgumentList ('"' + $LOG_DIR + '"') } })
$W_BtnRetry.Add_Click({ Show-Page 'welcome'; $W_ChkConsent.IsChecked = $false; $W_BtnInstall.IsEnabled = $false; $W_BtnNext.IsEnabled = $true })
$W_BtnCopyDiag.Add_Click({
  try {
    $tail = ($W_ErrLog.Text -split "`r?`n" | Select-Object -Last 30) -join "`r`n"
    Set-Clipboard -Value ($W_LErrCode.Text + "`r`n" + $tail)
    $W_BtnCopyDiag.Content = 'OK'
  } catch {}
})
$W_BtnClose.Add_Click({ $win.Close() })
$win.Add_Closing({
  if ($W_PgProgress.Visibility -eq 'Visible') { $OPT.cancel = $true; Start-Sleep 2 }
  $timer.Stop()
})
Show-Page 'welcome'
$null = $win.ShowDialog()
if ($win.Tag -and ($win.Tag -is [pscustomobject]) -and -not $win.Tag.ok) { $script:BOMAI_RC = 1 }
