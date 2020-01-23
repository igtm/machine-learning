from gensim.models import word2vec
from learning import WordDividor
from loadQiita import saveJSON, loadJSON
import logging

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    
    POPULATION = 'qiita-all.json'
    events = loadJSON(POPULATION)
    
    wd = WordDividor()
    description = [wd.extract_words(e['description']) for e in events if 'description' in e]
    
    model = word2vec.Word2Vec(description, size=200, min_count=20, window=15)
    model.save("./model/qiita.model")