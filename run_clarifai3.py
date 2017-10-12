"""
Create random character images by identifying traits using Clarifai
"""

#setup
import argparse
import os, pprint
import boto3

from models import FaceImageUrls
import run_match3

DEBUG=True

os.environ['CLARIFAI_API_KEY'] = 'f22221dbd1874a3986d0941a47c7d023'
from clarifai import rest
from clarifai.rest import ClarifaiApp, Image
app = ClarifaiApp()
workflow = app.workflows.get('Demographics')

urls=[
    {'desc':'Walter White with mustache goatee beard, glasses',
     'url':'https://i.pinimg.com/736x/c4/c7/13/c4c7139f1222d6b7e3e1a6bbe3b9bead--mustache-and-goatee-goatee-beard.jpg'},
    {'desc':'Jack Black with beard',
     'url':'https://i.pinimg.com/originals/3c/66/74/3c667494758c2fedd01bc7fad52c9961.jpg'},
    {'desc':'James Bond as clean shaven',
     'url':'https://image.afcdn.com/album/D20150130/483279111-916103_H172246_L.jpg'},
    {'desc':'Oprah as black female',
     'url':'http://atlantablackstar.com/wp-content/uploads/2013/09/Oprah-Winfrey.jpg'},
    {'desc':'Lucy Liu as asian',
     'url':'http://2.bp.blogspot.com/-sDpC5BQQeok/VGjuWQQVroI/AAAAAAAAbW0/mwEGh9w5lkE/s1600/lucy%2Bliu.jpg'},
    {'desc':'Donald Trump as age 72',
     'url':'https://fm.cnbc.com/applications/cnbc.com/resources/img/editorial/2017/08/03/104630007-GettyImages-825587596-donald-trump.jpg'},
    {'desc':'Billy Bob Thorton with soulpatch, sunglasses',
     'url':'http://menshaircutstyle.com/wp-content/uploads/celebrities-with-soul-patch-600x600.jpg'},
    {'desc':'Raj Koothrappali indian clean male',
     'url':'http://media2.intoday.in/indiatoday/images/stories/kunalstory_647_072816080151.jpg'},
    {'desc':'Shahrukh Khan clean cut',
     'url':'http://stylesatlife.com/wp-content/uploads/2014/11/Shahrukh-Khan.jpg'},
]

def get_dictlist(d, keylist):
    for key in keylist:
        d = d[key]
    return d

def identify1(result):
    _result = {'url':get_dictlist(result, ['input','data','image','url'])}
    # _result['age'] = {'name':'56',value:'0.56999'}
    face_data = get_dictlist(result, ['outputs',0,'data','regions',0,'data','face'])
    _result['age'] = get_dictlist(face_data, ['age_appearance','concepts',0])
    _result['gender'] = get_dictlist(face_data, ['gender_appearance','concepts',0])
    _result['skin'] = get_dictlist(face_data, ['multicultural_appearance','concepts',0])

    # _result['beard'] = {'name':'beard','value':0.9517182}
    general_data = get_dictlist(result, ['outputs',1,'data','concepts'])
    _result['mustache'] = next((_data for _data in general_data if _data['name'] == 'mustache'), None)
    _result['beard'] = next((_data for _data in general_data if _data['name'] == 'beard'), None)
    _result['goatee'] = next((_data for _data in general_data if _data['name'] == 'goatee'), None)
    _result['eyeglasses'] = next((_data for _data in general_data if _data['name'] == 'eyeglasses'), None)
    _result['sunglasses'] = next((_data for _data in general_data if _data['name'] == 'sunglasses'), None)
    _result['bald'] = next((_data for _data in general_data if _data['name'] == 'bald'), None)

    # save the entire result here
    _result['result'] = result
    return _result

def identify2(results):
    res = []
    for res2 in results['results']:
        res3 = identify1(res2)
        res.append(res3)
    return res

