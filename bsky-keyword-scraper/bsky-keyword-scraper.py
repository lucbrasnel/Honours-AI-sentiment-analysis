from atproto import Client
import json
from datetime import datetime, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta
import numpy as np
import math
import time
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

def get_posts_with_earliest(output_file, keyword, since, until, lim = None, sort= 'latest', verbose = False):
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
        data, remainder = get_more_posts(keyword, since, earliest, sort, None, remainder) # retrieve next set posts with until = timestamp
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
def get_more_posts(q, since, until, sort, next_page = None, remainder = None):
  params = {
    'q' : q, 
    'sort' : sort, 
    'lang' : 'en', 
    'since' : since, 
    'until' : until
  }

  if next_page != None:
    params['cursor'] = next_page

  if remainder == None:
    params['limit'] = 100
    data = client.app.bsky.feed.search_posts(params)
  else:
    if remainder > 100:
      params['limit'] = 100
      data = client.app.bsky.feed.search_posts(params)
      remainder = remainder - len(data.posts)
    else:
      params['limit'] = remainder
      data = client.app.bsky.feed.search_posts(params)
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
    req_amount = math.ceil((amount*1.1)/100) #amount of requests to be sent

  date_format = "%Y-%m-%dT%H:%M:%SZ"

  since_date = datetime.strptime(since, date_format)
  until_date = datetime.strptime(until, date_format)

  # calc the amount of time that can be skipped between requests
  total_time = (until_date - since_date).total_seconds()  + 1
  print(total_time)
  max_time = math.floor(total_time/req_amount)
  min_time = math.ceil(max_time*0.75) # do not want too small of a skip between requests
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

