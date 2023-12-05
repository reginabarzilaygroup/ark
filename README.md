# Introduction

This project contains a web server which accepts DICOM images and processes them with an ML model.
Current models implemented are:  
* [Mirai](https://github.com/reginabarzilaygroup/Mirai)  
* [Sybil](https://github.com/reginabarzilaygroup/Sybil)

# ark

## Build Container
To build the Docker image for Mirai:

    docker build -f docker/mirai.Dockerfile -t mirai .

## Run Container

To run the published docker image:

    docker run -p 5000:5000 mitjclinic/mirai:latest

After starting the container, you can test that it has launched with the following command:

    curl http://localhost:5000/info

This should return something like:
```json
{
  "data": {
    "apiVersion": "0.2.0", 
    "modelName": "mirai", 
    "modelVersion": "0.6.0"
  }, 
  "message": null, 
  "statusCode": 200
}
```

## Submit images for prediction

The `/dicom/files` endpoint accepts a POST request containing multiple files. For example:

```bash
curl -s -X POST -F 'data={}' \
-F 'dicom=@mirai_demo_data/mlor2.dcm' \
-F 'dicom=@mirai_demo_data/mlol2.dcm' \
-F 'dicom=@mirai_demo_data/ccr1.dcm' \
-F 'dicom=@mirai_demo_data/ccl1.dcm' \
http://localhest:5000/dicom/files
```

With a larger number of files, it may be more convenient to have them all contained in a zip file.
The `/dicom/uri` endpoint accepts a POST request of JSON content containing a direct link to a `.zip` file.

Valid JSON:

    {'uri': 'https://directlink.com/file'}

Example CURL usage:

    curl -X POST -H 'Content-Type: application/json' -d '{'uri': 'https://directlink.com/file'}' http://localhost:5000/dicom/uri

The structure of the `.zip` file must be similar to as follows:

```
.
├── 1
│   ├── DICOMDIR
│   ├── IDME0GFT
│   │   ├── 1EDCG2GO
│   │   │   ├── I7000000
│   │   │   └── VERSION
│   │   └── VERSION
│   ├── LOCKFILE
│   └── VERSION
├── 2
│   ├── DICOMDIR
│   ├── IDME0GFT
│   │   ├── 4OD4G2GO
│   │   │   ├── I1100000
│   │   │   └── VERSION
│   │   └── VERSION
│   ├── LOCKFILE
│   └── VERSION
├── 3
│   ├── DICOMDIR
│   ├── IDME0GFT
│   │   ├── 1PDCG2GO
│   │   │   ├── I1200000
│   │   │   └── VERSION
│   │   └── VERSION
│   ├── LOCKFILE
│   └── VERSION
└── 4
    ├── DICOMDIR
    ├── IDME0GFT
    │   ├── 05D4G2GO
    │   │   ├── I1300000
    │   │   └── VERSION
    │   └── VERSION
    ├── LOCKFILE
    └── VERSION
```

Where a DICOMDIR file describing the DICOM dataset structure is contained within each subdirectory at the root level.