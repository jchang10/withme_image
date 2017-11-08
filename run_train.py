"""
       - python run_train.py download <output_path>
         - download the input urls
       - python run_train.py facecrop <api_key> <input_path>
       - python run_train.py model create <api_key> [<concept_list>]
       - python run_train.py input <input_path> [<concept_list>] [<not_concept_list>]
       - python run_train.py test


"""

import argparse, datetime, io, json, os, pprint, random, re, urllib
from collections import defaultdict
import PIL, PIL.ImageDraw

import boto3
from clarifai.rest import ClarifaiApp, Image, Concept

from pynamodb.attributes import UnicodeAttribute, BooleanAttribute, \
    UTCDateTimeAttribute, NumberAttribute, MapAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.models import Model

from colorama_util import YELLOW, RED
from gen_util import chunks
import urllib_util,pilutil

import numpy as np

DEBUG=True
MYCACHE_FILENAME='mycache.json'

REGION='us-west-2'
BUCKET='withmelabs-faces'
URL_PREFIX='https://s3-us-west-2.amazonaws.com/withmelabs-faces/'
os.environ['AWS_PROFILE']='imvu'
os.environ['STAGE'] = 'dev'

MYMODEL='mymodel'

#Clarifai api_keys
# d67c7c8cc16f482d8b9cbd920ca561bf jc-clarifai3 - hit predict limits
# c39bab083bc64dfebb5034ee71233ff2 jc-clarifai4

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

    download_parser = subparsers.add_parser('download', help='download urls')
    check_parser = subparsers.add_parser('check', help='check downloads')
    s3_parser = subparsers.add_parser('s3', help='copy to s3')
    facecrop_parser = subparsers.add_parser('facecrop', help='face cropping')
    model_parser = subparsers.add_parser('model', help='model manipulation')
    input_parser = subparsers.add_parser('input', help='input manipulation')

    parser.add_argument('--dry-run', help='dry run', default=False, action="store_true")
    parser.add_argument('--count', help='only process count items for debugging', type=int)

    download_parser.set_defaults(cmd='download')
    download_parser.add_argument('output_path', help='must be a directory')

    check_parser.set_defaults(cmd='check')
    check_parser.add_argument('input_path', help='must be a directory')
    check_parser.add_argument('--output_urls_path', help='write pass urls to new file')
    check_parser.add_argument('--delete', help='delete failed urls',
                              default=False, action="store_true")
    
    s3_parser.set_defaults(cmd='s3')
    s3_parser.add_argument('subcmd', help='must be a directory')
    s3_parser.add_argument('input_path', help='must be a directory')
    
    facecrop_parser.set_defaults(cmd='facecrop')
    facecrop_parser.add_argument('api_key', help='Clarifai api_key')
    facecrop_parser.add_argument('input_path', help='must be a directory')

    model_parser.set_defaults(cmd='model')
    model_parser.add_argument('subcmd', help='Clarifai api_key')
    model_parser.add_argument('api_key', help='Clarifai api_key')

    input_parser.set_defaults(cmd='input')
    input_parser.add_argument('subcmd', help='Clarifai api_key')
    input_parser.add_argument('api_key', help='Clarifai api_key')
    input_parser.add_argument('input_path', help='must be a directory')

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
    if cmd == 'check':
        args = create_args(['check','train','--output_urls_path','output_urls.py','--delete'])
    elif cmd == 's3_copy':
        args = create_args(['s3','copy','train'])
    elif cmd == 's3_delete':
        args = create_args(['s3','delete','train/mustaches/'])
    elif cmd == 'facecrop':
        # api_key belongs to jc-clarifai3. my-first-application
        args = create_args(['facecrop','a7d4adb4103d4e0482981233770ef056','train'])
    elif cmd == 'model_create':
        # api_key belongs to jc-clarifai3. my-third
        args = create_args(['model','create','d67c7c8cc16f482d8b9cbd920ca561bf'])
    elif cmd == 'input_add':
        # api_key belongs to jc-clarifai3. my-third
        args = create_args(['--dry-run','--count','10','input','add','d67c7c8cc16f482d8b9cbd920ca561bf','train'])
        #args = create_args(['--count','10','input','add','d67c7c8cc16f482d8b9cbd920ca561bf','train'])
        #args = create_args(['input','add','d67c7c8cc16f482d8b9cbd920ca561bf','train'])
    elif cmd == 'input_score':
        # api_key belongs to jc-clarifai3. my-third
        args = create_args(['input','score','d67c7c8cc16f482d8b9cbd920ca561bf','train'])
    else:
        assert False, 'No matching cmd'
    return args

