import pandas as pd
import numpy as np
import json
import configparser
import re


# ===================================== Global vars ===========================================

config = configparser.ConfigParser()

# ====================================== func defs ============================================

def get_post_data(posts_file verbose = False):
    posts = []

    # open file
    with open(post_file, 'r', encoding='utf-8') as fp:
      # for every line, extract json
      count = 1
      for line in fp:
        if verbose: print(f"reading line:{count}")
        
        ljson = json.loads(line)

        text = str(ljson['text'])
        count += 1

        # clean text
        # replace \n chars in text
        text = re.sub('\r?\n', ' ', text)
        text = re.sub('\n', ' ', text)
        text = re.sub('\r', ' ', text)

        # posts with multiple sentinces need to split for vader
        sentences = tokenize.sent_tokenize(text)

        # export each sentence with the uri of the post it came from
        for i in sentences:
           add = []
           add.append(text)
           add.append(ljson['uri'])
           posts.append(add)

    print(f"{posts[-1]}")
    return posts

#----------------------------------------------------------------------------------------------

def get_sent_data()

#----------------------------------------------------------------------------------------------
   
def get_topic_data()
   
#----------------------------------------------------------------------------------------------
   
def merge_data()
   
#----------------------------------------------------------------------------------------------

def write_data_to_file(outfile, data):
    #write line to file
    with open(outfile, 'a') as f:
      json.dump(data, f)
      f.write('\n')

# ===================================== Main func =============================================

if __name__ == "__main__":
    # config setup:
    config.read("config.ini")

    post_file = config['DEFUALT']['datafile']
    sentiment_file = config['DEFUALT']['savefile']
    topic_file = config['DEFUALT']['savefile']
    verbose = config['DEFUALT'].getboolean('verbose')

    # get post data

    # get sent data

    # get topic data

    # export as file

# ===================================== end of program ========================================