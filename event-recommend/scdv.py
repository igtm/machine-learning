## create gwbowv
from sklearn.feature_extraction.text import TfidfVectorizer,HashingVectorizer
import pickle
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from gensim.models import word2vec
import numpy as np
from learning import WordDividor, WordPreProcessor
import time
from loadQiita import saveJSON, loadJSON

def cluster_GMM(num_clusters, word_vectors):
    # Initalize a GMM object and use it for clustering.
    clf =  GaussianMixture(n_components=num_clusters,
                    covariance_type="tied", init_params='kmeans', max_iter=50)
    # Get cluster assignments.
    clf.fit(word_vectors)
    idx = clf.predict(word_vectors)
    # Get probabilities of cluster assignments.
    idx_proba = clf.predict_proba(word_vectors)
    # Dump cluster assignments and probability of cluster assignments. 
    pickle.dump(idx, open('./gmm_latestclusmodel_len2alldata.pkl',"wb"))
    print ("Cluster Assignments Saved...")

    pickle.dump(idx_proba,open( './gmm_prob_latestclusmodel_len2alldata.pkl',"wb"))
    print ("Probabilities of Cluster Assignments Saved...")
    return (idx, idx_proba)

def read_GMM(idx_name, idx_proba_name):
    # Loads cluster assignments and probability of cluster assignments. 
    idx = pickle.load(open('./gmm_latestclusmodel_len2alldata.pkl',"rb"))
    idx_proba = pickle.load(open( './gmm_prob_latestclusmodel_len2alldata.pkl',"rb"))
    print ("Cluster Model Loaded...")
    return (idx, idx_proba)

def get_probability_word_vectors(featurenames, word_centroid_map, num_clusters, word_idf_dict, model, word_centroid_prob_map, num_features):
    # This function computes probability word-cluster vectors
    prob_wordvecs = {}
    for word in word_centroid_map:
        prob_wordvecs[word] = np.zeros( num_clusters * num_features, dtype="float32" )
        for index in range(0, num_clusters):
            try:
                prob_wordvecs[word][index*num_features:(index+1)*num_features] = model[word] * word_centroid_prob_map[word][index] * word_idf_dict[word]
            except:
                continue

    # prob_wordvecs_idf_len2alldata = {}
    # i = 0
    # for word in featurenames:
    #     i += 1
    #     if word in word_centroid_map:    
    #         prob_wordvecs_idf_len2alldata[word] = {}
    #         for index in range(0, num_clusters):
    #                 prob_wordvecs_idf_len2alldata[word][index] = model[word] * word_centroid_prob_map[word][index] * word_idf_dict[word] 



    # for word in prob_wordvecs_idf_len2alldata.keys():
    #     prob_wordvecs[word] = prob_wordvecs_idf_len2alldata[word][0]
    #     for index in prob_wordvecs_idf_len2alldata[word].keys():
    #         if index==0:
    #             continue
    #         prob_wordvecs[word] = np.concatenate((prob_wordvecs[word], prob_wordvecs_idf_len2alldata[word][index]))
    return prob_wordvecs

def create_cluster_vector_and_gwbowv(prob_wordvecs, wordlist, word_centroid_map, word_centroid_prob_map, dimension, word_idf_dict, featurenames, num_centroids, train=False):
    # This function computes SDV feature vectors.
    bag_of_centroids = np.zeros( num_centroids * dimension, dtype="float32" )
    global min_no
    global max_no

    for word in wordlist:
        try:
            temp = word_centroid_map[word]
        except:
            continue

        bag_of_centroids += prob_wordvecs[word]

    norm = np.sqrt(np.einsum('...i,...i', bag_of_centroids, bag_of_centroids))
    if(norm!=0):
        bag_of_centroids /= norm

    # To make feature vector sparse, make note of minimum and maximum values.
    if train:
        min_no += min(bag_of_centroids)
        max_no += max(bag_of_centroids)

    return bag_of_centroids

