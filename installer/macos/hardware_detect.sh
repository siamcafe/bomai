#!/bin/bash
# ============================================================
# BOM AI - hardware_detect_macos.sh
# Part of: bomai installer_assembly (project bomai, step installer-config-assembly)
# Source: K3 deep research art#44899 topic_1.macos.script
# Purpose: RAM/VRAM(unified-aware)/CPU/OS probe -> JSON (double-clickable .command)
# License: (c) iCafeFX - BOM AI installer payload
# ============================================================

# BOM AI hardware probe — macOS (.command double-clickable)
# Outputs: ram_gb, vram_gb (or unified), gpu_name, cpu_cores, os_version
set -u

# Total physical RAM (bytes -> GB)
RAM_BYTES=$(sysctl -n hw.memsize)
RAM_GB=$(awk "BEGIN{printf \"%.1f\", $RAM_BYTES/1073741824}")

# Chip / model (Apple Silicon: "Apple M3 Pro"; Intel: processor name)
CHIP=$(system_profiler SPHardwareDataType 2>/dev/null | awk -F': ' '/Chip|Processor Name/{print $2; exit}')
CPU_CORES=$(sysctl -n hw.physicalcpu)     # physical cores; hw.ncpu = logical
OS_VER=$(sw_vers -productVersion)

# GPU: system_profiler SPDisplaysDataType
# Discrete (Intel Macs): "VRAM (Total): 8 GB" line exists.
# Apple Silicon: NO VRAM line — unified memory; "Chipset Model: Apple M3" only.
DISP=$(system_profiler SPDisplaysDataType 2>/dev/null)
GPU_NAME=$(echo "$DISP" | awk -F': ' '/Chipset Model/{print $2; exit}' | sed 's/^ *//')
VRAM_LINE=$(echo "$DISP" | awk -F': ' '/VRAM \(Total\)/{print $2; exit}' | sed 's/^ *//')

IS_APPLE_SILICON=0
[ "$(uname -m)" = "arm64" ] && IS_APPLE_SILICON=1

if [ -n "$VRAM_LINE" ]; then
  VRAM_GB=$(echo "$VRAM_LINE" | awk '{print $1}')   # discrete GPU VRAM
  MEM_MODE="dedicated"
else
  # Apple Silicon unified memory. GPU-usable default cap ~ 75% of RAM
  # (Metal MTLDevice.recommendedMaxWorkingSetSize; overridable via
  #  sudo sysctl iogpu.wired_limit_mb=<MB>).
  # Exact value (needs Xcode CLT swift):
  #   swift -e 'import Metal; if let d = MTLCreateSystemDefaultDevice { print(d.recommendedMaxWorkingSetSize) }'
  WIRED=$(sysctl -n iogpu.wired_limit_mb 2>/dev/null || echo 0)
  if [ "$WIRED" != "0" ]; then
    VRAM_GB=$(awk "BEGIN{printf \"%.1f\", $WIRED/1024}")
  else
    VRAM_GB=$(awk "BEGIN{printf \"%.1f\", $RAM_BYTES/1073741824*0.75}")  # Metal default ~75%
  fi
  MEM_MODE="unified"
fi

# Metal GPU family (informational): system_profiler reports "Metal Support: Metal 3/4"
METAL=$(echo "$DISP" | awk -F': ' '/Metal/{print $2; exit}' | sed 's/^ *//')

printf '{"ram_gb":%s,"vram_gb":%s,"mem_mode":"%s","gpu_name":"%s","metal":"%s","cpu_cores":%s,"chip":"%s","os_version":"%s"}\n' \
  "$RAM_GB" "$VRAM_GB" "$MEM_MODE" "$GPU_NAME" "$METAL" "$CPU_CORES" "$CHIP" "$OS_VER"
