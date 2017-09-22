
import os, sys

from PIL import Image

DEBUG=False
WIDTH=1200
HEIGHT=1300

infile_path=None
items_path='items'
output_path='output_path'

db = {
    'head'      :{'file':{'name':None}, 'offsets':(72, 238)},
    'eye'       :{'file':{'name':None}, 'offsets':(72, 448)},
    'eyebrow'   :{'file':{'name':None}, 'offsets':(72, 411)},
    'mouth'     :{'file':{'name':None}, 'offsets':(212, 966)},
    'facehair'  :{'file':{'name':None}, 'offsets':(212, 816)},
    'nose'      :{'file':{'name':None}, 'offsets':(421, 667)},
    'hair'      :{'file':{'name':None}, 'offsets':(-29, 38)},
    'spectacle' :{'file':{'name':None}, 'offsets':(71, 467)},
    }
item_keys=list(db.keys())

def create_db():
    for k in item_keys:
        for file in os.listdir(os.path.join(items_path, k+'s')):
            if file[-4:] == '.png':
                name = file[:-4]
                path = os.path.join(items_path, k+'s', file)
                image = Image.open(path)
                db[k]['file'][name] = image
    return db

def process_line(line):
    index, *items = line.split('-')
    print(index, end=' ', flush=True)
    image = Image.new('RGB', (WIDTH, HEIGHT), color='white')
    for i, name in enumerate(items):
        k = item_keys[i]
        if name in db[k]['file']:
            im = db[k]['file'][name]
            image.paste(im, db[k]['offsets'], im)
    path = os.path.join(output_path,line+'.png')
    if DEBUG: print('saving image '+path)
    if not DEBUG: image.save(path)

if __name__ == '__main__':
    assert len(sys.argv) == 4, "3 args missing. <infile> <items> <output>"
    _, infile_path, items_path, output_path = sys.argv
    assert os.path.isfile(infile_path), "Given <infile> must be a dir."
    assert os.path.isdir(items_path), "Given <items> must be a dir."
    assert os.path.isdir(output_path), "Given <output> must be a dir."
    create_db()
    with open(infile_path) as infile:
        for line in infile:
            process_line(line.rstrip())
    print()
