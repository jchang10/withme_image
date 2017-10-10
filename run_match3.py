"""
run_combos2.py - run through the different combinations for face item parts.
"""

import argparse
import os, re, sys
assert sys.version.startswith('3.6'), "Python version 3.6 is required"

import run_combos3
import run_image3

DEBUG=True

def _match_skin(filename, file, files):
    if not args.match_skin:
        return
    if 'skin' in file:
        if args.match_skin in file.get('skin'):
            # force skin
            file['skin'] = args.match_skin
        else:
            del files[filename]

def _match_gender(filename, file, files):
    if not args.match_gender:
        return
    if 'gender' in file:
        if args.match_gender in file.get('gender'):
            # force gender
            file['gender'] = args.match_gender
        else:
            del files[filename]

def _match_item(item, filenames):
    if not filenames:
        return
    files = item['files']
    for filename, file in list(files.items()):
        if filename not in filenames:
            del files[filename]

def run_matches():
    for _key, _item in db.items():
        if _item.get('has_skin'):
            for filename, file in list(_item['files'].items()):
                _match_skin(filename, file, _item['files'])
        if _item.get('has_color'):
            for filename, color in list(_item['colors'].items()):
                _match_skin(filename, color, _item['colors'])
        if _item.get('has_gender'):
            for filename, file in list(_item['files'].items()):
                _match_gender(filename, file, _item['files'])
    if args.match_mustache:
        _match_item(db['facehair'], 'facehair1')
    elif args.match_beard:
        _match_item(db['facehair'], ('facehair2','facehair3','facehair4','facehair5'))
    _match_item(db['spectacle'], args.match_sunglasses)
    _match_item(db['spectacle'], args.match_eyeglasses)

def create_random_path():
    from random import randint
    path = ['1']
    for _key, _item in db.items():
        count = len(_item['files'])
        if count == 0:
            print('Error. Likely unable to create with the given matches. Quitting.')
            exit(0)
        ri = randint(0,count-1)
        filename = list(_item['files'].keys())[ri]
        if '!' not in filename \
           and filename != 'none' \
           and _item.get('has_color'):
            count = len(_item['colors'])
            ri = randint(0,count-1)
            colorname = list(_item['colors'].keys())[ri]
            if colorname != 'orig':
                filename = filename+'!'+colorname
            else:
                pass #skip the color
        path.append(filename)
    return '-'.join(path)
    
def create_random_image():
    line = create_random_path()
    if DEBUG:
        print(line)
    im = run_image3.create_image_from_line(line, db, args)
    return im

def run_random():
    i = 0
    while args.count == -1 or i < args.count:
        i += 1
        create_random_image()
    

def create_args(args=None):
    parser = argparse.ArgumentParser(description='Images infile processor')
    parser.add_argument('items_path', metavar='items-path', default='items',
                        help='must be a directory')
    parser.add_argument('output_path', metavar='output', default='output',
                        help='must be a directory')
    parser.add_argument('--count', default=-1, type=int,
                        help='max count')
    parser.add_argument('--items', 
                        help='comma separated list of items to process. rest will be "none".'
                        'e.g. --items "head,nose,eye"')
    parser.add_argument('--match_skin', help='match item')
    parser.add_argument('--match_gender', help='match item')
    parser.add_argument('--match_beard', help='match item', default=False, action="store_true")
    parser.add_argument('--match_mustache', help='match item', default=False, action="store_true")
    parser.add_argument('--match_eyeglasses', help='match item')
    parser.add_argument('--match_sunglasses', help='match item')
    args = parser.parse_args(args)
    if args.items:
        d = vars(args)
        d['items'] = args.items.strip().split(',')
    return args

def create_test_args():
    args = create_args(['items', 'output2', '--match_sunglasses','spectacle2','--match_skin','a', '--match_gender','f','--count','100','--match_beard'])
    return args

if __name__ == '__main__':
    args = create_args()
    db = run_combos3.create_db(args)
    run_matches()
    db = run_image3.create_db(db,args,False)
    run_random()
    
"""
Testing
args = create_test_args()
db = run_combos3.create_db(args)
run_matches()
db = run_image3.create_db(db,args,False)
run_random()
"""
