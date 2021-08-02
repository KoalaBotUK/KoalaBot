from cogs.Announce import Announce
from os import listdir
import os
import importlib
from inspect import getmembers, isfunction, ismethod, isclass
import glob
import re
import json

"""
KoalaBot utility function for generating bot command docs
Created By: Charlie Bowe, Aqeel Little 
"""


class DocumentationEntry:
    """Class for storing documentation entries for bot commands
    """
    name = None
    params = []
    desc = None
    
    def __init__(self,name: str,params,desc: str):
        self.name = name
        self.params = params
        self.desc = desc

class CogDocumentation:
    """Stores a list of documentation entries for a cog
    """
    name = None
    docs = []

    def __init__(self,name: str, docs):
        #Change BaseCog to KoalaBot
        if name == 'BaseCog':
            self.name = 'KoalaBot'
        else:    
            self.name = name
        self.docs = docs

docList = []


#Get the directory of the cogs folder
dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'cogs')
#Grab the names of all the .py files in the cogs folder
modules = [ fl for fl in listdir(dir) if fl.endswith('.py') ]

cogs = []
#for i in range 0 to amount of cogs

def get_decorators(function):
  # If we have no func_closure, it means we are not wrapping any other functions.
  if not function.func_closure:
    return [function]
  decorators = []
  # Otherwise, we want to collect all of the recursive results for every closure we have.
  for closure in function.func_closure:
    decorators.extend(get_decorators(closure.cell_contents))
  return [function] + decorators

def get_cog_docs():
    for i in range (0,len(modules)):
        #Cut off the .py extension
        modules[i] = modules[i][:-3]
        #Import the library and store it in cogs
        cogs.append(__import__('cogs.'+modules[i]))

        #get the refernce to the current library
        #E.g. cogs.Announce
        currentLib = getattr(cogs[i], modules[i])

        #Store all of the classes of the cog in classes
        classes = [ obj for obj in getmembers(currentLib) if isclass(obj[1]) ]
        #print(f'Current classes: {classes} \n') 

        docs = []
        for cls in classes:
            if cls[0] != modules[i]:
                print(f'{cls[0]} is not {modules[i]}')

            #Store the functions of each classes in class_funcs
            class_funcs = [ obj for obj in getmembers(cls[1]) ]

            for obj in class_funcs:
                try:
                    text = getattr(getattr(currentLib,modules[i]),str(obj[0])).help.splitlines()
                except AttributeError:
                    pass
                    continue
                except:
                    print("Unexpected error")
                    continue
                    
                name = getattr(getattr(currentLib,modules[i]),str(obj[0])).name

                if getattr(getattr(currentLib,modules[i]),str(obj[0])).parent != None:
                    name = f'{getattr(getattr(currentLib,modules[i]),str(obj[0])).parent} {name}'
                
                desc = ""
                params = []
                for line in text:
                    matchObj = re.match( r':param (.*): (.*)', line, re.M|re.I)

                    if matchObj:
                        if matchObj.group(1) == 'ctx':
                            continue
                        params.append(matchObj.group(1))
                    else:
                        desc += line
                docs.append(DocumentationEntry(name,params,desc))
                
            
        docList.append(CogDocumentation(modules[i],docs))
    return docList

docList = get_cog_docs()

for cogDoc in docList:
    print(f'-= {cogDoc.name} =-')
    for doc in cogDoc.docs:
        print(doc.name)

def parse_docs(docList, filename):
    """Pass a list of CogDocumentation objects into a json file
    :param docList: List of CogDocumentation
    :param filename: filename of json file
    """
    data = []
    for cogDoc in docList:
        cog = {}
        cog['name'] = cogDoc.name
        commands = []
        for docEntry in cogDoc.docs:
            entry = {}
            entry['command'] = docEntry.name
            entry['parameters'] = docEntry.params
            entry['description'] = docEntry.desc
            commands.append(entry)
        cog['commands'] = commands
        data.append(cog)

    file = open(filename, "w")
    file.write(json.dumps(data, indent=2))
    file.close()

parse_docs(docList,'test.json')