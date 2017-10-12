#!/bin/bash -xe

# This script is run within a docker container to generate release notes.

/generate_reno_report.sh $NEW_TAG reno_report.md
cat reno_report.md > all_notes.md
