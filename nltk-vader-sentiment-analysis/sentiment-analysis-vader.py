from nltk.classify import NaiveBayesClassifier
from nltk.corpus import subjectivity
from nltk.sentiment import SentimentAnalyzer
from nltk.sentiment.util import *
import configparser
import vaderSentiment

# ===================================== Global vars ===========================================

config = configparser.ConfigParser()

# ====================================== func defs ============================================

#----------------------------------------------------------------------------------------------

# ===================================== Main func =============================================

if __name__ == "__main__":
    # config setup:
    config.read("config.ini")

# ===================================== end of program ========================================