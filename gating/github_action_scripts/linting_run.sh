#!/bin/bash

set -euo pipefail

python3 -m pip install 'tox>=4,<5'

# Run the tox tests
tmp_tox_dir=$(mktemp -d)
trap 'rm -rf "$tmp_tox_dir"' EXIT
python3 -m tox -c tox-ci.ini -e "${RE_JOB_SCENARIO:?}" --workdir "$tmp_tox_dir"

