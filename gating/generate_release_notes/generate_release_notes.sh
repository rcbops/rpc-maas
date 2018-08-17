#!/bin/bash -xe

gating/generate_release_notes/generate_reno_report.sh $NEW_TAG reno_report.md
cat reno_report.md > all_notes.md
