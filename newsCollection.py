import nltk, nltk.data, pickle, re
import email as emailProcessor
import time, imaplib
from dateutil import parser
import datetime
import numpy as np
#import ner
import bsddb, string
from nltk.stem import WordNetLemmatizer
from sklearn import decomposition
import matplotlib.pyplot as plt
import subprocess, sys, random
from unidecode import unidecode
from topia.termextract import extract
from calais import Calais

"""toGephi takes as input an adjacency matrix (graph), a list of node names (wordList) in the same order as the
input graph, and a file name (fName). It creates a file that contains the input graph in a format that can be read by
Gephi"""

def toGephi(graph, wordList, fName):
    def fix(word):
        temp = word.split()
        temp = [word[0].upper()+word[1:] for word in temp]
        return "".join(temp)
    wordList = [fix(word) for word in wordList]
    #print "first", wordList[0], "last", wordList[-1]
    gephiString = reduce(lambda d, x: d+";"+x, wordList, "")
    #print gephiString
    for i in xrange(0, len(wordList)):
        gephiString += "\n"+wordList[i]+reduce(lambda d, x: d+";"+str(x), graph[i,:].T.tolist(), "")
    #print gephiString
    open(fName, "w").write(gephiString)

print "testing gephi translator"
graph = np.zeros((5, 5))
for i in xrange(0, 5):
 for j in xrange(0, 5):
     graph[i,j] = i-j
words = [str(i) for i in xrange(1, 6)]
print graph
print words
toGephi(graph, words, "test.txt")

"""ArticleReader deals with maintaining an up-to-date database of news articles (which are sourced from rss feeds
and aggregated in the email account newsprojectvidur@gmail.com which has the password newsanalytics) and creating the database
of processed articles, and the co-occurrence graph.
Example:
To update the article database we would run,
articleReader = ArticleReader()
articleReader.updateArticleDB()"""

