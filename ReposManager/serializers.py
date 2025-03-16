from rest_framework import serializers
from .models import Package

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ['pkg_name', 'pkg_version', 'pkg_publish_date', 'pkg_file']