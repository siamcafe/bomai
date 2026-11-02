#!/usr/bin/env bash
# Activate only an independently qualified release. Run on CAT from extracted bundle.
set -euo pipefail
SOURCE_BOMAI="$(cd "${1:-.}" && pwd -P)"
DEST_BOMAI=/home/siamcar/domains/bomai.app/public_html/dl
BACKUP_BOMAI="/home/bom/bomai-backups/astra-$(date -u +%Y%m%dT%H%M%SZ)"
test -d "$DEST_BOMAI"
test -w "$DEST_BOMAI" || { echo 'Download directory is not writable by this account.' >&2; exit 2; }
python3 - "$SOURCE_BOMAI" <<'PY'
import hashlib,json,pathlib,sys
p=pathlib.Path(sys.argv[1])
g=json.loads((p/'evidence/qc_gates.json').read_text())
rows=g['gates']; required={'G'+str(i) for i in range(1,16)}
assert {x['id'] for x in rows}==required,'Incomplete gate matrix'
assert all(x['status']=='PASS' for x in rows),'Release blocked: gates not all PASS'
m=json.loads((p/'web/release.json').read_text())
assert m['release_channel']=='stable','Candidate cannot be activated as stable'
paths={'windows':'windows/Install-BOM-AI-Online.bat','macos':'macos/install-bom-ai-mac.zip','linux':'linux/install-bom-ai-linux.sh'}
for k,f in paths.items():
    b=(p/f).read_bytes(); a=m['assets'][k]
    assert len(b)==a['size'] and hashlib.sha256(b).hexdigest()==a['sha256'],k+' checksum mismatch'
print('All release gates and source asset hashes verified')
PY
mkdir -p "$BACKUP_BOMAI"
for file in Install-BOM-AI-Online.bat install-bom-ai-mac.zip install-bom-ai-linux.sh index.html release.json; do
  if [[ -f "$DEST_BOMAI/$file" ]]; then cp -p -- "$DEST_BOMAI/$file" "$BACKUP_BOMAI/$file"; fi
done
stage_one() {
  local from="$1" name="$2" mode="$3"
  install -m "$mode" -- "$SOURCE_BOMAI/$from" "$DEST_BOMAI/.$name.astra-new"
  if [[ -f "$DEST_BOMAI/$name" ]]; then
    chown --reference="$DEST_BOMAI/$name" "$DEST_BOMAI/.$name.astra-new"
  fi
  mv -f -- "$DEST_BOMAI/.$name.astra-new" "$DEST_BOMAI/$name"
}
stage_one windows/Install-BOM-AI-Online.bat Install-BOM-AI-Online.bat 0644
stage_one macos/install-bom-ai-mac.zip install-bom-ai-mac.zip 0644
stage_one linux/install-bom-ai-linux.sh install-bom-ai-linux.sh 0755
stage_one web/index.html index.html 0644
# Manifest last: clients never see new hashes before the corresponding files.
stage_one web/release.json release.json 0644
printf 'Activated verified files. Backup: %s\n' "$BACKUP_BOMAI"