class ArticleReader():
    def __init__(self):
        """A set containing all the email uids already present in the database of news articles"""
        self.inStoredDumpsDB = pickle.load(open("inStoredDumpsDB", "rb"))
        """A set containing all the news article urls previously visited"""
        self.visitedURLS = pickle.load(open("visitedURLS", "rb"))
        """A set containing all the email uids already present in the database of PROCESSED news articles"""
        self.inProcessedArticlesDB = set()#pickle.load(open('inProcessedArticlesDB', "rb"))

    """"prepareEmailConnections is run through updateArticleDB and it sets up the connection to gmail so that the article
    links can be recovered from the emails from the rss aggregator blogtrottr"""
    def _prepareEmailConnections(self):
        from goose import Goose
        self.goose = Goose()#{'browser_user_agent': 'Mozilla'})
        self.mail = imaplib.IMAP4_SSL('imap.gmail.com')
        self.mail.login('newsprojectvidur@gmail.com', 'newsanalytics')
        self.mail.list()
        self.mail.select("reuters")
        self.linkPattern = re.compile(r"(http://.+?\.html|http://.+?\.htm|http://.+?\.aspx|http://.+?-sa|http://.+?\.cms)", re.DOTALL)
        self.htmlFix = re.compile(r"(http://.+?2Ehtml|http://.+?2Ehtm|http://.+?2Easpx|http://.+?2Ecms)", re.DOTALL)
        self.table = string.maketrans("","")

    """updateArticleDB is called to download all articles that have been emailed but have not yet been put into the database"""
    def updateArticleDB(self):
        """Preparing Connections"""
        self._prepareEmailConnections()
        self.unreadable = ""
        """Creating Update to DB"""
        result, data = self.mail.uid('search', None, "ALL")
        emailUIDStoVisit = sorted(set(data[0].split()).difference(self.inStoredDumpsDB), key = lambda x: int(x))
        result, data = self.mail.uid('fetch', reduce(lambda stringa, uid: stringa+","+uid, emailUIDStoVisit), '(RFC822)')
        emails = filter(lambda x: type(x) is tuple, data)
        """Making sure that google's response assigns uids the way I assume they are assigned"""
        test = [x[0].split()[2] for x in emails[:20]]
        assert test==emailUIDStoVisit[:20], "%r %r" %(test, emailUIDStoVisit[:20])
        todo = [(emailUIDStoVisit[i], emails[i][1]) for i in xrange(0, len(emailUIDStoVisit))]
        random.shuffle(todo)
        print "unread emails: ",len(emailUIDStoVisit)
        toDatabase = map(self._storeEmailedArticle, zip(range(len(emailUIDStoVisit), 0, -1), todo))
        """Adding it to the DB"""
        self._addToDB(toDatabase, "articleDumps.db")
        """Updating Log Files"""
        self._updateSets()
        open("unreadableURLS", "a").write(self.unreadable)

    """The databases are written to in a single step so as to prevent them from being corrupted. This is done through
    _addToDB which takes a dictionary (addToDB) and adds its contents to the berkley db OVERWRITING ANY OVERLAPS!"""

    def _addToDB(self, addToDB, dbName):
        db = bsddb.btopen(dbName, 'c')
        for key, value in addToDB:
            if key!=None:
                db[key] = value
        db.sync()
        db.close()
        print "successfuly updated ", dbName
    def _extractLink(self, text):
        lines = text.replace("=\r\n", "").split("\r\n")
        date = filter(lambda phrase: phrase[:6]=="Date: ", lines)
        if len(date)==1:
            date = parser.parse(date[0][6:])
        else:
            print "date trouble!", text
            date = datetime.datetime.now()
        links = filter(lambda phrase: phrase[:4]=="http", lines)
        return links, date
    def _cleanLink(self, link):
        newLink = ""
        wait = 0
        for i in xrange(0, len(link)):
            if wait>0:
                wait -= 1
                continue
            if link[i]=="%" or link[i]=="=" and i<len(link)-2:
                try:
                    newLink+=link[i+1:i+3].decode("hex")
                    wait = 2
                except:
                    newLink+=link[i]
            else:
                newLink+=link[i]
        return newLink
    def _logLink(self, link):
        self.unreadable += "\n"+link
    def _storeEmailedArticle(self, curPosEmailStr):
        curPos, uidEmailStr = curPosEmailStr
        uid, emailStr = uidEmailStr
        print "remaining: ", curPos
        self.inStoredDumpsDB.add(uid)
        links, date = self.extractLink(emailStr)
        if len(links)<2:
            print "Not a news article", links
            return (None, None)
        link = links[0]
        if "news.google.com" in link:
            link = re.findall("http.*", link[4:])
            assert len(link)==1
            link = link[0]
        if "=" in link or "%" in link:
            link = self._cleanLink(link)
        if link in self.visitedURLS:
            print "already seen ", link
            return (None, None)
        self.visitedURLS.add(link)
        try:
            extract = self.goose.extract(url=link)
        except:
            print "Goose extractor crashed on page ", link
            print "Unexpected error:", sys.exc_info()[0]
            self._logLink(link)
            return (None, None)
        time.sleep(random.randint(1, 6))
        text = extract.cleaned_text
        if text=="" or text==None:
            print "failed to parse url ", link
            self._logLink(link)
        title = extract.title
        value = pickle.dumps((text, link, date, title))
        return (uid, value)
    """Called to process all the articles in the database of downloaded articles that have not yet been processed i.e.
    do not have their uids in self.inProcessedArticlesDB"""

    def updateProcessedDb(self):
        API_KEY = "vwk375uecnazrcrpu8n4y3yf"
        self.calaisObj = Calais(API_KEY, submitter="python-calais demo")
        self.articleDumps = bsddb.btopen('articleDumps.db', 'r')
        self.processedArticles = bsddb.btopen("openCalis.db", 'c')
        toDo = set(self.articleDumps.keys()).difference(self.inProcessedArticlesDB)
        data = reduce(lambda data, curPosUid: self._termExtractor(curPosUid, data), zip(range(len(toDo), 0, -1), toDo), {})
        toDatabase = [(key, pickle.dumps(value)) for key, value in data.iteritems()]
        self._addToDB(toDatabase, "openCalis.db")
        self._updateSets()

    """Uses open Calis on the text of the news articles to recover tagged entities"""

    def _openCalis(self, text):
        def clean(entity):
            del entity['_typeReference']
            del entity['instances']
            return entity
        response = False
        while not response:
            try:
                response = self.calaisObj.analyze(text)
            except ValueError:
                print "Calais Server Busy"
                time.sleep(120)
                response = False
        if response:
            try:
                return map(clean, response.entities)
            except:
                print "calis failed!"
                print text
                return None
        else:
            return None
    """Processed the given uid and adds the result to a dictionary which the processed articles
    database is then updated with"""

    def _termExtractor(self, curPosUid, data):
        curPos, uid = curPosUid
        print "remaining: ", curPos
        self.inProcessedArticlesDB.add(uid)
        try:
            text, link, date, title = pickle.loads(self.articleDumps[uid])
        except ValueError:
            text, link, date = pickle.loads(self.articleDumps[uid])
        text = unidecode(text)#.encode("ascii", errors = "ignore")
        entities = self._openCalis(text)#self.returnEntities(text)
        if entities:
            print map(lambda e: e['name'], entities)
            key = pickle.dumps(date)
            if key in data:
                value = data[key]
                value.append(entities)
                data[key] = value
            elif self.processedArticles.has_key(key):
                value = pickle.loads(self.processedArticles[key])
                value.append(entities)
                data[key] = value
            else:
                data[key] = [entities]
        return data
    """Creates the adjacency matrix (or co-occurence graph) of the entities occuring in the news articles"""
    def createGraph(self):
        self.processedArticles = bsddb.btopen("openCalis.db", 'r')
        wordCounts = self._countWords()
        articlesN = len(self.processedArticles)#len(self.processedArticles.keys())
        print "Number of times being considered = ", articlesN
        indexToWord = [word for word, count in wordCounts.iteritems() if len(word.strip())>2 and count>50 and count<articlesN/50]
        allowed = set(indexToWord)
        print "Number of words being considered for the graph = ", len(indexToWord)
        wordIndices = dict(zip(indexToWord, xrange(0, len(indexToWord))))
        graph = np.zeros((len(indexToWord), len(indexToWord)))
        for value in self.processedArticles.itervalues():
            listOfLists = pickle.loads(value)
            for aList in listOfLists:
                for i in xrange(0, len(aList)):
                    for j in xrange(i+1, len(aList)):
                        if aList[i] in allowed and aList[j] in allowed:
                            graph[wordIndices[aList[i]], wordIndices[aList[j]]]+= 1.0#/(wordCounts[aList[i]]+wordCounts[aList[j]])
        graph = graph + graph.T
        #graph = graph/[[wordCounts[indexToWord[i]]] for i in xrange(0, len(indexToWord))]
        np.save("graph.data", graph)
        pickle.dump(indexToWord, open("words.data","wb"))
        toGephi(graph, indexToWord, "graph.csv")
