"""
       - python run_train.py download <output_path>
         - download the input urls
       - python run_train.py facecrop <api_key> <input_path>
       - python run_train.py model create <api_key> [<concept_list>]
       - python run_train.py input <input_path> [<concept_list>] [<not_concept_list>]
       - python run_train.py test


"""

import argparse, datetime, io, json, os, re, urllib
import PIL, PIL.ImageDraw

import boto3
from clarifai.rest import ClarifaiApp, Image, Concept

from pynamodb.attributes import UnicodeAttribute, BooleanAttribute, \
    UTCDateTimeAttribute, NumberAttribute, MapAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.models import Model

from colorama_util import YELLOW, RED
from gen_util import chunks
from input_urls4 import input_urls
import urllib_util,pilutil

DEBUG=True
MYCACHE_FILENAME='mycache.json'

REGION='us-west-2'
BUCKET='withmelabs-faces'
os.environ['AWS_PROFILE']='imvu'
os.environ['STAGE'] = 'dev'

class FaceImageUrls(Model):
    class Meta:
        table_name = os.environ.get('STAGE', 'dev') + '.FaceImageUrls'
        region = boto3.Session().region_name
        #host = 'http://localhost:8000' if not os.environ.get('LAMBDA_TASK_ROOT') else None
    numid = NumberAttribute()
    url = UnicodeAttribute(hash_key=True)
    created_date = UTCDateTimeAttribute(default=datetime.datetime.now())
    result = MapAttribute()

    @staticmethod
    def mycreate_table():
        FaceImageUrls.create_table(read_capacity_units=1, write_capacity_units=1)
 
class MyCache(dict):

    @staticmethod
    def open(filename=MYCACHE_FILENAME):
        return MyCache(filename)

    def __init__(self, filename):
        self.filename = filename
        self.myinit(filename)
    
    def myinit(self, filename):
        if os.path.exists(filename):
            with open(filename,'r') as fp:
                mydict = json.load(fp)
                self.update(mydict)

    def save(self):
        with open(self.filename,'w') as fp:
            json.dump(self,fp)

def create_parser():
    parser = argparse.ArgumentParser(description='Image trainer')
    subparsers = parser.add_subparsers(help='download urls')

    download_parser = subparsers.add_parser('download', help='face cropping')
    copys3_parser = subparsers.add_parser('copys3', help='copy to s3')
    facecrop_parser = subparsers.add_parser('facecrop', help='face cropping')
    model_parser = subparsers.add_parser('model', help='model manipulation')
    input_parser = subparsers.add_parser('input', help='input manipulation')

    parser.add_argument('--dry-run', help='dry run', default=False, action="store_true")
    parser.add_argument('--s3', help='save to s3. default to saving locally.',
                        default=False, action="store_true")

    download_parser.set_defaults(cmd='download')
    download_parser.add_argument('output_path', help='must be a directory')
    download_parser.add_argument('--count', help='download only count files', type=int)
    download_parser.add_argument('--check-size', help='check downloaded image sizes', default=False, action="store_true")
    
    copys3_parser.set_defaults(cmd='copys3')
    copys3_parser.add_argument('input_path', help='must be a directory')
    copys3_parser.add_argument('--count', help='match item', type=int)
    
    facecrop_parser.set_defaults(cmd='facecrop')
    facecrop_parser.add_argument('api_key', help='Clarifai api_key')
    facecrop_parser.add_argument('input_path', help='must be a directory')
    
    parser.add_argument('--numid', help='optional number prefix')
    parser.add_argument('--match_skin', help='match item')
    parser.add_argument('--match_gender', help='match item')
    parser.add_argument('--match_age', help='match item', type=int)
    parser.add_argument('--match_facehair', help='can be "mustache, goatee, beard"')
    parser.add_argument('--match_bald', help='match item', default=False, action="store_true")
    parser.add_argument('--match_eyeglasses', help='match item', default=False, action="store_true")
    parser.add_argument('--match_sunglasses', help='match item', default=False, action="store_true")

    return parser
            
def create_args(args=None):
    parser = create_parser()
    args = parser.parse_args(args)
    if 'input_path' in args and not args.input_path.endswith('/'):
        d = vars(args)
        d['input_path'] = args.input_path+'/'
    return args

def create_test_args(cmd):
    if cmd == 'download':
        args = create_args(['download','train','--count','10'])
    if cmd == 'checksize':
        args = create_args(['download','train','--check-size'])
    elif cmd == 'copys3':
        args = create_args(['copys3','train'])
    elif cmd == 'facecrop':
        args = create_args(['facecrop','a7d4adb4103d4e0482981233770ef056','train'])
    else:
        assert False, 'No matching cmd'
    return args

