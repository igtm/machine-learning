import json
import requests
import time
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta

connpass_endpoint = 'https://connpass.com/api/v1/event/'

def loadJSON(filename):
    try:
        with open(filename, 'r') as f:
            d = json.load(f)
            return d
    except Exception as e:
        print(e)
        return []
def saveJSON(filename, d):
    with open(filename, 'w') as f:
        json.dump(d, f)

# 配列jsonファイルをマージする
def mergeJSON(a, b, merged):
    aEvents = loadJSON(a)
    bEvents = loadJSON(b)
    saveJSON(merged, aEvents + bEvents)

# Qiitaにあるイベントをjsonとして保存
def updateQiita(filename, opt):
    COUNT = 100
    for i in range(1,100):
        params = {'order': '2', 'count': COUNT, 'start': (i-1) * COUNT + 1}
        r = requests.get(connpass_endpoint, params={**params, **opt})
        events = loadJSON(filename)
        saveJSON(filename, events + r.json()['events'])
        print('count: {}, results_returned: {}'.format(i, r.json()['results_returned']))
        # next
        if r.json()['results_returned'] < COUNT:
            break
        time.sleep(2)

if __name__ == '__main__':
    opt = {}
    now = dt.now()
    one_month_after = now + relativedelta(months=1)
    opt['ym'] = '{},{}'.format(dt.strftime(now, '%Y%m'), dt.strftime(one_month_after, '%Y%m'))
    print(opt)
    # opt['nickname'] = 'igtm'
    #updateQiita('qiita.json', opt)
    #mergeJSON('qiita.json', 'qiita-igtm.json', 'qiita-all.json')
