#!/bin/bash
# usage: run.sh scenario...   One process per scenario, so a crash only ends that scenario.
S="$(cd "$(dirname "$0")" && pwd)"; EXE=/c/3D_Stuff/bfa_build_windows_Release_x64_vc17_Release/bin/bforartists.exe
export BLENDER_USER_CONFIG="$S/config" BLENDER_USER_SCRIPTS="$S/config/scripts" BLENDER_USER_DATAFILES="$S/config/data"
for s in "$@"; do
  rm -f "$S/$s.log"
  timeout 150 "$EXE" --factory-startup --enable-event-simulate --debug-memory --window-geometry 0 0 1600 1000 --python "$(cygpath -w "$S/harness.py")" -- "$s" "$(cygpath -w "$S")" > "$S/$s.out" 2>&1
  c=$?
  echo "== $s exit=$c last: $(tail -n 1 "$S/$s.log" 2>/dev/null | cut -c1-120)"
  grep -E '^(FAIL|EXCEPTION)' "$S/$s.log" 2>/dev/null | cut -c1-200
  [ $c -ne 0 ] && grep -aE 'Error|EXCEPTION|double|free|corrupt|access violation|Traceback' "$S/$s.out" | head -6 | cut -c1-200
done
