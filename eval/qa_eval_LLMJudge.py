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
# Role
You are a senior scientist with deep expertise.

# Task
The user will input a reference answer and a candidate answer, you should evaluate the quality of the candidate answer based on the reference answer, and output a JSON object containing a reasoned explanation and a score.

# Scoring Criteria
- 5 (Perfect): The answer is entirely correct, logically rigorous, and comprehensive. It is highly consistent with the reference answer on all core facts.
- 4 (Excellent): The answer is correct on core facts and logically sound, but may have minor flaws in detail, completeness, or phrasing.
- 3 (Passable): The answer contains some correct information but also has significant factual errors, logical inconsistencies, or is missing key information.
- 2 (Poor): The answer is largely incorrect or irrelevant, failing to accurately address the question.
- 1 (Incorrect): The answer is completely wrong or contains fundamental scientific fallacies.

# Output JSON Format
{
    "reason": str,  // A detailed explanation of the score, highlighting strengths and weaknesses of the candidate answer.
    "score": int  // An integer score from 1 to 5 based on the criteria above.
}

NOTE: Return ONLY a valid JSON object, WITHOUT markdown code blocks or backticks.
"""

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
            response_text = res.choices[0].message.content.strip()

            try:
                result = json.loads(response_text)
                return result
            except Exception as e:
                print(f"Error parsing JSON: {e}\nResponse text: {response_text}")  ### debug
                return {
                    "error": str(e),
                    "response": response_text
                }

        except Exception as e:
            # print(e)  ### debug
            # raise e
            return f"Error: {str(e)}"


    async def async_qa(self, output_path, input_path):
        Q = pd.read_csv(input_path)
        # Q = Q.iloc[0:2, :]  ### debug

        async def job(ref_a, cand_a):
            if str(cand_a) == 'nan':
                return 0, "Candidate answer is NaN"
            async with self.sem:
                user_prompt = f"# Reference Answer:\n{ref_a}\n\n# Candidate Answer:\n{cand_a}"
                response = await self.qa(user_prompt)
                score = response.get("score", 0)
                reason = response.get("reason", "")
                return score, reason

        tasks = [job(ref_a, cand_a) for ref_a, cand_a in zip(Q["answer"], Q["response"])]
        results = await tqdm_asyncio.gather(*tasks)

        scores, reasons = zip(*results)

        Q["LLMAJ"] = scores
        Q["LLMAJ_reason"] = reasons
        Q.to_csv(output_path, index=False)

        return Q

    async def eval(self, output_path, input_path, only_eval=False):
        QA = await self.async_qa(output_path, input_path)

    
def main(output_path, input_path, api_key, base_url, model_name, max_concurrency, chat_args, only_eval):
    pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    qa = LLMQA(api_key, base_url, model_name, max_concurrency, chat_args)
    asyncio.run(qa.eval(output_path, input_path, only_eval))
    print("--- All done ---")



if __name__ == "__main__":
    args = parse_args()
    main(**vars(args))