def cmd_download():
    """
    download urls to output_path.
    for categories
      check dir exists?
      cleanurl = quoted url
      check file exists?
        if file exists skip unless --force flag is on
      download url
      save into file with cleanurl filename    
    """
    for category in input_urls:
        category_path = os.path.join(args.output_path, category)
        if os.path.isdir(category_path) is False:
            os.mkdir(category_path)
        if args.count:
            myurls = input_urls[category][:args.count]
        else:
            myurls = input_urls[category]
        for url in myurls:
            qurl = urllib.parse.quote(url, safe='')
            url_path = os.path.join(category_path, qurl)
            if os.path.isfile(url_path):
                print(f'URL already exists. Skipping... {os.path.join(category,qurl):.70}')
                continue
            print(f'Downloading... {url}')
            if not args.dry_run: urllib_util.save_url_to_file(url, url_path)

def gen_all_files(inpath):
    for root,dirs,files in os.walk(inpath, topdown=True):
        for name in files:
            if name.startswith('.'):
                continue
            path = os.path.join(root,name)
            yield path

def cmd_check_size():
    """
    check the image resolution. separate to pass and fail images.
    """
    pass_urls = []
    fail_urls = []
    for path in get_all_files(args.output_path):
        size = pilutil.image_size(url_path)
        if any(dim>min(CROP_SIZE) for dim in size):
            pass_urls.append(url_path)
        else:
            fail_urls.append(fail_urls)
            print(RED('  Image size too small.'))
    print('Pass urls:',len(pass_urls),'Fail urls:',len(fail_urls))

URL_PREFIX='https://s3-us-west-2.amazonaws.com/withmelabs-faces/'
FOLDER='train/'

def get_s3_keys():
    s3 = boto3.resource('s3')
    mybucket = s3.Bucket(BUCKET)
    mykeys = {}
    for file in mybucket.objects.filter(Prefix=FOLDER):
        mykeys[file.key] = 1
    return mykeys


patt = re.compile(r'^(\w+)/(\w+)/(.*)?')

def split_key(key):
    res = patt.match(key)
    if res:
        train,category,urlq = res[1],res[2],res[3]
        return train,category,urlq
    else:
        return None,None,None

def get_category_keys(keys):
    image_keys = {}
    for key in keys:
        train,category,urlq = split_key(key)
        if train is None:
            continue # probably a folder
        if '-' in category:
            continue # skip -facecrop folders
        if not urlq:
            continue
        image_keys[key] = {
            'train':train,
            'category':category,
            'urlq':urlq,
        }
    return image_keys

def cmd_copys3():
    """
    copy the local files to s3
    """

    all_keys = get_s3_keys()
    images = get_category_keys(all_keys)
    all_files = [path for path in gen_all_files(args.input_path) if path in images]

    if DEBUG: print(YELLOW('debug:'),"Number of files on S3:", len(images))
    if DEBUG: print(YELLOW('debug:'),"Number of files upload to S3:",len(all_files))

    s3 = boto3.resource('s3')
    mybucket = s3.Bucket(BUCKET)
    for file in all_files:
        print("Copying file to S3",f'{file:.70}')
        mybucket.upload_file(file, file, ExtraArgs={'ACL':'public-read'})
            
    """
    get category keys from s3
    only copy files that are not on s3:
      walk local directory tree
      check if s3object exists, remove from list
    copy remaining files to s3
    """

    
CROP_SIZE=(750,750)

