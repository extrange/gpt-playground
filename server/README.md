# Server

To be run on the GCloud GPU instance.

**Note: The folder containing the GPT2 model should be in this folder (`server`)  as `chat-model`.**

Start with `python app.py`.

## Sample `systemctl` startup script:

```bash
sudo nano /etc/systemd/system/chatbot.service
```

Enter the following (adjust `WorkingDirectory` to where `app.py` is located):

```text
[Unit]
Description=Chatbot
Wants=network-online.target

[Service]
Type=simple
Environment="PATH=/usr/local/cuda/bin:/opt/conda/bin:/opt/conda/condabin:/usr/local/bin:/usr/bin:"
ExecStart=/opt/conda/bin/python app.py
User=<USERNAME>
Group=<USERNAME>
WorkingDirectory=/home/<USERNAME>/gpt-playground/server/

[Install]
WantedBy=multi-user.target
```