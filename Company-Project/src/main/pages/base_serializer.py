from typing import Dict, Any

from rest_framework import serializers
from wagtail.core import fields
from wagtail.api.v2 import serializers as wagtail_serializers

from sitesettings.models import SiteSetting
from sitesettings.serializers import SiteSettingSerializer
from ..serializers import SeoSerializer
from .base import BasePage


class BasePageSerializer(serializers.ModelSerializer):
    serializer_field_mapping = (
        serializers.ModelSerializer.serializer_field_mapping.copy()
    )
    serializer_field_mapping.update(
        {fields.StreamField: wagtail_serializers.StreamField}
    )

    seo = serializers.SerializerMethodField()
    site_setting = serializers.SerializerMethodField()

    class Meta:
        model = BasePage
        fields = [
            "title",
            "last_published_at",
            "seo_title",
            "search_description",
            "seo",
            "site_setting",
        ]

    def get_seo(self, page) -> Dict[str, Any]:
        return SeoSerializer(page).data

    def get_site_setting(self, page) -> Dict[str, Any]:
        site_setting = SiteSetting.for_site(page.get_site())
        return SiteSettingSerializer(site_setting).data
