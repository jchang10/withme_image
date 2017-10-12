"""
Create random character images by identifying traits using Clarifai
"""

#setup
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
    {'desc':'walter white with mustache goatee beard',
     'url':'https://i.pinimg.com/736x/c4/c7/13/c4c7139f1222d6b7e3e1a6bbe3b9bead--mustache-and-goatee-goatee-beard.jpg'},
    {'desc':'jack black with mustache beard',
     'url':'https://i.pinimg.com/originals/3c/66/74/3c667494758c2fedd01bc7fad52c9961.jpg'},
    {'desc':'james bond clean shaven',
     'url':'https://image.afcdn.com/album/D20150130/483279111-916103_H172246_L.jpg'},
    {'desc':'oprah as black',
     'url':'http://atlantablackstar.com/wp-content/uploads/2013/09/Oprah-Winfrey.jpg'},
    {'desc':'lucy liu as asian',
     'url':'http://2.bp.blogspot.com/-sDpC5BQQeok/VGjuWQQVroI/AAAAAAAAbW0/mwEGh9w5lkE/s1600/lucy%2Bliu.jpg'},
    {'desc':'donald trump as age 72',
     'url':'https://fm.cnbc.com/applications/cnbc.com/resources/img/editorial/2017/08/03/104630007-GettyImages-825587596-donald-trump.jpg'},
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
    _result['eyeglasses'] = next((_data for _data in general_data if _data['name'] == 'eyeglasses'), None)
    _result['sunglasses'] = next((_data for _data in general_data if _data['name'] == 'sunglasses'), None)
    _result['bald'] = next((_data for _data in general_data if _data['name'] == 'bald'), None)

    return _result

def identify(results):
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
    if id['mustache']:
        match_args['--match_mustache'] = True
    if id['beard']:
        match_args['--match_beard'] = True
    if id['eyeglasses']:
        match_args['--match_eyeglasses'] = True
    if id['sunglasses']:
        match_args['--match_sunglasses'] = True
    if id['bald']:
        match_args['--match_bald'] = True
    if id['age']:
        match_args['--match_age'] = name = id['age']['name']

    return match_args

def run_identify():
    for urlobj in urls:
        url = urlobj['url']
        try:
            faceimageurl = FaceImageUrls.get(url)
            if DEBUG: print('get succeeded. already have identifcation.')
        except:
            faceimageurl = FaceImageUrls(url)
            if DEBUG: print('get failed. calling clarifai to obtain identification.')
            res1 = workflow.predict([Image(url) for url in url_list])
            res2 = identify(res1)
            faceimageurl.identification = res2
            faceiamgeurl.numid = FaceImageUrls.count()+1
        faceimageurl.description = urlobj['desc']
        faceimageurl.save()
            
    for urlobj in urls:
        url = urlobj['url']
        try:
            faceimageurl = FaceImageUrls.get(url) # should not fail
        except:
            print('get failed. should not have failed for url', url)
        urlobj['faceimageurl'] = faceimageurl
        print(faceimageurl.numid,faceimageurl.description,url)
        if DEBUG: pprint.pprint(faceimageurl.identification.as_dict())
        match_args = get_match_args(faceimageurl.identification)
        args = ['items','output2','--numid',str(faceimageurl.numid)]
        for key,value in match_args.items():
            args.append(key)
            if not type(value) is bool:
                args.append(value)
        if DEBUG: print('before:',match_args)
        if DEBUG: print('after:',args)
        run_match3.run_random(10, args)

    print()
    for urlobj in urls:
        print('{numid} {description}'.format(numid=urlobj['faceimageurl'].numid,
                                             description=urlobj['faceimageurl'].description))


if __name__ == '__main__':
    if not FaceImageUrls.exists():
        FaceImageUrls.mycreate_table()
    run_identify()
    
