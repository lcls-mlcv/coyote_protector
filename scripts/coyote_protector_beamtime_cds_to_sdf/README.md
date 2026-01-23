## RUNNING COYOTE FOR AN EXPERIMENT

As of January 2026, the proposed solution for detector protection is a pre-scan of the chip followed by a post-process of the images using the coyote algorithm. The output of the algorithm is a .csv file with the positions, in pixel coordinates, of each cristal whose size is above `alert_um`, for each frame that compose the pre-scanning.  

## Key Highlights:
- Fine-tuned YOLOv11 model for accurate crystal detection
- Pixel-to-micron size conversion and threshold alert system
- GPU Inference script that save results with bounding boxes and size info
- Dataflow management between different clusters

## Overview of the scripts

To use the routine, the user has to understand the different scripts in the coyote_protector_beamtime folder. 
This README.md is made according to SLAC's infrastructure : The data will be collected on `cds/` and exported on `s3df/` for processing. The results will then be imported to `cds/`.

On one hand, there is the main algorithm to run `coyote_detection_routine_v2.sh` has to be located on `cds/.../`or wherever the images will be located after there acquisition. This algorithm deals with the export, post-processing via SLURM and the import of the results.

On the other hand, the user has :
- inference_coyote.py
- run_inference.sh
- weight_yolov11n_150epochs.

Those three algorithms are in charge of the inference and the generation of the .csv file. In particular, the .pt (PyTorch) file, corresponds to the weights of the YOLO model used. It can be changed with any other weight file.


## Setting up the coyote protector


### 1. On `/sdf`

In your workspace (needs a lot of available quota), clone the repo coyote_protector/scripts/coyote_protector_beamtime_cds_to_sdf

In `inference_coyote.py` change :
- weights_path -> path to the weights of the algo, (for instance '/sdf/data/lcls/ds/prj/prjlumine22/results/pmonteil/coyote_beamtime_19jan/weight_yolov11n_150epochs.pt')         
- mag_factor -> magnification factor (for instance 1)
- px_size -> size of the pixels in um, (for instance 0.5)
- alert_um -> threshold for alert, (for instance 100.0 um)

`run_inference.sh` should not be changed


### 2. On `/cds` (or where the data are stored)

Clone the repo coyote_protector/scripts/coyote_protector_beamtime_cds_to_sdf

In `coyote_detection_routine_v2.sh`, change : 
- SOURCE_PATH -> put the path where the images are located, (for instance "/cds/data/iocData/ioc-icl-alvium05/logs")
- DEST_BASE -> put the path of the base folder on S3DF where runs are created. THIS HAS TO BE THE FOLDER WHERE the repo coyote_protector/scripts/coyote_protector_beamtime_cds_to_sdf has been cloned. (for instance "/sdf/data/lcls/ds/prj/prjlumine22/results/pmonteil/coyote_beamtime_19jan")
- RESULTS_BACK_BASE -> put the path where you want results to be copied back on CDS, (for instance "/cds/home/p/pmonteil")


## Using the coyote detector

On `/cds`, run 

``` bash
./coyote_detection_routine_v2.sh --user=name_of_the_user
```
If the user wants a passwordless experience, refer to the issue related to key creations.
