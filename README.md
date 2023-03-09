prometheus-json-exporter
===============

​		这是一个Python3编写的prometheus采集器，将http上的json转换成prometheus采集的数据格式



一、依赖模块
---------------

~~~~
prometheus-client==0.12.0
pyaml==21.10.1
Flask~=2.2.3
jsonpath-python~=1.0.6
~~~~


二、配置文件
-----------------
​		要检查此导出程序支持的JSONPath配置，请访问[jsonpath-python](https://github.com/zhangxianbing/jsonpath-python)

​		在/examples目录中查看示例导出器配置、预期的数据格式

​		默认使用 <u>config/json-config.yml</u> 作为配置文件，也可以通过修改 <u>json_collector.py</u> 改变配置文件，如下所示

```python
@app.route(rule='/metric/<module>', methods=['get'])
def metric(module):
    conf = safe_load(open('config/json-config.yml', mode='r', encoding='utf-8'))   # 加载配置文件

    try:
        module = JSONPath('modules.%s' % module).parse(conf)[0]   # ### 提取 module配置信息
    except Exception as e:
        info = 'module: %s not found in config file' % module
        logging.error(info)
        return Response(info), 404

    data = json_collector_module(module)
    return Response(data, mimetype="text/plain"), 200
```



### Example Usage

```shell
$ cat examples/data.json
```

​		事实上，这是hbase-RegionServer的jmx部分数据，完整数据可通过 http://ip:port/jmx获取，其中ip为hbase-RegionServer服务器的ip，port为hbase-RegionServer监听的端口

```json
{
  "beans": [
    {
      "name": "java.lang:type=OperatingSystem",
      "modelerType": "sun.management.OperatingSystemImpl",
      "OpenFileDescriptorCount": 526,
      "MaxFileDescriptorCount": 65536,
      "CommittedVirtualMemorySize": 6561718272,
      "TotalSwapSpaceSize": 17180913664,
      "FreeSwapSpaceSize": 17180913664,
      "ProcessCpuTime": 145399970000000,
      "TotalPhysicalMemorySize": 16656277504,
      "SystemCpuLoad": 0.003418470137128745,
      "ProcessCpuLoad": 5.979073243647235E-4,
      "FreePhysicalMemorySize": 5160378368,
      "AvailableProcessors": 8,
      "Name": "Linux",
      "Arch": "amd64",
      "Version": "3.10.0-1160.31.1.el7.x86_64",
      "SystemLoadAverage": 0.01,
      "ObjectName": "java.lang:type=OperatingSystem"
    },
    {
      "name": "Hadoop:service=HBase,name=JvmMetrics",
      "modelerType": "JvmMetrics",
      "tag.Context": "jvm",
      "tag.ProcessName": "IO",
      "tag.SessionId": "",
      "tag.Hostname": "guangd-mec-xxsf11d002-yh01x.cam.com"
    },
    {
      "name": "Hadoop:service=HBase,name=RegionServer,sub=Server",
      "modelerType": "RegionServer,sub=Server",
      "tag.zookeeperQuorum": "guangd-mec-xxsf11d002-yh01x:2181,guangd-mec-xxsf11d002-yh02x:2181,guangd-mec-xxsf11d002-yh03x:2181",
      "tag.serverName": "guangd-mec-xxsf11d002-yh01x.cam.com,16020,1671591144989",
      "tag.clusterId": "a0132e20-0b35-48b3-8a2c-5036f851492a",
      "tag.Context": "regionserver",
      "tag.Hostname": "guangd-mec-xxsf11d002-yh01x.cam.com",
      "regionCount": 2,
      "storeCount": 2,
      "hlogFileCount": 3,
      "hlogFileSize": 342238,
      "storeFileCount": 2,
      "memStoreSize": 85560,
      "storeFileSize": 204953859,
      "storeFileIndexSize": 45920,
      "staticIndexSize": 371632,
      "readRequestRatePerSecond": 0.0,
      "writeRequestRatePerSecond": 0.0,
      "totalRequestCount": 27471000,
      "totalRowActionRequestCount": 13749831,
      "readRequestCount": 11009624,
      "filteredReadRequestCount": 30086467481,
      "writeRequestCount": 2740207,
      "flushedCellsCount": 2738755,
      "compactedCellsCount": 94949412,
      "majorCompactedCellsCount": 27336488,
      "flushedCellsSize": 160851595,
      "blockedRequestCount": 0,
      "splitRequestCount": 0,
      "splitSuccessCount": 0,
      "slowGetCount": 0
    }
  ]
}
```



```shell
$ cat examples/json-config.yml
```

```yaml
---
modules:
 # # # #================ hbase jmx =========================
  hbase:							# module，可以有多个，名字不同即可
    target:
      - http://ip1:16030/jmx		# 需要修改为实际可用的 hbase-RegionServer的ip:port
      - http://ip2:16030/jmx
      - http://ip3:16030/jmx
    headers:						# 不需要时，可不配置 headers
      X-Dummy: my-header			# 请求上面的target url时，会加上这些 headers
    metrics:
      - name: OperatingSystem		
        type: guage					# 该k:v未使用，可注销
        help: sun.management.OperatingSystemImpl	
        path: '{.beans}'			# 用于获取json-path下面的数据
        labels:						# k:v字典，当v是以{开头，以}结尾，则会在json数据中获取对应的值
          SystemArch: '{[?(@.name=="java.lang:type=OperatingSystem")].Arch}'  # 主机操作系统架构
          SystemName: '{[?(@.name=="java.lang:type=OperatingSystem")].Name}'
          SystemVersion: '{[?(@.name=="java.lang:type=OperatingSystem")].Version}'  # 主机操作系统
          Hostname: "{[?(@.name==\"Hadoop:service=HBase,name=JvmMetrics\")].tag'.'Hostname}"	# 特殊字符.的写法
        values:						# k:v字典，当v是以{开头，以}结尾，则会在json数据中获取对应的值
          AvailableProcessors: '{[?(@.name=="java.lang:type=OperatingSystem")].AvailableProcessors}'         # 主机 可用进程数==CPU个数
          CommittedVirtualMemorySize: '{[?(@.name=="java.lang:type=OperatingSystem")].CommittedVirtualMemorySize}'  # 提交的虚拟内存大小
          FreePhysicalMemorySize: '{[?(@.name=="java.lang:type=OperatingSystem")].FreePhysicalMemorySize}'      # 主机空闲物理内存大小
          TotalPhysicalMemorySize: '{[?(@.name=="java.lang:type=OperatingSystem")].TotalPhysicalMemorySize}'     # 主机总的物理内存大小
          FreeSwapSpaceSize: '{[?(@.name=="java.lang:type=OperatingSystem")].FreeSwapSpaceSize}'           # 主机空闲交换分区大小
          TotalSwapSpaceSize: '{[?(@.name=="java.lang:type=OperatingSystem")].TotalSwapSpaceSize}'          # 主机总的交换分区大小
          SystemLoadAverage: '{[?(@.name=="java.lang:type=OperatingSystem")].SystemLoadAverage}'           # 主机平均负载
          SystemCpuLoad: '{[?(@.name=="java.lang:type=OperatingSystem")].SystemCpuLoad}'               # 主机CPU负载
          OpenFileDescriptorCount: '{[?(@.name=="java.lang:type=OperatingSystem")].OpenFileDescriptorCount}'     # 主机当前打开文件数
          MaxFileDescriptorCount: '{[?(@.name=="java.lang:type=OperatingSystem")].MaxFileDescriptorCount}'      # 主机可以打开的最大文件数

      - name: HBase_RegionServer_Server
        type: guage
        help: RegionServer,sub=Server
        path: '{.beans[?(@.name=="Hadoop:service=HBase,name=RegionServer,sub=Server")]}'
        labels:
          Hostname: "{.tag'.'Hostname}"              # 主机名
        values:
          totalRequestCount: '{.totalRequestCount}'                   # Regionserver 总请求数
          readRequestCount: '{.readRequestCount}'                     # Regionserver 读请求数
          writeRequestCount: '{.writeRequestCount}'                   # Regionserver 写请求数
          compactedCellsCount: '{.compactedCellsCount}'               # Regionserver 合并Cell的个数
          majorCompactedCellsCount: '{.majorCompactedCellsCount}'     # Regionserver 大合并Cell的个数
          flushedCellsSize: '{.flushedCellsSize}'                     # Regionserver flush到磁盘的大小
          blockedRequestCount: '{.blockedRequestCount}'               # Regionserver 因memstore大于阈值而引发flush的次数
          splitRequestCount: '{.splitRequestCount}'                   # Regionserver region分裂请求次数
          splitSuccessCount: '{.splitSuccessCount}'                   # Regionserver region分裂成功次数
          slowGetCount: '{.slowGetCount}'                             # Regionserver 请求完成时间超过1000ms的次数
          regionCount: '{.regionCount}'                               # Regionserver 管理region数量
          memStoreSize: '{.memStoreSize}'                             # Regionserver 管理的总memstoresize
          storeFileSize: '{.storeFileSize}'                           # Regionserver 管理的storefile大小
          staticIndexSize: '{.staticIndexSize}'                       # Regionserver 所管理的表索引大小
          storeFileCount: '{.storeFileCount}'                         # Regionserver 所管理的storefile个数
          hlogFileSize: '{.hlogFileSize}'                             # Regionserver WAL文件大小
          hlogFileCount: '{.hlogFileCount}'                           # Regionserver WAL文件个数
          storeCount: '{.storeCount}'                                 # Regionserver 所管理的store个数
```

## 三、启动应用

​		默认使用8100端口，可在代码中修改

```shell
$ python3 json_collector.py
```

## 四、检验

path: /metric/<module> ，modules指配置文件中的某个modules名字

```shell
$ curl http://127.0.0.1:8100/metric/hbase
```

```console
# HELP OperatingSystem_AvailableProcessors sun.management.OperatingSystemImpl
# TYPE OperatingSystem_AvailableProcessors gauge
OperatingSystem_AvailableProcessors{Hostname="guangd-mec-xxsf11d002-yh03x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 8.0
OperatingSystem_AvailableProcessors{Hostname="guangd-mec-xxsf11d002-yh02x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 8.0
OperatingSystem_AvailableProcessors{Hostname="guangd-mec-xxsf11d002-yh01x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 8.0
# HELP OperatingSystem_CommittedVirtualMemorySize sun.management.OperatingSystemImpl
# TYPE OperatingSystem_CommittedVirtualMemorySize gauge
OperatingSystem_CommittedVirtualMemorySize{Hostname="guangd-mec-xxsf11d002-yh03x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 6.519033856e+09
OperatingSystem_CommittedVirtualMemorySize{Hostname="guangd-mec-xxsf11d002-yh02x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 6.532026368e+09
OperatingSystem_CommittedVirtualMemorySize{Hostname="guangd-mec-xxsf11d002-yh01x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 6.561718272e+09
# HELP OperatingSystem_FreePhysicalMemorySize sun.management.OperatingSystemImpl
# TYPE OperatingSystem_FreePhysicalMemorySize gauge
OperatingSystem_FreePhysicalMemorySize{Hostname="guangd-mec-xxsf11d002-yh03x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 5.106208768e+09
OperatingSystem_FreePhysicalMemorySize{Hostname="guangd-mec-xxsf11d002-yh02x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 5.232484352e+09
OperatingSystem_FreePhysicalMemorySize{Hostname="guangd-mec-xxsf11d002-yh01x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 5.23808768e+09
# HELP OperatingSystem_TotalPhysicalMemorySize sun.management.OperatingSystemImpl
# TYPE OperatingSystem_TotalPhysicalMemorySize gauge
OperatingSystem_TotalPhysicalMemorySize{Hostname="guangd-mec-xxsf11d002-yh03x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 1.6656269312e+010
OperatingSystem_TotalPhysicalMemorySize{Hostname="guangd-mec-xxsf11d002-yh02x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 1.6656277504e+010
OperatingSystem_TotalPhysicalMemorySize{Hostname="guangd-mec-xxsf11d002-yh01x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 1.6656277504e+010
# HELP OperatingSystem_FreeSwapSpaceSize sun.management.OperatingSystemImpl
# TYPE OperatingSystem_FreeSwapSpaceSize gauge
OperatingSystem_FreeSwapSpaceSize{Hostname="guangd-mec-xxsf11d002-yh03x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 1.7180913664e+010
OperatingSystem_FreeSwapSpaceSize{Hostname="guangd-mec-xxsf11d002-yh02x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 1.7180913664e+010
OperatingSystem_FreeSwapSpaceSize{Hostname="guangd-mec-xxsf11d002-yh01x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 1.7180913664e+010
# HELP OperatingSystem_TotalSwapSpaceSize sun.management.OperatingSystemImpl
# TYPE OperatingSystem_TotalSwapSpaceSize gauge
OperatingSystem_TotalSwapSpaceSize{Hostname="guangd-mec-xxsf11d002-yh03x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 1.7180913664e+010
OperatingSystem_TotalSwapSpaceSize{Hostname="guangd-mec-xxsf11d002-yh02x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 1.7180913664e+010
OperatingSystem_TotalSwapSpaceSize{Hostname="guangd-mec-xxsf11d002-yh01x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 1.7180913664e+010
# HELP OperatingSystem_SystemLoadAverage sun.management.OperatingSystemImpl
# TYPE OperatingSystem_SystemLoadAverage gauge
OperatingSystem_SystemLoadAverage{Hostname="guangd-mec-xxsf11d002-yh03x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 0.0
OperatingSystem_SystemLoadAverage{Hostname="guangd-mec-xxsf11d002-yh02x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 0.0
OperatingSystem_SystemLoadAverage{Hostname="guangd-mec-xxsf11d002-yh01x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 0.01
# HELP OperatingSystem_SystemCpuLoad sun.management.OperatingSystemImpl
# TYPE OperatingSystem_SystemCpuLoad gauge
OperatingSystem_SystemCpuLoad{Hostname="guangd-mec-xxsf11d002-yh03x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 0.0013302294645826404
OperatingSystem_SystemCpuLoad{Hostname="guangd-mec-xxsf11d002-yh02x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 0.0013123359580052493
OperatingSystem_SystemCpuLoad{Hostname="guangd-mec-xxsf11d002-yh01x.cam.com",SystemArch="amd64",SystemName="Linux",SystemVersion="3.10.0-1160.31.1.el7.x86_64"} 0.003286230693394676
```
