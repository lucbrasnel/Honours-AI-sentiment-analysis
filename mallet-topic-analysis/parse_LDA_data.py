import little_mallet_wrapper as lmw
import numpy as np
import pandas as pd
import configparser
import json
import re
import os

config = configparser.ConfigParser()

# config setup:
config.read("config.ini")

mallet_path = config['DEFAULT']['malletpath']
data_file = config['DEFAULT']['datafile']
setName = config['DEFAULT']['setName']
numTopics = config['DEFAULT']['numTopics']
verbose = config['DEFAULT'].getboolean('verbose')

file_path = os.getcwd()
output_data_path = f"{file_path}/projects/{setName}"

path_training_data = output_data_path + '/training.txt'
path_formatted_training_data = output_data_path + '/mallet.training'
path_model = output_data_path + '/mallet.model.' + str(numTopics)
path_topic_keys  = output_data_path + '/mallet.topic_keys.' + str(numTopics)
path_topic_distributions = output_data_path + '/mallet.topic_distributions.' + str(numTopics)
path_word_weights = output_data_path + '/mallet.word_weights.' + str(numTopics)
path_diagnostics = output_data_path + '/mallet.diagnostics.' + str(numTopics) + '.xml'

# extract topics
topic_keys = lmw.load_topic_keys(path_topic_keys)

if verbose: print(f"topic dist len: {len(topic_keys)}")

print('writing topic keys to txt file')
for i, topics in enumerate(topic_keys):
    with open((output_data_path+'topic_keys.txt'), 'a') as f:
        f.write(f"{i}\t{topics}")
        f.write('\n')

# extract top docs
t_dist = lmw.load_topic_distributions(path_topic_distributions)
with open(path_training_data, 'r') as f:
    assert(len(t_dist) == len(f.readlines))

if verbose: print(f"topic dist len: {len(t_dist), len(t_dist[0])}")

for p, d in lmw.get_top_docs(textData, t_dist, topic_index=0, n=100):
    with open((output_data_path+'top_docs.txt'), 'a') as f:
        f.write(f"{round(p,4)}\t{d}")
        f.write('\n')

# extract word probablity distributions
word_prob_dist = lmw.load_topic_word_distributions(path_word_weights)

if verbose: print(f"Word prob dist len: {len(word_prob_dist)}")

for _t, _wp in word_prob_dist.items():
    print('Topic', _t)
    for _w, _p in sorted(_wp.items(), key=lambda x: x[1], reverse=True)[:5]:
        with open((output_data_path+'Word_prob_dist.txt'), 'a') as f:
            f.write(f"{round(_p,4)}\t{_w}")
            f.write('\n')
    f.write('\n')