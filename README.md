# Honours-AI-sentiment-analysis
Repository for Honours project 2025

## Context
This study aims to analyse the public perceptions of Artificial Intelligence and the technologies that utilize or facilitate it through opinions expressed in social media posts. Specifically, this will be done through topic modelling and sentiment analysis, which will quantize the opinions gathered, allowing for statisical analysis techniques to be applied.

## Tools
The following tools are used through the programs contained in this repository:
- [The BlueSky API](https://atproto.blue/en/latest/)
- [MALLET Topic Modeling](https://mimno.github.io/Mallet/)
	- [MALLET python wrapper](http://github.com/maria-antoniak/little-mallet-wrapper/tree/master)
- [VADER sentiment analysis](https://github.com/cjhutto/vaderSentiment)
	- [through NLTK](https://www.nltk.org/api/nltk.sentiment.vader.html)
- Statistical Analysis (TBD)

## Config And Data files
Example config files are included, but must be named config.ini for programs to utilize them.

Data files are produced by each program, but must be supplied in this order:
- bsky_keyword_scraper:
	- .jsonl

MALLET
- Clean data, but retain jsonl format
- Put jsonl through MALLET exporter:
	- .txt
- Put txt file in project folder:
	- training data .txt
	- diagnostics file
	- model file
	- topic distributions file
	- topic keys file
	- .training file
	- word weights file

VADER Sentiment Analysis
- Clean data, but retain jsonl format
- Put jsonl file in project folder:
	- .jsonl