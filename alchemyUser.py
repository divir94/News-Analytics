import nltk, nltk.data, pickle, re
import email as emailProcessor
import time, imaplib
from dateutil import parser
import datetime
import numpy as np
import ner
import bsddb, string
from nltk.stem import WordNetLemmatizer
from sklearn import decomposition
import matplotlib.pyplot as plt
import subprocess, sys, random
from unidecode import unidecode
from topia.termextract import extract

def gen(x):
    while True: yield x

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


class ArticleReader():
    def __init__(self):
        self.inStoredDumpsDB = pickle.load(open("inStoredDumpsDB", "rb"))
        self.visitedURLS = pickle.load(open("visitedURLS", "rb"))
        self.inProcessedArticlesDB = pickle.load(open('inProcessedArticlesDB', "rb"))
    def backup(self):
        subprocess.call("cp articleDumps.db .\backups\articleDumps.backup")#+str(datetime.datetime.now()))
        subprocess.call("cp processedArticles.db .\backups\processedArticles.backup")
        subprocess.call("cp inProcessedArticlesDB .\backups\inProcessedArticlesDB.backup")
        subprocess.call("cp inStoredDumpsDB .\backups\inStoredDumpsDB.backup")
        subprocess.call("cp visitedURLS .\backups\visitedURLS.backup")
    def prepareEmailConnections(self):
        from goose import Goose
        self.goose = Goose()#{'browser_user_agent': 'Mozilla'})
        self.mail = imaplib.IMAP4_SSL('imap.gmail.com')
        self.mail.login('newsprojectvidur@gmail.com', 'newsanalytics')
        self.mail.list()
        self.mail.select("reuters")
        self.linkPattern = re.compile(r"(http://.+?\.html|http://.+?\.htm|http://.+?\.aspx|http://.+?-sa|http://.+?\.cms)", re.DOTALL)
        self.htmlFix = re.compile(r"(http://.+?2Ehtml|http://.+?2Ehtm|http://.+?2Easpx|http://.+?2Ecms)", re.DOTALL)
        self.table = string.maketrans("","")
    def createNERServer(self):
        self.lemmatizer = WordNetLemmatizer()
        self.extractor = extract.TermExtractor()
        self.extractor.filter = extract.permissiveFilter
        self._digits = re.compile('\d')
        self.punctuationRemoval = re.compile('[%s]' % re.escape(string.punctuation))
        self.sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
        self.table = string.maketrans("","")