def cmd_facecrop():
    """
    construct categories list

    for each key in s3
      is the facecrop cached?
      does the facecrop_file exist already? skip it.
    """
    def get_s3_urlqs(categories):
        for category in categories:
            prefixarg = f'{args.input_path}{category}/'
            results = paginator.paginate(Bucket=BUCKET, Delimiter='/', Prefix=prefixarg)
            for r in results:
                for r2 in r['Contents'][1:]:
                    key = r2['Key']
                    res = patt.match(key)
                    category,urlq = res[2],res[3]
                    yield category,urlq
            
    s3 = boto3.resource('s3')
    mybucket = s3.Bucket(BUCKET)
    mytrain_folder = FOLDER
    assert mytrain_folder and mytrain_folder.endswith('/'), "FOLDER must be assigned with trailing '/'"

    def get_s3_categories():
        client = boto3.client('s3')
        paginator = client.get_paginator('list_objects')
        result = paginator.paginate(Bucket=BUCKET, Delimiter='/', Prefix=args.input_path)
        categories = []
        for prefix in result.search('CommonPrefixes'):
            key = prefix.get('Prefix')
            if DEBUG: print(YELLOW('debug:'),'get_s3_categories:key:',key)
            res = patt.match(key)
            train, category = res[1],res[2]
            if not '-' in category:
                categories.append(category)
        return categories

    def s3_file_exists(key):
        objs = list(mybucket.objects.filter(Prefix=key))
        if len(objs) > 0 and objs[0].key == key:
            return True
        else:
            return False

    def s3_url_quote(url):
        s = url.replace('%','%25')
        return s

    app = ClarifaiApp(api_key=args.api_key)
    face_detect_model = app.models.get('face-v1.3')

    def predict_urls(image_urls):
        climages = [Image(url=url) for url in image_urls]
        detect_results = face_detect_model.predict(climages)
        found={}
        for r in detect_results['outputs']:
            if r['data']:
                url = r['input']['data']['image']['url']
                bb = r['data']['regions'][0]['region_info']['bounding_box']
                found[url] = {'bounding_box':bb}
                if DEBUG: print(YELLOW('debug:'),'Predict success',f'{url:70}')
        return found

    def create_bounding_box_image(url,bounding_box):
        """ create an image with bounding_box
        bounding_box=[left_x,left_y,right_x,right_y]
        """
        bb = bounding_box
        # adjust bottom_row 10 % bigger for facial hair
        bb = [bb['left_col'],bb['top_row'],
              bb['right_col'],bb['bottom_row']] 
        bb_adjust = (-10,-10,10,10)
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'blah'})
            buf = io.BytesIO(urllib.request.urlopen(req).read())
        except urllib.error.HTTPError as ex:
            print('Error:create_bounding_box_image: Request failed.Skipping URL.\n',f'  {url:.70}')
            return
        im = PIL.ImageDraw.Image.open(buf)
        bb2 = size = im.size*2
        bb2 = [b*b2 for b,b2 in zip(bb,bb2)] #convert fractions to pixels
        bb3 = [bb2[0]+bb_adjust[0]/100*size[0],
               bb2[1]+bb_adjust[1]/100*size[1],
               bb2[2]+bb_adjust[2]/100*size[2],
               bb2[3]+bb_adjust[3]/100*size[3]]
        #draw=PIL.ImageDraw.Draw(im)
        #draw.rectangle(bb2,outline='blue')
        #draw.rectangle(bb3,outline='red')
        newim = im.crop(bb3)
        return newim


    all_keys = get_s3_keys()
    images = get_category_keys(all_keys)

    # filter out keys that already exist as facecrops
    for key in list(images):
        train = images[key]['train']
        category = images[key]['category']
        urlq = images[key]['urlq']
        category = category+'-facecrop'
        new_key = os.path.join(train,category,urlq)
        if new_key in all_keys:
            del images[key]
            
    # list of keys for predict
    predicts = {}
    URL_PREFIX='https://s3-us-west-2.amazonaws.com/withmelabs-faces/'
    for key in list(images):
        newurl = s3_url_quote(URL_PREFIX+key)
        images[key]['s3url'] = newurl
        if key in mc and mc[key].get('bounding_box'):
            pass
        else:
            predicts[newurl] = {'key':key}
            
    # time to predict
    if len(predicts) == 0:
        if DEBUG: print(YELLOW('debug:'),"No Images to predict. Returning")
    else:
        print(YELLOW('debug:'),'Start predicting...')
        for chunk in chunks(list(predicts), 127):
            print('predict:',len(chunk))
        
        return
    
        found = predict_urls(list(predicts))
        for url in found:
            key = predicts[url]['key']
            mc[key] = found[url]
        mc.save()

    # run thru images and set the bounding_boxes
    for key in list(images):
        if key in mc:
            if DEBUG: print(YELLOW("debug:"),"Predict SUCCESS", f'{key:.70}')
            images[key]['bounding_box'] = mc[key]['bounding_box']
        else:
            if DEBUG: print(YELLOW("debug:"),"Predict FAILED. Skipping...", f'{key:.70}')
            del images[key]

    # time to crop
    for key in list(images):
        im = create_bounding_box_image(images[key]['s3url'],images[key]['bounding_box'])
        newkey = f"{images[key]['train']}/{images[key]['category']}-facecrop/{images[key]['urlq']}"
        testpath = f"{images[key]['train']}/{images[key]['category']}-facecrop/{images[key]['urlq']}"
        ratio = min(CROP_SIZE[0]/im.size[0], CROP_SIZE[1]/im.size[1])
        newsize = (int(ratio*im.size[0]),int(ratio*im.size[1]))
        im = im.resize(newsize)
        pilutil.save_image(im, testpath)
        print('Cropped image saved...',f'{newkey:.70}')

    """
    urls = {}
    for category,urlq in get_s3_urlqs(categories):
        url = urllib.parse.unquote(urlq)
        newcategory = category+'-facecrop'
        path = os.path.join(newcategory,urlq)
        if s3_file_exists(path) == Fals:
            if DEBUG: print("S3 key does not exist:",path)
            urls[url] = get_cache_faceid(url)
    predict_urls = []
    for url in urls:
        if urls[url] is None:
            predict_urls.append(url)
    assert len(predict_urls) < 128, "Clarifai max of 128 images exceeded."

    found_urls = predict_urls(predict_urls)
    
    get all s3 keys
    create a list of all s3 urls
    remove urls that are already processed.
        for each key in s3
          does facecrop exist already?
          get faceid - lookup in cache first
          with faceid, generate the cropped image
    """

    return

if __name__ == '__main__':
    mc = MyCache.open(MYCACHE_FILENAME)
    parser = create_parser()
    args = create_args()
    if args.cmd == 'download':
        if args.check_size:
            cmd_check_size()
        else:
            cmd_download()
    elif args.cmd == 'copys3':
        cmd_copys3()
    elif args.cmd == 'facecrop':
        cmd_facecrop()
    else:
        create_parser().print_help()

def test1():
    pass