if __name__ == "__main__":
    num_features = 200     # Word vector dimensionality

    # Load the trained Word2Vec model.
    model = word2vec.Word2Vec.load("./model/qiita.model")
    # Get wordvectors for all words in vocabulary.
    word_vectors = model.wv.vectors

    # Load train data.
    # train,test = train_test_split(df,test_size=0.3,random_state=40)

    # Set number of clusters.
    num_clusters = 60
    idx, idx_proba = cluster_GMM(num_clusters, word_vectors)

    # Create a Word / Index dictionary, mapping each vocabulary word to
    # a cluster number
    word_centroid_map = dict(zip( model.wv.index2word, idx ))
    # Create a Word / Probability of cluster assignment dictionary, mapping each vocabulary word to
    # list of probabilities of cluster assignments.
    word_centroid_prob_map = dict(zip( model.wv.index2word, idx_proba ))


    # ===============================================================
    # Computing tf-idf values.
    POPULATION = 'qiita-all.json'
    events = loadJSON(POPULATION)
    description = [e['description'] for e in events if 'description' in e]

    wd = WordDividor()
    wpp = WordPreProcessor(analyze_method=wd.extract_words)
    tfidf_condition, feature_matrix = wpp.wordspreprocess(raw_data=description)
    # 保存
    tfidf_condition.set_params(analyzer='word')

    # tfidfmatrix_traindata = wpp.tfidf.fit_transform(traindata)
    featurenames = wpp.tfidf.get_feature_names()
    idf = wpp.tfidf._tfidf.idf_

    # Creating a dictionary with word mapped to its idf value 
    print ("Creating word-idf dictionary for Training set...")

    word_idf_dict = {}
    for pair in zip(featurenames, idf):
        word_idf_dict[pair[0]] = pair[1]
    # print(word_idf_dict)

    # Pre-computing probability word-cluster vectors.
    prob_wordvecs = get_probability_word_vectors(featurenames, word_centroid_map, num_clusters, word_idf_dict, model, word_centroid_prob_map, num_features)
    pickle.dump(prob_wordvecs, open( './prob_wordvecs.pkl',"wb"))





    # gwbowv is a matrix which contains normalised document vectors.
    gwbowv = np.zeros( (len(description), num_clusters*(num_features)), dtype="float32")

    counter = 0

    min_no = 0
    max_no = 0
    for review in description:
        words = review
        gwbowv[counter] = create_cluster_vector_and_gwbowv(prob_wordvecs, words, word_centroid_map, word_centroid_prob_map, num_features, word_idf_dict, featurenames, num_clusters, train=True)
        counter+=1
        if counter % 1000 == 0:
            print ("Train News Covered : ",counter)

    gwbowv_name = "SDV_" + str(num_clusters) + "cluster_" + str(num_features) + "feature_matrix_gmm_sparse.npy"

    gwbowv_test = np.zeros( (len(description), num_clusters*(num_features)), dtype="float32")

    counter = 0

    for review in description:
        # Get the wordlist in each news article.
        words = review
        gwbowv_test[counter] = create_cluster_vector_and_gwbowv(prob_wordvecs, words, word_centroid_map, word_centroid_prob_map, num_features, word_idf_dict, featurenames, num_clusters)
        counter+=1
        if counter % 1000 == 0:
            print ("Test News Covered : ",counter)

    test_gwbowv_name = "TEST_SDV_" + str(num_clusters) + "cluster_" + str(num_features) + "feature_matrix_gmm_sparse.npy"

    print ("Making sparse...")
    # Set the threshold percentage for making it sparse. 
    percentage = 0.04
    min_no = min_no*1.0/len(description)
    max_no = max_no*1.0/len(description)
    print ("Average min: ", min_no)
    print ("Average max: ", max_no)
    thres = (abs(max_no) + abs(min_no))/2
    thres = thres*percentage

    # Make values of matrices which are less than threshold to zero.
    temp = abs(gwbowv) < thres
    gwbowv[temp] = 0

    temp = abs(gwbowv_test) < thres
    gwbowv_test[temp] = 0

    #saving gwbowv train and test matrices
    np.save("./model/"+gwbowv_name, gwbowv)
    np.save("./model/"+test_gwbowv_name, gwbowv_test)
