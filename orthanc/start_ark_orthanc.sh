#!/bin/bash

model_name=${1:-"mirai"}

# Launch Orthanc
Orthanc ./orthanc/orthanc.json &
sleep 5

# Run regular ark
ark-run ${model_name} &

# Run Orthanc listener
python orthanc/rest_listener.py &

wait
