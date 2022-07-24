# coding=utf-8
import aiohttp
import asyncio
import json
from loguru import logger

from discordmonitor.channel_token import *


class DiscordMonitor:
    def __init__(self):
        logger.info("init discord monitor")

    async def start(self):
        gather_result = await asyncio.gather(
            self.start_new_dc_connection(
                TOE_TOKEN, "TOE_TOKEN_NAME")
        )
        logger.info(f'{gather_result}')

    async def start_new_dc_connection(self, token: str, token_name: str, connect_times = 0):
        logger.info("start_new_dc_connection")
        if connect_times >= 100:
            return f"connect {token_name} error"

        WS_URL = "wss://gateway.discord.gg/?encoding=json&v=9"
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0)) as client:
            async with client.ws_connect(WS_URL, autoclose=False, max_msg_size=0) as ws:
                await ws.send_str(get_dc_identify_info(token))

                # 心跳保活
                asyncio.create_task(self.keep_connection(token, token_name, connect_times, ws))

                # 处理消息
                await self.dispatch(token, token_name, ws)

    async def keep_connection(self, token: str, token_name: str, connect_times, ws):
        await asyncio.sleep(10)
        keep_times = 0;
        while True:
            try:
                logger.debug(f"{token_name} keep connection :{keep_times}")
                await ws.send_str('{"op":1,"d":3}')
                await asyncio.sleep(41.25)
                keep_times+=1
            except Exception as e:
                await asyncio.sleep(5)
                await ws.close()
                asyncio.create_task(self.start_new_dc_connection(
                    token, token_name, connect_times+1))

    async def dispatch(self, token: str, token_name: str, ws):
        while True:
            dc_response = await ws.receive()
            dc_response = json.loads(dc_response.data).get('d', False)
            logger.info(f"{dc_response}")

            dc_response = await ws.receive()
            if dc_response.type == aiohttp.WSMsgType.TEXT:
                dc_response = json.loads(dc_response.data).get('t', False)
                logger.info(f"{dc_response}")

            dc_response = await ws.receive()
            if dc_response.type == aiohttp.WSMsgType.TEXT:
                dc_response = json.loads(dc_response.data)
                logger.info(f"{dc_response}")