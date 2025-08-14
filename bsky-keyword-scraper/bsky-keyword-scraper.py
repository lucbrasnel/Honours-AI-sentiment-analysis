from atproto import Client
import json
from datetime import datetime, timedelta
import numpy as np
import math
import ast
import configparser

# ===================================== Global vars ===========================================
client = Client()

config = configparser.ConfigParser()

# ====================================== func defs ============================================

# log client instance in
def login(username, passw):

  try:
    client.app.bsky.feed.get_suggested_feeds()
    print('session already exists')
    return True
  except:
    print('logging in')
    
  bSuccess = False

  try:
    print('sending login details')
    client.login('lucbrasnel.bsky.social', 'LsneEgpi(0')
  except Exception as e:
    if(e.response.content.error == 'AuthFactorTokenRequired'):
      authCode = input('Get auth code from email: ')
      try:
        client.login(login = username, password = passw, auth_factor_token = authCode)
      except Exception as e:
        print(f"login error: {e}")
      else:
        print('successful login')
        bSuccess = True
    else:
      print(f"login error: {e}")

  return bSuccess

#----------------------------------------------------------------------------------------------

def get_posts_with_earliest(output_file, keyword, since, until, lim = None, verbose = False):
  #set vars
  b_next = True
  remainder = lim
  post_count = 0
  data_out = []

  if lim is not None: # if limit is given
    # Get initial latest posts
    if lim > 100:
      data = client.app.bsky.feed.search_posts({'q' : keyword, 'lang' : 'en', 'since' : since, 'until' : until, 'limit' : 100})
      remainder = lim - len(data.posts)
    else:
      data = client.app.bsky.feed.search_posts({'q' : keyword, 'lang' : 'en', 'since' : since, 'until' : until, 'limit' : lim})
      remainder = 0

  else: # No limit is given
    # Get initial latest posts
    data = client.app.bsky.feed.search_posts({'q' : keyword, 'lang' : 'en', 'since' : since, 'until' : until, 'limit' : 100})
    remainder = None

  # for each post in prev dataset, export relavant data
  posts = data.posts  
  post_count += len(posts)

  for post in posts: 
    post_data = get_post_data(post)
    data_out.append(post_data)
    save_to_file(post_data, output_file) # save data to jsonl file

  if verbose: print(f"Saved init {post_count} posts to file: {output_file}")

  while (b_next and (remainder is None or (isinstance(remainder, (int, float)) and remainder > 0))):
    # get timestamp of earliest
    if len(posts) > 0:
      earliest = posts[-1].record.created_at
    else:
      break

    # if posts still in date range
    if (remainder == None or remainder != 0):
      if(earliest >= since):
        data, remainder = get_more_posts(keyword, since, earliest, remainder) # retrieve next set posts with until = timestamp
      else:
        b_next = False # no more posts to collect within date range
    else:
      b_next = False # remainder = 0
        
    # for each post in prev dataset, export relavant data
    posts = data.posts    

    for post in posts: 
      post_data = get_post_data(post)
      data_out.append(post_data)
      save_to_file(post_data, output_file) # save data to jsonl file
    
    post_count += len(posts) #update post count with next batch
    if verbose: print(f"saved {post_count} posts to file so far. Earliest: {earliest}")
  
  if verbose: print(f"Done: saved total of {post_count} posts to file: {output_file}")
  return data_out

#----------------------------------------------------------------------------------------------

