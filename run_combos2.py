"""
run_combos2.py - run through the different combinations for face item parts.
"""

import argparse
import os, re, sys
assert sys.version.startswith('3.6'), "Python version 3.6 is required"

db = {
    'skin'      :{'done':False, 'has_skin':True,
                  'files':{
                      'skina':{'skin':'a'},
                      'skinb':{'skin':'b'},
                      'skinc':{'skin':'c'},
                      'skind':{'skin':'d'},
                  }},
    'head'      :{'done':False, 'has_skin':True,
                  'files':{
                      'heada0':{'skin':'a'},
                      'heada1':{'skin':'a'},
                      'heada2':{'skin':'a'},
                      'heada3':{'skin':'a'},
                      'heada4':{'skin':'a'},
                      'heada5':{'skin':'a'},
                      'headb0':{'skin':'b'},
                      'headb1':{'skin':'b'},
                      'headb2':{'skin':'b'},
                      'headb3':{'skin':'b'},
                      'headb4':{'skin':'b'},
                      'headb5':{'skin':'b'},
                      'headc0':{'skin':'c'},
                      'headc1':{'skin':'c'},
                      'headc2':{'skin':'c'},
                      'headc3':{'skin':'c'},
                      'headc4':{'skin':'c'},
                      'headc5':{'skin':'c'},
                      'headd0':{'skin':'d'},
                      'headd1':{'skin':'d'},
                      'headd2':{'skin':'d'},
                      'headd3':{'skin':'d'},
                      'headd4':{'skin':'d'},
                      'headd5':{'skin':'d'},
                  }},
    'eye'       :{'done':False, 'has_gender':True, 'has_skin':True,
                  'files':{
                      'eye0':{'skin':'a,  c,d'},
                      'eye1':{'skin':'a,  c,d'},
                      'eye1':{'skin':'a,  c,d'},
                      'eye2':{'skin':'a,  c,d'},
                      'eye3':{'skin':'a,  c,d'},
                      'eye4':{'skin':'a,  c,d'},
                      'eye5':{'skin':'  b',       'gender':'m'},
                      'eye6':{'skin':'a,  c,d'},
                      'eye7':{'skin':'  b',       'gender':' f'},
                      'eye8':{'skin':'  b,c',     'gender':'m'},
                      'eye9':{'skin':'  b,c',     'gender':' f'},
                      'eye10':{'skin':'a, c,d',   'gender':' f'},
                  }},
    'eyebrow'   :{'done':False,
                  'files':{}},
    'mouth'     :{'done':False, 'has_gender':True,
                  'files':{
                      'mouth0':{'gender':'m'},
                      'mouth1':{'gender':'m'},
                      'mouth2':{'gender':'  f'},
                      'mouth3':{'gender':'  f'},
                      'mouth4':{'gender':'  f'},
                      'mouth7':{'gender':'  f'},
                      'mouthb0':{'gender':'m'},
                      'mouthb1':{'gender':'m'},
                      'mouthb2':{'gender':' f'},
                      'mouthb3':{'gender':' f'},
                      'mouthb4':{'gender':' f'},
                      'mouthb7':{'gender':' f'},
                  }},
    'facehair'  :{'done':False,'has_gender':True,
                  'files':{
                      'none':{'name':'none'},
                      'facehair0':{'gender':'m'},
                      'facehair1':{'gender':'m'},
                      'facehair2':{'gender':'m'},
                      'facehair3':{'gender':'m'},
                      'facehair4':{'gender':'m'},
                      'facehair5':{'gender':'m'},
                  }},
    'nose'      :{'done':False, 'has_skin':True,
                  'files':{
                      'nose0':{'skin':'a,b'},
                      'nose1':{'skin':'a,b'},
                      'nose2':{'skin':'a,b'},
                      'nose3':{'skin':'a,b'},
                      'nose4':{'skin':'a,b'},
                      'nose5':{'skin':'a,b'},
                      'nose6':{'skin':'a,b'},
                      'noseb0':{'skin':'  c,d'},
                      'noseb1':{'skin':'  c,d'},
                      'noseb2':{'skin':'  c,d'},
                      'noseb3':{'skin':'  c,d'},
                      'noseb4':{'skin':'  c,d'},
                      'noseb5':{'skin':'  c,d'},
                      'noseb6':{'skin':'  c,d'},
                  }},
    'hair'      :{'done':False,'has_gender':True, 'has_skin':True, 'has_color':True,
                  'files':{
                      'none':{'name':'none', 'gender':'m'}, # bald heads only male
                      'hair0':{'gender':'m',},# 'skin':'a,b,c,d'},
                      'hair1':{'gender':'m',},# 'skin':'a,b,c,d'},
                      'hair2':{'gender':'m',},# 'skin':'a,b,c,d'},
                      'hair3':{'gender':'m',},# 'skin':'a,b,c,d'},
                      'hair4':{'gender':'m',},# 'skin':'a,b,c,d'},
                      'hair5':{'gender':'m',},# 'skin':'a,b,c,d'},
                      'hair6':{'gender':'m',},# 'skin':'a,b,c,d'},
                      'hair7':{'gender':' f', 'skin':'a,b,c'},
                      'hair9':{'gender':' f', 'skin':'a,b,c,d'},
                      'hair10':{'gender':'f', 'skin':'a,b,c,d'},
                      'hair11':{'gender':'f', 'skin':'a,b,c'},
                      'hair12':{'gender':'f', 'skin':'a,b,c'},
                      'hair13':{'gender':'f', 'skin':'a,b,c'},
                      'hair14':{'gender':'f', 'skin':'a,b,c,d'},
                      'hair15':{'gender':'f', 'skin':'a,b,c,d'},
                      'hair16':{'gender':'f', 'skin':'a,b,c,d'},
                      'hair17':{'gender':'f', 'skin':'a,b,c,d'},
                      'hair19':{'gender':'f', 'skin':'a,b,c,d'},
                  },
                  'colors':{
                      'orig':{'skin':      'a,  c'},
                      'black':{'skin':     '  b,c,d'},
                      'blonde':{'skin':    'a,  c'},
                      'darkbrown':{'skin': 'a,  c'},
                      'white':{'skin':     'a,b,c,d'},
                  }
    },
    'spectacle' :{'done':False,
                  'files':{'none':{'name':'none'}}},
}
item_keys=list(db.keys())