#         self.server = subprocess.call("java -mx1000m -cp NERServer/stanford-ner.jar edu.stanford.nlp.ie.NERServer -loadClassifier NERServer/classifiers/english.muc.7class.distsim.crf.ser.gz -port 8080 -outputFormat inlineXML &", shell=True)
#         time.sleep(1)
#         self.tagger = ner.SocketNER(host='localhost', port=8080)
    def updateArticleDB(self):
        """Preparing Connections"""
        self.prepareEmailConnections()
        self.unreadable = ""
        """Creating Update to DB"""
        result, data = self.mail.uid('search', None, "ALL")
        #print len(self.inStoredDumpsDB), len(self.articleDumps.keys())
        emailUIDStoVisit = sorted(set(data[0].split()).difference(self.inStoredDumpsDB), key = lambda x: int(x))
        #random.shuffle(emailUIDStoVisit)
        #emailUIDStoVisit = emailUIDStoVisit[:500]
        result, data = self.mail.uid('fetch', reduce(lambda stringa, uid: stringa+","+uid, emailUIDStoVisit), '(RFC822)')
        emails = filter(lambda x: type(x) is tuple, data)
        """Making sure that google's response assigns uids the way I assume they are assigned"""
        test = [x[0].split()[2] for x in emails[:20]]
        assert test==emailUIDStoVisit[:20], "%r %r" %(test, emailUIDStoVisit[:20])
        todo = [(emailUIDStoVisit[i], emails[i][1]) for i in xrange(0, len(emailUIDStoVisit))]
        random.shuffle(todo)
        print "unread emails: ",len(emailUIDStoVisit)
        toDatabase = map(self.storeEmailedArticle, zip(range(len(emailUIDStoVisit), 0, -1), todo))
        """Adding it to the DB"""
        self.addToDB(toDatabase, "articleDumps.db")
        """Updating Log Files"""
        self.updateSets()
        open("unreadableURLS", "a").write(self.unreadable)
    def removeDeletedEmails(self):
        self.prepareEmailConnections()
        result, data = self.mail.uid('search', None, "ALL")
        deletedEmailUids = self.inStoredDumpsDB.difference(set(data[0].split()))
        self.inStoredDumpsDB = self.inStoredDumpsDB.difference(deletedEmailUids)
        self.updateSets()
        print len(deletedEmailUids)
        db = bsddb.btopen("articleDumps.db", 'c')
        for uid in deletedEmailUids:
            del db[uid]
        db.sync()
        db.close()
    def addToDB(self, addToDB, dbName):
        db = bsddb.btopen(dbName, 'c')
        for key, value in addToDB:
            if key!=None:
                db[key] = value
        db.sync()
        db.close()
        print "successfuly updated ", dbName
    def extractLink(self, text):
        lines = text.replace("=\r\n", "").split("\r\n")
        date = filter(lambda phrase: phrase[:6]=="Date: ", lines)
        if len(date)==1:
            date = parser.parse(date[0][6:])
        else:
            print "date trouble!", text
            date = datetime.datetime.now()
        links = filter(lambda phrase: phrase[:4]=="http", lines)
        return links, date
    def cleanLink(self, link):
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
    def logLink(self, link):
        self.unreadable += "\n"+link
    def storeEmailedArticle(self, curPosEmailStr):
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
            link = self.cleanLink(link)
        if link in self.visitedURLS:
            print "already seen ", link
            return (None, None)
        self.visitedURLS.add(link)
        try:
            extract = self.goose.extract(url=link)
        except:
            print "Goose extractor crashed on page ", link
            print "Unexpected error:", sys.exc_info()[0]
            self.logLink(link)
            return (None, None)
        time.sleep(random.randint(1, 6))
        text = extract.cleaned_text
        if text=="" or text==None:
            print "failed to parse url ", link
            self.logLink(link)
        title = extract.title
        value = pickle.dumps((text, link, date, title))
        return (uid, value)
    def updateProcessedDb(self):
        self.createNERServer()
        self.articleDumps = bsddb.btopen('articleDumps.db', 'r')
        self.processedArticles = bsddb.btopen("processedArticles.db", 'r')
        toDo = set(self.articleDumps.keys()).difference(self.inProcessedArticlesDB)
        data = reduce(lambda data, curPosUid: self.termExtractor(curPosUid, data), zip(range(len(toDo), 0, -1), toDo), {})
        toDatabase = [(key, pickle.dumps(value)) for key, value in data.iteritems()]
        self.addToDB(toDatabase, "processedArticles.db")
        self.updateSets()
        #subprocess.call("killall java &", shell=True)
    def stem(self, phrase):
        stemmed = reduce(lambda phrase, word: phrase+" "+self.lemmatizer.lemmatize(word), phrase.split(), "")[1:]
        #if stemmed!=phrase:
        #    print stemmed, phrase
        return stemmed
    def termExtractor(self, curPosUid, data):
        curPos, uid = curPosUid
        print "remaining: ", curPos
        self.inProcessedArticlesDB.add(uid)
        text, link, date, title = pickle.loads(self.articleDumps[uid])
        text = unidecode(text)#.encode("ascii", errors = "ignore")
        sentences = self.sent_detector.tokenize(text)
        entities = map(lambda sentence: map(lambda phraseP: self.punctuationRemoval.sub('', self.stem(phraseP[0]).lower()) if not bool(self._digits.search(phraseP[0])) else None, self.extractor(sentence)), sentences)
        entities = reduce(lambda total, addition: total.union(addition), entities, set())
        entities = set(filter(lambda x: x!=None and len(x)>1, entities))
