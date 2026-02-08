import pathlib, glob
import pandas as pd
import evaluate

import asyncio
from tqdm.asyncio import tqdm_asyncio

from openai import AsyncOpenAI

from prompt import PROMPT_CENTRALITY


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
        self.system_prompt = PROMPT_CENTRALITY

    async def qa(self, user_prompt, system_prompt=None):
        if system_prompt is None:
            system_prompt = self.system_prompt

        try:
            res = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "system", "content": system_prompt},{"role": "user", "content": user_prompt}],
                **self.chat_args
            )
            response_text = res.choices[0].message.content.strip()
            return response_text

        except Exception as e:
            # raise e
            return f"Error: {str(e)}"


    async def async_qa(self, output_path, input_path, output_key="centrality", batch_size=5):
        Q = pd.read_csv(input_path).reset_index()
        # Q = Q.iloc[:30, :]  # debug

        def batched(df, batch_size):
            for i in range(0, len(df), batch_size):
                yield df.iloc[i:i + batch_size]

        async def job(q_batch):
            async with self.sem:
                q = '| id | abstract | question | answer |\n|---|---|---|---|\n'
                q += '\n'.join([f'| {row["index"]} | "{row["abstract"]}" | "{row["question"]}" | "{row["answer"]}" |' for _, row in q_batch.iterrows()])
                response = await self.qa(q)
                
                result = response.split('\n')[2:]
                id_list = []
                score_list = []
                for line in result:
                    try:
                        line_splited = line.split('|')
                        if len(line_splited) == 4:
                            _, id, score, __ = line.split('|')
                        elif len(line_splited) == 5:
                            _, id, score, ___, __ = line.split('|')
                        else:
                            print(f"Unexpected format in line: {line}")
                            continue
                        id_list.append(int(id.strip()))
                        score_list.append(int(score.strip()))
                    except:
                        print(f"Failed to parse line: {line}")
                        continue

                return id_list, score_list

        tasks = [job(q_batch) for q_batch in batched(Q, batch_size)]
        results = await tqdm_asyncio.gather(*tasks)
        results = {id: score for ids, scores in results for id, score in zip(ids, scores)}

        Q[output_key] = Q["index"].map(results)
        del Q["index"]
        Q.to_csv(output_path, index=False)

        await self.client.close()

        return Q

    
def main(output_path, input_path, api_key, base_url, model_name, max_concurrency, chat_args, system_prompt=None, output_key="relevance"):
    qa = LLMQA(api_key, base_url, model_name, max_concurrency, chat_args)
    if system_prompt:
        qa.system_prompt = system_prompt
    asyncio.run(qa.async_qa(output_path, input_path, output_key))
    print("--- All done ---")



if __name__ == "__main__":
    MAX_CONCURRENCY = 20
    API_KEY = ""
    BASE_URL = ""
    MODEL_NAME = ""
    chat_args = {}

    output_path = ""
    Q_path = ""

    main(output_path, Q_path, API_KEY, BASE_URL, MODEL_NAME, MAX_CONCURRENCY, chat_args)
