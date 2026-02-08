# DBench

This is the python implementation of our paper.


## Enviroment

- Python 3.11.13
- biopython 1.86
- evaluate 0.4.6
- openai 1.109.1
- pandas 2.3.3


## Construct Benchmark

In `benchmark.py`, set parameters such as `MAX_CONCURRENCY`, `API_KEY`, `BASE_URL`, `MODEL_NAME`, `year_month`, `ab_dir` and `output_dir`. Then run `benchmark.py` to construct the benchmark dataset. The output will be saved in the specified `output_dir` as CSV files.

Then your can run `merge_qa.py` to merge the generated CSV files into one file named `all.csv` in the same directory. You can also split the merged file into several parts if needed.


## Evaluate

In `eval/script/eval.sh`, set relevant parameters, and run `bash script/eval.sh` in the `eval` folder to conduct the evaluation.

Then run `bash script/eval_judge.sh` to conduct the evaluation with LLM Judge. The results will be saved in the specified `output_dir` as CSV files, and the logs will be saved in the specified `log_dir`.