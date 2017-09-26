import os, sys
assert sys.version.startswith('3.6'), "Python version 3.6 is required"

from PIL import Image

DEBUG=False
WIDTH=1200
HEIGHT=1300

infile_path=None
items_path='items'
output_path='output_path'

db = {
    'skin'      :{'file':{'name':'to-image'}, 'offset':(-25, 500)},
    'head'      :{'file':{'name':'to-image'}, 'offset':(72, 238)},
    'eye'       :{'file':{'name':'to-image'}, 'offset':(72, 499)},
    'eyebrow'   :{'file':{'name':'to-image'}, 'offset':(72, 470)},
    'mouth'     :{'file':{'name':'to-image'}, 'offset':(72, 888)},
    'facehair'  :{'file':{'name':'to-image'}, 'offset':(72, 700)},
    'nose'      :{'file':{'name':'to-image'}, 'offset':(421, 657)},
    'hair'      :{'file':{'name':'to-image'}, 'offset':(-29, 38),
                  'back':{'file':{'name':'to-image'}}},
    'spectacle' :{'file':{'name':'to-image'}, 'offset':(71, 509)},
}
item_keys=list(db.keys())

def create_db():
    for k in item_keys:
        for file in os.listdir(os.path.join(items_path, k+'s')):
            if file[-4:] == '.png':
                name = file[:-4]
                path = os.path.join(items_path, k+'s', file)
                image = Image.open(path)
                if k == 'hair' and file[-5:] == 'b.png':
                    #back of the hair file
                    db[k]['back'][name] = image
                else:
                    db[k]['file'][name] = image
    return db

def process_line(line):
    index, *items = line.split('-')
    print(index, end=' ', flush=True)
    image = Image.new('RGB', (WIDTH, HEIGHT), color='white')
    trans = Image.new('RGBA', (WIDTH, HEIGHT))
    for i, name in enumerate(items):
        k = item_keys[i]
        if name in db[k]['file']:
            im = db[k]['file'][name]
            trans.paste(im, db[k]['offset'], im)
        back_name = name+'b'
        if back_name in db[k].get('back', []):
            im = db[k]['back'][back_name]
            image.paste(im, db[k]['offset'], im)
    image.paste(trans, (0,0), trans)
    path = os.path.join(output_path,line+'.png')
    if DEBUG:
        print('saving image '+path)
    else:
        im2 = image.resize((int(image.width/4),int(image.height/4)), Image.ANTIALIAS)
        im2.save(path)

def process_infile(infile_path):
    with open(infile_path) as infile:
        for line in infile:
            process_line(line.rstrip())
    print()

outputs = []
def process_random(infile_path):
    print("Reading infile")
    line = None
    index = -1
    with open(infile_path) as infile:
        for line in infile:
            index, _ = line.split('-', maxsplit=1)
            outputs.append(line.rstrip())
    print("Done with infile. Index =",index)
    print("Processing images ...")
    from random import randint
    size = len(outputs)
    while size:
        size = size-1
        ri = randint(0, size)
        process_line(outputs[ri])
        outputs[ri] = outputs[size]
    
if __name__ == '__main__':
    assert len(sys.argv) == 4, "3 args missing. <infile> <items> <output>"
    _, infile_path, items_path, output_path = sys.argv
    assert os.path.isfile(infile_path), "Given <infile> must be a dir."
    assert os.path.isdir(items_path), "Given <items> must be a dir."
    assert os.path.isdir(output_path), "Given <output> must be a dir."
    create_db()
    process_random(infile_path)
    
