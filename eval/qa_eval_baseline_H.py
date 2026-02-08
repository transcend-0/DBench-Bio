import argparse, json
import pathlib, glob
import pandas as pd
import evaluate

import asyncio
from tqdm.asyncio import tqdm_asyncio

from openai import AsyncOpenAI



def parse_args():
    # return my_args()
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--input_path", type=str, required=True)
    parser.add_argument("--api_key", type=str, required=True)
    parser.add_argument("--base_url", type=str, required=True)
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--max_concurrency", type=int, default=20)
    parser.add_argument("--chat_args", type=str, help="JSON string for chat arguments")
    parser.add_argument("--only_eval", action="store_true")
    args = parser.parse_args()

    args.chat_args = json.loads(args.chat_args) if args.chat_args else {}

    return args


class LLMQA:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        max_concurrency: int = 5,
        chat_args: dict = {}
    ):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name
        self.sem = asyncio.Semaphore(max_concurrency)
        self.chat_args = chat_args
        self.system_prompt = """
# ROLE:
You are a biomedical expert. Respond with precision, clarity, and up-to-date evidence.

# TASK
Answer the user's biomedical question concisely yet comprehensively.

# OUTPUT FORMAT
List every distinct point as a numbered bullet (1. 2. 3. ...).
Separate numbered bullet points with `\n`.
Each bullet is a single, concise sentence that directly answers the question and is unique among the list.
Limit your answer to no more than 5 bullet points.
Do not include any extraneous text, headers, or commentary outside this structure.
"""

    def parse_response(self, res: str) -> str:
        response_text = ""
        reasoning_content = ""
        if isinstance(res, str):  # streaming
            res = res.split("\n\n")
            for r in res[:-4]:  # the last 4 lines are [DONE] and empty lines
                r = json.loads(r[5:])["choices"][0]["delta"]
                if r.get("content", ""):
                    response_text += r.get("content", "")
                if r.get("reasoning_content", ""):
                    reasoning_content += r.get("reasoning_content", "")
        else:
            response_text = res.choices[0].message.content.strip()
            if hasattr(res.choices[0].message, "reasoning_content"):
                reasoning_content = res.choices[0].message.reasoning_content.strip()
        return response_text, reasoning_content

    async def qa(self, user_prompt, system_prompt=None):
        if system_prompt is None:
            system_prompt = self.system_prompt

        try:
            res = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "system", "content": system_prompt},{"role": "user", "content": user_prompt}],
                **self.chat_args
            )
            # print(res, '\n\n\n')  ### debug
            response_text, reasoning_content = self.parse_response(res)
            return response_text, reasoning_content
        except Exception as e:
            # print(e)  ### debug
            # raise e
            return f"Error: {str(e)}", ""

    async def async_qa(self, output_path, input_path):
        Q = pd.read_csv(input_path)
        # Q = Q.iloc[0:2, :]  ### debug

        async def job(q):
            async with self.sem:
                q = f"Below is a scientific hypothesis question that requires deep reasoning and analysis. The answer to the question DOES NOT exist in the existing data (literature, databases, etc.), you need to conduct logical analysis based on existing knowledge, and infer the answer to the question. You need to deeply reason about the possible influencing mechanisms rather than generalize with existing knowledge.\nQuestion: {q}"
                response_text, reasoning_content = await self.qa(q)
                return response_text, reasoning_content

        tasks = [job(q) for q in Q["question"]]
        results = await tqdm_asyncio.gather(*tasks)

        response_text_results, reasoning_content_results = zip(*results)
        Q["response"] = response_text_results
        Q["reasoning_content"] = reasoning_content_results
        Q.to_csv(output_path, index=False)

        return Q

    async def eval(self, output_path, input_path, only_eval=False):
        if only_eval:
            QA = pd.read_csv(input_path)
        else:
            if not pathlib.Path(output_path).parent.exists():
                pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            QA = await self.async_qa(output_path, input_path)

        rouge = evaluate.load("rouge")
        metrics = rouge.compute(
            predictions=QA["answer"].to_list(), references=QA["response"].to_list(), 
            use_stemmer=True, use_aggregator=False,
            # rouge_types=["rougeL"],
        )
        for k, v in metrics.items():
            QA[k] = v
        QA.to_csv(output_path, index=False)

    
def main(output_path, input_path, api_key, base_url, model_name, max_concurrency, chat_args, only_eval):
    qa = LLMQA(api_key, base_url, model_name, max_concurrency, chat_args)
    asyncio.run(qa.eval(output_path, input_path, only_eval))
    print("--- All done ---")



if __name__ == "__main__":
    args = parse_args()
    main(**vars(args))