#         try:
#             entities.remove(None)
#         except KeyError:
#             pass
        entities = tuple(entities)
        key = pickle.dumps(date)
        if len(entities)>1:
            print entities, link[:30]
            if key in data:
                value = data[key]
                value.add(entities)
                data[key] = value
            elif self.processedArticles.has_key(key):
                value = pickle.loads(self.processedArticles[key])
                value.add(entities)
                data[key] = value
            else:
                data[key] = set([entities])
        return data
    def stanfordNET(self, curPosUid):
        curPos, uid = curPosUid
        print "remaining: ", curPos
        try:
            text, link, date = pickle.loads(self.articleDumps[uid])
        except EOFError:
            print "failed to unpickle"
            return (None, None)
        allowed = set(['LOCATION', 'PERSON', 'ORGANIZATION'])
        entities = reduce(lambda tupleOfEntities, keyValuePair: tupleOfEntities+zip(keyValuePair[1], gen(keyValuePair[0])) if keyValuePair[0] in allowed else tupleOfEntities, self.tagger.get_entities(text).iteritems(), [])
        entities = tuple(set(entities))
        unpickledPrevValue = pickle.loads(self.processedArticles.get(pickle.dumps(date), pickle.dumps(set())))
        unpickledPrevValue.add(entities)
        self.inProcessedArticlesDB.add(uid)
        key = pickle.dumps(date)
        value = pickle.dumps(unpickledPrevValue)
        return (key, value)
    def readEmail(self, email_message_instance):
        maintype = email_message_instance.get_content_maintype()
        if maintype == 'multipart':
            for part in email_message_instance.get_payload():
                if part.get_content_maintype() == 'text':
                    return part.get_payload()
        elif maintype == 'text':
            return email_message_instance.get_payload()
#     def createArticleGraph(self):
#         self.processedArticles = bsddb.btopen("processedArticles.db", 'r')
#         allArticles = []
#         for key, value in self.processedArticles.iteritems():
#             listOfLists = list(pickle.loads(value))
#             for i in xrange(0, len(listOfLists)):
#                 for j in xrange(0, len(listOfLists[i])):
#                     allArticles.append((key, i, j))
#         graph = np.zeros((len(allArticles), len(allArticles)))
#         for i in xrange(0, len(allArticles)):
#             key1, i1, j1 = allArticles[i]
#             wordBag1 = list(pickle.loads(self.processedArticles[key1]))[i1][j1]
#             for j in xrange(i+1, len(allArticles)):
#                 key2, i2, j2 = allArticles[j]
#                 wordBag2 = list(pickle.loads(self.processedArticles[key2]))[i2][j2]
#                 if wordBag1!=set() and wordBag2!=set():
#                     graph[i, j] = len(wordBag1.intersection(wordBag2))/float(len(wordBag1.union(wordBag2)))
#         graph = graph + graph.T
#         np.save("articlesGraph", graph)
#         pickle.dump(["a" for i in xrange(0, len(allArticles))], open("words.data","wb"))
#         toGephi(graph, ["a" for i in xrange(0, len(allArticles))], "graph.csv")
    def createGraph(self):
        self.processedArticles = bsddb.btopen("processedArticles.db", 'r')
        wordCounts = self.countWords()
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
    def countWords(self):
        wordCounts = {}
        for value in self.processedArticles.itervalues():
            listOfLists = pickle.loads(value)
            for aList in listOfLists:
                for taggedWord in aList:
                    wordCounts[taggedWord] = wordCounts.get(taggedWord, 0)+1
        return wordCounts
    def updateSets(self):
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



