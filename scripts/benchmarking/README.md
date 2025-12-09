## Benchmarking 

### 1.Comparing different models with fixed computational ressources

It's also possible to train several models and compare them. They can differ in many ways, the easiest one is to change the YOLO version of the model. Once those training are done, the user obtain different weights and weights paths.
You can benchmark different models by doing the following :
- Open benchmark.py and edit:
  - MODELS → model names and path to the trained .pt files
  - DATA_YAML → path to your dataset YAML file
  - PX_TO_UM → size of a pixel
  - ALERT_UM → threshold for too big cristals
  - N_RUNS → number of repeated runs for speed benchmark
- Run:
``` bash
python benchmark_models.py
```
You can also chose to run it on the cluster by running (you need to ajust the path line 20) :
``` bash
sbatch run_benchmark_models.sh
```
Note : it's possible to run it on GPUs by changing the SLURM file.

The script will calculate and display:
- Metrics for each models as histograms: 
  - Precision: Percentage of correct positive predictions
  - Recall: Percentage of actual positives correctly identified
  - mAP@0.5: Mean Average Precision at IoU threshold of 0.5
- Inference speeds for each models as violin plots:
  - run level average
  - per-image average
- Pareto plot : accuracy as a function of mean inference speed.

### 2.Comparing the same model for different computational ressources

It's also possible to compare the performance in time (for now) of a model for different computational ressources by doing the following :
- Export the .pt model to .onnx format (see cpp section for that)
- Open onnx_threads_benchmark.py and edit parameters if needed
- Open run_onnx_threads_benchmark.sh and edit : 
  - MODEL → .onnx file
  - SRC_IMG_DIR → chip pics folder
  - SCRIPT_DIR → folder containing the scripts
  - THREADS_LIST → CPUs computational ressources ex :(1 2 4 6 8 10)
  - RUNS → number of runs per configuration to do the statistics
- Run:
``` bash
sbatch run_onnx_threads_benchmark.sh
```
The script will calculate and display:
- Per-image inference times for each intra_op_num_threads configuration and run (saved to onnx_infer_times.csv).
- Summary statistics per configuration (mean / std of inference time across runs), saved to onnx_infer_summary_per_config.csv.
- CPU usage per configuration and run (max %CPU and approximate number of cores used), saved to cpu_usage_summary.csv and a human-readable cpu_usage.txt
-A violin plot of inference time vs thread count (violin_infer_time_by_threads.png) to visualize speed vs threading configuration.