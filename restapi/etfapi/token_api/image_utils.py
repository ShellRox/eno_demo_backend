import imgkit
import os

preview_gen_path = os.path.join(os.path.dirname(__file__), "preview_gen")

def make_article_preview(article_name, article_description, article_id):
    with open(os.path.join(preview_gen_path, "template.html"), "rb") as fl:
        article_html = (fl.read()).decode('utf-8').format(article_name, article_description)

    imgkit.from_string(article_html, os.path.join(preview_gen_path, "previews", "{0}.png".format(article_id)), options={"enable-local-file-access": None, "width": 340, "height": 430})
