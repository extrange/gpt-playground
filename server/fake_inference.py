import time

from transformers import AutoModelForCausalLM, AutoTokenizer

# casting to fp16 "half" gives a large speedup during model loading
tokenizer = AutoTokenizer.from_pretrained("gpt2-medium")
tokenizer.pad_token = tokenizer.eos_token
model = AutoModelForCausalLM.from_pretrained("gpt2-medium", pad_token_id=tokenizer.eos_token_id)

# Approximate benchmarks:
# Interruptible: 27.93s
# Default: 10.98s
# I must therefore resort to thread cancelling solutions

def infer_deepspeed_single(text, tokens_to_generate=40):
    start_time = time.time()
    model_input = tokenizer(text, padding=True, return_tensors='pt').input_ids
    prompt_length = len(tokenizer.decode(model_input[0], skip_special_tokens=True))

    # Generate one token at a time and add to model_input repeatedly
    for i in range(tokens_to_generate):
        input_length = len(model_input[0])
        model_input = model.generate(model_input,
                                     top_p=0.9,
                                     temperature=0.9,
                                     max_length=input_length + 1,
                                     do_sample=True,
                                     use_cache=True)  # Without this you get a dimension error
        print(f'I{input_length=}, {prompt_length=}')

    gen_text = tokenizer.batch_decode(model_input, skip_special_tokens=True)[0][prompt_length:]

    print(f'Inference took {time.time() - start_time: .2f}s')

    return {'time': time.time() - start_time,
            'original': text,
            'generated': gen_text}


def infer_deepspeed(text, tokens_to_generate):
    start_time = time.time()
    model_input = tokenizer(text, padding=True, return_tensors='pt').input_ids
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


