"""
run_combos2.py - run through the different combinations for face item parts.
"""

import argparse
import copy, os, re, sys
assert sys.version.startswith('3.6'), "Python version 3.6 is required"

import run_combos3
import run_image3

DEBUG=True

db = 'test'

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

def _match_item(item, matches, files_or_colors='files'):
    if not matches:
        return
    files = item[files_or_colors]
    for filename, file in list(files.items()):
        if filename == matches:
            pass
        elif type(matches) is str and matches.startswith('re'):
            try:
                if re.search(matches[2:], filename):
                    pass
                else:
                    del files[filename]
            except:
                print('regular expression failed:',matches,'for items:',items)
        elif filename not in matches:
            del files[filename]

def run_matches():
    # skin and gender matches can occur on a lot of items
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

    # age matches only hair color
    if args.match_age:
        if args.match_age > 60:
            _match_item(db['hair'], 'white', 'colors')
        else:
            _match_item(db['hair'], 're^(?!white)', 'colors')

    if args.match_facehair == 'goatee':
        _match_item(db['facehair'], 'facehair5')
    elif args.match_facehair == 'beard':
        _match_item(db['facehair'], 'facehair1')
    elif args.match_facehair == 'mustache':
        _match_item(db['facehair'], 'facehair0')
    else:
        _match_item(db['facehair'], 'none,facehair2,facehair3')
            
    if args.match_sunglasses:
        _match_item(db['spectacle'], 'spectacle2')
    elif args.match_eyeglasses:
        _match_item(db['spectacle'], 'spectacle0,spectacle1,spectacle3')
    else:
        _match_item(db['spectacle'], 'none')
        
    if args.match_bald:
        _match_item(db['hair'], 'none')
    else:
        _match_item(db['hair'], 're^(?!none)')

def create_random_path():
    from random import randint
    path = [str(args.numid)] if args.numid else ['1']
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
    im = run_image3.create_image_from_line(line, args, db)
    return im

def create_random(count):
    for i in range(0,count):
        create_random_image()

def run_random(count,args_list):
    global db, args
    args = create_args(args_list)
    db = run_combos3.create_db(args)
    run_matches()
    run_image3.init_db(db,args,False)
    create_random(count)
        
def create_args(args=None):
    parser = argparse.ArgumentParser(description='Images infile processor')
    parser.add_argument('items_path', metavar='items-path', default='items',
                        help='must be a directory')
    parser.add_argument('output_path', metavar='output', default='output',
                        help='must be a directory')
    parser.add_argument('--count', default=-1, type=int,
                        help='max count')
    parser.add_argument('--items',  help='comma separated list of items to process. rest will be "none".'
                        'e.g. --items "head,nose,eye"')
    parser.add_argument('--numid', help='optional number prefix')
    parser.add_argument('--match_skin', help='match item')
    parser.add_argument('--match_gender', help='match item')
    parser.add_argument('--match_age', help='match item', type=int)
    parser.add_argument('--match_facehair', help='can be "mustache, goatee, beard"')
    parser.add_argument('--match_bald', help='match item', default=False, action="store_true")
    parser.add_argument('--match_eyeglasses', help='match item', default=False, action="store_true")
    parser.add_argument('--match_sunglasses', help='match item', default=False, action="store_true")
    args = parser.parse_args(args)
    if args.items:
        d = vars(args)
        d['items'] = args.items.strip().split(',')
    return args

def create_test_args():
    args = create_args(['items', 'output2', '--match_sunglasses','spectacle2','--match_skin','a', '--match_gender','f','--count','100'])
    return args

if __name__ == '__main__':
    args = create_args()
    db = run_combos3.create_db(args)
    run_matches()
    run_image3.init_db(db,args,False)
    create_random(count)
    
"""
Testing
args = create_test_args()
db = run_combos3.create_db(args)
run_matches()
run_image3.init_db(db,args,False)
create_random(10)
"""
