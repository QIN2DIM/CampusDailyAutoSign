#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import nonebot
from nonebot.adapters.cqhttp import Bot as CQHTTPBot
# Custom your logger
# 
# from nonebot.log import logger, default_format
# logger.add("error.log",
#            rotation="00:00",
#            diagnose=False,
#            level="ERROR",
#            format=default_format)

# You can pass some keyword args config to init function
nonebot.init()
app = nonebot.get_asgi()

driver = nonebot.get_driver()
driver.register_adapter('cqhttp', CQHTTPBot)

nonebot.load_builtin_plugins()

nonebot.load_plugins('alkaid/plugins')

if __name__ == "__main__":
    nonebot.run(host='0.0.0.0', port=6501
                )
