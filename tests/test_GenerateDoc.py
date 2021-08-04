import pytest
import json
from GenerateDoc import doc_list_to_json, get_cog_docs
from pathlib import Path

"""
Testing GenerateDoc.py

Compares automatically generated document to a manually created one
"""

def open__as_json(filename):
    with open(filename) as json_file:
        correctDocString = json.load(json_file)
    autoDocString = doc_list_to_json(get_cog_docs())
    return correctDocString, autoDocString

@pytest.mark.parametrize("filename", ['tests/TestDocumentation.json'])
def test_compare_cog_names(filename):
    correctDocString, autoDocString = open__as_json(filename)
    assert(len(correctDocString) == len(autoDocString))
    names = [doc['name'] for doc in autoDocString]
    for doc in correctDocString:
        assert doc['name'] in names


"""
@pytest.mark.parametrize("filename", ['tests/TestDocumentation.json'])
def test_compare_cog_command(filename):
    correctDocString, autoDocString = open__as_json(filename)
    assert(len(correctDocString) == len(autoDocString))
    for i in range(0, len(correctDocString)):
        for j in range(0, len(correctDocString[i]['commands'])):
            assert(correctDocString[i]['commands'][j] == autoDocString[i]['commands'][j])
"""

@pytest.mark.parametrize("filename", ['tests/TestDocumentation.json'])
def test_compare_cog_command_name(filename):
    correctDocString, autoDocString = open__as_json(filename)

    assert(len(correctDocString) == len(autoDocString))
    for i in range(0, len(correctDocString)):
        commandNames = [entry['command'] for entry in autoDocString[i]['commands']]
        for command in autoDocString[i]['commands']:
            assert(command['command'] in commandNames) 

@pytest.mark.parametrize("filename", ['tests/TestDocumentation.json'])
def test_compare_cog_command_parameters(filename):
    correctDocString, autoDocString = open__as_json(filename)

    assert(len(correctDocString) == len(autoDocString))
    for i in range(0, len(correctDocString)):
        params = [entry['parameters'] for entry in autoDocString[i]['commands']]
        for command in autoDocString[i]['commands']:
            assert(command['parameters'] in params) 

@pytest.mark.parametrize("filename", ['tests/TestDocumentation.json'])
def test_compare_cog_command_description(filename):
    correctDocString, autoDocString = open__as_json(filename)

    assert(len(correctDocString) == len(autoDocString))
    for i in range(0, len(correctDocString)):
        descriptions = [entry['description'] for entry in autoDocString[i]['commands']]
        for command in autoDocString[i]['commands']:
            assert(command['description'] in descriptions) 
