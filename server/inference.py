import time

import deepspeed
import torch
from transformers import GPTNeoForCausalLM, AutoTokenizer

# casting to fp16 "half" gives a large speedup during model loading
model = GPTNeoForCausalLM.from_pretrained("chat-model").half().to("cuda:0")
tokenizer = AutoTokenizer.from_pretrained("chat-model")
tokenizer.pad_token = tokenizer.eos_token

# using deepspeed inference is optional: it gives about a 2x speed up
deepspeed.init_inference(model, mp_size=1, dtype=torch.half, replace_method='auto')


def infer_deepspeed(text, tokens_to_generate):
    start_time = time.time()
    model_input = tokenizer(text, padding=True, return_tensors='pt').to('cuda:0').input_ids
    prompt_length = len(tokenizer.decode(model_input[0], skip_special_tokens=True))

    gen_tokens = model.generate(model_input,
                                top_p=0.9,
                                temperature=0.9,
                                max_length=len(model_input[0]) + tokens_to_generate,
                                do_sample=True,
                                use_cache=True)  # Without this you get a dimension error

    gen_text = tokenizer.batch_decode(gen_tokens, skip_special_tokens=True)[0][prompt_length:]
    return {'time': time.time() - start_time,
            'original': text,
            'generated': gen_text}
