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
    #get data from line
    stuff = data.split('\t')

    text = str(stuff[2:])
    uri = stuff[0]
    topic = stuff[1]

    # replace \n chars in text
    text = re.sub('\r?\n', ' ', text)
    text = re.sub('\n', ' ', text)
    text = re.sub('\r', ' ', text)

    if verbose: print(f"extracted uri:{uri} on {topic}")

    return uri, topic, text

#----------------------------------------------------------------------------------------------

def get_posts_data(infile, verbose = False):
    text_data = []
    topics = []
    uris = []

    # open file
    with open(infile, 'r') as f:
      # for every line, extract json
      count = 1
      for line in f:
        if verbose: print(f"reading line:{count}")

        # extract data
        uri, topic, text = format_data(line, verbose)

        text_data.append(text)
        topics.append(topic)
        uris.append(uri)

        # add post to list
        count += 1

    return text_data, topics, uris
    
# ===================================== Main func =============================================

if __name__ == "__main__":
    # config setup:
    config.read("config.ini")

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
    
    file_path = os.getcwd()
    output_data_path = f"{file_path}/projects/{setName}"
    data_file = output_data_path+'/'+data_file

    path_training_data = output_data_path + '/training.txt'
    path_formatted_training_data = output_data_path + '/mallet.training'
    path_model = output_data_path + '/mallet.model.' + str(numTopics)
    path_topic_keys  = output_data_path + '/mallet.topic_keys.' + str(numTopics)
    path_topic_distributions = output_data_path + '/mallet.topic_distributions.' + str(numTopics)
    path_word_weights = output_data_path + '/mallet.word_weights.' + str(numTopics)
    path_diagnostics = output_data_path + '/mallet.diagnostics.' + str(numTopics) + '.xml'

    # get training data
    textData, fileTopics, uris = get_posts_data(data_file, verbose)

    # import into mallet  
    lmw.import_data(mallet_path, path_training_data, path_formatted_training_data, textData, uris)

    # train topic model
    lmw.train_topic_model(mallet_path, path_formatted_training_data, path_model, path_topic_keys, path_topic_distributions, path_word_weights, path_diagnostics, numTopics)

# ===================================== end of program ========================================