#!/bin/bash
# ============================================================
# BOM AI - hardware_detect_linux.sh
# Part of: bomai installer_assembly (project bomai, step installer-config-assembly)
# Source: K3 deep research art#44899 topic_1.linux.script
# Purpose: RAM/VRAM/CPU/OS probe -> JSON (nvidia-smi + sysfs + rocm-smi cascade)
# License: (c) iCafeFX - BOM AI installer payload
# ============================================================

# BOM AI hardware probe — Linux (v2: fixed NVIDIA CSV name/mem comma-parse; v1 bug: read word-split broke multi-word GPU names)
# Outputs: ram_gb, vram_gb, gpu_name, gpu_vendor, cpu_cores, os_version
set -u

# Total RAM: /proc/meminfo MemTotal is in KiB
RAM_GB=$(awk '/^MemTotal:/{printf "%.1f", $2/1048576}' /proc/meminfo)
CPU_CORES=$(nproc)                          # logical; physical: lscpu -p=CORE | sort -u | wc -l
OS_VER=$(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME" || uname -sr)

GPU_NAME=""; GPU_VENDOR=""; VRAM_BYTES=0

# 1) NVIDIA via nvidia-smi (sysfs mem_info_vram_total does NOT exist for NVIDIA — reports 0)
if command -v nvidia-smi >/dev/null 2>&1; then
  NV_LINE=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d '')
  GPU_NAME=${NV_LINE%,*}
  VRAM_MIB=${NV_LINE#*,}
  VRAM_MIB=${VRAM_MIB//[[:space:]]/}
  case "$VRAM_MIB" in ''|*[!0-9.]*) VRAM_MIB='';; esac
  [ -n "$VRAM_MIB" ] && VRAM_BYTES=$(( ${VRAM_MIB%.*} * 1024 * 1024 )) && GPU_VENDOR="NVIDIA"
fi

# 2) AMD/Intel via DRM sysfs (amdgpu exposes mem_info_vram_total in bytes; kernel docs:
#    docs.kernel.org/gpu/amdgpu/driver-misc.html)
if [ "$VRAM_BYTES" = "0" ]; then
  for d in /sys/class/drm/card[0-9]/device; do
    [ -f "$d/vendor" ] || continue
    V=$(cat "$d/vendor")
    case "$V" in
      0x1002) GPU_VENDOR="AMD";;
      0x8086) GPU_VENDOR="INTEL";;
      0x10de) GPU_VENDOR="NVIDIA";;
    esac
    if [ -f "$d/mem_info_vram_total" ]; then
      B=$(cat "$d/mem_info_vram_total")
      if [ "$B" -gt "$VRAM_BYTES" ] 2>/dev/null; then
        VRAM_BYTES=$B
        SLOT=$(basename "$(dirname "$d")")
        GPU_NAME=$(lspci -s "$(cat "$d/uevent" 2>/dev/null | sed -n 's/PCI_SLOT_NAME=//p')" 2>/dev/null | sed 's/.*: //')
      fi
    fi
  done
fi

# 3) ROCm cross-check (AMD): rocm-smi --showmeminfo vram -> "Total Memory (B): N"
if [ "$GPU_VENDOR" = "AMD" ] && command -v rocm-smi >/dev/null 2>&1; then
  RB=$(rocm-smi --showmeminfo vram 2>/dev/null | sed -n 's/.*Total Memory (B): //p' | head -1 | tr -d ' ,')
  [ -n "${RB:-}" ] && [ "$RB" -gt 0 ] 2>/dev/null && VRAM_BYTES=$RB
  command -v rocminfo >/dev/null 2>&1 && ROCM_OK=1 || ROCM_OK=0
fi

# 4) lspci fallback for the name
[ -z "$GPU_NAME" ] && GPU_NAME=$(lspci 2>/dev/null | grep -iE 'vga|3d|display' | head -1 | sed 's/.*: //')

VRAM_GB=$(awk "BEGIN{printf \"%.1f\", $VRAM_BYTES/1073741824}")
printf '{"ram_gb":%s,"vram_gb":%s,"gpu_name":"%s","gpu_vendor":"%s","cpu_cores":%s,"os_version":"%s"}\n' \
  "$RAM_GB" "$VRAM_GB" "$GPU_NAME" "$GPU_VENDOR" "$CPU_CORES" "$OS_VER"
