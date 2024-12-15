from openai.types.beta import assistant, thread
from openai.types.beta.threads import message
from typing_extensions import override
from openai import AssistantEventHandler
from openai import OpenAI
import json
import argparse
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored  
import os


from tools import music_player
client = OpenAI()

GPT_MODEL = "gpt-4o-mini"
available_functions = {"play_music": music_player,}

def create_assistant():
    my_tools = [
        {
            "type": "function",
            "function": {
                "name": "play_music",
                "description": "帮助用户播放音乐",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "music_name": {
                            "type": "string",
                            "description": "音乐名称，例如：暖暖，青花瓷",
                        },
                        "toggle_button": {
                            "type": "string",
                            "enum": ["play", "stop"],
                            "description": "决定要播放音乐还是停止播放",
                        },
                    },
                    "required": ["music_name", "toggle_button"],
                },
            }
        },
        {"type": "code_interpreter"}
    ]
    assistant = client.beta.assistants.create(
        name="assistant",
        instructions="你是一个ai助理，你可以帮助用户播放或停止播放音乐或者解决其他问题",
        tools=my_tools,
        model="gpt-4o-mini",
    )
    with open(os.path.join(os.path.dirname(__file__), "assistant_ids"), "a+") as file:
        file.write(assistant.id + '\n')
    return assistant

def create_thread():
    thread = client.beta.threads.create()
    with open(os.path.join(os.path.dirname(__file__), "thread_ids"), "a+") as file:
        file.write(thread.id + '\n')
    return thread

def create_message(content, thread_id):
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=content
    ) 
    return message

def list_message(thread_id):
    message = client.beta.threads.messages.list(
        thread_id=thread_id,
    ) 
    return message.data

def get_assistant_id():
    with open(os.path.join(os.path.dirname(__file__), "assistant_ids"), "r") as file:
        lines = file.readlines()
        if lines:
            return lines[-1].strip()  # 返回最后一行，并去掉空格和换行符
        else:
            return None  # 文件为空

def get_thread_id():
    with open(os.path.join(os.path.dirname(__file__), "thread_ids"), "r") as file:
        lines = file.readlines()
        if lines:
            return lines[-1].strip()
        else:
            return None  # 文件为空

def del_last_thread():
    with open(os.path.join(os.path.dirname(__file__), "thread_ids"), "r") as file:
        lines = file.readlines()
        if lines:
            client.beta.threads.delete(lines[-1].strip())
        else:
            return None
    with open(os.path.join(os.path.dirname(__file__), "thread_ids"), "w") as file:
        file.writelines(lines[:-1])

class EventHandler(AssistantEventHandler):    
    @override
    def on_event(self, event):
    # Retrieve events that are denoted with 'requires_action'
    # since these will have our tool_calls
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id  # Retrieve the run ID from the event data
            self.handle_requires_action(event.data, run_id)

    def handle_requires_action(self, data, run_id):
        tool_outputs = []
        for tool in data.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name == "play_music":
                func_args = tool.function.arguments
                func_to_call = available_functions[tool.function.name]
                function_args = json.loads(func_args)
                result = func_to_call(**function_args)
                tool_outputs.append({"tool_call_id": tool.id, "output": result})
            
        # Submit all tool_outputs at the same time
        self.submit_tool_outputs(tool_outputs, run_id)

    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        with client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.current_run.thread_id,
            run_id=self.current_run.id,
            tool_outputs=tool_outputs,
            event_handler=EventHandler(),
        ) as stream:
            for text in stream.text_deltas:
                pass
                #print(text, end="", flush=True)
            print()

    @override
    def on_text_created(self, text) -> None:
        print(f"\n\033[1;33m{GPT_MODEL}\033[0m > ", end="", flush=True)
        
    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)
        
    def on_tool_call_created(self, tool_call):
        print(f"\n\033[1;36m{GPT_MODEL}\033[0m > ", flush=True)
    
    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)
        elif delta.type == 'function':
            pass

    # Then, we use the `stream` SDK helper 
    # with the `EventHandler` class to create the Run 
    # and stream the response.

def run_assistant(thread_id, assistant_id):
    with client.beta.threads.runs.stream(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions="Please address the user as 主人. The user has a premium account.",
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('content', type=str, help='传入用户消息')
    args = parser.parse_args()
    #assistant = create_assistant()
    #print(f"thread id:{thread.id}", f"assistant id:{assistant.id}")
    content = args.content
    thread_id = get_thread_id()
    assistant_id = ""
    try:
        create_message(content, thread_id)
    except:
        thread_id = create_thread().id
        print("New thread created.")
        print(thread_id)
        create_message(content, thread_id)
    run_assistant(thread_id, assistant_id)
    print("")
    print("")
