# Server

To be run on the GCloud GPU instance.

Start with `flask run --host=0.0.0.0`.

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
WorkingDirectory=/home/<USERNAME>

[Install]
WantedBy=multi-user.target
```