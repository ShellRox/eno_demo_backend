from django.db import models

class Author(models.Model):
    author_address = models.CharField(max_length=50)
    reg_date = models.DateTimeField()

    def __str__(self):
        return self.author_address

class Article(models.Model):
    article_address = models.CharField(max_length=25)
    title = models.CharField(max_length=200)
    description = models.TextField()
    content = models.TextField()
    image_url = models.TextField()
    price = models.FloatField()
    cre_date = models.DateTimeField()
    author = models.ForeignKey('Author', on_delete=models.CASCADE)

    def __str__(self):
        return '/'.join([self.title, self.article_address])

class APIKey(models.Model):
    key_owner = models.CharField(max_length=16)
    api_key = models.CharField(max_length=32)

    def __str__(self):
        return self.key_owner
