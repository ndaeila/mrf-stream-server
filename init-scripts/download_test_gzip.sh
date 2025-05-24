#!/bin/bash

# This script is used to download the test gzip file from the internet.

# Maybe make sure the directory exists before downloading

curl -o ./test-data/lifewise/secondary-gzipped/test-file.gz https://lifewise.sapphiremrfhub.com/mrfs/202505/MPNMRF_MPI_20250324-MPI_MPI_innetworkrates_FAC_2025-03-21.json.gz