#Get posts containing a keyword and save it to a jsonl file    
def get_posts_with_pages(output_file, keyword, since, until, lim = None, sort = 'latest', verbose = False):
  #set vars
  b_next = True
  remainder = lim
  post_count = 0
  data_out = []

  if lim is not None: # if limit is given
    # Get initial latest posts
    if lim > 100:
      data = client.app.bsky.feed.search_posts({'q' : keyword, 'sort' : sort, 'lang' : 'en', 'since' : since, 'until' : until, 'limit' : 100})
      remainder = lim - len(data.posts)
    else:
      data = client.app.bsky.feed.search_posts({'q' : keyword, 'sort' : sort, 'lang' : 'en', 'since' : since, 'until' : until, 'limit' : lim})
      remainder = 0

  else: # No limit is given
    # Get initial latest posts
    data = client.app.bsky.feed.search_posts({'q' : keyword, 'sort' : sort, 'lang' : 'en', 'since' : since, 'until' : until, 'limit' : 100})
    remainder = None

  # for each post in init dataset, export relavant data
  posts = data.posts  
  post_count += len(posts)

  for post in posts: 
    post_data = get_post_data(post)
    data_out.append(post_data)
    save_to_file(post_data, output_file) # save data to jsonl file

  if verbose: print(f"Saved init {post_count} posts to file: {output_file}")

  # get pagination cursor
  next_page = data.cursor

  while (b_next and (remainder is None or (isinstance(remainder, (int, float)) and remainder > 0))):
    # retrieve next page of posts
    data, remainder = get_more_posts(keyword, since, until, next_page, sort, remainder) 
    
    # if any more posts are retrieved
    if (len(data.posts) > 0):
      next_page = data.cursor # get next page cursor

      # for each post in prev dataset, export relavant data
      posts = data.posts

      for post in posts:
        post_data = get_post_data(post)
        data_out.append(post_data)
        save_to_file(post_data, output_file) # save data to jsonl file
    else:
      b_next = False # no posts left
    
    post_count += len(posts) #update post count with next batch
    if verbose: print(f"saved {post_count} posts to file so far. Cursor: {next_page}")
  
  if verbose: print(f"Done: saved total of {post_count} posts to file: {output_file}")
  return data_out

#----------------------------------------------------------------------------------------------

# for recursive post collection
def get_more_posts(q, since, until, next_page, sort, remainder = None):
  if remainder == None:
    data = client.app.bsky.feed.search_posts({'q' : q, 'sort' : sort, 'lang' : 'en', 'since' : since, 'until' : until, 'limit' : 100, 'cursor' : next_page})
  else:
    if remainder > 100:
      data = client.app.bsky.feed.search_posts({'q' : q, 'sort' : sort, 'lang' : 'en', 'since' : since, 'until' : until, 'limit' : 100, 'cursor' : next_page})
      remainder = remainder - len(data.posts)
    else:
      data = client.app.bsky.feed.search_posts({'q' : q, 'sort' : sort, 'lang' : 'en', 'since' : since, 'until' : until, 'limit' : remainder, 'cursor' : next_page})
      remainder = 0

  return data, remainder

#----------------------------------------------------------------------------------------------

# Get random posts containing a keyword across a date range and save it to a jsonl file
# Gets 100 posts with a random date as until param in request
def get_random_posts(output_file, keyword, since, until, amount = 1000, sort = 'latest', verbose = False):
  #set vars
  post_count = 0
  data_out = []

  if verbose: print(f"Saving random posts to file: {output_file}")

  # need amount to get from date range. Othereise just randomly collecting everything
  if amount == None:
    print('Cannot use random without a limit')
    return None
  
  # calc amount of requests needed to get all posts wanted 
  if amount <= 100:
    req_amount = 1
  else:
    req_amount = math.ceil(amount/100) #amount of requests to be sent

  date_format = "%Y-%m-%dT%H:%M:%SZ"

  since_date = datetime.strptime(since, date_format)
  until_date = datetime.strptime(until, date_format)

  # calc the amount of time that can be skipped between requests
  total_time = (until_date - since_date).total_seconds()  + 1
  print(total_time)
  max_time = math.floor(total_time/req_amount)
  min_time = math.ceil(max_time/2) # do not want too small of a skip between requests
  print(f"max t: {max_time}, min t: {min_time}")

  #set 1st date as until date
  next_date = until_date

  # collect sets of data with random dates that span the date range
  for d in range(req_amount):
    if d == 0: random_time = np.random.randint(0, min_time) #on 1st date add smaller randomness
    else: random_time = np.random.randint(min_time, max_time) # on rest add same randomess

    next_date = next_date - timedelta(seconds = random_time) # add randomess to date
    use_date = next_date.strftime(date_format)

    data = client.app.bsky.feed.search_posts({'q' : keyword, 'sort' : sort, 'lang' : 'en', 'until' : use_date, 'limit' : 100})
    
    if (len(data.posts) > 0):
      # for each post in dataset, export relavant data
      posts = data.posts

      for post in posts:
        post_data = get_post_data(post)
        data_out.append(post_data)
        save_to_file(post_data, output_file) # save data to jsonl file

      post_count += len(posts) #update post count with next batch

      if verbose: print(f"saved {len(posts)} posts from date: {use_date}")

    # get earliest date from prev data and set as next date
    earliest = posts[-1].record.created_at

    next_date = datetime.fromisoformat(earliest)

  
  if verbose: print(f"Done: saved total of {post_count} posts to file: {output_file}")
  return data_out

