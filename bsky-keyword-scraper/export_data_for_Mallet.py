import json
import re

# extracts text from jsonl file to text file, which can be converted for Mallet analysis by mallect command

def write_to_file(data, outfile, verbose):
    #get data from json obj
    text = data['text']
    uri = data['uri']
    topic = data['Topic']

    # replace \n chars in text
    text = re.sub('\r?\n', ' ', text)

    #reformat to mallet tab-delimited format: [ID] [tag] [text]
    out = f"{uri}\t{topic}\t{text}"

    #write line to file
    with open(outfile, 'a', encoding='utf-8') as f:
        f.write(out)
        f.write('\n')

    if verbose: print(f"wrote uri:{uri} on {topic}")

def get_posts_data(infile, outfile, verbose = False):
    # open file
    with open(infile, 'r', encoding='utf-8') as f:
      # for every line, extract json
      count = 1
      for line in f:
        if verbose: print(f"reading line:{count}")
        #lstr = line
        ljson = json.loads(line)

        write_to_file(ljson, outfile, verbose)
        count += 1

if __name__ == "__main__":
    infile = "Scraper_Out/Hons-bsky-Posts-cleaning.jsonl"
    outfile = "Scraper_Out/bsky_posts_text.txt"

    verbose = True

    get_posts_data(infile, outfile, verbose)