import random, copy
from multiprocessing import Pool
import test
from pybrain.structure import RecurrentNetwork
from pybrain.structure import FeedForwardNetwork
from pybrain.structure import LinearLayer, SigmoidLayer
from pybrain.structure import FullConnection
from sklearn import svm
import numpy as np
import scipy.sparse

class InputNeuron():
    def input(self, val):
        self.val = val
    def fire(self):
        return self.val
    def learn(self, data, soln):
        pass

class Neuron():
    def __init__(self):
        self.threshold = random.random()
    def connect(self, cons):
        self.cons = cons
        self.weights = [random.random() for i in xrange(0, len(cons))]
    def fire(self):
        self.answers = [con.fire() for con in self.cons]
        val = [self.answers[i]*self.weights[i] for i in xrange(0, len(self.cons))]
        if val>self.threshold:
            self.val = 1
        else:
            self.val = 0
        return self.val
    def learn(self, soln):
        if self.val<soln:
            self.threshold *= 0.9
            for i in xrange(0, len(self.cons)):
                if self.answers[i]*self.weights[i]>0:
                    self.weights[i] *= 1.1
                else:
                    self.cons[i].learn(1)
                    self.weights[i] *=0.9
        if self.val>soln:
            self.threshold *= 1.1
            for i in xrange(0, len(self.cons)):
                if self.answers[i]*self.weights[i]>0:
                    self.weights[i] *= 0.9
                    self.cons[i].learn(0)
                else:
                    self.weights[i] *=1.1

class NNN():
    def __init__(self, inputN, length):
        self.neuron = FeedForwardNetwork()
        inLayer = LinearLayer(inputN)
        hiddenLayer = SigmoidLayer(length)
        outLayer = LinearLayer(1)
        self.neuron.addInputModule(inLayer)
        self.neuron.addModule(hiddenLayer)
        self.neuron.addOutputModule(outLayer)
        in_to_hidden = FullConnection(inLayer, hiddenLayer)
        hidden_to_out = FullConnection(hiddenLayer, outLayer)
        self.neuron.addConnection(in_to_hidden)
        self.neuron.addConnection(hidden_to_out)
        self.neuron.sortModules()


class NN():
    def __init__(self, inputN, length):
        self.outputN = Neuron()
        self.inputLayer = [InputNeuron() for i in xrange(0, inputN)]
        middleLayer = [Neuron() for i in xrange(0, length)]
        map(lambda n: n.connect(self.inputLayer), middleLayer)
        self.outputN.connect(middleLayer)
    def predict(self, data):
        map(lambda i: self.inputLayer[i].input(data[i]), xrange(0, len(self.inputLayer)))
        self.prediction = self.outputN.fire()
        return self.prediction
    def learn(self, data, soln):
        self.outputN.learn(data, soln)

class svmLearner():
    def __init__(self, inputN):
        self.features = range(0, inputN)
        random.shuffle(self.features)
        self.features = self.features[:random.randint(1, inputN-1)/10]
        self.svm = svm.SVC()
    def predict(self, data):
        return self.svm.predict(data)
    def learn(self, data, soln):
        self.svm.fit(data, soln)

class Animal():
    def __init__(self):
        self.genome = None
        self.tag = random.random()
    def AdamNEve(self, genomeLength, inputN, data, soln):
        self.genome = [svmLearner(inputN) for i in xrange(0, genomeLength)] #NN(inputN, random.randint(2, middleLayerLength))
        map(lambda s: s.learn(data, soln), self.genome)
    def mate(self, partner):
        if partner.tag==self.tag:
            return partner
        offspring = Animal()
        offspring.genome = [self.genome[i] if random.random()<0.5 else partner.genome[i] for i in xrange(0, len(self.genome))]
        return offspring
    def answer(self, data):
        return sum([gene.predict(data) for gene in self.genome])/float(len(self.genome))>0.5
    def learn(self, data, soln):
        map(lambda gene: gene.learn(data, soln), self.genome)
    def liveLife(self, totalData, soln):
        score = np.sum(self.answer(totalData)==soln)
        self.learn(totalData, soln)
        return score/float(len(totalData))


def live(input):
    animal, data, solns = input
    return (animal, animal.liveLife(data, solns))

class Environment():
    def __init__(self, animalsN, genomeLength, inputN, data, soln):
        self.animals = [Animal() for i in xrange(0, animalsN)]
        map(lambda animal: animal.AdamNEve(genomeLength, inputN, data, soln), self.animals)
        self.pool = Pool()
    def newLearningEnv(self, data, solns):
        self.totalData = data
        self.solns = solns
    def nextTimeStep(self, animalsN, stochasticity):
        rankings = map(live, zip(self.animals, test.gen(data), test.gen(solns)))
        rankings.sort(key = lambda x: -1*x[1])
        print map(lambda x: x[1], rankings)
        #print len(rankings)
        median = rankings[len(rankings)/2][1]
        willReproduce = [animal for animal, fitness in rankings if random.random()<fitness/median+(random.randint(0,1)*2-1)*stochasticity]
        #print len(willReproduce)
        males = copy.deepcopy(willReproduce)
        random.shuffle(willReproduce)
        pairs = zip(males, willReproduce)
        self.animals = map(lambda pair: pair[0].mate(pair[1]), pairs[:animalsN])
    def newBirths(self, n, genomeLength, inputN, data, soln):
        newBirths = [Animal() for i in xrange(0, n)]
        map(lambda animal: animal.AdamNEve(genomeLength, inputN, data, soln), newBirths)
        self.animals.extend(newBirths)

def genTSet(size):
    data = np.random.random((100, inputN))#randint(0, high=100, size =((100, inputN)))#[[random.random() for i in xrange(0, 2)] for j in xrange(0, 1000)]
    solns = data.sum(axis=1)/data.shape[1] > 0.5
    return data, solns

inputN = 20
genomeLength = 10
initialPop = 100

data, solns = genTSet(100)
#animalsN, genomeLength, inputN, data, soln
env = Environment(initialPop, genomeLength, inputN, data, solns)
for i in xrange(0, 10**6):
    data, solns = genTSet(100)
    #print np.sum(solns)/float(solns.size)
    env.newLearningEnv(data, solns)
    env.nextTimeStep(initialPop, 0.5)
    env.newBirths(5, genomeLength, inputN, data, solns)
