import json
import logging
import os

import click as click
import openai


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

openai.api_key = os.environ["OPENAI_API_KEY"]


# 関数の実装
def get_response_of_ls(directory="."):
    ls_response = os.popen("ls " + directory).read()
    return json.dumps(ls_response)


def get_response_of_date(directory="."):
    ls_response = os.popen("date").read()
    return json.dumps(ls_response)


def get_response_of_unix_command(command):
    ls_response = os.popen(command).read()
    return json.dumps(ls_response)


# def get_table_columns():
#     return json.dumps(' '.join(os.popen("head -n 1 datasource.csv").read().strip().split(',')))

def make_sql_query(query):
    # select count(*) from stdin
    print(f"QUERY: {query}")
    response = os.popen(f"csvq \"{query}\" <datasource.csv").read()
    return json.dumps(response)


# AIが使うことができる関数を羅列する
functions = [
    # {
    #     "name": "get_response_of_ls",
    #     "description": "カレントディレクトリのファイル一覧を返す",
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             "directory": {
    #                 "type": "string",
    #                 "description": "取得したいディレクトリのパス",
    #             },
    #         },
    #         "required": [],
    #     },
    # },
    # {
    #     "name": "get_response_of_date",
    #     "description": "日時情報を返します",
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             # "directory": {
    #             #     "type": "string",
    #             #     "description": "取得したいディレクトリのパス",
    #             # },
    #         },
    #         "required": [],
    #     },
    # },
    # {
    #     "name": "get_response_of_unix_command",
    #     "description": "ローカルでUnixコマンドを実行して標準出力を返します",
    #
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             "command": {
    #                 "type": "string",
    #                 "description": "実行したいコマンドを入力してください",
    #             },
    #         },
    #         "required": [],
    #     },
    # },
    # {
    #     "name": "get_table_columns",
    #     "description": "stdinテーブルのカラムを返します",
    #
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #         },
    #         "required": [],
    #     },
    # },
    {
        "name": "make_sql_query",
        "description": "stdinテーブル(id,告示番号,通番,施設名,MDC番号,診断群分類名称,処置区分,件数,在院日数,年,MDC)に標準SQLを投げて集計結果を返します",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "問い合わせしたいクエリを入力してください",
                },
            },
            "required": ['query'],
        },
    }
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
