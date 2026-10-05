# ============================================================
# BOM AI - hardware_detect_windows.ps1
# Part of: bomai installer_assembly (project bomai, step installer-config-assembly)
# Source: K3 deep research art#44899 topic_1.windows.powershell_script
# Purpose: RAM/VRAM/CPU/OS probe -> JSON; drives V4B/V8B/V12B tier pick
# Encoding: UTF-8 with BOM (per spec). ASCII-only body.
# License: (c) iCafeFX - BOM AI installer payload
# ============================================================

# BOM AI hardware probe — Windows (PowerShell 5.1+ inbox on Win10/11)
# Outputs: ram_gb, vram_gb, gpu_name, gpu_vendor, cpu_cores, os_version
# Detection order per GPU: registry QWORD -> nvidia-smi -> known-GPU table -> WMI (capped)
# Cross-checked against cascade-scanner (fsantos094tmc) which uses the same order:
# registry QWORD first, known-card correction table second, WMI last resort.

function Get-SystemRamGB {
    # TOTAL physical RAM (not available). Win32_ComputerSystem.TotalPhysicalMemory = bytes (uint64, no cap)
    [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
}

function Get-CpuCores {
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    # NumberOfCores = physical; NumberOfLogicalProcessors = threads
    @{ cores = $cpu.NumberOfCores; threads = $cpu.NumberOfLogicalProcessors; name = $cpu.Name.Trim() }
}

function Get-OsVersion {
    $os = Get-CimInstance Win32_OperatingSystem
    $build = [int]$os.BuildNumber
    # Win10 22H2 = 19045; Win11 starts at 22000
    @{ caption = $os.Caption; build = $build; is_win10_22h2_plus = ($build -ge 19041) }
}

function Get-GpuVendorFromPnp($pnpId) {
    if ($pnpId -match 'VEN_10DE') { return 'NVIDIA' }
    if ($pnpId -match 'VEN_1002') { return 'AMD' }
    if ($pnpId -match 'VEN_8086') { return 'INTEL' }
    return 'UNKNOWN'
}

# Known-GPU VRAM table (GB) — fallback when registry + nvidia-smi both fail
$KnownGpuTable = @{
    'RTX 3060'  = 12; 'RTX 3070' = 8;  'RTX 3080' = 10; 'RTX 3090' = 24
    'RTX 4060'  = 8;  'RTX 4070' = 12; 'RTX 4080' = 16; 'RTX 4090' = 24
    'RTX 5060 Ti' = 16; 'RTX 5070' = 12; 'RTX 5080' = 16; 'RTX 5090' = 32
    'RX 6600' = 8; 'RX 6700' = 10; 'RX 6800' = 16; 'RX 6900' = 16
    'RX 7600' = 8; 'RX 7700' = 12; 'RX 7800' = 16; 'RX 7900 XT' = 20; 'RX 7900 XTX' = 24
    'Arc A750' = 8; 'Arc A770' = 16; 'Arc B580' = 12; 'Arc B570' = 10
}

function Get-GpuInfo {
    $gpus = Get-CimInstance Win32_VideoController |
            Where-Object { $_.Name -notmatch 'Microsoft Basic|Remote Display|Virtual' }
    # Registry QWORD workaround — display-class keys, one numbered subkey per adapter
    $regPath = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\????'
    $reg = Get-ItemProperty -Path $regPath -Name MatchingDeviceId, 'HardwareInformation.qwMemorySize' -ErrorAction SilentlyContinue

    # nvidia-smi table (if driver utils installed), keyed loosely by name
    $smi = $null
    if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
        $smi = nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>$null
    }

    $results = @()
    foreach ($g in $gpus) {
        $vramBytes = 0; $source = 'none'
        # 1) Registry QWORD (true 64-bit; written by NVIDIA/AMD/Intel display drivers at boot)
        $m = $reg | Where-Object { $g.PNPDeviceID -like "$($_.MatchingDeviceId)*" } | Select-Object -First 1
        if ($m -and $m.'HardwareInformation.qwMemorySize' -gt 0) {
            $vramBytes = [int64]$m.'HardwareInformation.qwMemorySize'; $source = 'registry_qword'
        }
        # 2) nvidia-smi fallback (NVIDIA only)
        if ($vramBytes -eq 0 -and $smi) {
            $line = $smi | Where-Object { $_ -match [regex]::Escape(($g.Name -replace 'NVIDIA ','')) } | Select-Object -First 1
            if ($line -match ',\s*(\d+)') { $vramBytes = [int64]$Matches[1] * 1MB; $source = 'nvidia_smi' }
        }
        # 3) Known-GPU table
        if ($vramBytes -eq 0) {
            foreach ($k in $KnownGpuTable.Keys) {
                if ($g.Name -match [regex]::Escape($k)) { $vramBytes = [int64]$KnownGpuTable[$k] * 1GB; $source = "table:$k"; break }
            }
        }
        # 4) WMI AdapterRAM LAST RESORT — uint32, silently caps >4GB to 4293918720 bytes or wraps
        if ($vramBytes -eq 0 -and $g.AdapterRAM) {
            $vramBytes = [int64]$g.AdapterRAM; $source = 'wmi_capped_untrusted'
        }
        $results += [pscustomobject]@{
            gpu_name   = $g.Name
            vendor     = Get-GpuVendorFromPnp $g.PNPDeviceID
            vram_gb    = [math]::Round($vramBytes / 1GB, 1)
            vram_source = $source
            driver_ver = $g.DriverVersion
        }
    }
    # Pick the primary = highest VRAM (discrete beats integrated)
    $results | Sort-Object vram_gb -Descending
}

# --- emit machine-readable result ---
$cpu = Get-CpuCores; $os = Get-OsVersion; $gpu = Get-GpuInfo | Select-Object -First 1
[pscustomobject]@{
    ram_gb     = Get-SystemRamGB
    vram_gb    = $gpu.vram_gb
    gpu_name   = $gpu.gpu_name
    gpu_vendor = $gpu.vendor
    cpu_cores  = $cpu.cores
    cpu_threads = $cpu.threads
    os_version = "$($os.caption) build $($os.build)"
} | ConvertTo-Json -Compress