def get_match_args(idrecord):
    id = idrecord
    #[skin,gender,hair,beard,mustache,glasses,sunglasses]
    match_args = {}
    if id['skin']:
        name = id['skin']['name']
        if 'white' in name:
            match_args['--match_skin'] = 'a'
        elif 'asian' in name:
            match_args['--match_skin'] = 'b'
        elif 'hispanic' in name:
            match_args['--match_skin'] = 'c'
        elif 'black' in name:
            match_args['--match_skin'] = 'd'
            
    if id['gender']:
        name = id['gender']['name']
        if 'feminine' in name:
            match_args['--match_gender'] = 'f'
        elif 'masculine' in name:
            match_args['--match_gender'] = 'm'
            
    if id['age']:
        match_args['--match_age'] = name = id['age']['name']

    if id['bald']:
        match_args['--match_bald'] = True

    if id['goatee']:
        match_args['--match_facehair'] = 'goatee'
    elif id['mustache']:
        match_args['--match_facehair'] = 'mustache'
    elif id['beard']:
        match_args['--match_facehair'] = 'beard'
        
    if id['eyeglasses']:
        match_args['--match_eyeglasses'] = True
    if id['sunglasses']:
        match_args['--match_sunglasses'] = True

    return match_args

"""
clarifai_refresh=True to call clarifai all over again.
matchargs_refresh=True recreates identification but does not call clarifai
"""
def identify(matchargs_refresh=False, clarifai_refresh=False):
    url_list = []
    for urlobj in urls:
        url = urlobj['url']
        if clarifai_refresh:
            url_list.append(url)
        else:
            try:
                faceimageurl = FaceImageUrls.get(url)
                if DEBUG: print('get succeeded. already have identification.')
            except:
                url_list.append(url)
                if DEBUG: print('get failed. calling clarifai for url',url)
    # batch the clarifai call
    if len(url_list):
        if DEBUG: print('calling Clarifai now for {} images'.format(len(url_list)))
        res1 = workflow.predict([Image(url) for url in url_list])
        res2 = identify2(res1)
        res3 = dict(zip(url_list, res2))
    for urlobj in urls:
        url = urlobj['url']
        try:
            faceimageurl = FaceImageUrls.get(url)
            if clarifai_refresh or matchargs_refresh:
                faceimageurl.identification = None
        except:
            faceimageurl = FaceImageUrls(url)
            faceimageurl.numid = FaceImageUrls.count()+1
            if DEBUG: print('creating new FaceImageUrl: {} {} {}'.format(faceimageurl.numid,
                                                                         faceimageurl.description,
                                                                         faceimageurl.url))
        if faceimageurl.identification == None:
            faceimageurl.identification = res3[url]
        faceimageurl.description = urlobj['desc']
        faceimageurl.save()
    # all urls should be identified now
    for urlobj in urls:
        url = urlobj['url']
        try:
            faceimageurl = FaceImageUrls.get(url) # should not fail
        except:
            print('get failed. should not have failed for url', url)
        urlobj['faceimageurl'] = faceimageurl
        print(faceimageurl.numid,faceimageurl.description,url)
        #if DEBUG: pprint.pprint(faceimageurl.identification.as_dict())
        match_args = get_match_args(faceimageurl.identification)
        args = ['items','output2','--numid',str(faceimageurl.numid)]
        for key,value in match_args.items():
            args.append(key)
            if not type(value) is bool:
                args.append(value)
        if DEBUG: print('before:',match_args)
        if DEBUG: print('after:',args)
        try:
            run_match3.run_random(10, args)
        except Exception as ex:
            print("Failed to create images for URL. errmsg:", ex)

    print()
    for urlobj in urls:
        print('{numid} {description}'.format(numid=urlobj['faceimageurl'].numid,
                                             description=urlobj['faceimageurl'].description))

def run_identify():
    identify()

def dump_clarifai(numid=-1):
    for urlobj in urls:
        url = urlobj['url']
        try:
            faceimageurl = FaceImageUrls.get(url)
        except:
            print('get failed. calling clarifai for url',url)
            continue
        if numid == -1 or faceimageurl.numid == numid:
            pprint.pprint(faceimageurl.identification.as_dict())
    
def create_args(args=None):
    parser = argparse.ArgumentParser(description='Images infile processor')
    parser.add_argument('--dump_clarifai', help='match item', default=False, action="store_true")
    args = parser.parse_args(args)
    return args

def create_test_args():
    args = create_args(['--dump_clarifai'])
    return args

if __name__ == '__main__':
    if not FaceImageUrls.exists():
        FaceImageUrls.mycreate_table()
    args = create_args()
    if args.dump_clarifai:
        dump_clarifai
    else:
        run_identify()
    

