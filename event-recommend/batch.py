import numpy as np
from gensim.models import word2vec
from gensim import models
from gensim.models.doc2vec import LabeledSentence
from loadQiita import saveJSON, loadJSON, mergeJSON, updateQiita
from learning import WordDividor
from datetime import datetime as dt
import math
import requests, json
from dateutil.relativedelta import relativedelta
import locale
locale.setlocale(locale.LC_TIME, "ja_JP")

def train(filename): 
    events = loadJSON(filename)
    print([e['event_id'] for e in events if 'description' in e])

    wd = WordDividor()
    sentences = [LabeledSentence(words=wd.extract_words(e['description']), tags=[e['event_id']]) for e in events if 'description' in e]

    model = models.Doc2Vec(sentences, dm=0, size=300, window=15, alpha=.025,
        min_alpha=.025, min_count=1, sample=1e-6)

    print('\n訓練開始')
    for epoch in range(20):
        print('Epoch: {}'.format(epoch + 1))
        model.train(sentences, epochs=model.iter, total_examples=model.corpus_count)
        model.alpha -= (0.025 - 0.0001) / 19
        model.min_alpha = model.alpha
    
    model.save('./model/'+filename+'.doc2vec.model')
    return model

def loadObject(filename):
    j = loadJSON(filename)
    obj = {}
    for e in j:
        obj[e['event_id']] = e
    return obj

# 0.0 ~ 1.0の値を、赤 ~ 緑 で返す
def getGradColor(prob):
    color = (0,255,0)
    if prob <= 0.5:
        r = math.floor(prob * 2 * 255)
        color = (r, 255, 0)
    if prob > 0.5:
        g = math.floor((1 - prob) * 2 * 255)
        color = (255, g, 0)
    return '#%02X%02X%02X' % (color[0],color[1],color[2])

def postToSlack(qiitas):
    WEB_HOOK_URL = 'https://hooks.slack.com/services/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'
    data = {
        'channel': 'G4ZQ9NYFL',
        'username': u'Connpassレコメンド-Bot',  #ユーザー名
        'icon_emoji': u':connpass:',  #アイコン
        'link_names': 1,  #名前をリンク化
    }
    data['attachments'] = []
    for qiita, cos in qiitas:
        started_at = dt.strptime(qiita['started_at'], '%Y-%m-%dT%H:%M:%S+09:00')
        started_at = started_at.strftime('%m/%d %H:%M(%a)')
        color = getGradColor(qiita['accepted'] / qiita['limit']) if qiita['accepted'] != None and qiita['limit'] != None else '#cccccc'
        data['attachments'].append({
            "color": color,
            'title': '[{}]<cos類似度:{}> {} ({}/{}人)'.format(started_at, '{:.3g}'.format(cos), qiita['title'], qiita['accepted'], qiita['limit']),
            'title_link': qiita['event_url'],
        })
    requests.post(WEB_HOOK_URL, data = json.dumps(data))

# https://deepage.net/machine_learning/2017/01/08/doc2vec.html
# Doc2Vec
# まあまあ精度あるやん。
if __name__ == "__main__":
    POPULATION = 'qiita.json'
    SAMPLE = 'qiita-igtm.json'
    MERGED = 'qiita-all.json'

    # 1. Qiitaからデータ取ってくる
    opt = {}
    now = dt.now()
    one_month_after = now + relativedelta(months=1)
    opt['ym'] = '{},{}'.format(dt.strftime(now, '%Y%m'), dt.strftime(one_month_after, '%Y%m'))
    updateQiita(POPULATION, opt)
    updateQiita(SAMPLE, {'nickname': 'igtm'})
    mergeJSON(POPULATION, SAMPLE, MERGED)

    # # 2. Doc2Vecでmodel生成
    model = train(MERGED)
    # model = models.Doc2Vec.load('./model/'+MERGED+'.doc2vec.model')

    # 3. 自分の参加したeventから似てるイベントを取得
    events = loadJSON(SAMPLE)
    event_ids = [e['event_id'] for e in events if 'description' in e]
    most_similars = model.docvecs.most_similar(topn=100, positive=event_ids)

    # event_idから中身戻す
    future_events_obj = loadObject(POPULATION)
    ret = {}
    for event_id, cos in most_similars:
        ret[event_id] = future_events_obj[event_id]
        ret[event_id]['similarity'] = cos
    print(len(ret))
    # filter: ①東京都内開催 ②募集期間中
    filtered_ret = []
    for k in ret:
        # ①東京都内開催
        if ret[k]['address'] == None:
            continue
        if '東京都' not in ret[k]['address']:
            continue
        # ②募集期間中
        now = dt.now()
        started_at = dt.strptime(ret[k]['started_at'], '%Y-%m-%dT%H:%M:%S+09:00')
        if now > started_at:
            continue
        # +申込済みのやつには＜申込済＞をつける
        if ret[k]['event_id'] in event_ids:
            ret[k]['title'] = '＜申込済＞' + ret[k]['title']
        filtered_ret.append((ret[k], ret[k]['similarity']))

    # 4. Slackにおすすめイベント一覧を投稿
    postToSlack(filtered_ret)
