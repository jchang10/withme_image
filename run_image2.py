import argparse
import os, sys
assert sys.version.startswith('3.6'), "Python version 3.6 is required"
from PIL import Image, ImageEnhance

DEBUG=False
WIDTH=1150
HEIGHT=1350

db = {
    'skin'      :{'offset':(-25, 500),
                  'files':{
                      'name':{'image':'image-object'}
                  }
    },
    'head'      :{'offset':(72, 238),
                  'files':{
                      'name':{'image':'image-object'}
                  }
    },
    'eye'       :{'offset':(72, 499),
                  'files':{
                      'name':{'image':'image-object'}
                  }
    },
    'eyebrow'   :{'offset':(72, 470),
                  'files':{
                      'name':{'image':'image-object'}
                  }
    },
    'mouth'     :{'offset':(72, 870),
                  'files':{
                      'name':{'image':'image-object'}
                  }
    },
    'facehair'  :{'offset':(72, 680),
                  'files':{
                      'name':{'image':'image-object'}
                  }
    },
    'nose'      :{'offset':(421, 635),
                  'files':{
                      'name':{'image':'image-object'}
                  }
    },
    'hair'      :{'offset':(-29, 38),
                  'files':{
                      'name':{'image':'image-object'}
                  }, 
                  'colors':{
                      'orig':{'skin':'a,c'},
                      'black':{'skin':'b,c,d'}
                  }
    },
    'spectacle' :{'offset':(71, 509),
                  'files':{
                      'name':{'image':'image-object'}
                  },
    }
}
item_keys=list(db.keys())

def create_db():
    for k in item_keys:
        for file in os.listdir(os.path.join(args.items_path, k+'s')):
            if file[-4:] == '.png':
                name = file[:-4]
                path = os.path.join(args.items_path, k+'s', file)
                image = Image.open(path)
                if k == 'hair' and file[-5:] == 'b.png':
                    #back of the hair file
                    name = file[:-5]
                    db[k]['files'][name]['back'] = image
                else:
                    db[k]['files'][name] = {'image':image}
    return db

def get_color_adjust(image, color):
    newim = None
    if color == 'black':
        newim = Image.new('LA', image.size)
        newim.paste(image, (0,0), image)
        newim = newim.convert('RGBA')
        newim = ImageEnhance.Brightness(newim).enhance(0.5)
    assert newim != None, "get_color_adjust failure"
    return newim

def process_line(line):
    index, *items = line.split('-')
    print(index, end=' ', flush=True)
    image = Image.new('RGB', (WIDTH, HEIGHT), color='white')
    trans = Image.new('RGBA', (WIDTH, HEIGHT))
    skin = items[0][-1]
    for i, name in enumerate(items):
        k = item_keys[i]
        if name in db[k]['files']:
            file = db[k]['files'][name]
            im = file['image']
            backim = db[k]['files'][name].get('back')
            colors = db[k].get('colors')
            if colors:
                for k2,color in colors.items():
                    if skin in color.get('skin',''):
                        # no color adjust needed
                        if k2 == 'orig':
                            continue
                        newim = file.get(k2)
                        if not newim:
                            newim = get_color_adjust(im, k2)
                            file[k2] = newim
                        items[i] = items[i]+'!'+k2
                        im = newim
                        if backim:
                            newbackim = file.get(k2+'!back')
                            if not newbackim:
                                newbackim = get_color_adjust(backim, k2)
                                file[k2+'!back'] = newbackim
                            backim = newbackim
                        trans.paste(im, db[k]['offset'], im)
                        if backim:
                            image.paste(backim, db[k]['offset'], backim)
                        image.paste(trans, (0,0), trans)
                        line = str(index)+'-'+'-'.join(items)
                        path = os.path.join(args.output_path,line+'.png')
    image.paste(trans, (0,0), trans)
    line = str(index)+'-'+'-'.join(items)
    path = os.path.join(args.output_path,line+'.png')
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
    i = 0
    while size and (args.count != -1 and i < args.count):
        size = size-1
        ri = randint(0, size)
        i += 1
        print(str(i)+'.', end='')
        process_line(outputs[ri])
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


if __name__ == '__main__':
    args = create_args()
    create_db()
    process_random(args.infile_path)


