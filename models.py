import boto3, os
from datetime import datetime

from pynamodb.attributes import UnicodeAttribute, BooleanAttribute, UTCDateTimeAttribute, NumberAttribute, \
    MapAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.models import Model

'''
class UsersUsernameIndex(GlobalSecondaryIndex):
    class Meta:
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()
    username = UnicodeAttribute(hash_key=True)


class UsersEmailIndex(GlobalSecondaryIndex):
    class Meta:
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()
    email = UnicodeAttribute(hash_key=True)
'''

os.environ['STAGE'] = 'dev'
os.environ['AWS_PROFILE']='imvu'

class FaceImageUrls(Model):
    class Meta:
        table_name = os.environ.get('STAGE', 'dev') + '.FaceImageUrls'
        region = boto3.Session().region_name
        #host = 'http://localhost:8000' if not os.environ.get('LAMBDA_TASK_ROOT') else None
    numid = NumberAttribute()
    url = UnicodeAttribute(hash_key=True)
    description = UnicodeAttribute()
    created_date = UTCDateTimeAttribute(default=datetime.now())
    identification = MapAttribute()
    '''
    username_index = UsersUsernameIndex()
    email_index = UsersEmailIndex()
    '''    
    @staticmethod
    def mycreate_table():
        FaceImageUrls.create_table(read_capacity_units=1, write_capacity_units=1)

