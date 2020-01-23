import pickle
import re
import numpy as np
from loadQiita import saveJSON, loadJSON
import MeCab
from sklearn.feature_extraction.text import TfidfVectorizer

'''
MeCabで名詞だけを抜き取るクラスの定義
辞書は"mecab-ipadic-neologd"を使用
'''

f = open("./stopwords.txt","rb")
stopwords = pickle.load(f)

class WordDividor:
    INDEX_CATEGORY = 0
    TARGET_CATEGORY = ['名詞']

    def __init__(self, dictionary="mecabrc"):
        self.dictionary = dictionary
        self.tagger = MeCab.Tagger(self.dictionary)

    def extract_words(self, text):
        if not text:
            return []

        # テキストの余分なデータの削除(ex : httpなど)
        text = re.sub(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-…]+', "", text)
        text = re.sub(r'[!-~]', "", text)  # 半角記号,数字,英字
        text = re.sub(r'[︰-＠]', "", text)  # 全角記号
        text = re.sub('\n', " ", text)  # 改行文字
        text = re.sub(r'<[a-zA-Z0-9]+>', "", text)  # HTMLタグ FIXME: ちゃんとやる

        words = []
        # 文字列がGCされるのを防ぐ
        self.tagger.parse('')
        node = self.tagger.parseToNode(text)
        while node:
            # "，"で文字列の分割を行い, ターゲットになる品詞と比較を行う.
            if node.feature.split(',')[self.INDEX_CATEGORY] in self.TARGET_CATEGORY:
                # ストップワードの判定を行う(stopwordsに引っかかってない名詞を入れる)
                if node.surface not in stopwords:
                    words.append(node.surface)
            node = node.next

        return words

'''
TF-IDF変換を行うクラスの定義
1. TfidfVectorizerインスタンスの作成(analyzerにmecabの形態素解析手法を指定)
2. fitメソッドを行ったTfidfVectorizerインスタンスを返す(新しいデータに用いるため)
'''
class WordPreProcessor:

    # コンストラクタ
    def __init__(self, analyze_method):
        self.tfidf = TfidfVectorizer(analyzer=analyze_method, use_idf=True, norm='l2', smooth_idf=True)

    def wordspreprocess(self, raw_data):
        # fitの状態を格納(TfidfVectorizerインスタンスが格納される)
        tfidf_condition = self.tfidf.fit(raw_data)
        # 形態素解析されたワードを、fitで作ったTF-IDF特徴空間行列に変換する
        tfidf_vector = self.tfidf.transform(raw_data).toarray()

        return tfidf_condition, np.matrix(tfidf_vector)


if __name__ == '__main__':
    POPULATION = 'qiita-all.json'
    events = loadJSON(POPULATION)
    description = [e['description'] for e in events if 'description' in e]

    wd = WordDividor()
    wpp = WordPreProcessor(analyze_method=wd.extract_words)
    tfidf_condition, feature_matrix = wpp.wordspreprocess(raw_data=description)
    print(feature_matrix)
    # 保存
    tfidf_condition.set_params(analyzer='word')
    pickle.dump(tfidf_condition, open("qiita-all-tfidf.pkl", "wb"))