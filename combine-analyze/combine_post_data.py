import pandas as pd
import numpy as np
import json
import configparser
import os


# ===================================== Global vars ===========================================

config = configparser.ConfigParser()

# ====================================== func defs ============================================

def get_post_data(posts_file, verbose = False):
	posts = pd.read_json(posts_file, lines = True)
    
	posts = posts[['uri','likes','replies','reposts','created_at','has_imgvid']]

	if verbose: print(f"\nExtracted posts from file: {posts.info()}\n{posts.head(n=3)}\n")
	return posts

#----------------------------------------------------------------------------------------------

def get_sent_data(sent_file, verbose = False):
	sents = pd.read_json(sent_file, lines = True)

	if verbose: print(f"\nExtracted sents from file: {sents.info()}\n{sents.head(n=3)}\n")
	return sents

#----------------------------------------------------------------------------------------------
   
def get_topic_data(topic_file, verbose = False):
	# create colomn names
	headers = ['id', 'uri']

	# get num of topics from file name
	num_topics = int((topic_file.split('.'))[-1])

	for i in range(num_topics):
		headers.append(f"topic_{i}")

	topics = pd.read_csv(topic_file, sep = '\t', names = headers)

	if verbose: print(f"\nExtracted Topic Distributions from file: {topics.info()}\n{topics.head(n=3)}\n")
	
	return topics, num_topics
   
#----------------------------------------------------------------------------------------------
   
def merge_data(posts, sents, topics, topic_num, verbose = False):
	# Merge datasets
	merged_data = pd.merge(posts, sents, how = 'inner', on = 'uri')
	if verbose: print(f"\nMerged posts and sents: {merged_data.shape}\n{merged_data.head(n=3)}\n")

	merged_data = pd.merge(merged_data, topics, how = 'inner', on = 'uri')
	if verbose: print(f"\nMerged with topic dists: {merged_data.info()}\n{merged_data.head(n=3)}\n")

	headers = ['uri']
	for x in range(topic_num):
		headers.append(f'topic_sent_{x}')

	out = []
	for i in range(len(merged_data)):
		uri = merged_data.iat[i, 0]

		# get sent scores
		compound_sent = merged_data.at[i, 'compound_sent']
		#negative_sent = merged_data.iloc[i, 'neg_sent']
		#positive_sent = merged_data.iloc[i, 'pos_sent']
		#neutral_sent = merged_data.iloc[i, 'neu_sent']
		
		# create list of uri and topic sentiments for each post
		t_sents = []
		t_sents.append(uri)

		for t in range(topic_num):
			# Matrix mult sents and topic distributions
			t_sents.append(compound_sent * merged_data.at[i, f'topic_{t}'])

		out.append(t_sents)

	#Create DF for calcuated sents for each topic (matrix mult)
	topic_sents = pd.DataFrame(out, columns = headers)

	if verbose: print(f"\nCreated topic sentiment dataset: {topic_sents.info()}\n{topic_sents.head(n=3)}\n")


	return merged_data, topic_sents
   
#----------------------------------------------------------------------------------------------

def write_data_to_file(outfile, data, verbose = False):
	#write line to file
	data.to_json(path_or_buf = outfile, orient = 'records', lines = True)
	if verbose: print(f"\nCreated output file: {outfile}")


# ===================================== Main func =============================================

if __name__ == "__main__":
	# config setup:
	config.read("config.ini")

	post_file = config['DEFUALT']['post_file']
	sentiment_file = config['DEFUALT']['sent_file']
	topic_file = config['DEFUALT']['topic_file']

	output_path = config['DEFUALT']['out_path']

	verbose = config['DEFUALT'].getboolean('verbose')

	# get post data
	posts = get_post_data(post_file, verbose)

	# get sent data
	sents = get_sent_data(sentiment_file, verbose)

	# get topic data
	topic_dists, numTopics = get_topic_data(topic_file, verbose)

	# Merge # calc topic sents with matrix mult
	merged, topic_sents = merge_data(posts, sents, topic_dists, numTopics, verbose)

	# export as files
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