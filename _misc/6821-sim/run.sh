#!/bin/bash
# usage: run.sh scenario...   One process per scenario, so a crash only ends that scenario.
# SIM_EXE picks another build. SIM_RECORD_REF=1 records reference shots, see ref_check.
S="$(cd "$(dirname "$0")" && pwd)"; EXE="${SIM_EXE:-/c/3D_Stuff/bfa_build_windows_Release_x64_vc17_Release/bin/bforartists.exe}"
# SIM_CONFIG picks another config folder, SIM_FACTORY=0 starts from what's saved there and SIM_ARGS
# adds arguments, later ones winning. See run_chain.sh, which uses all three.
CONFIG="${SIM_CONFIG:-$S/config}"
FACTORY="--factory-startup"; [ "$SIM_FACTORY" = "0" ] && FACTORY=""
export BLENDER_USER_CONFIG="$CONFIG" BLENDER_USER_SCRIPTS="$CONFIG/scripts" BLENDER_USER_DATAFILES="$CONFIG/data"
# A normal quit writes quit.blend to the temporary folder, which is the user's Recover Last Session.
mkdir -p "$CONFIG/tmp"
export TEMP="$(cygpath -w "$CONFIG/tmp")" TMP="$(cygpath -w "$CONFIG/tmp")"
for s in "$@"; do
  rm -f "$S/$s.log"
  timeout 150 "$EXE" $FACTORY --enable-event-simulate --debug-memory --window-geometry 0 0 1600 1000 $SIM_ARGS --python "$(cygpath -w "$S/harness.py")" -- "$s" "$(cygpath -w "$S")" > "$S/$s.out" 2>&1
  c=$?
  echo "== $s exit=$c last: $(tail -n 1 "$S/$s.log" 2>/dev/null | cut -c1-120)"
  grep -E '^(FAIL|EXCEPTION)' "$S/$s.log" 2>/dev/null | cut -c1-200
  # Only scenarios ending in finish_with_memory_report print these, see there.
  grep -aE 'Not freed memory|new render|panel_tear_off_gesture_begin' "$S/$s.out" | head -8 | cut -c1-120
  [ $c -ne 0 ] && grep -aE 'Error|EXCEPTION|double|free|corrupt|access violation|Traceback' "$S/$s.out" | head -6 | cut -c1-200
done
