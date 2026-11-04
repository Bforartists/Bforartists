# Tear-Off Menus and Panels: extras (#6821)

Not part of the code, and not meant to be merged. Kept apart so `master` stays clean.

- `pr-images/`: the pictures shown in the pull request. Deleting them breaks that page.
- `tests/`: the test suite, which drives a real build with simulated events and compares screenshots.
  `bash run.sh scenario...` runs scenarios one process at a time. `SIM_EXE` picks the build.
- `plans/`: the design notes the work followed.

https://github.com/Bforartists/Bforartists/issues/6821
