from django.db import models


# class BaseICom(models.Model):
#     id = models.IntegerField()
#     comment = models.CharField()
#     time_created = models.DateTimeField()
#     time_updated = models.DateTimeField()
#
#     class Meta:
#         abstract = True
#
#
# class BaseStructure(BaseICom):
#     name = models.CharField(max_length=20)
#
#
# class Structure(BaseICom):
#     struct_type = models.CharField(max_length=20)
#     number = models.FloatField()
#     side = models.CharField(max_length=3)

class Upload(models.Model):
    title = models.CharField(max_length=50)
    upload = models.FileField(upload_to="media")
