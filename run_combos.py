import argparse
import os, sys
assert sys.version.startswith('3.6'), "Python version 3.6 is required"

db = {
    'skin'      :{'done':False,
                  'files':{}},
    'head'      :{'done':False,
                  'files':{}},
    'eye'       :{'done':False,
                  'files':{
                      'eye7':{'gender':'m', 'skin':'c'},
                      'eye9':{'gender':'m', 'skin':'c'},
                  }},
    'eyebrow'   :{'done':False,
                  'files':{}},
    'mouth'     :{'done':False,
                  'files':{
                      'mouth0':{'gender':'m'},
                      'mouth1':{'gender':'m'},
                      'mouth2':{'gender':'f'},
                      'mouth3':{'gender':'f'},
                      'mouth4':{'gender':'f'},
                      'mouth7':{'gender':'f'},
                      'mouthb0':{'gender':'m'},
                      'mouthb1':{'gender':'m'},
                      'mouthb2':{'gender':'f'},
                      'mouthb3':{'gender':'f'},
                      'mouthb4':{'gender':'f'},
                      'mouthb7':{'gender':'f'},
                  }},
    'facehair'  :{'done':False,
                  'files':{'none':{}}},
    'nose'      :{'done':False,
                  'files':{}},
    'hair'      :{'done':False,
                  'files':{
                      'none':{},
                      'hair0':{'gender':'m'},
                      'hair1':{'gender':'m'},
                      'hair2':{'gender':'m'},
                      'hair3':{'gender':'m'},
                      'hair4':{'gender':'m'},
                      'hair7':{'gender':'f'},
                      'hair9':{'gender':'f'},
                      'hair10':{'gender':'f'},
                      'hair11':{'gender':'f'},
                      'hair12':{'gender':'f'},
                      'hair13':{'gender':'f'},
                      'hair14':{'gender':'f'},
                      'hair15':{'gender':'f'},
                      'hair16':{'gender':'f'},
                      'hair17':{'gender':'f'},
                      'hair19':{'gender':'f'},
                  }},
    'spectacle' :{'done':False,
                  'files':{'none':{}}},
}

item_keys=list(db.keys())

def create_db():
    for k in item_keys:
        path = os.path.join(args.items_path, k+'s')
        for filename in os.listdir(path):
            if filename[-4:] == '.png':
                name = filename[:-4]
                files = db[k]['files']
                if name in files:
                    pass
                else:
                    files[name] = {}
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

def get_attr(myfile, attribute):
    """ Return attribute if exists, or None """
    return myfile.get(attribute, None)

def item_generator(path, index):
    """ Run through all combinations """
    if index == len(item_keys):
        yield path
        return
    item = item_keys[index]
    item = db[item_keys[index]]
    files = item['files']
    for filename in files:
        currfile = files[filename]
        if item == 'head':
            skin = path[0][-1]
            #skip if the skin does not match
            if filename[-2] != skin:
                continue
        if item == 'eye':
            skin = path[0][-1]
            # eyes match skin
            if get_attr(currfile, 'skin') != None:
                if get_attr(currfile, 'skin') != skin:
                    continue
        if item == 'nose':
            skin = path[0][-1]
            # match light skin noses
            if skin in ('a','b') and filename[-2] != 'e':
                continue
            # match dark skin noses
            if skin in ('c','d') and filename[-2] != 'b':
                continue
        if item == 'mouth':
            skin = path[0][-1]
            if skin in ('a','b') and filename[-2] != 'h':
                continue
            if skin in ('c','d') and filename[-2] != 'b':
                continue
        if item == 'facehair':
            # skip if has facehair and mouth is female
            mouth = path[4]
            if filename != 'none':
                if get_attr(db['mouth']['files'][mouth], 'gender') == 'f':
                    continue
        if item == 'hair':
            # skip if the filename ends in 'b'. only used for back hair
            if filename[-1] == 'b':
                continue
            if get_attr(currfile, 'gender') != None:
                # if hair is female and has facehair, skip 
                facehair = path[5]
                if facehair != 'none' and get_attr(currfile, 'gender') == 'f':
                    continue
                # hair gender must match mouth gender
                mouth = path[4]
                if get_attr(db['mouth']['files'][mouth], 'gender'):
                    if get_attr(db['mouth']['files'][mouth], 'gender') != get_attr(currfile, 'gender'):
                        continue
        newpath = path + [filename]
        yield from item_generator(newpath, index+1)

def run_items():
    for i, filenames in enumerate(item_generator([], 0)):
        print(i, '-', '-'.join(filenames), sep='')

def run_recurse():
    item_recurse('', 0)

def create_args(args=None):
    parser = argparse.ArgumentParser(description='Images infile processor')
    parser.add_argument('items_path', metavar='items', default='items',
                        help='must be a directory')
    return parser.parse_args(args)

if __name__ == '__main__':
    args = create_args()
    create_db()
    run_items()
    #run_recurse()

