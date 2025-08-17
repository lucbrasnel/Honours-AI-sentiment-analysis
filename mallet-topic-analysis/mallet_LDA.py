import little_mallet_wrapper as lmw
import numpy as np
import pandas as pd
import configparser
import json
import re
import os

# ===================================== Global vars ===========================================

config = configparser.ConfigParser()

# ====================================== func defs ============================================

#----------------------------------------------------------------------------------------------
  
def format_data(data, verbose):    
    #get data from json obj
    text = data['text']
    uri = data['uri']
    topic = data['Topic']

    # replace \n chars in text
    text = re.sub('\\n', ' ', text)

    #reformat to mallet tab-delimited format: [ID] [tag] [text]
    #out = f"{uri}\t{topic}\t{text}"

    if verbose: print(f"extracted uri:{uri} on {topic}")

    return uri, topic, text

#----------------------------------------------------------------------------------------------

def get_posts_data(infile, verbose = False):
    text_data = []
    topics = []
    uris = []

    # open file
    with open(infile, 'r', encoding='utf-8') as f:
      # for every line, extract json
      count = 1
      for line in f:
        if verbose: print(f"reading line:{count}")
        #lstr = line
        ljson = json.loads(line)

        # extract data
        uri, topic, text = format_data(ljson, verbose)

        text_data.append(text)
        topics.append(topic)
        uris.append(uri)

        # add post to list
        count += 1

    return text_data, topics, uris
    
# ===================================== Main func =============================================

if __name__ == "__main__":
    # config setup:
    config.read(os.path.dirname(os.path.abspath(__file__))+"config.ini")

    mallet_path = config['DEFAULT']['malletpath']
    data_file = config['DEFAULT']['datafile']
    setName = config['DEFAULT']['setName']
    numTopics = config['DEFAULT']['numTopics']
    verbose = config['DEFAULT'].getboolean('verbose')

    # create dir for project + file paths
    try:
        os.mkdir(f"projects/{setName}")
    except FileExistsError:
       print(f"{setName} dir already exists in projects")
    except PermissionError:
        print(f"Permission denied: Unable to create 'projects/{setName}'.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    output_data_path = f"pojects/{setName}"

    path_training_data = output_data_path + '/training.txt'
    path_formatted_training_data = output_data_path + '/mallet.training'
    path_model = output_data_path + '/mallet.model.' + str(numTopics)
    path_topic_keys  = output_data_path + '/mallet.topic_keys.' + str(numTopics)
    path_topic_distributions = output_data_path + '/mallet.topic_distributions.' + str(numTopics)
    path_word_weights = output_data_path + '/mallet.word_weights.' + str(numTopics)
    path_diagnostics = output_data_path + '/mallet.diagnostics.' + str(numTopics) + '.xml'

    textData, fileTopics, uris = get_posts_data(data_file, verbose)

    # import into mallet  
    lmw.import_data(mallet_path, path_training_data, path_formatted_training_data, textData, uris)

    # train topic model
    lmw.train_topic_model(path_topic_keys)

    # extract topics
    topic_keys = lmw.load_topic_keys(path_topic_keys)

    if verbose: print(f"topic dist len: {len(topic_keys)}")

    print('writing topic keys to txt file')
    for i, topics in enumerate(topic_keys):
        with open((output_data_path+'topic_keys.txt'), 'a', encoding='utf-8') as f:
            f.write(f"{i}\t{topics}")
            f.write('\n')

    # extract top docs
    t_dist = lmw.load_topic_distributions(path_topic_distributions)
    assert(len(t_dist) == len(textData))

    if verbose: print(f"topic dist len: {len(t_dist), len(t_dist[0])}")

    for p, d in lmw.get_top_docs(textData, t_dist, topic_index=0, n=100):
        with open((output_data_path+'top_docs.txt'), 'a', encoding='utf-8') as f:
            f.write(f"{round(p,4)}\t{d}")
            f.write('\n')

    # extract word probablity distributions
    word_prob_dist = lmw.load_topic_word_distributions(path_word_weights)

    if verbose: print(f"Word prob dist len: {len(word_prob_dist)}")

    for _t, _wp in word_prob_dist.items():
        print('Topic', _t)
        for _w, _p in sorted(_wp.items(), key=lambda x: x[1], reverse=True)[:5]:
            with open((output_data_path+'Word_prob_dist.txt'), 'a', encoding='utf-8') as f:
                f.write(f"{round(_p,4)}\t{_w}")
                f.write('\n')
        f.write('\n')


# ===================================== end of program ========================================