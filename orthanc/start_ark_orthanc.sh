#!/bin/bash

# Launch Orthanc
Orthanc ./orthanc/orthanc.json &
sleep 5

# Run regular ark
ark-run mirai &

# Run Orthanc listener
python orthanc/rest_listener.py &

wait
