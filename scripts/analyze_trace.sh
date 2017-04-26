#!/usr/bin/env bash

echo 'SANITY CHECK'
python3 code/analyze.py trace_logging check


echo 'SUMMARY'
python3 code/analyze.py trace_logging summary
