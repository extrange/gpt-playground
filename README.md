# Guide: Finetune GPT-NEO (2.7 Billion Parameters) on a single GPU with Huggingface Transformers using DeepSpeed (adapted from ![xirider](https://github.com/Xirider/finetune-gpt2xl))

- Due to the large amount of RAM/VRAM required to train these models (even with `deepspeed`), GPUs (e.g. A100, V100) are used on Google Cloud
- VRAM requirement with `deepspeed` for finetuning: 19GB
- Inference with `deepspeed` takes 8.6GB VRAM, 6.53s for ~300 tokens
- Inference without `deepspeed` takes 7.3GB VRAM, 13.44s for ~300 tokens
- The script `clean_telegram.py` is provided to process single user telegram chats into trainable material.

## 1. (Optional) Setup VM with GPUs in Google Compute Engine

This can be done using the Google Cloud Console. 

Recommended specs:

- GPU: A100 (much faster than T4s, slightly faster than V100)
- RAM: 70GB or more
- HDD: 200GB
- Image: Use a [Deep Learning VM](https://cloud.google.com/deep-learning-vm) image (comes with pytorch & drivers installed)

This setup costs around $2.50USD/hr for a non-preemptible instance.

To make jupyter notebook start on launch:

Setup `jupyter notebook` to run via `systemctl` as a service with autorestart (replace `<USERNAME>`):

```bash
sudo nano /etc/systemd/system/jupyter.service
```

Enter the following:

```text
[Unit]
Description=Jupyter Notebook
Wants=network-online.target

[Service]
Type=simple
Environment="PATH=/usr/local/cuda/bin:/opt/conda/bin:/opt/conda/condabin:/usr/local/bin:/usr/bin:
ExecStart=/opt/conda/bin/jupyter notebook --no-browser --ip=0.0.0.0 --port=5000
User=<USERNAME>
Group=<USERNAME>
WorkingDirectory=/home/<USERNAME>/
Restart=always
RestartSec=10
```

Run:

```bash
systemctl enable jupyter
systemctl start jupyter
```

Finally, the VM's firewall must be configured to allow inbound HTTP traffic on the port you chose

## 2. Download script and install libraries

Clone this repo: `git clone <my-repo>`

Then startup `jupyter notebook` and open `main.ipynb`.

## 3. Finetune and test the model

Then add your training data:
- replace the example train.txt and validation.txt files in the folder with your own training data with the same names and then run `python text2csv.py`. This converts your .txt files into one column csv files with a "text" header and puts all the text into a single line. We need to use .csv files instead of .txt files, because Huggingface's dataloader removes line breaks when loading text from a .txt file, which does not happen with the .csv files.
- If you want to feed the model separate examples instead of one continuous block of text, you need to pack each of your examples into an separate line in the csv train and validation files.
- Be careful with the encoding of your text. If you don't clean your text files or if you just copy text from the web into a text editor, the dataloader from the datasets library might not load them.

If you're using telegram chats, modify the `chatfile` parameter in `clean_telegram.py` and run it.

Then follow the rest of the instructions in the `main.ipynb` notebook.