def check_file_size(url_path):
    try:
        size = pilutil.image_size(url_path)
    except Exception as ex:
        return False
    if any(dim>min(CROP_SIZE) for dim in size):
        return True
    else:
        return False

#from input_urls4 import input_urls
#from train6.input_urls6 import input_urls
from test_urls import input_urls
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
            try:
                if not args.dry_run:
                    urllib_util.save_url_to_file(url, url_path)
                    if check_file_size(url_path) == False:
                        print(RED('Failed file size check.'), f'Deleting... {url_path:.70}')
                        os.remove(url_path)
            except Exception as ex:
                print(RED('Failed. Skipping...'),ex)

def gen_all_files(inpath):
    for root,dirs,files in os.walk(inpath, topdown=True):
        for name in files:
            if name.startswith('.'):
                continue
            path = os.path.join(root,name)
            yield path

def cmd_check():
    """
    check the image resolution. separate to pass and fail images.
    """
    pass_urls = defaultdict(list)
    fail_urls = defaultdict(list)
    fail_all = []
    for url_path in gen_all_files(args.input_path):
        train,category,urlq = split_key(url_path)
        try:
            size = pilutil.image_size(url_path)
        except Exception as ex:
            fail_urls[category].append(url_path)
            fail_all.append(url_path)
            if DEBUG: print(RED('  Failed to open:'),size,f'{url_path:.70}')
            continue
        if any(dim>min(CROP_SIZE) for dim in size):
            pass_urls[category].append(url_path)
        else:
            fail_urls[category].append(url_path)
            fail_all.append(url_path)
            if DEBUG: print(RED('  Image size too small:'),size,f'{url_path:.70}')
    print('Pass urls:')
    for category in pass_urls:
        print(category,len(pass_urls[category]))
    print('Fail urls:')
    for category in fail_urls:
        print(category,len(fail_urls[category]))

    if args.output_urls_path:
        print('Writing pass urls to',args.output_urls_path)
        with open(args.output_urls_path,'w') as fp:
            pprint.pprint(pass_urls, fp)

    if args.delete:
        for path in fail_all:
            print(f'Deleting... {path:.70}')
            os.remove(path)
        
    return pass_urls,fail_urls

def get_s3_keys(folder):
    s3 = boto3.resource('s3')
    mybucket = s3.Bucket(BUCKET)
    myobjects = mybucket.objects.filter(Prefix=folder)
    return [obj.key for obj in mybucket.objects.filter(Prefix=folder)]

patt = re.compile(r'^(\w+)/([\w-]+)/(.*)?')

def split_key(key):
    res = patt.match(key)
    if res:
        train,category,urlq = res[1],res[2],res[3]
        return train,category,urlq
    else:
        return None,None,None

def get_image_keys(keys):
    image_keys = {}
    for key in keys:
        train,category,urlq = split_key(key)
        if train is None:
            continue # probably a folder
        if not urlq:
            continue
        image_keys[key] = {
            'train':train,
            'category':category,
            'urlq':urlq,
        }
    return image_keys

def get_facecrops(images):
    facecrops = defaultdict(list)
    for key in images:
        category = images[key]['category']
        if '-' not in category:
            continue
        category,_ = category.split('-',1)
        facecrops[category].append(key)
    return facecrops

def cmd_s3_copy():
    """
    copy local files to s3
    """

    all_keys = get_s3_keys(args.input_path)
    images = get_image_keys(all_keys)
    local_files = [path for path in gen_all_files(args.input_path) if path not in images]

    if DEBUG: print(YELLOW('debug:'),"Number of files on S3:", len(images))
    if DEBUG: print(YELLOW('debug:'),"Number of files upload to S3:",len(local_files))

    s3 = boto3.resource('s3')
    mybucket = s3.Bucket(BUCKET)
    for file in local_files:
        print("Copying file to S3",f'{file:.70}')
        mybucket.upload_file(file, file, ExtraArgs={'ACL':'public-read'})
            
    """
    get category keys from s3
    only copy files that are not on s3:
      walk local directory tree
      check if s3object exists, remove from list
    copy remaining files to s3
    """

