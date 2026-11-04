#!/bin/bash
# usage: run_chain.sh name...   For what spans a restart, such as Save Startup File: runs name_a from
# factory settings, then name_b from what it saved, on the same temporary config. The second run's
# first log line is written after the splash, which shows because no file is loaded.
# SIM_ARGS_B adds arguments to the second run, such as a smaller window.
S="$(cd "$(dirname "$0")" && pwd)"
for name in "$@"; do
  CONFIG="$S/chain_config_$name"
  rm -rf "$CONFIG"
  mkdir -p "$CONFIG"
  SIM_CONFIG="$CONFIG" bash "$S/run.sh" "${name}_a"
  SIM_CONFIG="$CONFIG" SIM_FACTORY=0 SIM_ARGS="$SIM_ARGS_B" bash "$S/run.sh" "${name}_b"
  rm -rf "$CONFIG"
done
