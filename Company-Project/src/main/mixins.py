from typing import List, Set, Dict, Tuple, Optional, Any

from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.http.request import HttpRequest
from django.utils.functional import cached_property
from wagtail.utils.decorators import cached_classmethod
from wagtail.admin.edit_handlers import (
    ObjectList,
    TabbedInterface,
    FieldPanel,
    MultiFieldPanel,
)
from rest_framework import serializers
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.core.models import Page


class RedirectUpMixin:
    def serve(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        parent = self.get_parent()  # type: ignore
        return HttpResponseRedirect(parent.url)


class SeoMixin(Page):
    og_title = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        verbose_name=_("Facebook title"),
        help_text=_("Fallbacks to seo title if empty"),
    )

    og_description = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name=_("Facebook description"),
        help_text=_("Fallbacks to seo description if empty"),
    )

    og_image = models.ForeignKey(
        "customimage.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_(
            "If you want to override the image used on Facebook for \
                    this item, upload an image here. \
                    The recommended image size for Facebook is 1200 × 630px"
        ),
        related_name="+",
    )

    twitter_title = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        verbose_name=_("Twitter title"),
        help_text=_("Fallbacks to facebook title if empty"),
    )

    twitter_description = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name=_("Twitter description"),
        help_text=_("Fallbacks to facebook description if empty"),
    )

    twitter_image = models.ForeignKey(
        "customimage.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Twitter image"),
        help_text=_("Fallbacks to facebook image if empty"),
    )

    robot_noindex = models.BooleanField(
        default=False,
        verbose_name=_("No index"),
        help_text=_("Check to add noindex to robots"),
    )

    robot_nofollow = models.BooleanField(
        default=False,
        verbose_name=_("No follow"),
        help_text=_("Check to add nofollow to robots"),
    )

    canonical_link = models.URLField(
        blank=True, null=True, verbose_name=_("Canonical link")
    )

    promote_panels = [
        FieldPanel("slug"),
        MultiFieldPanel(
            [FieldPanel("seo_title"), FieldPanel("search_description")],
            _("SEO settings"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("og_title"),
                FieldPanel("og_description"),
                ImageChooserPanel("og_image"),
                FieldPanel("twitter_title"),
                FieldPanel("twitter_description"),
                ImageChooserPanel("twitter_image"),
            ],
            _("Social settings"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("robot_noindex"),
                FieldPanel("robot_nofollow"),
                FieldPanel("canonical_link"),
            ],
            _("Robot settings"),
        ),
    ]

    og_image_list = ["og_image"]

    @cached_property
    def seo_og_image(self):
        images = [getattr(self, x) for x in self.og_image_list]
        images = list(filter(None.__ne__, images))

        if not len(images):
            return None

        return images[0]

    @cached_property
    def seo_html_title(self) -> str:
        return self.seo_title or self.title

    @cached_property
    def seo_meta_description(self) -> str:
        return self.search_description

    @cached_property
    def seo_og_title(self) -> str:
        return self.og_title or self.title

    @cached_property
    def seo_og_description(self) -> str:
        return self.og_description or self.title

    @cached_property
    def seo_og_url(self) -> str:
        return self.seo_canonical_link

    @cached_property
    def seo_canonical_link(self) -> str:
        return self.canonical_link or self.full_url

    @cached_property
    def seo_og_type(self) -> Optional[str]:
        return None

    @cached_property
    def seo_twitter_title(self) -> str:
        return self.twitter_title or self.title

    @cached_property
    def seo_twitter_description(self) -> Optional[str]:
        return self.twitter_description

    @cached_property
    def seo_twitter_url(self) -> str:
        return self.seo_canonical_link

    @cached_property
    def seo_twitter_image(self) -> str:
        return self.twitter_image or self.seo_og_image

    @cached_property
    def seo_meta_robots(self) -> str:
        index = "noindex" if self.robot_noindex else "index"
        follow = "nofollow" if self.robot_nofollow else "follow"
        return "{},{}".format(index, follow)

    class Meta:
        abstract = True


class EnhancedEditHandlerMixin:
    @cached_classmethod
    def get_edit_handler(cls):
        """
        Get the EditHandler to use in the Wagtail admin when editing
        this page type.
        """

        if hasattr(cls, "edit_handler"):
            return cls.edit_handler.bind_to_model(cls)

        # construct a TabbedInterface made up of content_panels, promote_panels
        # and settings_panels, skipping any which are empty
        tabs = []

        if cls.content_panels:
            tabs.append(ObjectList(cls.content_panels, heading=_("Content")))

        if hasattr(cls, "extra_panels"):
            for panel_id, heading in cls.extra_panels:
                tabs.append(ObjectList(getattr(cls, panel_id), heading=heading))

        if cls.promote_panels:
            tabs.append(
                ObjectList(cls.promote_panels, heading=_("SEO"), classname="seo")
            )

        if cls.settings_panels:
            tabs.append(
                ObjectList(
                    cls.settings_panels, heading=_("Settings"), classname="settings"
                )
            )

        EditHandler = TabbedInterface(tabs, base_form_class=cls.base_form_class)

        return EditHandler.bind_to_model(cls)


class TimestampMixin(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ReactViewMixin(object):
    template_name: str = "pages/react.html"
    component_name: str = ""
    request: HttpRequest
    serializer_class: serializers.Serializer

    def render_to_response(self, context: Dict, **response_kwargs) -> HttpResponse:
        if self.should_serve_json(self.request):
            props = self.to_dict({"request": self.request})
            return JsonResponse(props)

        return super().render_to_response(context, **response_kwargs)  # type: ignore

    @staticmethod
    def should_serve_json(request: HttpRequest) -> bool:
        return (
            request.GET.get("format", None) == "json"
            or request.content_type == "application/json"
        )

    def get_context_data(self, *args, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(*args, **kwargs)  # type: ignore

        return {**context, "props": self.to_dict({"request": self.request})}

    def to_dict(self, context: Dict) -> Dict[str, Any]:
        serializer_cls = self.get_serializer_class()
        serializer = serializer_cls(
            self.get_component_props(), context={"request": context["request"]}
        )

        return {
            "component_name": self.component_name,
            "component_props": serializer.data,
        }

    def get_serializer_class(self) -> serializers.Serializer:
        if isinstance(self.serializer_class, str):
            return import_string(self.serializer_class)

        return self.serializer_class

    def get_component_name(self) -> str:
        if self.component_name:
            return self.component_name

        return self.__class__.__name__

    def get_component_props(self) -> Dict[str, Any]:
        return {}
