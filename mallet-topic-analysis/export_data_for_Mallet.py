import json
import re
import os
import configparser
from nltk.corpus import stopwords
from nltk.tokenize import WordPunctTokenizer
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag

# extracts text from jsonl file to text file, which can be converted for Mallet analysis by mallect command

# ===================================== Global vars ===========================================

config = configparser.ConfigParser()
lemmatizer = WordNetLemmatizer()
tokenizer = WordPunctTokenizer()
stop_words = set(stopwords.words('english'))

# ====================================== func defs ============================================

def write_to_file(data, outfile, verbose):
    #get data from json obj
    text = data['text']
    uri = data['uri']
    topic = data['Topic']

    #reformat to mallet tab-delimited format: [ID] [tag] [text]
    out = f"{uri}\t{topic}\t{text}"

    #write line to file
    with open(outfile, 'a') as f:
        f.write(out)
        f.write('\n')

    if verbose: print(f"wrote uri:{uri} on {topic}")

#----------------------------------------------------------------------------------------------

def get_posts_data(infile, outfile, verbose = False):
    # open file
    with open(infile, 'r', encoding='utf-8') as f:
      # for every line, extract json
      count = 1
      for line in f:
        if verbose: print(f"reading line:{count}")
        #lstr = line
        data = json.loads(line)

        new_data = format_post(data, verbose)

        write_to_file(new_data, outfile, verbose)
        count += 1

#----------------------------------------------------------------------------------------------

def format_post(data, verbose = False):
    out = data

    #get data from json obj
    text = data['text']
    text = text.lower()

    # replace \n chars in text
    text = re.sub('\r?\n', ' ', text)
    text = re.sub('\n', ' ', text)
    text = re.sub('\r', ' ', text)

    # remove any unencodeable chars
    rem_text = text.encode(encoding='cp1252', errors='ignore')
    text = rem_text.decode(encoding='cp1252')

    # Tokenize
    tok_txt = tokenizer.tokenize(text)

    # POS tagging
    pos_tagged_txt = pos_tag(tok_txt, lang='eng')

    # Lemmatization
    # Wordnet Lemmatizer:  It returns the shortest lemma found in WordNet, or the input string unchanged if nothing is found.
    lem_txt = []

    for word, tag in pos_tagged_txt:
        lem_wrd = lemmatizer.lemmatize(word, get_WordNet_pos(tag))
        lem_txt.append(lem_wrd)

    # remove common words (stopwords)
    out_txt = []

    for word in lem_txt:
        if not (word in stop_words):
            out_txt.append(word)

    # recombine post
    text = ' '.join(out_txt)

    text = text.strip()

    out['text'] = text

    return out


#----------------------------------------------------------------------------------------------

def get_WordNet_pos(tag):
    if tag.startswith('J'):  
        return 'a'
    elif tag.startswith('V'):  
        return 'v'
    elif tag.startswith('N'):  
        return 'n'
    elif tag.startswith('R'):  
        return 'r'
    else:
        return 'n'

# ===================================== Main func =============================================

if __name__ == "__main__":
    # config setup:
    config.read("config.ini")

    data_file = config['DEFAULT']['datafile']
    jsonfile = config['DEFAULT']['jsonfile']
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

    outfile = output_data_path+'/'+data_file
    infile = jsonfile

    get_posts_data(infile, outfile, verbose)

# ===================================== end of program ========================================

# POS tags 
# CC coordinating conjunction 
# CD cardinal digit 
# DT determiner 
# EX existential there (like: "there is" ... think of it like "there exists") 
# FW foreign word 
# IN preposition/subordinating conjunction 
# JJ adjective - 'big' 
# JJR adjective, comparative - 'bigger' 
# JJS adjective, superlative - 'biggest' 
# LS list marker 1) 
# MD modal - could, will 
# NN noun, singular '- desk' 
# NNS noun plural - 'desks' 
# NNP proper noun, singular - 'Harrison' 
# NNPS proper noun, plural - 'Americans' 
# PDT predeterminer - 'all the kids' 
# POS possessive ending parent's 
# PRP personal pronoun -  I, he, she 
# PRP$ possessive pronoun - my, his, hers 
# RB adverb - very, silently, 
# RBR adverb, comparative - better 
# RBS adverb, superlative - best 
# RP particle - give up 
# TO - to go 'to' the store. 
# UH interjection - errrrrrrrm 
# VB verb, base form - take 
# VBD verb, past tense - took 
# VBG verb, gerund/present participle - taking 
# VBN verb, past participle - taken 
# VBP verb, sing. present, non-3d - take 
# VBZ verb, 3rd person sing. present - takes 
# WDT wh-determiner - which 
# WP wh-pronoun - who, what 
# WP$ possessive wh-pronoun, eg- whose 
# WRB wh-adverb, eg- where, when