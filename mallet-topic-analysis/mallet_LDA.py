import little_mallet_wrapper as lmw
import configparser
import re
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# ===================================== Global vars ===========================================

config = configparser.ConfigParser()

# ====================================== func defs ============================================

#----------------------------------------------------------------------------------------------
  
def format_data(data, verbose):    
    #get data from line
    stuff = data.split('\t')

    text = ' '.join(stuff[2:])
    uri = stuff[0]
    topic = stuff[1]

    #clean text
    text = text.strip()

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

#----------------------------------------------------------------------------------------------

def calc_model_perplexity(path_to_output_probabilities, test_data):
    with open(path_to_output_probabilities, 'r') as f:
        log_prob = float(f.readline())

    token_count = 0

    for text in test_data:
        token_count += len(text.split(' '))

    preplexity = np.exp((-1 * (log_prob / token_count)))

    if verbose: print(f"log prob:{log_prob}\ntoken_count:{token_count}")

    return preplexity

#---------------------------------------------------------------------------------------------- 
# added method for wrapping MALLET evaluate-topics
def evaluate_topics(path_to_mallet,
                 path_to_formatted_test_data,
                 path_to_evaluation_doc,
                 path_to_document_probs,
                 path_to_output_probs
                 ):

    print('Evaluating topics using pre-trained model...')
    os.system(path_to_mallet + ' evaluate-topics --evaluator "' + path_to_evaluation_doc + '"' \
                                          + ' --input "' + path_to_formatted_test_data + '"' \
                                          + ' --output-doc-probs "' + path_to_document_probs + '"' \
                                          + ' --output-prob "' + path_to_output_probs + '"')
    print('Complete')

#----------------------------------------------------------------------------------------------  
# updated train-topics method from lmw to also save evaluation file
def train_get_evaluate(path_to_mallet,
                      path_to_formatted_training_data,
                      path_to_model,
                      path_to_topic_keys,
                      path_to_topic_distributions,
                      path_to_word_weights,
                      path_to_diagnostics,
                      path_to_evaluation_doc,
                      num_topics):

    print('Training topic model...')
    os.system(path_to_mallet + ' train-topics --input "' + path_to_formatted_training_data + '"' \
                                          + ' --num-topics ' + str(num_topics) \
                                          + ' --inferencer-filename "' + path_to_model + '"' \
                                          + ' --output-topic-keys "' + path_to_topic_keys + '"' \
                                          + ' --output-doc-topics "' + path_to_topic_distributions + '"' \
                                          + ' --topic-word-weights-file "' + path_to_word_weights + '"' \
                                          + ' --diagnostics-file "' + path_to_diagnostics + '"' \
                                          + ' --evaluator-filename "' + path_to_evaluation_doc + '"' \
                                          + ' --optimize-interval 10' \
                                          + ' --alpha 1' \
                                          + ' --num-iterations 2000')
    print('Complete')
    
# ===================================== Main func =============================================

