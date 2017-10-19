"""
run_image2.py - process input file. assemble each line into a face.
"""

import argparse
import os, sys, copy
assert sys.version.startswith('3.6'), "Python version 3.6 is required"
from PIL import Image, ImageEnhance

from pilutil import new_hair_color

DEBUG=False
WIDTH=1150
HEIGHT=1350
SAVE_FORMAT='.jpg'

db = {
    'skin'      :{'offset':(-25, 500),
                  'files':{'name':{'image':'image-object'}}
    },
    'head'      :{'offset':(72, 238),
                  'files':{'name':{'image':'image-object'}}
    },
    'eye'       :{'offset':(72, 499),
                  'files':{'name':{'image':'image-object'}}
    },
    'eyebrow'   :{'offset':(72, 470),
                  'files':{'name':{'image':'image-object'}}
    },
    'mouth'     :{'offset':(72, 870),
                  'files':{'name':{'image':'image-object'}}
    },
    'facehair'  :{'offset':(72, 680),
                  'files':{'name':{'image':'image-object'}}
    },
    'nose'      :{'offset':(421, 635),
                  'files':{'name':{'image':'image-object'}}
    },
    'hair'      :{'offset':(-29, 38),
                  'files':{'name':{'image':'image-object'}}
    },
    'spectacle' :{'offset':(71, 509),
                  'files':{'name':{'image':'image-object'}},
    }
}
item_keys=list(db.keys())
args = None
image_db = db

def create_db(args):
    newdb = copy.deepcopy(db)
    init_db(newdb, args)
    return newdb
    
def init_db(db,args=args,newfiles=True):
    """
    initialize the db.
    db: db
    args: args
    newfiles: whether any new found files should be added to the db or not.
    """
    for k in item_keys:
        for file in os.listdir(os.path.join(args.items_path, k+'s')):
            if file[-4:] == '.png':
                name = file[:-4]
                path = os.path.join(args.items_path, k+'s', file)
                image = Image.open(path)
                if k == 'hair' and file[-5:] == 'b.png':
                    #back of the hair file
                    name = file[:-5]
                    if newfiles or name in db[k]['files']:
                        db[k]['files'][name]['back'] = image
                    #remove the unused back hair file
                    if name+'b' in db[k]['files']: 
                        del db[k]['files'][name+'b']
                else:
                    if newfiles or name in db[k]['files']:
                        db[k]['files'][name] = {'image':image}

def new_color_adjust(image, color):
    newim = new_hair_color(image, color)
    assert newim != None, "new_color_adjust failure"
    return newim

def create_image_from_line(line,args=args,db=db):
    index, *items = line.split('-')
    image = Image.new('RGB', (WIDTH, HEIGHT), color='white')
    trans = Image.new('RGBA', (WIDTH, HEIGHT))
    skin = items[0][-1]
    subname = None
    for i, name in enumerate(items):
        k = item_keys[i]
        # skip the placeholder
        if name == 'none':
            continue
        if name not in db[k]['files']:
            # color?
            if '!' not in name:
                # skip this line entirely
                print(f'Missing file {name}. Skipping line entirely: {line}')
                break
            (subname, color) = name.split('!')
            assert subname in db[k]['files'], 'Could not process color for line: '+line
        file = db[k]['files'].get(name)
        im, backim = None, None
        if file:
            im = file['image']
            backim = file.get('back')
        else:
            # create the color adjusted image file
            im = db[k]['files'][subname]['image']
            backim = db[k]['files'][subname].get('back')
            assert im, 'Image is missing for line: '+line
            im = new_color_adjust(im, color)
            db[k]['files'][name] = {'image':im}
            if backim:
                backim = new_color_adjust(backim, color)
                db[k]['files'][name]['back'] = backim
        trans.paste(im, image_db[k]['offset'], im)
        if backim:
            image.paste(backim, image_db[k]['offset'], backim)
    image.paste(trans, (0,0), trans)
    line = str(index)+'-'+'-'.join(items)
    path = os.path.join(args.output_path,line+SAVE_FORMAT)
    if DEBUG:
        print('saving image '+path)
    else:
        im2 = image.resize((int(image.width/4),int(image.height/4)), Image.ANTIALIAS)
        im2.save(path)
    return im2

def process_infile(infile_path):
    with open(infile_path) as infile:
        for line in infile:
            create_image_from_line(line.rstrip())
    print()

outputs = []
def process_random(infile_path,args=args):
    from random import randint
    print("Reading infile")
    line = None
    index = -1
    with open(infile_path) as infile:
        for line in infile:
            index, _ = line.split('-', maxsplit=1)
            outputs.append(line.rstrip())
    print("Done with infile. Index =",index)
    print("Processing images ...")
    size = len(outputs)
    for i in range(0, args.count):
        if size == 0:
            break
        size = size-1
        ri = randint(0, size)
        print(str(i)+'.', end='')
        create_image_from_line(outputs[ri],args)
        outputs[ri] = outputs[size]
        

def create_args(args=None):
    parser = argparse.ArgumentParser(description='Images processor')
    parser.add_argument('infile_path', metavar='infile',
                        help='must be a file')
    parser.add_argument('items_path', metavar='items', default='items',
                        help='must be a directory')
    parser.add_argument('output_path', metavar='output', default='output',
                        help='must be a directory')
    parser.add_argument('--count', default=-1, type=int,
                        help='max count')
    return parser.parse_args(args)


def create_test_args():
    args = create_args(['/tmp/runtest.txt', 'items', 'output', '--count', '10'])
    return args

if __name__ == '__main__':
    args = create_args()
    init_db(db, args)
    process_random(args.infile_path)


