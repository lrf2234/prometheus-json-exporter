from yaml import safe_load
from prometheus_client import Gauge, CollectorRegistry, generate_latest
from flask import Flask, Response
from wsgiref.simple_server import make_server
from concurrent.futures import ThreadPoolExecutor, as_completed
from jsonpath import JSONPath
from json import loads
from re import compile as re_compile
import urllib.request
import logging

app = Flask(__name__)
logging.basicConfig(
    # filename='application.log',
    level=logging.INFO,
    format='[%(asctime)s] %(filename)s:%(lineno)d [%(levelname)s] %(message)s',
)


def http_json_data(urls: list, headers: dict = None) -> [dict]:
    """
    :param headers:
    :param urls:
    :return:
    """
    def httpd(url):
        try:
            req = urllib.request.Request(url=url, headers=headers, method='GET')
            resp = urllib.request.urlopen(req)
            return loads(resp.read())
        except Exception as e:
            logging.error(e)
            return {}

    headers = headers if headers else {}
    Executor = ThreadPoolExecutor(max_workers=20)     # 线程池，最多 max_workers 个线程同时执行
    result = [f.result() for f in as_completed([Executor.submit(httpd, url) for url in urls])]
    Executor.shutdown()

    return result


def registry_metric(module: dict, registry: CollectorRegistry) -> dict:
    result = {}
    for met in module.get('metrics'):
        label_keys = met.get('labels', {}).keys()
        met_name = met.get('name')
        if met.get('values'):                           # ## "values" in module config
            for v_name in met.get('values').keys():
                name = '_'.join([met_name, v_name])
                result.update({
                    name: Gauge(name, met.get('help', ''), labelnames=label_keys, registry=registry)
                })
        else:                                           # ## "values" not in module config
            result.update({
                met_name: Gauge(met_name, met.get('help', ''), labelnames=label_keys, registry=registry)
            })
    return result


def json_collector_module(module: dict) -> (bytes, int):
    registry = CollectorRegistry(auto_describe=False)
    reg_metrics = registry_metric(module, registry)     # # 用于记录 注册的 metrics 有哪些，避免重复 注册
    replace_regx = re_compile('^{|}$')
    measure_regx = re_compile('^{.*}$')

    for met in module.get('metrics', {}):               # # 配置文件中提取 metrics
        met_name = met.get('name')
        path = '$%s' % replace_regx.sub('', met.get('path', '{}'))

        for data in http_json_data(module.get('target'), module.get('headers', {})):     # ### 通过 http 获取json数据
            path_data = JSONPath(path).parse(data)      # # 提取 json 数据中 path 下对应的数据，返回是 list
            for each_p_data in path_data:
                labels = {}
                for k, v in met.get('labels', {}).items():      # # # 生成labels 的字典{key: v}， metric 需要该字典的 key，value
                    if measure_regx.match(v):           # # 如果value 符合正则 ‘^{.*}$’ ，则要动态从json数据中获取对应值
                        labels.update({
                            k: ','.join(map(str, JSONPath('$%s' % (replace_regx.sub('', v))).parse(each_p_data)))
                        })
                    else:                               # # 如果value 不符合正则 ‘^{.*}$’ ，则本身就是label的值
                        labels.update({k: v})

                # ### 生成 values 的字典{key: v}, key 后续也作为metric的name使用，v 为metric 的值
                if met.get('values'):               # ## 如果配置中有 values 配置，则通过配置中的 path+value构成的jsonpath获取值
                    values = {}
                    for k, v in met.get('values', {}).items():
                        if measure_regx.match(v):       # # 如果value 符合正则 ‘^{.*}$’ ，则要动态从json数据中获取对应值
                            values.update({
                                '_'.join([met_name, k]): JSONPath('$%s' % (replace_regx.sub('', v))).parse(each_p_data)
                            })
                        else:                           # # 如果value 不符合正则 ‘^{.*}$’ ，则本身就是label的值
                            values.update({'_'.join([met_name, k]): v})

                else:                                   # ## 如果配置中 没有 values 配置，则通过配置中的 path构成jsonpath获取值
                    values = {met_name: JSONPath(path).parse(data)[0]}

                for name, val in values.items():
                    gauge_metric = reg_metrics.get(name)      # # 该 metrics 已经注册，直接取出来用
                    gauge_metric.labels(**labels).set(val[0])         # # 设置 该 metrics 的labels和 值

    return generate_latest(registry)         # ###### 返回 bytes 文本, 200 状态码


@app.route(rule='/metric/<module>', methods=['get'])
def metric(module):
    conf = safe_load(open('config/json-config.yml', mode='r', encoding='utf-8'))   # 加载配置文件

    try:
        module = JSONPath('modules.%s' % module).parse(conf)[0]             # ### 配置文件中 提取 module配置信息
    except Exception as e:
        info = 'module: %s not found in config file' % module
        logging.error(info)
        return Response(info), 404

    data = json_collector_module(module)
    return Response(data, mimetype="text/plain"), 200


if __name__ == '__main__':
    make_server('', 8100, app).serve_forever()
