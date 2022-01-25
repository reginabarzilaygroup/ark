# ark
[![coverage](coverage.svg)](https://pypi.org/project/coverage-badge/) (out-of-date)

To run the docker image:

    docker run -p 5000:5000 ark/mirai

### `POST` /dicom/uri

Accepts a POST request of JSON content containing a direct link to a `.zip` file.

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