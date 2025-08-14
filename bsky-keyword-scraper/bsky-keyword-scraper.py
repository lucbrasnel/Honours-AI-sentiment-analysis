from atproto import Client
import json
from datetime import datetime
import ast
import configparser

# ===================================== Global vars ===========================================
client = Client()

config = configparser.ConfigParser()

# ====================================== func defs ============================================

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
      
def get_posts_with(output_file, keyword, since, until, lim = None, sort = 'latest', verbose = False):
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

      print(f"saved {len(posts)} posts to file")
    else:
      b_next = False # no posts left
    
    post_count += len(posts) #update post count with next batch
    if verbose: print(f"saved {post_count} posts to file so far. Cursor: {next_page}")
  
  if verbose: print(f"Done: saved total of {post_count} posts to file: {output_file}")
  return data_out


def get_more_posts(q, since, until, next_page, sort, remainder = None):
  #for recursive post collection
  if remainder == None:
    data = client.app.bsky.feed.search_posts({'q' : q, 'lang' : 'en', 'since' : since, 'until' : until, 'limit' : 100})
  else:
    if remainder > 100:
      data = client.app.bsky.feed.search_posts({'q' : q, 'lang' : 'en', 'since' : since, 'until' : until, 'limit' : 100})
      remainder = remainder - len(data.posts)
    else:
      data = client.app.bsky.feed.search_posts({'q' : q, 'lang' : 'en', 'since' : since, 'until' : until, 'limit' : remainder})
      remainder = 0

  return data, remainder

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
      output_file = f"{output_path}/{x}_{since_date.strftime('%d%b%Y')}_{until_date.strftime('%d%b%Y')}_posts.jsonl"

      data = get_posts_with(output_file, x, since, until, limit, sort, verbose)
      print(f"successfully extracted {output_file}\n")
  else:
    print('Couldnt login')

# ===================================== end of program ========================================