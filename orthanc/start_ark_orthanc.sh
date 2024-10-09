#!/bin/bash

model_name=${1:-"mirai"}

# Replace value in config file with environment variable, if present.
# Can't use Orthanc built-in mechanism because it needs to be an integer.
ARK_DICOM_PORT=${ARK_DICOM_PORT:-4242}
sed "s/\$ARK_DICOM_PORT/${ARK_DICOM_PORT}/" orthanc/orthanc.json > orthanc/tmp_orthanc.json
cat orthanc/tmp_orthanc.json

# Launch Orthanc
Orthanc ./orthanc/tmp_orthanc.json &
sleep 5

# Run regular ark
ark-run ${model_name} &

# Run Orthanc listener
python orthanc/rest_listener.py &

wait
