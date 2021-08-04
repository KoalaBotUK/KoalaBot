from os import listdir, path
from inspect import getmembers, isclass
import re
import json

"""
KoalaBot utility function for auto generating bot command docs
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

    #Dictionary of cogs that have different names in the doc for clarity
    docNameChanges = {
        'BaseCog': 'KoalaBot',
        'ReactForRole': 'ReactForRole (RFR)',
        'Verification': 'Verify',
        'Voting': 'Vote'
    }

    def __init__(self,name: str, docs):
        #If name of the cog is not the name that should be in the doc
        if name in self.docNameChanges.keys():
            #change it
            self.name = self.docNameChanges.get(name)
        else:    
            self.name = name
        self.docs = docs
    
def add_cog_to_cog(add,to,docList):
    """Add all DocumentationEntry of one CogDocumentation to another
    :param add: CogDocumentation to move and destroy
    :param to: CogDocumentation to add to
    :param docList: list of CogDocumentation that add and to are in
    :return: new list of CogDocumentation
    """
    addCog = None
    toCog = None

    for doc in docList:
        if doc.name == add:
            addCog = doc
        elif doc.name == to:
            toCog = doc

    if(addCog != None) and (toCog != None):
        docList.remove(addCog)
        toCog.docs.extend(addCog.docs)
    
    return docList

def get_cog_docs():
    """Imports all cogs in directory cogs and stores the name, params and 
    docstring description of bot commands
    :return: list of CogDocumentation
    """
    #List fo Cogdocumentation
    docList = []
    #Get the directory of the cogs folder
    dir = path.join(path.dirname(path.realpath(__file__)),'cogs')
    #Grab the names of all the .py files in the cogs folder
    modules = []
    modules = [ fl for fl in listdir(dir) if fl.endswith('.py') ]
    cogs = []

    #for i in range 0 to amount of cogs
    for i in range (0,len(modules)):
        if modules[i].endswith('.py'):
            modules[i] = modules[i][:-3]

        #Import the library and store it in cogs
        cogs.append(__import__('cogs.'+modules[i]))

        #get the refernce to the current library
        #E.g. cogs.Announce
        currentLib = getattr(cogs[i], modules[i])

        #Store all of the classes of the cog in classes
        classes = [ obj for obj in getmembers(currentLib) if isclass(obj[1]) ]

        #list of DocumentationEntry for each class
        docs = []
        for cls in classes:
            #Store the functions of each classes in class_funcs
            class_funcs = [ obj for obj in getmembers(cls[1]) ]

            for obj in class_funcs:
                try:
                    #Get the docstring of the function
                    text = getattr(getattr(currentLib,modules[i]),str(obj[0])).help.splitlines()
                except AttributeError:
                    #On attribute error, function has no docstring
                    pass
                    continue
                except Exception:
                    print(f'Error {Exception} when reading docstring of {obj} in {modules[i]}')
                    continue
                    
                #Get the name of the command object
                name = getattr(getattr(currentLib,modules[i]),str(obj[0])).name

                #If function is nested, append its nested commadn to its font
                #E.g. announce create
                if getattr(getattr(currentLib,modules[i]),str(obj[0])).parent != None:
                    name = f'{getattr(getattr(currentLib,modules[i]),str(obj[0])).parent} {name}'
                
                desc = ""
                params = []
                for line in text:
                    #Match each line to regex for checking for parameter descriptions
                    matchObj = re.match( r':(.*) (.*): (.*)', line, re.M|re.I)

                    #If its a parameter
                    if matchObj and (matchObj.group(1) == 'param'):
                        #Do not add it if its a ctx, as that is not useful for the doc
                        if matchObj.group(2) == 'ctx':
                            continue
                        params.append(matchObj.group(2))
                    else:
                        #Else, its a description of the command, so add it to desc
                        desc += line
                #Create a new Documentation entry for the command
                docs.append(DocumentationEntry(name,params,desc)) 

        docList.append(CogDocumentation(modules[i],docs))

    #Add everything in IntroCog to KoalaBot for clarity
    docList = add_cog_to_cog('IntroCog','KoalaBot',docList)

    return docList

def doc_list_to_json(docList):
    """Converts a list of CogDocumentation into a json string
    :param docList: List fo CogDocumentation
    :return: JSON string
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
    return data

def parse_docs(docList, filename):
    """Pass a list of CogDocumentation objects into a json file
    :param docList: List of CogDocumentation
    :param filename: filename of json file
    """
    data = doc_list_to_json(docList)
    file = open(filename, "w")
    file.write(json.dumps(data, indent=2))
    file.close()

def generate_doc():
    """Runs the script that will automatically generate documentation.json using the docstrings
    of cogs in directory cogs
    """
    docList = get_cog_docs()
    parse_docs(docList,'documentation.json')

if __name__ == "__main__":
    print('Generating document.json')
    generate_doc()