FROM continuumio/anaconda3
RUN apt-get update && \
    apt-get install libssl-dev gcc build-essential -y
RUN mkdir /opt/notebooks
WORKDIR /tmp
ADD mecab-0.996.tar.gz /tmp
ADD mecab-ipadic-2.7.0-20070801.tar.gz /tmp
RUN cd mecab-0.996 && \ 
    ./configure --with-charset=utf8  && \ 
    make && \ 
    make check && \ 
    su && \ 
    make install
ENV LD_LIBRARY_PATH /usr/local/lib:$LD_LIBRARY_PATH
RUN cd mecab-ipadic-2.7.0-20070801 && \
    ./configure --with-charset=utf8 && \
    make && \
    su && \
    make install
RUN pip install --upgrade pip && \
    pip install mecab-python3 urllib3 gensim
# locale
RUN apt-get install locales -y && \
    echo "ja_JP UTF-8" > /etc/locale.gen && \
    locale-gen
CMD bash -c "conda install jupyter -y --quiet && jupyter notebook --notebook-dir=/opt/notebooks --ip='*' --no-browser --allow-root"``