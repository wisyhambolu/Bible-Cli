#!/usr/bin/python3
#import modules
import json
import sys
import os
import argparse
import re
from difflib import get_close_matches
from prettytable import PrettyTable, ALL

parser = argparse.ArgumentParser()

#usage statement
parser.add_argument("scripture",help="'1 John 1:2-5'")

#load json dataset
dataset = json.load(open("dataset.json"))

#create PrettyTable object; set Header to True; hrules sets borders between rows
table = PrettyTable(["Scripture","Text"],hrules=ALL,header=True)

#get the length of th terminal and resize text
terminal_length = os.get_terminal_size()[0] - os.get_terminal_size()[0] / 3

#function is format scripture text
def format_text(text,max_length):
    #accumulated line length
    ACC_length = 0
    words = text.split(" ")
    formatted_text = ""
    for word in words:
        #if ACC_length + len(word) and a space is <= max_line_length 
        if ACC_length + (len(word) + 1) <= max_length:
            #append the word and a space
            formatted_text = formatted_text + word + " "
            #length = length + length of word + length of space
            ACC_length = ACC_length + len(word) + 1
        else:
            #append a line break, then the word and a space
            formatted_text = formatted_text + "\n" + word + " "
            #reset counter of length to the length of a word and a space
            ACC_length = len(word) + 1
    return formatted_text

#Function to lookup scripture
def lookup(book,chapter,verse,end_verse):

    #try-except statements to catch ValueErrors, -1 due to zero index
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

    #loop json dataset; use 999998 as empty parameter indicator
    for dataset_item in dataset:
        if book.lower() in dataset_item["name"].lower():
            if chapter == 999998:
                    return { 'book' : dataset_item["chapters"] }
            elif verse == 999998:
                try:
                    return dataset_item["chapters"][chapter]
                except IndexError:
                    return "Error: Chapter incorrect, Please check and try again"
            elif end_verse != 999998:
                end_verse=(end_verse+1)
                try:
                    return tuple( dataset_item["chapters"][chapter][verse:end_verse] )
                except IndexError:
                    return "Error: Start/End Verse Incorrect, Please check and try again"
            else:
                try:
                    return dataset_item["chapters"][chapter][verse]
                except IndexError:
                    return "Error : Verse is incorrect, Please check and try again"

#read command line arguments
args = parser.parse_args()

#check if the inputted string can be split
scripture_string = re.split('[:-]',args.scripture)


if len(scripture_string) > 1: #eg: 1 John 2:1 [ '1 John 2', '1' ]
    book = scripture_string[:1] #get only first item in list
    verse_start_end = scripture_string[1:] #get only last item in list

    if len(verse_start_end) == 2:   
        start_verse = verse_start_end[0]
        end_verse = verse_start_end[1]
    else:
        start_verse = verse_start_end[0]
    
    book = ' '.join(scripture_string[0].split()[:-1]) #convert list to string
    chapter = ' '.join(scripture_string[0].split()[-1]) #convert list to string

else: #eg: 1 John 2 ['1 John 2']
    if scripture_string[0].split()[-1].isdigit() == True: #check if book has a chapter
        book = ' '.join(scripture_string[0].split()[:-1]) #convert list to string
        chapter = ' '.join(scripture_string[0].split()[-1]) #convert list to string
    else:
        book = ' '.join(scripture_string) #convert list to string


#try except blocks to catch undefined variables
try:
    book
except NameError:
    book = ""

try:
    chapter
except NameError:
    chapter = ""

try:
    start_verse
except NameError:
    start_verse = ""    

try:
    end_verse
except NameError:
    end_verse = ""


#check if variables are empty string and set default value
book_input = all
if book != "":
    book_input = book

chapter_input = 999999
if chapter != "":
    chapter_input = chapter

start_verse_input = 999999
if start_verse != "":
    start_verse_input = start_verse

end_verse_input = 999999
if end_verse != "":
    end_verse_input = end_verse

##""" Possible inputs:
#1 kings
#1 kings 1
#1 kings 1-2
#1 kings 1:1
#1 kings 1:1-2
#Song of Solomon 1
#John 1 """

#lookup scripture with function and parameters            
output=(lookup(book_input,chapter_input,start_verse_input,end_verse_input))

#different input scenarios are differentiated by different data types
#dict ===> book only
#list ===> book and chapter
#str ===> book, chapter and start verse
#tuple ===> book, chapter, start verse and end verse
if type(output) == dict:
    #book is the key in the dictionary "output"
    output_len=len(output["book"]) #get length of dictionary, number of chapters
    output=output["book"]

    for chapter in range(output_len):
        for text,verse in zip(output[chapter],range(len(output[chapter]))):
            text=format_text(text,terminal_length)
            table.add_row([book_input + " " + str(chapter + 1) + " : " + str(verse + 1),text])  #add row to output table
    print(table)

elif type(output) == list:
    output_len=len(output)
    for text,verse in zip(output,range(len(output))):
        text=format_text(text,terminal_length)
        table.add_row([book_input + " " + chapter_input + " : " + str(verse + 1),text]) #add row to output table
    print(table)

elif type(output) == str:
    text=format_text(output,terminal_length)
    table.add_row([book_input + " " + chapter_input + " : " + start_verse_input,text])  #add row to output table
    print(table)

elif type(output) == tuple:
    end_verse_input=(int(end_verse_input)+1)
    for text,start_verse in zip(output,range(int(start_verse_input),int(end_verse_input))):
            text=format_text(text,terminal_length)
            table.add_row([book_input + " " + chapter_input + " : " + str(start_verse),text])   #add row to output table          
    print(table)