import json
import logging
import os

import click as click
import openai


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


openai.api_key = os.environ["OPENAI_API_KEY"]


def get_response_of_unix_command(command):
    """任意のUnixコマンドを実行する"""

    ls_response = os.popen(command).read()
    return json.dumps(ls_response)


# AIが使うことができる関数を羅列する
functions = [
    {
        "name": "get_response_of_unix_command",
        "description": "ローカルでUnixコマンドを実行して標準出力を返します",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "実行したいコマンドを入力してください",
                },
            },
            "required": [],
        },
    },
]


@click.command()
@click.argument('question')
def main(question):
    # Step1: AIに質問を投げる
    response = openai.ChatCompletion.create(
        model="gpt-4-0613",
        # model="gpt-3.5-turbo-0613",
        messages=[
            {"role": "user", "content": question},
        ],
        functions=functions,
        function_call="auto",
    )
    logger.debug(json.dumps(response))
    message = response["choices"][0]["message"]
    if "function_call" not in message.keys():
        return
    # 関数名
    function_name = message["function_call"]["name"]
    function = eval(function_name)
    # 引数
    arguments = json.loads(message["function_call"]["arguments"])

    # Step2
    # 関数を実行して結果を取得
    function_response = function(**arguments)
    logger.debug(function_response)

    # Step3
    # 関数の結果をAIに投げる
    second_response = openai.ChatCompletion.create(
        model="gpt-4-0613",
        messages=[
            {"role": "user", "content": question},
            message,
            {
                "role": "function",
                "name": function_name,
                "content": function_response,
            },
        ],
    )

    logger.debug(json.dumps(second_response))
    logger.info(second_response.choices[0]["message"]["content"].strip())


if __name__ == "__main__":
    main()
