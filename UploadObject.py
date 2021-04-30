import json
import boto3
import requests

s3 = boto3.resource('s3')
bucket_name = 's3823026-artist'

def get_image(music_list):

    for music in music_list['songs']:
        image_url = music['img_url']
        image_name = image_url.split('/')[::-1][0]
        print("Adding music:", image_name, image_url)
        load_image(image_url, image_name)
        

def load_image(image_url, image_name):
    req_image = requests.get(image_url, stream=True)
    file_object = req_image.raw
    req_data = file_object.read()

    s3.Bucket(bucket_name).put_object(Key=image_name, Body=req_data)


if __name__ == '__main__':
    with open("a2.json") as json_file:
        music_list = json.load(json_file)
    get_image(music_list)