def get_s3_categories():
    client = boto3.client('s3')
    paginator = client.get_paginator('list_objects')
    result = paginator.paginate(Bucket=BUCKET, Delimiter='/', Prefix=args.input_path)
    categories = {}
    for prefix in result.search('CommonPrefixes'):
        category = prefix.get('Prefix')
        if DEBUG: print(YELLOW('debug:'),'get_s3_categories:category:',category)
        train, category, urlq = split_key(category)
        categories[category] = dict(zip(('train','category','urlq'),(train,category,urlq)))
        categories[category]['key'] = os.path.join(train,category,'')
    return categories

def cmd_s3_delete():
    key = args.input_path
    if input(f'Are you sure you want to delete all S3 keys={key}? (y/n) ') != 'y':
        return
    s3 = boto3.resource('s3')
    mybucket = s3.Bucket(BUCKET)
    if not args.dry_run:
        mybucket.objects.filter(Prefix=key).delete()
    
def s3_url_quote(url):
    s = url.replace('%','%25')
    return s

def s3_bucket_url(key):
    return s3_url_quote(URL_PREFIX+key)
    
CROP_SIZE=(750,750)
#API_CHUNK_SIZE=128
API_CHUNK_SIZE=64

def cmd_facecrop():
    """
    construct categories list

    for each category in s3
      is the facecrop cached?
      does the facecrop_file exist already? skip it.
    """
    def get_s3_urlqs(categories):
        for category in categories:
            prefixarg = f'{args.input_path}{category}/'
            results = paginator.paginate(Bucket=BUCKET, Delimiter='/', Prefix=prefixarg)
            for r in results:
                for r2 in r['Contents'][1:]:
                    category = r2['Key']
                    train,category,urlq = split_key(category)
                    yield category,urlq
            
    s3 = boto3.resource('s3')
    mybucket = s3.Bucket(BUCKET)

    def s3_file_exists(category):
        objs = list(mybucket.objects.filter(Prefix=category))
        if len(objs) > 0 and objs[0].category == category:
            return True
        else:
            return False


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
        bb_adjust = (0,0,0,10)
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


    all_keys = get_s3_keys(args.input_path)
    if args.count:
        all_keys = random.sample(all_keys, args.count)
    images = get_image_keys(all_keys)
    categories = defaultdict(int)
    
    # filter out facecrop categories
    for key in list(images):
        category = images[key]['category']
        if '-' in category:
            del images[key]
        else:
            categories[category] = 1

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
    for key in list(images):
        newurl = s3_bucket_url(key)
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
        for chunk in chunks(list(predicts), API_CHUNK_SIZE):
            print('predict:',len(chunk))
            found = predict_urls(chunk)
            print('predict: found:', len(found))
            for url in found:
                key = predicts[url]['key']
                mc[key] = found[url]
            print('Saving mycache...',len(mc))
            mc.save()

    # run thru images and set the bounding_boxes
    for key in list(images):
        if key in mc:
            if DEBUG: print(YELLOW("debug:"),"MyCache HIT", f'{key:.70}')
            images[key]['bounding_box'] = mc[key]['bounding_box']
        else:
            if DEBUG: print(YELLOW("debug:"),"Predict FAILED. Skipping...", f'{key:.70}')
            del images[key]

    # create the crop directories
    for category in categories:
        cat_path = os.path.join(args.input_path,category+'-facecrop')
        if not os.path.isdir(cat_path):
            print("Creating directory", cat_path)
            os.mkdir(cat_path)

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

    '''
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
    '''

def cmd_model_create():
    app = ClarifaiApp(api_key=args.api_key)
    mymodel = app.models.create(MYMODEL)
    mymodel.add_concepts(['beard','goatee','mustache','cleanshaven'])
    mymodel.update(concepts_mutually_exclusive=True,closed_environment=False)

def get_climage_by_category(category, key):
    s3url = s3_bucket_url(key)
    if category is None:
        return Image(url=s3url)
    elif category == 'beards':
        return Image(url=s3url, concepts=['beard'])
    elif category == 'goatees':
        return Image(url=s3url, concepts=['goatee'])
    elif category == 'mustaches':
        return Image(url=s3url, concepts=['mustache'])
    elif category == 'cleanshavens':
        return Image(url=s3url, concepts=['cleanshaven'])
    elif category == 'females':
        return Image(url=s3url, not_concepts=['beard','goatee','mustache'])
    else:
        print(RED('found unknown category folder'),f'skipping... {category} {key:.70}')
        return None
    
def get_climages_by_category(category, keys):
    climages = []
    for key in keys:
        climage = get_climage_by_category(category, key)
        if climage:
            climages.append(climage)
    return climages

