import os
import pathlib
import pandas as pd
from paper_abstract_download_Entrez import download_abstract_by_journal
from gen_AbstractQA import main as abstract2QA
from eval_qa import main as eval_qa
from eval_aqa import main as eval_aqa
from prompt import *


def construct_benchmark(year_month, ab_dir, QA_dir, api_key, base_url, model_name, max_concurrency, chat_args):
    QA_dir = os.path.join(QA_dir, year_month)
    ab_dir = os.path.join(ab_dir, year_month)
    os.makedirs(QA_dir, exist_ok=True)
    os.makedirs(ab_dir, exist_ok=True)
    year, month = year_month[:4], year_month[4:]
    start_date = f"{year}/{month}/01"
    end_date = f"{year}/{month}/31"

    journal_csv_path = 'Biology_Biochemistry_JCR.csv'

    journal_df = pd.read_csv(journal_csv_path)

    target_category = ['BIOCHEMISTRY & MOLECULAR BIOLOGY', 'BIOPHYSICS', 'BIOTECHNOLOGY & APPLIED MICROBIOLOGY', 'CELL BIOLOGY', 'CELL & TISSUE ENGINEERING', 'CHEMISTRY, MEDICINAL', 'GENETICS & HEREDITY', 'MATHEMATICAL & COMPUTATIONAL BIOLOGY', 'NEUROSCIENCES', 'PHARMACOLOGY & PHARMACY', 'PATHOLOGY', 'PHYSIOLOGY']

    journal_df = journal_df.query('`JIF Quartile`=="Q1"')
    journal_df = journal_df[journal_df['Category'].isin(target_category)]

    for journal_df_category in journal_df.groupby('Category'):
        category = journal_df_category[0]
        journal_list = journal_df_category[1]['Journal name'].tolist()
        print(f"- Constructing benchmark for category: {category}")
        ab_path = os.path.join(ab_dir, f"{category}.json")
        if not os.path.exists(ab_path):
            print("- Downloading abstracts...")
            have_ab = download_abstract_by_journal(ab_path, start_date, end_date, journal_list)

            if not have_ab:
                print(f"  No abstracts found for category: {category}, skipping...")
                continue
        
        print("- Generating QA...")
        output_path = os.path.join(QA_dir, f"{category}.csv")
        if not os.path.exists(output_path):
            abstract2QA(
                output_path, ab_path, api_key, base_url, model_name, max_concurrency, chat_args,
            )

        print("- Evaluating relevance...")
        input_path = output_path
        output_path = f'{input_path[:-4]}_relevance.csv'
        if not os.path.exists(output_path):
            eval_qa(
                output_path, input_path, api_key, base_url, model_name, max_concurrency, chat_args, PROMPT_RELEVANCE.format(field=category), "relevance",
            )

            pd.read_csv(output_path).query('relevance >= 4').to_csv(output_path, index=False)

        print("- Evaluating clarity...")
        input_path = output_path
        output_path = f'{input_path[:-4]}_clarity.csv'
        if not os.path.exists(output_path):
            eval_qa(
                output_path, input_path, api_key, base_url, model_name, max_concurrency, chat_args, PROMPT_CLARITY, "clarity",
            )
            pd.read_csv(output_path).query('clarity >= 5').to_csv(output_path, index=False)

        print("- Evaluating centrality...")
        input_path = output_path
        output_path = f'{input_path[:-4]}_centrality.csv'
        if not os.path.exists(output_path):
            eval_aqa(
                output_path, input_path, api_key, base_url, model_name, max_concurrency, chat_args, PROMPT_CENTRALITY, "centrality",
            )
            pd.read_csv(output_path).query('centrality >= 5').to_csv(output_path, index=False)

    print("=== Constructing benchmark done ===")



if __name__ == "__main__":
    MAX_CONCURRENCY = 100

    API_KEY = ""
    BASE_URL = ""
    MODEL_NAME = ""
    chat_args = {}

    year_month = "202601"
    ab_dir = "paper_ab"
    output_dir = "result"

    construct_benchmark(
        year_month, ab_dir, output_dir, API_KEY, BASE_URL, MODEL_NAME, MAX_CONCURRENCY, chat_args,
    )