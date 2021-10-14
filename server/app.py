from argparse import ArgumentParser

from flask import Flask
from flask import request

from inference import infer_deepspeed

app = Flask(__name__)


@app.route("/", methods=['POST'])
def run_inference():
    json = request.get_json(force=True)
    text = json['text']
    tokens_to_generate = json.get('tokens_to_generate') or 40

    return infer_deepspeed(text, tokens_to_generate=tokens_to_generate)


if __name__ == '__main__':
    parser = ArgumentParser(description='Start Flask server')
    parser.add_argument('-p', '--port', type=int, default=5555, help='Port to run application on')
    args = parser.parse_args()
    app.run(host='0.0.0.0', port=args.port)
