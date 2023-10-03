#!/usr/bin/env python
import argparse

import org

import re

from datetime import datetime

import shutil
import os

state_file_name = '.last_export.orgexport'

#define a function to build the output text
outputtext = ""
def addoutput(text):
    global outputtext
    outputtext = outputtext + text
    return outputtext

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inputfile')

    args = ap.parse_args()

    #do not try to import notes from your ebookreader from before 1970
    last_export = datetime(year=1970, month=1, day=1)
    last_export_lines = []
    state_file = os.path.join(os.path.dirname(args.inputfile), state_file_name)

    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            lines = f.read()
        lines = lines.split('\n')
        last_export_lines = [l for l in lines if l]
        last_export = datetime.strptime(last_export_lines[-1], org.date_format)

    with open(args.inputfile, 'r') as inputfile:
        text = inputfile.read()

    #Value extraction handling
    note_sep = '''
-----------------------------------

'''

    notes = text.split(note_sep)

    note_re = re.compile(r'\n'.join([
        r'(?P<title>.+)'
        , r'((?P<type>Lesezeichen|Markierung|Notiz)[  ]+auf Seite[  ]+(?P<page>.+): )'
        #note is optional
        + r'''((?P<note>(?:.|\n)*)
)?''' + r'"(?P<quote>(?:.|\n)*)"'
        , r'''Hinzugefügt am (?P<day>\d{2}).(?P<month>\d{2}).(?P<year>\d{4}) \| (?P<hour>\d{1,2}):(?P<minute>\d{2})
''']))
    #define note types (from tolino notes.txt)
    types = dict(
        Markierung='markierung'
        , Notiz='notiz'
        , Lesezeichen='lesezeichen'
        )

    #Init a Note class (for storing data)
    class Note:
        def __init__(self, book_title, note_type, note_page, note_quote, note_date, note_title):
            self.book_title = book_title
            self.note_type = note_type
            self.note_page = note_page
            self.note_quote = note_quote
            self.note_date = note_date
            self.note_title = note_title
    #Init a list for note class objects
    store_notes = []

    for note in notes:
        if not note:
            continue
        #print('---------"' + note + '"')
        m = note_re.match(note)

        assert(m)

        #Date handling
        d = {}
        for k in ('year', 'month', 'day', 'hour', 'minute'):
            d[k] = int(m.group(k))

        created = datetime(**d)
        
        #Check if note isn't exported yet
        if created < last_export:
            continue
        
        book = m.group('title')
        page = m.group('page')
        typ = types[m.group('type')]
        quote = m.group('quote')

        #Make the title beautiful for org :)
        title = quote
        title = org.wrap(title, '"')
        if typ == 'note':
            title = m.group('note')

        title.replace('\n', ' ')
        n = 20
        content = ''
        title_words = title.split()
        if len(title_words) > n:
            #content += '[…] ' + org.wrap(' '.join(title_words[n:])) + '\n\n'
            title = ' '.join(title_words[:n])
            title += ' […]'

        #Store values in the store_notes object list
        store_notes.append(Note(book, typ, page, quote, created, title))

    #Store new last write state permanently
    last_export_lines.append(datetime.now().strftime(org.date_format))
    with open(state_file, 'w+') as f:
        f.write('\n'.join(last_export_lines))

    #Looping trough stored notes and create a list with all possible book titles
    store_booktitles = []
    for x in store_notes:
        if not x.book_title in store_booktitles:
            store_booktitles.append(x.book_title)

    #Create org output for every book
    for x in store_booktitles:
        #Booktitle (/Bookname)
        addoutput("* " + x + "\n")

        #Add a boolean for getting first created propertie for book heading only once
        first_item = True
        #For every stored note check if it is for the selected book
        for note_item in store_notes:
            if note_item.book_title == x:
                if first_item:
                    first_item = False
                    addoutput(org.datepropertie(note_item.note_date))

                #Create note text (/Bookname/Note)
                addoutput("** S. " + note_item.note_page + " " + note_item.note_title + ' :' + note_item.note_type + ":" "\n")
                #Datepropertie for note
                addoutput(org.datepropertie(note_item.note_date))
                #Quote
                addoutput("#+begin_quote\n")
                addoutput(note_item.note_quote + "\n")
                addoutput("#+end_quote\n")
                #Reference text
                addoutput('Von "' + note_item.book_title + '", S. ' + note_item.note_page)
                addoutput("\n")
    #Print the result
    print(outputtext)

if __name__ == '__main__':
    main()
