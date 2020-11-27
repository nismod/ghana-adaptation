# Proximity (no disruption)

## Process to tiff
ls proximity_results/*proximity.csv | parallel python ~/ghana-adaptation/src/ghaa/csv_to_geotiff.py {} length_km
## Downsample
ls proximity_results/*proximity.tif | parallel gdalwarp -ts 4000 5702 -r med {} {}_downsampled.tif
## Plot
ls proximity_results/*_downsampled.tif | parallel python ~/ghana-adaptation/src/ghaa/plot/test_raster.py {}

# Proximity (various disruptions)

## Process to tif
ls disruption_results/*proximity.csv | parallel python ~/ghana-adaptation/src/ghaa/csv_to_geotiff.py {} length_km
## Downsample
ls disruption_results/*proximity.tif | parallel gdalwarp -ts 4000 5702 -r med {} {}_downsampled.tif
## Plot
ls disruption_results/*_downsampled.tif | parallel python ~/ghana-adaptation/src/ghaa/plot/test_raster.py {}
