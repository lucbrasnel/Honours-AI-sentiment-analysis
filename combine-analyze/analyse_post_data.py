import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import configparser

# ===================================== Global vars ===========================================

config = configparser.ConfigParser()

# ====================================== func defs ============================================

def get_posts_data(posts_file, verbose = False):
	posts = pd.read_json(posts_file, lines = True)
    
	posts = posts[['uri','likes','replies','reposts','created_at','has_imgvid']]

	if verbose: print(f"\nExtracted posts from file: {posts.info()}\n{posts.head(n=3)}\n")
	return posts

#----------------------------------------------------------------------------------------------

# ===================================== Main func =============================================

if __name__ == "__main__":
	# config setup:
    config.read("config.ini")

    post_file = config['DEFUALT']['post_file']
    sentiment_file = config['DEFUALT']['sent_file']
    topic_file = config['DEFUALT']['topic_file']

    output_path = config['DEFUALT']['out_path']

    verbose = config['DEFUALT'].getboolean('verbose')

    # get sents and make dist graph

    # get topic sents

    # calc overall topic sents

    # create graphs


    # export

    # create dir for project + file paths
    try:
        os.mkdir(output_path)
    except FileExistsError:
        print(f"'{output_path}' dir already exists")
    except PermissionError:
        print(f"Permission denied: Unable to create '{output_path}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

    merged_data_path = output_path + "/merged_dataset.jsonl"
    topic_sents_path = output_path + "/topic_sents.jsonl"

    write_data_to_file(merged, merged_data_path, verbose)
    write_data_to_file(topic_sents, topic_sents_path, verbose)

# ===================================== end of program ========================================