from nonebot import on_command
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event

ai = on_command("ai", rule=to_me(), priority=5)


@ai.handle()
async def handle_first_receive(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        state["sentence"] = args  # 如果用户发送了参数则直接赋值

@ai.got("sentence", prompt="多少说点行不？")
async def handle_city(bot: Bot, event: Event, state: T_State):
    sentence = state["sentence"]
    replay = await get_replay(sentence)
    await ai.finish(replay)

async def get_replay(sentence: str):
    import re
    sentence = re.sub(r'[嘛吗呢么]', "", sentence)
    sentence = re.sub(r'[?？]', "!", sentence)
    sentence = re.sub(r'[你]', "我", sentence)
    sentence = re.sub(r'you', "me", sentence)
    # print('called!')
    return sentence
