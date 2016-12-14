import configparser
import hashlib
import threading
import time

from Fragmentation.fragmentor_calling import Fragmentor_calling


class Fragmentor():
    def __init__(self, sysfile):
        self.__settings = configparser.RawConfigParser()
        self.__settings.read_file(sysfile)
        options = {}
        self.__Fragoptions = {}
        for option in self.__settings.options('Fragmentor-hz'):
            self.__Fragoptions[option] = (self.__settings.get('Fragmentor-hz', option)).strip().split(",")
        self.__Fingeroptions = {}
        for option in self.__settings.options('Fingerprints'):
            self.__Fingeroptions[option] = (self.__settings.get('Fingerprints', option)).strip()

    def Fragmentation(self):
        j=0
        tasks=[]
        while j<len(self.__Fragoptions['-o']):
            if threading.active_count()<5:
                fragmentor = Fragmentor_calling(workpath='.',s_option=self.__Fragoptions['-s'][j], fragment_type=self.__Fragoptions['-t'][j],
                                                min_length=self.__Fragoptions['-l'][j], max_length=self.__Fragoptions['-u'][j],
                                                cgr_dynbonds=self.__Fragoptions['-d'][j], doallways=(True if self.__Fragoptions['additionaloptions'][j] else False))
                tasks.append(threading.Thread(target=fragmentor.get(inputfile="./SystemFiles/Reactions.sdf", outputfile="Fragmentation/OutFiles/" + self.__Fragoptions['-o'][j]), args=[]))
                tasks[-1].start()
                j+=1
            else:
                time.sleep(1)

        while threading.active_count()>1:
            time.sleep(1)

    def getFingerprints(self):
        fragmentations = {}
        for name in self.__Fragoptions['-o']:
            print("Fingerprinting " + name + "..")
            fragmentations[name] = self.makeFingerprint(name)
        return fragmentations


    def makeFingerprint(self, name):
        hashes = {}
        for line in open('./Fragmentation/OutFiles/' + name + '.hdr').readlines():
            p1 = int(hashlib.md5(line.split()[-1].strip().encode('utf8')).hexdigest(), 16) % int(self.__Fingeroptions['length'])
            p2 = int(hashlib.sha1(line.rstrip('\n').strip().split(' ')[-1].strip().encode('utf8')).hexdigest(), 16) % int(self.__Fingeroptions['length'])
            p_frag = line.split()[0].rstrip(".")
            hashes[p_frag] = [p1, p2]
        fingerprints = {}
        for line in open('./Fragmentation/OutFiles/' + name + '.svm').readlines():
            id = line.split()[0][:-2]
            fragments = [i.split(':')[0] for i in line.split()[1:] if float(i.split(':')[-1])>0]
            fingerprints[id] = [str(0) for i in range(int(self.__Fingeroptions['length']))]
            for frag in fragments:
                fingerprints[id][hashes[frag][0]] = str(1)
                fingerprints[id][hashes[frag][1]] = str(1)
        return fingerprints