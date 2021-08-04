import os
import re

class DocumentationEntry:
    """Class for storing documentation entries
    """
    name = None
    params = []
    desc = None
    
    def __init__(self,name: str,params,desc: str):
        self.name = name
        self.params = params
        self.desc = desc
    
    def getName(self):
        return self.name

class CogDocumentation:
    """Stores a list of documentation entries for a cog
    """
    name = None
    docs = []

    def __init__(self,name: str, docs):
        self.name = name
        self.docs = docs
    
    def addDoc(self,doc):
        self.docs.append(doc)

    def getDocs(self):
        return self.docs

files = os.listdir(os.getcwd()+"\cogs")

workingDir = os.path.join(os.getcwd(),"cogs")

def get_docstrings():
    cogs=[]
    for filename in files:
        if (filename[-3:] != '.py'):
            print(filename + " is not a python file")
            break
        f = open(os.path.join(workingDir, filename), "r")
        find_command(f, cogs)

        f.close()

def find_command(filename, cogs):
    try:
        filecontents = filename.readlines() #Gives a list of the lines in the cog file
    except ValueError: #this shouldn't happen
        print("End of file.")
        return
        
    #commands=[] #list of all the commands
    checkgroup = False #notes whether it found a decorator labeled @commands.group yet
    for line in filecontents:
        #print(line)

        if checkgroup: #if its found the decorator
            for name in groupnames:
                if "@" + name in line:
                    newline = filecontents[filecontents.index(line)+1]
                    foundDef = False
                    breakCatch = 0
                    while foundDef == False:
                        if "def " in newline:
                            temp = newline[newline.index("def ")+4:] #fix this
                            temp = temp[:temp.index("(")]
                            foundDef = True
                            cogs[len(cogs)-1].addDoc(DocumentationEntry(temp, "", ""))
                            #print(temp)
                            #commands += temp

                        else:
                            breakCatch+=1
                            if breakCatch > 4:
                                break
                            else:
                                newline = filecontents[filecontents.index(newline)+1]
                    #commands += line[:line[line.index('"')+1:].index('"')]
        else:
            if "@commands.group" in line:
                print("This bit runs")
                #temp = line
                #temp = temp[temp.index('"')+1:]
                #groupnames = [temp[:temp.index('')]]
                #groupnames = [line[:line[line.index('"')+1:].index('"')]]
                groupnames = (re.findall(r'"(.*?)"', line))
                #print(line)
                #print(groupnames)
                cogs.append(CogDocumentation(groupnames[0], []))
                checkgroup = True
                if "aliases" in line:
                    temp = line
                    temp = temp[temp.index('"')+1:]
                    temp = temp[temp.index('"')+1:]
                    for i in range(1, temp.count(",")):
                        temp = temp[temp.index('"')+1:]
                        groupnames += temp[:temp.index('"')]
                        temp = temp[temp.index('"')+1:]
                #print(groupnames)
    #print(commands)
    for doc in cogs[len(cogs)-1].getDocs():
        print(doc.getName())

#help(cogs.Announce.Announce)        
            
            
get_docstrings()