import json
from urllib import parse

import boto3
from PIL import Image

s3 = boto3.client("s3")

def lambda_handler(event, context):
    records = event.get("Records")
    download_dir = "/tmp/"
    origin_bucket = "orgin-bucket"  # 원본 이미지가 업로드 되는 버킷 이름
    resize_bucket = "resize-bucket"  # 크기가 조정된 이미지가 저장될 버킷 이름
    
    for record in records:
        print(record)
        print(f"event_name : {record['eventName']}")
        ref_cd, file_name = record["s3"]["object"]["key"].split("/")
        name, ext = file_name.rsplit(".", 1)
        name = parse.unquote(name)  # 한글이름 파일일 경우 url decoding
        name = name.replace("+", " ")
        print(name, ext)
        
        file_name = f"{name}.{ext}"
        resize_file_name = f"{name}_low.{ext}"
        key = f"{ref_cd}/{name}.{ext}"

        with open(download_dir + file_name, "wb") as img:
            print(origin_bucket, key)
            s3.download_fileobj(origin_bucket, key, img)
        
        with open(download_dir + file_name, "rb") as img:
            try:
                img_resized = Image.open(img)
            except:  # 이미지 파일이 아닐 경우
                print("no image file!")
                return {
                    "statusCode": 409,
                    "body": json.dumps("no image file")
                }
            print(f"original img size : {img_resized.size}")
            # 일단 120 x 120으로 맞추도록 설정
            r_width = 120 if img_resized.width >= 120 else img_resized.width
            r_height = 120 if img_resized.height >= 120 else img_resized.height

            print(f"resized img size : ({r_width}, {r_height})")
            img_resized = img_resized.resize((r_width, r_height))
            img_resized.save(download_dir + resize_file_name)
        
        with open(download_dir + resize_file_name, "rb") as img:
            s3.upload_fileobj(img, resize_bucket, key)
    
    
    return {
        "statusCode": 200,
        "body": json.dumps("ok")
    }
