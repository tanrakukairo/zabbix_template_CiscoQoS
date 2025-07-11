#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'tsuno teppei'
__version__ = '0.1.0'

'''
ZabbixでCiscoのQoS情報を取得するためのスクリプト
このスクリプトは、CiscoのQoS情報をSNMPを使用して取得し、Zabbixで利用できる形式で出力します。
QoS情報は以下のリスト形式で出力されます。[]はインデックスの長さです。
[
    {
        'index': QOS_CLASS_INDEX.INDEX[2],
        'interface': IF_NAME.VALUE,
        'qos_direction': QOS_IF_DIRECTION.VALUE,
        'class_name': QOS_CLASS_NAME.VALUE,
    }
]
リスト各要素のキー名をLLDマクロに変換します。
index        -> {#INDEX}
interface    -> {#IF_NAME}
qos_direction -> {#QOS_IF_DIRECTION}
class_name   -> {#CLASS_NAME}

LLDで次のOIDをアイテムプロトタイプで登録します。
packetのメトリクスを取得するOID: .1.3.6.1.4.1.9.9.166.1.15.1.1.3.{#INDEX}
dropのメトリクスを取得するOID:   .1.3.6.1.4.1.9.9.166.1.15.1.1.14.{#INDEX}
PreByteレートを取得するOID:      .1.3.6.1.4.1.9.9.166.1.15.1.1.6.{#INDEX}
PostByteレートを取得するOID:     .1.3.6.1.4.1.9.9.166.1.15.1.1.10.{#INDEX}

各メトリクスは次のApplicationタグが設定されます。
Application: {#IF_NAME}.{#QOS_IF_DIRECTION}
各メトリクスは次のアイテム名が設定されます。
{#CLASS_NAME}: METRICS
'''

import subprocess
import json
import argparse

parser = argparse.ArgumentParser(description='Cisco QoS Discovery Script')
parser.add_argument('-c', '--community', type=str, required=True, help='SNMP community string')
parser.add_argument('-t', '--target', type=str, required=True, help='Target device IP address or hostname')
ARGS = parser.parse_args()

# SNMPの実行ファイルのパス
SNMPWALK = '/usr/bin/snmpbulkwalk'
RETRY = 1
TIMEOUT = 5

# CiscoのQoS状態を取得するスクリプト
# インターフェイス名を取得する IF_NAME.INDEX[1] = IF_NAME.VALUE
IF_NAME = '.1.3.6.1.2.1.2.2.1.2'
# CISCO-CALSS-BASED-QOS-MIB
QOS_BASE = '.1.3.6.1.4.1.9.9.166'
# 設定されているインターフェイス、対象物理インターフェイスのINDEXが取得される QOS_IF.INDEX[1] = IF_NAME.INDEX[1]
QOS_IF = QOS_BASE + '.1.1.1.1.4'
# QoSインターフェイスの方向を取得する QOS_IF_DIRECTION.VALUE = 1:IN 2:OUT
QOS_IF_DIRECTION = QOS_BASE + '.1.1.1.3'
# QOSクラス名を取得する QOS_CLASS_NAME.INDEX[1] = QOS_CLASS_NAME.VALUE
QOS_CLASS_NAME = QOS_BASE + '.1.7.1.1.1'
# QOSメトリクスのインデックスとクラスインデックスの紐づけ QOS_CLASS_INDEX.INDEX[2] = QOS.CLASS_NAME.INDEX
QOS_CLASS_INDEX = QOS_BASE + '.1.5.1.1.2'


# snmpbulkで取得する
PARAMS = [
    SNMPWALK,
    '-v', '2c',
    '-c', ARGS.community,
    '-O', 'n',
    '-r', str(RETRY),
    '-t', str(TIMEOUT),
    ARGS.target
]

def get_qos_info(oid, id_len=1):
    params = PARAMS + [oid]
    try:
        output = subprocess.check_output(params, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print(f'Error executing SNMP walk for {oid}: {e}')
        return False
    # 改行して各行を処理
    result = {}
    for line in output.strip().split('\n'):
        if not line:
            # 空行はスキップ
            continue
        # 行を分割してOIDと値を取得
        oid, value = line.split(' = ')
        if value == '':
            # 値が空の場合はスキップ
            continue
        oid = oid.strip().split('.')
        value = value.split(':')[-1].strip()
        result.update(
            {
                '.'.join(oid[-id_len:]): value
            }
        )
    return result

if __name__ == '__main__':
    '''
    Cisco QoS Discovery Script
    '''
    output = []
    # インターフェイス名を取得
    if_name = get_qos_info(IF_NAME, 1)
    if not if_name:
        print('Failed to retrieve interface names.')
        exit(1)
    # QoSのインターフェイスを取得
    qos_if = get_qos_info(QOS_IF, 1)
    if not qos_if:
        print('Failed to retrieve QoS interface information.')
        exit(1)
    qos_if_direction = get_qos_info(QOS_IF_DIRECTION, 1)
    if not qos_if:
        print('Failed to retrieve QoS interface information.')
        exit(1)
    # QoSクラス名を取得
    qos_class_name = get_qos_info(QOS_CLASS_NAME, 1)
    if not qos_class_name:
        print('Failed to retrieve QoS class names.')
        exit(1)
    # QoSクラスインデックスを取得
    qos_class_index = get_qos_info(QOS_CLASS_INDEX, 2)
    if not qos_class_index:
        print('Failed to retrieve QoS class index information.')
        exit(1)
    # qos_class_indexをキーにして、物理インターフェイス名とQoSクラス名を取得
    for key, value in qos_class_index.items():
        # keyはqos_if_index.qos_class_idの構造
        qos_if_index = key.split('.')[0]
        # 物理インターフェイス名のインデックスを取得
        if_index = qos_if[qos_if_index]
        # 出力用の辞書を作成
        output.append(
            {
                'index': key,
                'interface': if_name[if_index],
                'qos_if_direction': 'IN' if qos_if_direction[qos_if_index] == '1' else 'OUT',
                'class_name': qos_class_name[value],
            }
        )
    # JSON形式で出力
    print(json.dumps(output, ensure_ascii=False))
    exit(0)
#EOS