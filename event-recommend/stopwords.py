import pickle
import urllib3
http = urllib3.PoolManager()

slothlib_path = 'http://svn.sourceforge.jp/svnroot/slothlib/CSharp/Version1/SlothLib/NLP/Filter/StopWord/word/Japanese.txt'
r = http.request('GET',slothlib_path)
print(r.data.decode('utf-8'))
slothlib_stopwords = r.data.decode('utf-8').splitlines()
slothlib_stopwords = [ss for ss in slothlib_stopwords if not ss==u'']
print(slothlib_stopwords)

f = open('stopwords.txt', 'wb')
pickle.dump(slothlib_stopwords, f)