import argparse
import os, sys
assert sys.version.startswith('3.6'), "Python version 3.6 is required"

db = {
    'skin'      :{'files':{},       'done':False},
    'head'      :{'files':{},       'done':False},
    'eye'       :{'files':{},       'done':False},
    'eyebrow'   :{'files':{},       'done':False},
    'mouth'     :{'files':{},       'done':False},
    'facehair'  :{'files':{'none':{}}, 'done':False},
    'nose'      :{'files':{},       'done':False},
    'hair'      :{
        'files':{
            'none':{},
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
    }, 'done':False },
    'spectacle' :{'files':{'none':{}}, 'done':False},
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
            
def item_generator(path, index):
    """ Run through all combinations """
    if index == len(item_keys):
        yield path
        return
    key = item_keys[index]
    item = db[item_keys[index]]
    files = item['files']
    for filename in files:
        if key == 'head':
            skin = path[0][-1]
            #skip if the skin does not match
            if filename[-2] != skin:
                continue
        if key == 'nose':
            skin = path[0][-1]
            # match light skin noses
            if skin in ('a','b') and filename[-2] != 'e':
                continue
            # match dark skin noses
            if skin in ('c','d') and filename[-2] != 'b':
                continue
        if key == 'mouth':
            skin = path[0][-1]
            if skin in ('a','b') and filename[-2] != 'h':
                continue
            if skin in ('c','d') and filename[-2] != 'b':
                continue
        if key == 'hair':
            facehair = path[5]
            # if hair is female and has facehair, skip 
            if 'gender' in files[filename] and facehair != 'none':
                continue
            # skip if the filename ends in 'b'. only used for back hair
            if filename[-1] == 'b':
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
    
