# CampusDailyAutoSign

今日校园体温检测自动上报脚本（For:HainanUniversity） 

## :carousel_horse: 服务条款

> 1. 本项目仅为 **海南大学** 学子提供服务；
> 3. 本项目 **开源免费** ，禁止任何人使用此项目及其分支提供任何形式的收费代理服务；
> 3. 本项目初衷在于帮助大家解决一些生活中的琐碎操作，避免一些客观原因导致的过失误伤。请各位**积极配合国家防疫战略并遵守异常体温上报相关规定**，如若身体异常，请及时联系辅导员/班主任/同学寻求帮助。

客官客官晚上好！不要吝啬手中的**一键三连**yo~:couple_with_heart_woman_woman:

## :goat: 项目简介

### 执行概述

- [程序流图1](https://github.com/QIN2DIM/CampusDailyAutoSign/blob/main/docs/FlowGraph_1.md) **||**[程序流图2](https://github.com/QIN2DIM/CampusDailyAutoSign/blob/main/docs/FlowGraph_2.md)

### 框架概述

- 本项目前端使用[`Nonebot2 Awesome-bot`](https://github.com/beiyuouo/hnu-temp-report-bot)交互，支持QQ群内@机器人实现体温签到打卡以及截图发送；
- 后端使用微服务框架；截图(base64)上传使用`Selenium + AliyunOSS`，打卡签到使用`Gevent + Requests` ；

- 数据库使用`RDS-MySQL`，中间件使用`Type-SuperClass`弹性伸缩，日志中心使用`loguru`；
- 签到节点使用`SuperuserCookie`机制越权执行；

### 注意事项

- 本项目部署工程量较大（前后端分离、写法基于异步且混入多语种开发），建议开发者将`osh_slaver.py`魔改后搭配`deploy`模块完成定时签到任务。

## :kick_scooter: 使用说明

- 【方案一】使用`quick_register.py`提交表单(Python用户推荐)
- 【方案二】下载信息验证脚本（约10mb）[Download (github.com)](https://github.com/QIN2DIM/CampusDailyAutoSign/raw/main/register.zip)**||** [备用地址](http://t.qinse.top/cpdaily/register.zip)
- 【方案三】开发者选项：请star项目后继续开发任务~:champagne:

## :world_map: 开源计划

- [ ] ~~植入太极~~
- [x] 用户管理
- [x] 弹性伸缩
- [x] 数据加密
- [x] 信息通知

## :e-mail: 联系我们

> 本项目由海南大学机器人与人工智能协会数据挖掘小组 **(A-RAI.DM)** 提供维护

- [Email](mailto:RmAlkaid@outlook.com?subject=CampusDailyAutoSign-ISSUE) **||** [Home](https://a-rai.github.io/)**||** [Update](https://github.com/QIN2DIM/CampusDailyAutoSign/blob/main/docs/about.md)

