export PYTHONUNBUFFERED=1

input_path=../result/202601/all.csv
output_dir=result/202601/all
log_dir=log/202601/all

mkdir -p ${output_dir}
mkdir -p ${log_dir}



model_list=(
    model_name
)
model_suffix_list=(
    model_suffix
)
chat_args_list=(
    '{}'
)

for i in "${!model_list[@]}"; do
    model=${model_list[$i]}
    chat_args=${chat_args_list[$i]}
    model_suffix=${model_suffix_list[$i]}
    nohup python qa_eval_baseline_H.py \
        --max_concurrency 100 \
        --api_key "" \
        --base_url "" \
        --chat_args "$chat_args" \
        --input_path "${input_path}" \
        --model_name ${model} \
        --output_path "${output_dir}/${model_suffix}.csv" \
        &> "${log_dir}/${model_suffix}.log" &
done


