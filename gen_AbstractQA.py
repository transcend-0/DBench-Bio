import re, pathlib, json, glob
import pandas as pd
import asyncio
from tqdm.asyncio import tqdm_asyncio

from openai import AsyncOpenAI

from prompt import PROMPT_ABSTRACT_QA



class MarkdownQA:
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
        self.outer_sem = asyncio.Semaphore(1 + max_concurrency // 4)
        self.prompt = PROMPT_ABSTRACT_QA
        self.chat_args = chat_args
        self.num_prompt_tokens = []
        self.num_completion_tokens = []

    async def qa(self, user_prompt, system_prompt=None):
        if system_prompt is None:
            system_prompt = self.prompt

        try:
            res = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "system", "content": system_prompt},{"role": "user", "content": user_prompt}],
                **self.chat_args
            )
            self.num_prompt_tokens.append(res.usage.prompt_tokens)
            self.num_completion_tokens.append(res.usage.completion_tokens)

            response_text = res.choices[0].message.content.strip()

            try:
                result = [json.loads(response_text)]
                return result
            except Exception as e:
                return [{
                    "error": str(e),
                    "response": response_text
                }]
        except Exception as e:
            # raise e
            return [{
                "error": str(e),
            }]


    async def generate_qa_from_abstract(self, json_path, output_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            abstract_list = json.load(f)
            # abstract_list = json.load(f)[:2]

        async def job(abstract):
            async with self.sem:
                response = await self.qa(abstract['abstract'])
                for r in response:
                    r['title'] = abstract['title']
                    r['abstract'] = abstract['abstract']
                return response

        tasks = [job(abstract) for abstract in abstract_list]
        results = await tqdm_asyncio.gather(*tasks, desc="Extracting")
        results = [item for sublist in results for item in sublist]

        df = pd.DataFrame(results)
        df = df[['title', 'abstract', 'question', 'answer']]
        df.to_csv(output_path, index=False)

        await self.client.close()

        return results


def main(output_path, input_path, api_key, base_url, model_name, max_concurrency, chat_args):
    if "response_format" not in chat_args:
        chat_args = {
            **chat_args,
            "response_format": {"type": "json_object"},
        }
    pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    qa = MarkdownQA(api_key, base_url, model_name, max_concurrency, chat_args)
    asyncio.run(qa.generate_qa_from_abstract(input_path, output_path))

    print(f"{'Metric':<25}{'Mean':<10}{'Min':<10}{'Max':<10}")
    print(f"{'num_prompt_tokens':<25}{sum(qa.num_prompt_tokens)/len(qa.num_prompt_tokens):<10.1f}{min(qa.num_prompt_tokens):<10}{max(qa.num_prompt_tokens):<10}")
    print(f"{'num_completion_tokens':<25}{sum(qa.num_completion_tokens)/len(qa.num_completion_tokens):<10.1f}{min(qa.num_completion_tokens):<10}{max(qa.num_completion_tokens):<10}")



if __name__ == "__main__":
    MAX_CONCURRENCY = 2
    API_KEY = ""
    BASE_URL = ""
    MODEL_NAME = ""
    chat_args = {}
    
    input_path = ""
    output_dir = ""
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    main(output_dir, input_path, API_KEY, BASE_URL, MODEL_NAME, MAX_CONCURRENCY, chat_args)
