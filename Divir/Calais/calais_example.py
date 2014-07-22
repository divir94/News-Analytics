from calais import Calais

API_KEY = "kpfyb7kb5wqbhpxbdnxjr52v"
calais = Calais(API_KEY, submitter="python-calais demo")

url = "http://www.reuters.com/article/2014/07/04/russia-usa-idUSL6N0PF1M420140704"
result = calais.analyze_url(url)

"""
print "\nSummary:\n"
result.print_summary()
print "\nTopics:\n"
result.print_topics()
print "\nEntities:\n"
result.print_entities()
print "\nRelations:\n"
result.print_relations()
"""

result.print_entities()

for i in range(len(result.entities)):
     print str(result.entities[i]["name"])
     print str(result.entities[i]["_type"])
     print str(result.entities[i]["relevance"])
     print