#         t = 0.6
#         L = laplacian(graph)
#         heatFlow = expm(-1*float(t)*L)
#         np.save("heatFlowGraph", heatFlow)
    def _countWords(self):
        wordCounts = {}
        for value in self.processedArticles.itervalues():
            listOfLists = pickle.loads(value)
            for aList in listOfLists:
                for entity in aList:
                    key = (entity['name'], entity['_type'])
                    wordCounts[key] = wordCounts.get(key, 0)+1
        return wordCounts
    """Updates the sets keeping track of which emails, articles and links have already been processed"""
    def _updateSets(self):
        FinProcessedArticlesDB = open("inProcessedArticlesDB", "wb")
        pickle.dump(self.inProcessedArticlesDB, FinProcessedArticlesDB)
        FinProcessedArticlesDB.close()
        FinStoredDumpsDB = open("inStoredDumpsDB", "wb")
        pickle.dump(self.inStoredDumpsDB, FinStoredDumpsDB)
        FinStoredDumpsDB.close()
        FvisitedURLS = open("visitedURLS","wb")
        pickle.dump(self.visitedURLS, FvisitedURLS)
        FvisitedURLS.close()
        try:
            self.articleDumps.close()
        except:
            pass
        try:
            self.processedArticles.close()
        except:
            pass
        print "successfully closed"

articleReader = ArticleReader()
articleReader.updateArticleDB()