#----------------------------------------------------------------------------------------------

# export relevant post data from api response
def get_post_data(post):
  txt = post.record.text #text
  createdAt = post.record.created_at #time
  cid = post.cid #cid - hash of post
  uri = post.uri #uri - for verification
  likes = post.like_count #likes
  replies = post.reply_count #replies count
  reposts = post.repost_count #repost count
  tags = post.record.tags #tags
  lang = post.record.langs #language of post

  #extract hashtags
  indexies = [h for h, v in enumerate(txt) if v == '#']
  htags = []

  for y in indexies:
    c = txt[y]
    htag = ''
    n = 0
    bflag = True

    while bflag:
      htag = htag + c

      n = n + 1

      if (y+n <= len(txt)-1):
        c = txt[y+n]
        if (c == ' ' or c == '\n'):
          bflag = False
      else:
        bflag = False

    htags.append(htag)


  # if has attached media that could be ai generated
  ai_content_types = ['app.bsky.embed.images', 'app.bsky.embed.video']

  if (post.record.embed != None):
    if (post.record.embed.py_type == 'app.bsky.embed.recordWithMedia'):
      if(post.record.embed.media.py_type in ai_content_types):
        has_imgvid = True
      else:
        has_imgvid = False

    elif (post.record.embed.py_type in ai_content_types):
      has_imgvid = True

    else:
      has_imgvid = False

  else:
    has_imgvid = False

  x = {
      "text": txt,
      "created_at": createdAt,
      "cid": cid,
      "uri": uri,
      "likes": likes,
      "replies": replies,
      "reposts": reposts,
      "langs" : lang,
      "tags": tags,
      "hastags": htags,
      "has_imgvid": has_imgvid
  }

  return x

#----------------------------------------------------------------------------------------------

# Write data to jsonl file
def save_to_file(data, filename):
  with open(filename, 'a') as f:
      json.dump(data, f)
      f.write('\n')

# ===================================== Main func =============================================

if __name__ == "__main__":
  # config setup:
  config.read('config.ini')

  keywords = ast.literal_eval(config['DEFAULT']['keywords'])
  limit = config['DEFAULT']['limit']
  if limit == 'None':
    limit = None
  else: limit = int(limit)

  verbose = config['DEFAULT'].getboolean('verbose')
  #rndm = config['DEFAULT'].getboolean('randdom')
  sort = config['DEFAULT']['sort']
  output_path = config['DEFAULT']['output_path']

  since = config['DEFAULT']['since_date']
  until = config['DEFAULT']['until_date']

  date_format = "%Y-%m-%dT%H:%M:%SZ"

  since_date = datetime.strptime(since, date_format)
  until_date = datetime.strptime(until, date_format)

  username = config['LOGIN']['username']
  password = config['LOGIN']['password']
  
  blogin = login(username, password)

  if blogin:
    for x in keywords:
      print(f"Extracting posts about {x} from {since} till {until}")
      output_file = f"{output_path}/{x}_{sort}_{since_date.strftime('%d%b%Y')}_{until_date.strftime('%d%b%Y')}_posts.jsonl"

      data = get_posts_with_earliest(output_file, x, since, until, limit, sort, verbose)
      #data = get_posts_with_pages(output_file, x, since, until, limit, sort, verbose) #if not(rndom):  #Not working for large collections
      #else: data = get_random_posts(output_file, x, since, until, limit, sort, verbose) #not finished
      print(f"successfully extracted {output_file}\n")
  else:
    print('Couldnt login')

# ===================================== end of program ========================================