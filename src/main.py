import time

from transformers import GPTNeoForCausalLM, GPT2Tokenizer

model = GPTNeoForCausalLM.from_pretrained('EleutherAI/gpt-neo-125M').to('cuda:0')
tokenizer = GPT2Tokenizer.from_pretrained('EleutherAI/gpt-neo-125M')


def infer(text):
    start_time = time.time()
    input_ids = tokenizer(text, return_tensors='pt').to('cuda:0').input_ids
    prompt_length = len(tokenizer.decode(input_ids[0], skip_special_tokens=True))
    gen_tokens = model.generate(input_ids,
                                top_p=0.9,
                                temperature=0.8,
                                max_length=prompt_length + 300,
                                do_sample=True)

    gen_text = tokenizer.batch_decode(gen_tokens, skip_special_tokens=True)[0][prompt_length:]

    print(f'Took {time.time() - start_time:.2f}s')
    print(f"\033[1m{text}\033[0m{gen_text}")
