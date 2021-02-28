from flask import Flask, request, jsonify, redirect

from src.BusinessCentralLayer.setting import PUBLIC_API_REDIRECT, PUBLIC_API_TOS, PUBLIC_API_STU_TWQD2, \
    PUBLIC_API_STU_TWQD
from src.BusinessViewLayer.myapp.api import *

# --------------------------------------------
# Service Registration
# --------------------------------------------

app = Flask(__name__)


@app.route(PUBLIC_API_REDIRECT, methods=['GET'])
def my_blog():
    return redirect('https://github.com/QIN2DIM/CampusDailyAutoSign')


@app.route(PUBLIC_API_TOS, methods=['GET'])
def __tos__():
    tos = '1.本项目仅为海南大学提供服务；\n\n' \
          '2.本项目由海南大学机器人与人工智能协会数据挖掘小组(A-RAI.DM)负责维护；\n\n' \
          '3.禁止任何人使用本项目及其分支提供任何形式的收费代理服务；\n\n'
    title = 'CampusDailyAutoSign[For.HainanUniversity]_dev'
    response = {'tos': tos, 'title': title}
    return jsonify(response)


# --------------------------------------------
# API：NoneBot2 hainanu twqd
# --------------------------------------------

@app.route(PUBLIC_API_STU_TWQD, methods=['POST'])
def cpds_twqd_general():
    resp = apis_stu_twqd(request.form)
    return jsonify(resp)


@app.route(PUBLIC_API_STU_TWQD2, methods=['POST'])
def cpds_twqd_capture_and_upload():
    """
    当OSS没有截图时使用此接口
    既已知OSS没有截图，故无论osh-slaver如何执行，都要调用 osh-core上传截图
    :return:
    """
    resp = apis_stu_twqd2(request.form)
    return jsonify(resp)


# --------------------------------------------
# API：Add, delete, modify and check timed tasks
# --------------------------------------------
# 0. 概念阐述
# （1）动态管理：对某个指定（id）任务进行增、删、该、查的操作；
# （2）用户区分：区分管理员及普通用户，引入差别的权限；
# （3）访问过滤：该接口仅允许bot调用，过滤其他渠道的访问
# 1. 权限声明
# 1.1 super-user
#      a.可一次性添加多个任务，至多动态管理6个账户；
#      b.具备对所有任务（gu+su）的部分可读权限；
#        - 具备对gu任务的统计可读权限，既用户id（暂定为加密QQ号，非学工号）、用户操作历史、管理任务数等；
#        - 具备对su任务的详细刻度权限，su-id、操作历史、管理任务数、管理
#      c.su动态管理任务隔离性，既su无法操作其他su管理的任务；
#      d.全局任务无法重复添加，已被添加的任务会被标记id，重复任务无法被添加；
#      e.运维日志调用权限，具备签到异常或接口异常的消息接收权限；
#        - SERVER酱/SMTP/qq消息
#        - 订阅发布
# 1.2 general-user
#      a.单账号最多一次性添加1个任务，至多动态管理1个账户；
#      b.gu无法访问/操作管理范围之外的所有任务；
#      c.见1.1 d
#      d.gu任务权限：增、删、改、查
#        - 查：查询管理范围内的任务签到历史（最多7天）、今日签到状态
#        - 增、删：增、删管理范围内的任务
#        - 改：修改管理范围内的任务，可修改项“签到时间”（合法范围内）
# 2. 增量需求
# 2.1 数据加密
# 2.2 任务优先级
# 2.3 操作冷却（并发引流与防御）
# 2.4 性能优化
# 2.5 自动注册机制
# -------------------------------------------
def scheduler_add_one_user_job():
    pass


def scheduler_del_one_user_job():
    pass


def memory_add_one_user_job():
    pass


def memory_del_one_user_job():
    pass


# --------------------------------------------
# API：Service Startup
# --------------------------------------------
if __name__ == '__main__':
    app.run(port=6600, host='0.0.0.0', debug=True)
