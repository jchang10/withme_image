import os, sys


items_path='items'

db = {
    'head'      :{'files':[],       'done':False},
    'eye'       :{'files':[],       'done':False},
    'eyebrow'   :{'files':[],       'done':False},
    'mouth'     :{'files':[],       'done':False},
    'facehair'  :{'files':['none'], 'done':False},
    'nose'      :{'files':[],       'done':False},
    'hair'      :{'files':['none'], 'done':False},
    'spectacle' :{'files':['none'], 'done':False},
    }

items=list(db.keys())

def create_db():
    for k in items:
        path = os.path.join(items_path, k+'s')
        for file in os.listdir(path):
            if file[-4:] == '.png':
                file = file[:-4]
                db[k]['files'].append(file)
    return db
    
def item_generator(path, index):
    """ Run through all combinations """
    if index == len(items):
        yield path
        return
    for filename in db[items[index]]['files']:
        newpath = str.join('-', (path, filename))
        yield from item_generator(newpath, index+1)

def flat_generator(path, index):
    """ Just run through all the items """
    if index == len(items):
        yield path
        return
    if db[items[index]]['done']:
        filename = db[items[index]]['files'][0]
        newpath = str.join('-', (path, filename))
        yield from flat_generator(newpath, index+1)
        return
    for filename in db[items[index]]['files']:
        newpath = str.join('-', (path, filename))
        yield from flat_generator(newpath, index+1)
    db[items[index]]['done'] = True

count = 0            
def item_recurse(path, index):
    """ Same as item_generator() but done recurisvely """
    global count
    if index == len(items):
        print(count,path,sep='')
        count +=1
        return
    for filename in db[items[index]]['files']:
        newpath = str.join('-', (path, filename))
        item_recurse(newpath, index+1)
            
def run():
    for i, item in enumerate(item_generator('', 0)):
        print(i, item, sep='')

def run_recurse():
    item_recurse('', 0)

def run_flat():
    for i, item in enumerate(flat_generator('', 0)):
        print(i, item, sep='')

if __name__ == '__main__':
    assert len(sys.argv) > 1, "Items path argument is missing."
    items_path=sys.argv[1] 
    assert os.path.exists(items_path), "Given items path does not exist."
    create_db()
    #run()
    #run_recurse()
    run_flat()
    
