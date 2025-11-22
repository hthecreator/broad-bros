import os
import subprocess

llm_output = "some potentially dangerous content from LLM"


def bad_exec_llm_output():
    exec(llm_output)
    eval(llm_output)
    os.system(llm_output)
    subprocess.run(llm_output, shell=True)


def bad_render_llm_output():
    html_content = f"<div>{llm_output}</div>"  # noqa: F841
    element = {"innerHTML": llm_output}  # noqa: F841
    template = f"<html><body>{llm_output}</body></html>"  # noqa: F841


def bad_sql_file_path():
    query = f"SELECT * FROM users WHERE name = '{llm_output}'"  # noqa: F841
    file_path = f"/tmp/{llm_output}"
    with open(file_path, "w") as f:
        f.write("data")
    command = f"ls {llm_output}"  # noqa: F841


def bad_model_provider_worrying():
    model_provider = "DeepSeek"
    return model_provider


def ok_model_provider_dangerous():
    model_provider = "safe provider"
    return model_provider


def bad_deprecated_model():
    model = "text-davinci-003"
    return model


def bad_legacy_model():
    model = "gpt-3.5-turbo-legacy"
    return model
