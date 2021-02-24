from flask import Flask, request, jsonify, redirect

from src.BusinessCentralLayer.setting import PUBLIC_API_REDIRECT, PUBLIC_API_TOS, PUBLIC_API_STU_TWQD2, \
    PUBLIC_API_STU_TWQD
from src.BusinessViewLayer.myapp.api import *

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


"""======================================================================"""


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


"""======================================================================"""
if __name__ == '__main__':
    app.run(port=6600, host='0.0.0.0', debug=True)
