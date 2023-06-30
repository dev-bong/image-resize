import json
from urllib import parse

import boto3
from PIL import Image

s3 = boto3.client("s3")

def image_ratio_4_to_3(img):
    # 이미지 4:3으로 만들기
    w, h = (img.width, img.height)
    w_43 = int(round(h * 1.333, 0))
    print(w, h, w_43)

    if w > w_43:  # 가로가 긴 경우, 양 옆 자르기
        crop_size = (w - w_43)//2
        img_43 = img.crop((crop_size, 0, w-crop_size, h))
    elif w < w_43:  # 세로가 긴 경우, 양 옆 채우기
        paste_img = Image.new("RGB", (w_43,h), "#d3d3d3")
        paste_img.paste(img, ((w_43//2) - (w//2),0))
        img_43 = paste_img
    else:
        img_43 = img
    
    return img_43

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
        key = f"{ref_cd}/{name}.{ext}"

        with open(download_dir + file_name, "wb") as img:
            print(origin_bucket, key)
            s3.download_fileobj(origin_bucket, key, img)
        
        with open(download_dir + file_name, "rb") as img:
            try:
                origin_img = Image.open(img)
            except:  # 이미지 파일이 아닐 경우
                print("no image file!")
                return {
                    "statusCode": 409,
                    "body": json.dumps("no image file")
                }
            print(f"original img size : {origin_img.size}")

            ratio_43_img = image_ratio_4_to_3(origin_img)
            print(origin_img.width, origin_img.height)

            resize_file_name = f"{name}.{ext}"
            resize_key = f"{ref_cd}/{resize_file_name}"
            resized_img = ratio_43_img.resize((1600, 1200))
            resized_img.save(download_dir + resize_file_name)

            with open(download_dir + resize_file_name, "rb") as img:
                s3.upload_fileobj(img, resize_bucket, resize_key)
    
    
    return {
        "statusCode": 200,
        "body": json.dumps("ok")
    }