# Get random posts containing a keyword across a date range by gathering over the months 
# and save it to a jsonl file
def get_posts_p_month(output_file, keyword, since, until, amount = 1000, sort = 'latest', verbose = False):
  #set vars
  post_count = 0
  data_out = []
  loss = 0

  if verbose: print(f"Saving posts per month to file: {output_file}")

  # need amount to get from date range. Othereise just randomly collecting everything
  if amount == None:
    print('Cannot use random without a limit')
    return None
  
  # calc how many months and which months
  date_format = "%Y-%m-%dT%H:%M:%SZ"

  since_date = datetime.strptime(since, date_format)
  until_date = datetime.strptime(until, date_format)

  month_diff = (until_date.year - since_date.year) * 12 + (until_date.month - since_date.month)

  # calc amount of posts needed per month
  posts_p_month = amount/month_diff

  next_month = datetime(year = until_date.year, month = until_date.month, day = monthrange(year = until_date.year, month = until_date.month)[1])

  if verbose: print(f"Month Diff: {month_diff}, Posts/Month: {posts_p_month}")

  # collect sets of data across each month
  for m in range(month_diff):
    # get which month
    month_num = next_month.month
    month_y = next_month.year

    # calc amount of days in month
    num_days = monthrange(month_y, month_num)[1]

    if verbose: print(f"\nMonth: {next_month.strftime("%Y %b")}, Num days: {num_days}")

    if m == 0: # for 1st month use until date to stay within range given
      since_lim = datetime(year = next_month.year, month = next_month.month, day = 1, hour = 0, minute = 0, second = 0)
      until_lim = until_date
    elif m == month_diff: # for last month use since date to stay within range given
      since_lim = since_date
      until_lim = datetime(year = next_month.year, month = next_month.month, day = num_days, hour = 23, minute = 59, second = 59)
    else:
      since_lim = datetime(year = next_month.year, month = next_month.month, day = 1, hour = 0, minute = 0, second = 0)
      until_lim = datetime(year = next_month.year, month = next_month.month, day = num_days, hour = 23, minute = 59, second = 59)

    since_lim_str = datetime.strftime(since_lim, date_format)
    until_lim_str = datetime.strftime(until_lim, date_format)

    # calc amount of requests needed per day / amount of posts per req
    # do test req (w/ 100 and limiters) to calc how many posts in month
    test_data = client.app.bsky.feed.search_posts({'q' : keyword, 'sort' : sort, 'lang' : 'en', 'since' : since_lim_str, 'until' : until_lim_str, 'limit' : 100})

    test_posts = test_data.posts
    num_posts = len(test_posts)

    if num_posts != 0: # if any posts to be collected in month      

      if (num_posts < 100) and (posts_p_month < 100): # if test returned less than 100, there are less than 100 posts in month, and if need less than 100, do not need to do another req
        if num_posts == posts_p_month:
          # got exactly how many posts as needed YAY :D
          if verbose: print(f"Perfect amount of posts for {next_month.strftime("%Y %b")} YAY")

          posts = test_posts
        else:
          # got less than what was needed
          if verbose: print(f"Not enough posts for {next_month.strftime("%Y %b")}")
          
          posts = test_posts # Take what u can get

      else: # 100 or more posts in month to collect || OR || want more than 100 posts per month
        posts_p_day = math.ceil(posts_p_month/num_days)

        if verbose: print(f"More than 100 posts for {next_month.strftime("%Y %b")}, Post/Day: {posts_p_day}")

        # get posts w/ limiters for each day
        for d in range(num_days):
          since_day = datetime(year = since_lim.year, month = since_lim.month, day = d+1, hour = 0, minute = 0, second = 0)
          until_day = datetime(year = until_lim.year, month = until_lim.month, day = d+1, hour = 23, minute = 59, second = 59)

          since_day_str = datetime.strftime(since_day, date_format)
          until_day_str = datetime.strftime(until_day, date_format)

          # collect all posts for the day
          posts_col = [] # to hold all posts of day
          bflag = True
          earliest_time = -1 # to hold last post request's time
          earliest_uri = '' # to compare if last post of day
          total_col = 0 # count of posts in posts_col

          # ================== TO DO ========================
          # do not rely on 100 posts to be returned if more than 100 available
          # WHY only save 6 posts?????

          while bflag:
            if earliest_time == -1: # 1st request
              test_data = client.app.bsky.feed.search_posts({'q' : keyword, 'sort' : sort, 'lang' : 'en', 'since' : since_day_str, 'until' : until_day_str, 'limit' : 100})
              test_posts = test_data.posts

              total_col = len(test_posts) # add to total

              if len(test_posts) == 0: # no posts in day, go to next
                bflag = False
              elif len(test_posts) < 90: # less than 100 posts in the day
                for p in test_posts: # save collected posts
                  posts_col.append(p)

                bflag = False
              else: # collected 100, musts test if last
                earliest_time = test_posts[-1].record.created_at
                earliest_uri = test_posts[-1].uri

              #if verbose: print(f"1st pass for {next_month.strftime("%Y %b")} {d+1}, Posts collected: {len(test_posts)}, Earliest: {earliest_time}, {earliest_uri}")

            else: # subsequent requests
              test_data = client.app.bsky.feed.search_posts({'q' : keyword, 'sort' : sort, 'lang' : 'en', 'since' : since_day_str, 'until' : earliest_time, 'limit' : 100})
              test_posts = test_data.posts

              if len(test_posts) > 0: # retrieved any more posts after last one
                total_col = total_col + len(test_posts) # add to total

                test_uri = test_posts[-1].uri

                if test_uri == earliest_uri: # the earliest post of prev is still last, no more in the day
                  bflag = False
                else: # collected more, musts test if last
                  for p in test_posts: # save collected posts
                    posts_col.append(p) 

                  earliest_time = test_posts[-1].record.created_at # must test again
                  earliest_uri = test_posts[-1].uri
              else: # no more posts after prev last
                bflag = False

              #if verbose: print(f"another pass for {next_month.strftime("%Y %b")} {d+1}, Posts collected: {len(test_posts)}, Total: {len(posts_col)}, Earliest: {earliest_time}, {earliest_uri}")

              time.sleep(5) # wait to avoid timeout and rate limits
                
          if verbose: print(f"Collected {len(posts_col)} posts for {next_month.strftime("%Y %b")} {d+1}")

          # Save random selection of posts for num wanted
          if total_col >= posts_p_day: # can randomly sample from larger population
            posts = np.random.choice(posts_col, posts_p_day, replace = False)
          else: # not enough in pop, take what can get
            posts = posts_col

          # adjust posts/req based on prev losses
          # calc total loss at end
          loss = loss + (posts_p_day - len(posts))

          month_file = output_file[:-6] + next_month.strftime("_%b_%y") + output_file[-6:]

          # save posts for month
          for post in posts:
            post_data = get_post_data(post)
            data_out.append(post_data)
            save_to_file(post_data, month_file) # save data to jsonl file

          if verbose: print(f"\n Saved {len(posts)} posts for: {next_month.strftime("%Y %b")} {d+1}, loss: {loss}")

          post_count = post_count + len(posts)
        
    else:
      # no posts in month
      if verbose: print(f"No posts for {next_month.strftime("%Y %b")}") 

      loss = loss + posts_p_month

    # set next month
    next_month = next_month + relativedelta(months = 1)

    time.sleep(30) # wait to avoid timeout and rate limits


  if verbose: print(f"Done: saved total of {post_count} posts to files with loss of: {loss}")
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

  rndm = config['DEFAULT']['random']

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
      output_file = f"{output_path}/{x}_{sort}_{rndm}_{since_date.strftime('%d%b%Y')}_{until_date.strftime('%d%b%Y')}_posts.jsonl"
       
      if rndm == 'none':  
        # data = get_posts_with_pages(output_file, x, since, until, limit, sort, verbose) #Not working for large collections
        data = get_posts_with_earliest(output_file, x, since, until, limit, sort, verbose)
      elif rndm == 'random': 
        #data = get_random_posts(output_file, x, since, until, limit, sort, verbose) #not finished
        print('Random collection is not finished')
      elif rndm == 'month':
        data = get_posts_p_month(output_file, x, since, until, limit, sort, verbose)
        
      print(f"successfully extracted {output_file}\n")
      
  else:
    print('Couldnt login')

# ===================================== end of program ========================================