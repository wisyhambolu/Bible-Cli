#!/usr/bin/python
import json
import sys
from difflib import get_close_matches

dataset = json.load(open("dataset.json"))

def lookup(book,chapter,verse,end_verse):

    try:
        chapter=int(chapter) - 1
    except ValueError:
        return "Error: The Chapter is expected to be a digit, Please try again"

    try:
        verse=int(verse) - 1
    except ValueError:
        return "Error : The Verse is expected to be a digit, Please try again"
    
    try:
        end_verse=int(end_verse) - 1
    except ValueError:
        return "Error : The End Verse is expected to be a digit, Please try again"

    for dataset_item in dataset:
        if book.lower() in dataset_item["name"].lower():
            if chapter == 999998:
                return { 'book' : dataset_item["chapters"] }
            elif verse == 999998:
                return dataset_item["chapters"][chapter]
            elif end_verse != 999998:
                end_verse=(end_verse+1)
                return tuple( dataset_item["chapters"][chapter][verse:end_verse] )
            else:
                return dataset_item["chapters"][chapter][verse]
                
param1 = all
if sys.argv[1:]:
    param1=sys.argv[1]

param2 = 999999
if sys.argv[2:]:
    param2=sys.argv[2]

param3 = 999999
if sys.argv[3:]:
    if sys.argv[3] == ":":
        if sys.argv[4:]:
            param3 = sys.argv[4]
    else:
        param3=sys.argv[3]

param4 = 999999
if sys.argv[5:]:
    if sys.argv[5] == "-":
        if sys.argv[6:]:
            param4 = sys.argv[6]
            
output=(lookup(param1,param2,param3,param4))
if type(output) == dict:
    output_len=len(output["book"]) 
    output=output["book"]

    for item in range(output_len):
        #if type(item) == list:
        for sub_item,sub_item_count in zip(output[item],range(len(output[item]))):
            print(148*"-")
            print(param1 + " " + str(item + 1) + " : " + str(sub_item_count + 1) + " | " + sub_item)
            print(148*"-")
elif type(output) == list:
    output_len=len(output)
    for item,item_count in zip(output,range(len(output))):
            print(148*"-")
            print(param1 + " " + param2 + " : " + str(item_count + 1) + " | " + item)
            print(148*"-")
elif type(output) == unicode:
    print(148*"-")
    print(param1 + " " + param2 + " : " + param3 + " | " + output)
    print(148*"-")
elif type(output) == tuple:
    param4=(int(param4)+1)
    for item,item_count in zip(output,range(int(param3),int(param4))):
            print(148*"-")
            print(param1 + " " + param2 + " : " + str(item_count) + " | " + item)
            print(148*"-")
elif type(output) == str:
    print(output)


#def search(book):
#    book = book.lower()
#    if book in dataset:
#        return dataset[book]
    #elif len(get_close_matches(word, dataset.keys())[0]) > 0:
    #    ans = input("Did you mean \"%s\" instead? Y or N: " % get_close_matches(word, dataset.keys())[0])
    #    if ans == "Y":
    #        return dataset[get_close_matches(word, dataset.keys())[0]]
    #    elif ans == "N":
    #        return "The word \""+ word +"\" doesn't exist, please double check and try again"
#    else:
#        return "The word \""+ book +"\" doesn't exist, please double check and try again"

#word = input("Enter a book: ")
#output=(search(book))
#if type(output) == list:
#    for item in output:
#        print(item)
#else:
#    print(output)