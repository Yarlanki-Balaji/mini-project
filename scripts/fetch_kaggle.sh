#!/usr/bin/env bash
# Requires ~/.kaggle/kaggle.json (Task 3). Run from repo root.
set -e
KAGGLE="ai_agents/.venv/Scripts/kaggle"
"$KAGGLE" datasets download -d arindam235/startup-investments-crunchbase -p data/raw --unzip
"$KAGGLE" datasets download -d sudalairajkumar/indian-startup-funding -p data/raw --unzip
"$KAGGLE" datasets download -d crowdflower/twitter-airline-sentiment -p data/raw --unzip
"$KAGGLE" datasets download -d mashlyn/online-retail-ii-uci -p data/raw --unzip