def cmd_input_add():
    app = ClarifaiApp(api_key=args.api_key)
    all_keys = get_s3_keys(args.input_path)
    images = get_image_keys(all_keys)
    # only keep facecrops
    facecrops = get_facecrops(images)
    climages=[]
    for category in facecrops:
        climages += get_climages_by_category(category, facecrops[category])
    if DEBUG: print(YELLOW('debug:'),'climages count',len(climages))
    if args.count:
        climages=climages[:args.count]
    if not args.dry_run:
        for chunk in chunks(climages, API_CHUNK_SIZE):
            res = app.inputs.bulk_create_images(chunk)
            print('successfully added images:',len(res))

    cmd_input_status()
    
    '''
    facecrop = {
      'beard': [ list keys ]
    for each category
      construct concept for category
      for each chunk of images.
        add images
    '''
        
def cmd_input_delete():
    app = ClarifaiApp(api_key=args.api_key)
    app.inputs.delete_all()

def cmd_input_status():
    app = ClarifaiApp(api_key=args.api_key)
    status = app.inputs.check_status()
    print(f'status processed:{status.processed} errors:{status.errors} to_process:{status.to_process}')

def get_result_values(results, concept, single_top_concept=False):
    values = []
    for output in results['outputs']:
        concepts = output['data']['concepts']
        count = 0
        for _concept in concepts:
            name = _concept['name']
            value = _concept['value']
            if concept is None or concept == name:
                values.append(float(value))
                count += 1
            if single_top_concept and count > 0:
                break
    return values

def get_accuracy_score(results, concept, single_top_concept=False):
    values = get_result_values(results, concept)
    values = np.array(values)
    return values.mean()

def cmd_input_score(nsample=-1):
    app = ClarifaiApp(api_key=args.api_key)
    mymodel = app.models.get(MYMODEL)
    all_keys = get_s3_keys(args.input_path)
    images = get_image_keys(all_keys)
    facecrops = get_facecrops(images)
    climages={}
    predict_scores={}
    for category in facecrops:
        climages[category] = get_climages_by_category(None, facecrops[category])
    predict_results={}
    for category in climages:
        climages2 = climages[category]
        if nsample == -1:
            nnsample = args.count if args.count else len(climages2)
        if DEBUG: print(f'calling mymodel.predict for category {category} with sample size={nnsample}')
        predict_results[category] = mymodel.predict(random.sample(climages2, nnsample))
        concept = category[:-1]
        predict_scores[concept] = get_accuracy_score(predict_results[category],concept)
    for concept in predict_scores:
        print(predict_scores[concept], f'{concept} score')

    '''
    predict_scores['beard'] = get_accuracy_score(predict_results['beards'], 'beard')
    print(" beard score", predict_scores['beard'])
    predict_scores['goatee'] = get_accuracy_score(predict_results['goatees'], 'goatee')
    print(" goatee score", predict_scores['goatee'])
    predict_scores['mustache'] = get_accuracy_score(predict_results['mustaches'], 'mustache')
    print(" mustache score", predict_scores['mustache'])
    #predict_scores['female'] = get_accuracy_score(predict_results['females'], None)
    #print(" female score", predict_scores['female'])
    predict_scores['cleanshaven'] = get_accuracy_score(predict_results['cleanshavens'], 'cleanshaven')
    print(" cleanshaven score", predict_scores['cleanshaven'])
    '''

    '''
    for each facecrop_category
      pick count number of images
      all mymodel.predict(images)

    '''
    
if __name__ == '__main__':
    mc = MyCache.open()
    parser = create_parser()
    args = create_args()
    if 'cmd' not in vars(args):
        parser.print_help()
    elif args.cmd == 'download':
        cmd_download()
    elif args.cmd == 'check':
        cmd_check()
    elif args.cmd == 's3':
        if args.subcmd == 'copy':
             cmd_s3_copy()
        elif args.subcmd == 'delete':
            cmd_s3_delete()
    elif args.cmd == 'facecrop':
        cmd_facecrop()
    elif args.cmd == 'model':
        if args.subcmd == 'create':
            cmd_model_create()
    elif args.cmd == 'input':
        if args.subcmd == 'add':
            cmd_input_add()
        elif args.subcmd == 'delete':
            cmd_input_delete()
        elif args.subcmd == 'status':
            cmd_input_status()
        elif args.subcmd == 'score':
            cmd_input_score()
    else:
        parser.print_help()

def test1():
    pass
