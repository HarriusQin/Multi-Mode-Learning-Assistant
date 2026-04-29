import asyncio
from dataclasses import dataclass
from collections import OrderedDict
from enum import Enum
from typing import Optional
from Assistant.openai_provider import OpenAIProvider, Message

compress_prompt = """请将以下对话内容进行压缩，保留关键信息，删除冗余部分，使得压缩后的内容更简洁但仍能表达原意。请尽量保留对话中的重要细节和上下文信息。"""

from Assistant.defs import Config, Role, TruncationStrategy, AgentState
from Assistant.context import Context, LRUCache
from Assistant.openai_provider import OpenAIProvider
from Assistant.agent import AgentLoopRunner

def loop(provider: OpenAIProvider, model: str):
    context = Context()
    agent = AgentLoopRunner(provider, "qwen/qwen3.6-27b")
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input in {"exit", "quit"}:
                print("Goodbye!")
                break
            
            agent.send_message(user_input)
            context.messages.append(Message(role="user", content=user_input))
            print("Assistant: ", end="", flush=True)
            response = ""
            for chunk in agent.send_message(user_input):
                print(chunk, end="", flush=True)
                response += chunk
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

def main():

    provider = OpenAIProvider(
        api_key="lm_studio",
        base_url="http://100.126.144.112:1234/v1"
    )

    loop(provider, "qwen/qwen3.6-27b")

if __name__ == '__main__':
    main()

