from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist

from etfapi.models import Author, Article, APIKey
#from apiutils import verify_api_keys

from datetime import datetime

import string
import random
import json
import base64
import os
import threading

from background_task import background
from etfapi.token_api.mainframe import new_article_token
from etfapi.token_api.image_utils import make_article_preview

@csrf_exempt
def add_article(request):
    if request.method == "POST":
        # expects a JSON request
        request_body = json.loads(request.body.decode('utf-8'))

        requested_api_key = request_body["api_key"]

        try:
            api_key = APIKey.objects.get(api_key=requested_api_key)
        except ObjectDoesNotExist:
            return JsonResponse({"status": "failure"})
        else:
            request_host = request.get_host()

            # content = base64 stringified file
            content_data = base64.b64decode(request_body["content"]).decode("utf-8")

            # file meta data in JSON
            meta_keys = ["author", "title", "description", "price"]
            meta_data = request_body["metadata"][0]
            meta_data = {m_key: meta_data.get(m_key, '') for m_key in meta_keys}

            author_address = meta_data["author"]
            article_title = meta_data["title"]
            article_description = meta_data["description"]
            article_price = float(meta_data["price"])

            author_obj = Author.objects.get_or_create(
                author_address=author_address,
                defaults={"reg_date": datetime.now()}
            )[0]

            unique_article_address_len = 6
            unique_article_address = ''.join([random.choice(string.digits) for _ in
             range(0, unique_article_address_len)])

            article_obj = Article.objects.get_or_create(article_address=unique_article_address,
            defaults={
            "author": author_obj,
            "content": content_data,
            "title": article_title,
            "description": article_description,
            "price": article_price,
            "cre_date": datetime.now(),
            "image_url": "https://{0}/{1}/{2}.png".format(request_host, "preview_data", unique_article_address)
            })[0]

            metadata_url = "https://{0}/{1}/{2}/".format(request_host, "article_token_metadata", unique_article_address)

            create_new_article_token(author_address, request_host, unique_article_address, article_title, article_description, metadata_url)

            return JsonResponse({
            "status": "success",
            "article_id": unique_article_address,
            "article_url": "{0}/{1}/{2}/".format(
            request_host, "articles", unique_article_address)})
    else:
        return HttpResponse(status=404)

@csrf_exempt
def get_article_data(request, article_id):
    selected_article = Article.objects.get(article_address=article_id)

    article_data = {
    "article_author_address": selected_article.author.author_address,
    "article_title": selected_article.title,
    "article_description": selected_article.description,
    "article_price": selected_article.price,
    "article_created": selected_article.cre_date.isoformat(),
    }

    return JsonResponse({
    "content": selected_article.content,
    "metadata": article_data
    })

def get_article_metaplex_metadata(request, article_id):
    selected_article = Article.objects.get(article_address=article_id)

    article_metadata = {
    "name": selected_article.title,
    "symbol": "",
    "description": selected_article.description,
    "image": selected_article.image_url,
    "external_url": "",
    "properties": {"files": [selected_article.image_url],
     "category": "image",
      "creators": [
          {"address": "https://twitter.com/nicokvar/",
          "verified": True,
          "share": 100}
      ]}
     }

    return JsonResponse(article_metadata)

def get_article_data(request, article_id):
    selected_article = Article.objects.get(article_address=article_id)

    article_data = {
    "article_author_address": selected_article.author.author_address,
    "article_title": selected_article.title,
    "article_description": selected_article.description,
    "article_price": selected_article.price,
    "article_created": selected_article.cre_date.isoformat(),
    }

    return JsonResponse({
    "content": selected_article.content,
    "metadata": article_data
    })

@csrf_exempt
def validate_ownership(request):
    if request.method == "POST":
        # expects a JSON request
        request_body = json.loads(request.body.decode('utf-8'))

        article_address = request_body["article"]
        author_pubkey = request_body["author"]

        ownership_resp = {"success": True}

        try:
            article = Article.objects.get(article_address=article_address)
        except Article.ObjectDoesNotExist:
            ownership_resp["success"] = True
        else:
            ownership_resp["success"] = (article.author.author_address == author_pubkey.strip())
            ownership_resp["article_link"] =  "{0}/{1}/{2}/".format(
                        request.get_host(), "articles", article_address)


        return JsonResponse(ownership_resp)
    else:
        return HttpResponse(status=401)

@background
def create_new_article_token(author_address, request_host, unique_article_address, article_title, article_description, metadata_url):
    metadata_url = "https://{0}/{1}/{2}/".format(request_host, "article_token_metadata", unique_article_address)
    mint_master_edition = new_article_token("Eno:{0}".format(unique_article_address), "ENO", author_address, metadata_url)
    article_preview = make_article_preview(article_title, article_description, unique_article_address)

def metadata_test(request):
    with open(os.path.join(os.path.dirname(__file__), "metatest", "metatest.json"), "rb") as fl:
        js_load = json.load(fl)

    return JsonResponse(js_load)

def metadata_image_test(request):
    with open(os.path.join(os.path.dirname(__file__), "metatest", "test.png"), "rb") as fl:
        return HttpResponse(fl.read(), content_type="image/jpeg")