if __name__ == "__main__":
    # config setup:
    config.read("config.ini")

    mallet_path = config['DEFAULT']['malletpath']
    data_file = config['DEFAULT']['datafile']
    setName = config['DEFAULT']['setName']
    numTopics = config['DEFAULT']['numTopics']
    verbose = config['DEFAULT'].getboolean('verbose')

    #==============================
    calc_perplexity = config['DEFAULT'].getboolean('perplexity')
    #==============================

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

    if calc_perplexity:
        output_data_path = output_data_path + '/perplexity'

        # create dir for project + file paths
        try:
            os.mkdir(f"projects/{setName}/perplexity")
        except FileExistsError:
            print(f"{setName}/perplexity dir already exists in projects")
        except PermissionError:
            print(f"Permission denied: Unable to create '{setName}/perplexity'.")
        except Exception as e:
            print(f"An error occurred: {e}")

        path_training_data = output_data_path + '/training_perplexity.txt'
        path_formatted_training_data = output_data_path + '/mallet_perplexity.training'

        path_test_data = output_data_path + '/test_perplexity.txt'
        path_formatted_test_data = output_data_path + '/mallet_test_perplexity.training'

        path_model = output_data_path + '/mallet.model.perplexity'
        path_topic_keys  = output_data_path + '/mallet.topic_keys.perplexity'
        path_topic_distributions = output_data_path + '/mallet.topic_distributions.perplexity'
        path_word_weights = output_data_path + '/mallet.word_weights.perplexity'
        path_diagnostics = output_data_path + '/mallet.diagnostics.perplexity.xml'

        path_document_probabilities = output_data_path + '/mallet.doc_probs.perplexity'
        path_output_probabilities= output_data_path + '/mallet.out_probs.perplexity'

        path_evaluation_doc = output_data_path + '/mallet.evaluation.perplexity'
    else:
        path_training_data = output_data_path + '/training.txt'
        path_formatted_training_data = output_data_path + '/mallet.training'
        path_model = output_data_path + '/mallet.model.' + str(numTopics)
        path_topic_keys  = output_data_path + '/mallet.topic_keys.' + str(numTopics)
        path_topic_distributions = output_data_path + '/mallet.topic_distributions.' + str(numTopics)
        path_word_weights = output_data_path + '/mallet.word_weights.' + str(numTopics)
        path_diagnostics = output_data_path + '/mallet.diagnostics.' + str(numTopics) + '.xml'
    

    # get training data
    textData, fileTopics, uris = get_posts_data(data_file, verbose)


    if calc_perplexity:
        # calc perplexity curve
        # train models for a variety of amounts of topics [2, 5, 10, 25, ..+25.., 400]
        topic_num_range = [2, 5, 10, 25, 50, 75, 100, 125, 150, 175, 200] #, 225, 250, 275, 300, 325, 350, 375, 400]
        perplexities = []

        # split dataset into a smaller section (250 000) and test set (50 000)
        idx = np.random.choice(np.arange(len(textData)), 300000, replace = False)
        rndm_uris = list(np.array(uris)[idx])
        rndm_posts = list(np.array(textData)[idx])

        train_uris = rndm_uris[:249999]
        train_text = rndm_posts[:249999]
        if verbose: print(f"training dataset len:{len(train_uris)}")

        test_uris = rndm_uris[250000:]
        test_text = rndm_posts[250000:]
        if verbose: print(f"training dataset len:{len(test_uris)}")

        #import training data
        lmw.import_data(mallet_path, path_training_data, path_formatted_training_data, train_text, train_uris)

        #import test data
        lmw.import_data(mallet_path, path_test_data, path_formatted_test_data, test_text, test_uris)

        for topic_num in topic_num_range:
            # train model
            train_get_evaluate(mallet_path, path_formatted_training_data, path_model, path_topic_keys, path_topic_distributions, path_word_weights, path_diagnostics, path_evaluation_doc, topic_num)
             
            # infer on test set
            evaluate_topics(mallet_path, path_formatted_test_data, path_evaluation_doc, path_document_probabilities, path_output_probabilities)

            # get perplexity
            perplex_topnum = []

            perp = calc_model_perplexity(path_output_probabilities, test_text)
            perplex_topnum.append(topic_num)
            perplex_topnum.append(perp)
            perplexities.append(perplex_topnum)

            print(perplexities)

        df = pd.DataFrame(perplexities, columns=['Topic Count', 'Perplexity'])
        perp_plot = sns.lineplot(df, x='Topic Count', y='Perplexity')

        plt.show()

        fig = perp_plot.get_figure()
        fig.savefig('projects/perplexity.png')
    else:
        # import into mallet  
        lmw.import_data(mallet_path, path_training_data, path_formatted_training_data, textData, uris)

        # train topic model
        lmw.train_topic_model(mallet_path, path_formatted_training_data, path_model, path_topic_keys, path_topic_distributions, path_word_weights, path_diagnostics, numTopics)

# ===================================== end of program ========================================