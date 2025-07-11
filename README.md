ZabbixでCiscoのQoS情報を取得するためのスクリプト

このスクリプトは、CiscoのQoS情報をSNMPを使用して取得し、Zabbixで利用できる形式で出力します。

QoS情報は以下のリスト形式で出力されます。[]はインデックスの長さです。
```
[
    {
        'index': QOS_CLASS_INDEX.INDEX[2],
        'interface': IF_NAME.VALUE,
        'qos_if_direction': QOS_IF_DIRECTION.VALUE,
        'class_name': QOS_CLASS_NAME.VALUE,
    }
]
```
テンプレートではリスト各要素のキー名をLLDマクロに変換します。

|JsonPath|LLD Macro|
|:--|:--|
|index|{#INDEX}|
|interface|{#IF_NAME}|
|qos_direction|{#QOS_IF_DIRECTION}|
|class_name|{#CLASS_NAME}|

LLDで次のOIDをアイテムプロトタイプで登録します。

|Item|OID|key|
|:--|:--|:--|
|{#CLASS_NAME}: packets|.1.3.6.1.4.1.9.9.166.1.15.1.1.3.{#INDEX}|cisco.qos[{#INDEX},{#CLASS_NAME},packet]|
|{#CLASS_NAME}: drops|.1.3.6.1.4.1.9.9.166.1.15.1.1.14.{#INDEX}|cisco.qos[{#INDEX},{#CLASS_NAME},drop]|
|{#CLASS_NAME}: pre traffic|.1.3.6.1.4.1.9.9.166.1.15.1.1.6.{#INDEX}|cisco.qos[{#INDEX},{#CLASS_NAME},pre]|
|{#CLASS_NAME}: post traffic|.1.3.6.1.4.1.9.9.166.1.15.1.1.10.{#INDEX}|cisco.qos[{#INDEX},{#CLASS_NAME},post]|
|{#CLASS_NAME}: drops over flow|.1.3.6.1.4.1.9.9.166.1.15.1.1.12.{#INDEX}|cisco.qos[{#INDEX},{#CLASS_NAME},drop_overflow]|
|{#CLASS_NAME}: drops no buffer|.1.3.6.1.4.1.9.9.166.1.15.1.1.21.{#INDEX}|cisco.qos[{#INDEX},{#CLASS_NAME},drop_nobuffer]|

各メトリクスは次のApplicationタグが設定されます。

Application:QoS.{#IF_NAME}.{#QOS_IF_DIRECTION},CISCO,QOS,{#CLASS}
