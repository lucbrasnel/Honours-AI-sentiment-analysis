from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk import tokenize
import configparser
import json
import re

# ===================================== Global vars ===========================================

config = configparser.ConfigParser()
sent_analyser = SentimentIntensityAnalyzer()

# ====================================== func defs ============================================

def get_tokenized_text(infile, verbose = False):
    posts = []

    # open file
    with open(infile, 'r', encoding='utf-8') as f:
      # for every line, extract json
      count = 1
      for line in f:
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

def export_sents_to_file(posts, outfile, verbose = False):
    out = {
        'uri' : '',
        'compound_sent' : 0,
        'neg_sent' : 0,
        'neu_sent' : 0,
        'pos_sent' : 0
    }

    count = 0

    # get sentiments for each post
    for post, uri  in posts:
        # get sentiment scores for text
        if verbose: print(f"{count} Getting scores for text with uri: {uri}")

        sent_scores = sent_analyser.polarity_scores(post)
        
        # check if text part of same post as prev
        if uri == out['uri']:
            # do not print yet
            # combine and store scores of text parts for same post
            for k in sorted(sent_scores):
                score_type = f"{k}_sent"
                score = sent_scores[k]

                old_score = out[score_type]

                new_score = round((score + old_score)/2, 4)

                out[score_type] = new_score

            if verbose: print(f"{count} Combined scores for post: {uri}\t| Compound:{out['compound_sent']}")
        else:
            # print prev score for uri
            if out['uri'] != '': # except for init value
                write_scores_to_file(outfile, out)
                if verbose: print(f"{count} Wrote scores for post: {uri}")

            # set new uri and score for it
            out['uri'] = uri
            count = count + 1

            for k in sorted(sent_scores):
                score_type = f"{k}_sent"
                score = sent_scores[k]

                out[score_type] = score

    # print scores for last uri
    write_scores_to_file(outfile, out)
            
#----------------------------------------------------------------------------------------------

def write_scores_to_file(outfile, data):
    #write line to file
    with open(outfile, 'a') as f:
      json.dump(data, f)
      f.write('\n')

# ===================================== Main func =============================================

if __name__ == "__main__":
    # config setup:
    config.read("config.ini")

    infile = config['DEFUALT']['datafile']
    outfile = config['DEFUALT']['savefile']
    verbose = config['DEFUALT'].getboolean('verbose')

    # get text from input
    posts = get_tokenized_text(infile, verbose)

    # export to file
    export_sents_to_file(posts, outfile, verbose)

# ===================================== end of program ========================================