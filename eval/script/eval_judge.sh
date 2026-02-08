input_dir="result/202601/all"

output_dir="result/202601/judge"
log_dir="log/202601/judge"


mkdir -p "${output_dir}"
mkdir -p "${log_dir}"


(
for file in "${input_dir}"/*.csv; do
    model=$(basename "$file" .csv)
    
    nohup python -u qa_eval_LLMJudge.py \
        --max_concurrency 100 \
        --api_key "" \
        --base_url "" \
        --model_name "" \
        --input_path "${file}" \
        --output_path "${output_dir}/${model}.csv" \
        &> "${log_dir}/${model}.log"
done
) &