def create_db():
    for k in item_keys:
        # skip items not in argument list
        if args.items and k not in args.items:
            db[k]['files'].clear()
            db[k]['files']['none'] = {'done':False, 'name':'none'}
            continue
        path = os.path.join(args.items_path, k+'s')
        for filename in os.listdir(path):
            if filename[-4:] == '.png':
                name = filename[:-4]
                files = db[k]['files']
                if name in files:
                    files[name]['name'] = name
                else:
                    files[name] = {'name':name}
    return db
    
count = 0            
def item_recurse(path, index):
    """ Same as item_generator() but done recurisvely """
    global count
    if index == len(item_keys):
        print(count,path,sep='')
        count +=1
        return
    for filename in db[item_keys[index]]['files']:
        newpath = str.join('-', (path, filename))
        item_recurse(newpath, index+1)

def gender_match(path, currfile):
    a = currfile.get('gender')
    for i, (pathname, file) in enumerate(path):
        b = file.get('gender')
        if not a:
            continue
        if not b:
            continue
        if a.strip() == b.strip():
            continue
        else:
            return False
    return True

def get_skin(path):
    if len(path) > 0:
        (name, file) = path[0]
        return name[-1]
    else:
        return None

import re
pattern = re.compile(r'[ ,]+')

def skin_match(path, currfile):
    seta = None
    if currfile.get('skinset', False):
        seta = currfile['skinset']
    else:
        a = currfile.get('skin')
        seta = set(pattern.split(a.strip())) if a else set()
        currfile['skinset'] = seta
    if get_skin(path) == None:
        return True
    for i, (pathname, file) in enumerate(path):
        if not db[item_keys[i]].get('has_skin'):
            return True
        setb = file['skinset']
        if len(seta) == 0:
            continue
        if len(setb) == 0:
            continue
        if len(seta & setb) > 0:
            continue
        else:
            return False
    return True

def item_generator(path, index):
    """ Run through all combinations """
    if index == len(item_keys):
        yield path
        return
    key = item_keys[index]
    item = db[item_keys[index]]
    files = item['files']
    for filename, currfile in files.items():
        if item.get('has_gender'):
            if not gender_match(path, currfile):
                continue
        if item.get('has_skin'):
            if not skin_match(path, currfile):
                continue
        if key == 'hair':
            # skip if the filename ends in 'b'. only used for back hair
            if filename[-1] == 'b':
                continue
        if item.get('has_color') and filename != 'none':
            skin = get_skin(path)
            for k, color in item['colors'].items():
                if skin in color.get('skin',''):
                    newname = filename if k == 'orig' else filename+'!'+k
                    yield from item_generator(path + [(newname,currfile)], index+1)
            continue
        yield from item_generator(path + [(filename, currfile)], index+1)
        
def run_items():
    for i, path in enumerate(item_generator([], 0)):
        print(i, '-', '-'.join([p[0] for p in path]), sep='')

def run_recurse():
    item_recurse('', 0)

def create_args(args=None):
    parser = argparse.ArgumentParser(description='Images infile processor')
    parser.add_argument('items_path', metavar='items-path', default='items',
                        help='must be a directory')
    parser.add_argument('--items', 
                        help='comma separated list of items to process. rest will be "none".'
                        'e.g. --items "head,nose,eye"')
    args = parser.parse_args(args)
    if args.items:
        d = vars(args)
        d['items'] = args.items.strip().split(',')
    return args

if __name__ == '__main__':
    args = create_args()
    create_db()
    run_items()
    #run_recurse()

