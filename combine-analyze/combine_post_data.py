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
   
def merge_datasets(posts, sents, topics, topic_num, verbose = False):
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
   
def get_top_topics(merged_data, topic_num, top_num, out_path, verbose = False):
	count = 0

	out = {
		'uri' : '',
		'compound_sent' : 0,
		'likes' : 0,
		'replies' : 0,
		'reposts' : 0,
		'created_at' : ''
	}
	
	# for each posts
	for i in range(len(merged_data)):

		# get sentiment and uri
		uri = merged_data.iat[i, 0]
		sent_score = merged_data.at[i, 'compound_sent']
		likes = int(merged_data.at[i, 'likes'])
		replies = int(merged_data.at[i, 'replies'])
		reposts = int(merged_data.at[i, 'reposts'])
		created_at = str(merged_data.at[i, 'created_at'])

		# get topic dits
		top_topics = [-1] * top_num

		for x in range(top_num):
			# calc top n topics
			for t in range(topic_num):
				# check if populated
				if(top_topics[x] == -1 and not(t in top_topics)):
					top_topics[x] = t
				elif(top_topics[x] != -1):
					topic_dist = merged_data.at[i, f'topic_{t}']
					compare_dist = merged_data.at[i, f'topic_{top_topics[x]}']

					# check if larger
					if (topic_dist > compare_dist):

						# if larger, check if already in list
						if not(t in top_topics):
							top_topics[x] = t
		
		if verbose: print(f"Processing top topics of post {count}: {top_topics}")
		# Recombine
		out['uri'] = uri
		out['compound_sent'] = sent_score
		out['likes'] = likes
		out['replies'] = replies
		out['reposts'] = reposts
		out['created_at'] = created_at

		# write to files
		for topic in top_topics:
			file_path = out_path + f'/top topics/post_sents_for_{topic}.jsonl'
			#write line to file
			with open(file_path, 'a') as f:
				json.dump(out, f)
				f.write('\n')

		# update count
		count = count + 1

	

#----------------------------------------------------------------------------------------------

def write_data_to_file(data, outfile, verbose = False):
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
	merged, topic_sents = merge_datasets(posts, sents, topic_dists, numTopics, verbose)

	# top topics
	top_topics = get_top_topics(merged, numTopics, 5, output_path, verbose)

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