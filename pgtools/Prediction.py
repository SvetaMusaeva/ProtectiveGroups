class Validation():
    def __init__(self, d, frag_name):
        self.frag_name=frag_name
        self.predictions={'TcMax': {}, 'kNN': {}, 'kNNw': {}}
        for j, PG in enumerate(sorted(d)):
            print(str(j)+" from "+str(len(d))+" analyzed..")
            for cat in sorted(d[PG]):
                for class1 in sorted(d[PG][cat]):
                    for jj, id1 in enumerate(sorted(d[PG][cat][class1][self.frag_name])):
                        if jj%50==0:
                            print(str(jj)+" out of "+str(len(set(d[PG][cat][class1][self.frag_name])))+"...", PG, "-", cat, "-", class1, '-', self.frag_name)
                        Tanimoto_vector_CPG=[]
                        Tanimoto_vector_RPG=[]
                        a1=d[PG][cat][class1][self.frag_name][id1]
                        a2=len(a1)
                        for class2 in d[PG][cat]:
                            for id2 in d[PG][cat][class2][self.frag_name]:
                                if id2!=id1:
                                    b=d[PG][cat][class2][self.frag_name][id2]
                                    c=len(a1&b)
                                    b=len(b)
                                    Tc=c/(a2+b-c)
                                    if class2=='CPG':
                                        Tanimoto_vector_CPG.append(round(Tc, 4))
                                    else:
                                        Tanimoto_vector_RPG.append(round(Tc, 4))
                        #Вызов функций для предсказания
                        self.TcMax(class1, Tanimoto_vector_CPG, Tanimoto_vector_RPG)
                        self.kNN(class1, Tanimoto_vector_CPG, Tanimoto_vector_RPG, 3, 10)
                        self.kNNw(class1, Tanimoto_vector_CPG, Tanimoto_vector_RPG, 3, 10)
                        #print('************************************************************************************************************************')


    def TcMax(self, class_init, CPG2, RPG2):
        CPG=sorted(CPG2, reverse=True)[0]
        RPG=sorted(RPG2, reverse=True)[0]
        for delta in range(0, 105, 5):
            delta=round(delta/100, 2)
            if delta not in self.predictions['TcMax']:
                self.predictions['TcMax'][delta]={'TP':0, 'FP':0, 'TN':0, 'FN':0, 'Unpredictable':0, 'P':0, 'N':0}
            if CPG-RPG>delta and class_init=='CPG':
                self.predictions['TcMax'][delta]['TP']+=1
                self.predictions['TcMax'][delta]['P']+=1
            elif CPG-RPG<(delta*(-1)) and class_init=='CPG':
                self.predictions['TcMax'][delta]['FN']+=1
                self.predictions['TcMax'][delta]['P']+=1
            elif CPG-RPG<(delta*(-1)) and class_init=='RPG':
                self.predictions['TcMax'][delta]['TN']+=1
                self.predictions['TcMax'][delta]['N']+=1
            elif CPG-RPG>delta and class_init=='RPG':
                self.predictions['TcMax'][delta]['FP']+=1
                self.predictions['TcMax'][delta]['N']+=1
            elif (CPG-RPG<delta and CPG-RPG>(delta*(-1))) or CPG==RPG:
                self.predictions['TcMax'][delta]['Unpredictable']+=1
                if class_init=='RPG':
                    self.predictions['TcMax'][delta]['N']+=1
                else:
                    self.predictions['TcMax'][delta]['P']+=1


    def kNN(self, class_init, CPG2, RPG2, min_neighbors, max_neighbors):
        for n_neighbors in range(min_neighbors, max_neighbors+1):
            CPG=sorted(list(set(CPG2)), reverse=True)
            RPG=sorted(list(set(RPG2)), reverse=True)
            if n_neighbors not in self.predictions['kNN']:
                self.predictions['kNN'][n_neighbors]={}
            weight_CPG=0
            total_weight=0
            for neighbor in range(n_neighbors):
                if CPG and RPG and CPG[0]>RPG[0]:
                    weight_CPG+=1
                    CPG.pop(0)
                    total_weight+=1
                elif CPG and RPG and CPG[0]<RPG[0]:
                    RPG.pop(0)
                    total_weight+=1
                elif CPG and RPG and CPG[0]==RPG[0]:
                    w=CPG.pop(0)
                    weight_CPG+=1
                    total_weight+=1
                    w=RPG.pop(0)
                    total_weight+=1
                elif CPG and len(RPG)==0:
                    weight_CPG+=1
                    CPG.pop(0)
                    total_weight+=1
                elif RPG and len(CPG)==0:
                    RPG.pop(0)
                    total_weight+=1
                else:
                    break
            for delta in range(0, 105, 5):
                delta=round(delta/100, 2)
                if delta not in self.predictions['kNN'][n_neighbors]:
                    self.predictions['kNN'][n_neighbors][delta] = {'TP':0, 'FP':0, 'TN':0, 'FN':0}
                if round(weight_CPG/total_weight, 2)>=delta and class_init=='CPG':
                    self.predictions['kNN'][n_neighbors][delta]['TP']+=1
                elif round(weight_CPG/total_weight, 2)<delta and class_init=='CPG':
                    self.predictions['kNN'][n_neighbors][delta]['FN']+=1
                elif round(weight_CPG/total_weight, 2)<delta and class_init=='RPG':
                    self.predictions['kNN'][n_neighbors][delta]['TN']+=1
                elif round(weight_CPG/total_weight, 2)>=delta and class_init=='RPG':
                    self.predictions['kNN'][n_neighbors][delta]['FP']+=1


    def kNNw(self, class_init, CPG2, RPG2, min_neighbors, max_neighbors):
        for n_neighbors in range(min_neighbors, max_neighbors+1):
            CPG=sorted(list(set(CPG2)), reverse=True)
            RPG=sorted(list(set(RPG2)), reverse=True)
            if n_neighbors not in self.predictions['kNNw']:
                self.predictions['kNNw'][n_neighbors]={}
            weight_CPG=0.0
            total_weight=0.0
            for neighbor in range(n_neighbors):
                if CPG and RPG and CPG[0]>RPG[0]:
                    w=CPG.pop(0)
                    weight_CPG+=w
                    total_weight+=w
                elif CPG and RPG and CPG[0]<RPG[0]:
                    total_weight+=RPG.pop(0)
                elif CPG and RPG and CPG[0]==RPG[0]:
                    w=CPG.pop(0)
                    weight_CPG+=w
                    total_weight+=w
                    w=RPG.pop(0)
                    total_weight+=w
                elif CPG and len(RPG)==0:
                    w=CPG.pop(0)
                    weight_CPG+=w
                    total_weight+=w
                elif RPG and len(CPG)==0:
                    total_weight+=RPG.pop(0)
                else:
                    break
            for delta in range(0, 105, 5):
                delta=round(delta/100, 2)
                if delta not in self.predictions['kNNw'][n_neighbors]:
                    self.predictions['kNNw'][n_neighbors][delta] = {'TP':0, 'FP':0, 'TN':0, 'FN':0}
                if round(weight_CPG/total_weight, 2)>=delta and class_init=='CPG':
                    self.predictions['kNNw'][n_neighbors][delta]['TP']+=1
                elif round(weight_CPG/total_weight, 2)<delta and class_init=='CPG':
                    self.predictions['kNNw'][n_neighbors][delta]['FN']+=1
                elif round(weight_CPG/total_weight, 2)<delta and class_init=='RPG':
                    self.predictions['kNNw'][n_neighbors][delta]['TN']+=1
                elif round(weight_CPG/total_weight, 2)>=delta and class_init=='RPG':
                    self.predictions['kNNw'][n_neighbors][delta]['FP']+=1





