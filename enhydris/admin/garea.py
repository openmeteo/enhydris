import os
import tempfile
import textwrap
from zipfile import BadZipFile, ZipFile

from django import forms
from django.contrib import messages
from django.contrib.gis import admin
from django.contrib.gis.forms import MultiPolygonField, OSMWidget
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import MultiPolygon
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import ugettext_lazy as _

from enhydris import models


class MissingAttribute(Exception):
    pass


@admin.register(models.GareaCategory)
class GareaCategory(admin.ModelAdmin):
    pass


class GareaUploadForm(forms.Form):
    category = forms.ModelChoiceField(
        required=True, label=_("Object category"), queryset=models.GareaCategory.objects
    )
    file = forms.FileField(
        required=True,
        label=_("File"),
        help_text=_(
            """
            The shapefile. It must be a .zip containing a .shp, a .shx and a .dbf. The
            objects in the shapefile must contain a "Name" attribute and optionally a
            "Code" attribute (any other attributes will be ignored). All objects in the
            selected category will be removed and replaced with the ones found in the
            shapefile.
            """
        ),
    )

    def clean_file(self):
        data = self.cleaned_data["file"]
        try:
            zipfile = ZipFile(data)
            interesting_files = {
                x
                for x in zipfile.namelist()
                if x.lower()[-4:] in (".shp", ".shx", ".dbf")
            }
            extensions = sorted([x.lower()[-4:] for x in interesting_files])
            if extensions != [".dbf", ".shp", ".shx"]:
                raise BadZipFile()
        except BadZipFile:
            raise forms.ValidationError(
                "This is not a zip file, or it doesn't contain exactly one .shp, .shx "
                "and .dbf file."
            )
        return data


class GareaForm(forms.ModelForm):
    geometry = MultiPolygonField(
        widget=OSMWidget,
        disabled=True,
        required=False,
        help_text=textwrap.dedent(
            """\
            This map is only for viewing, not for editing the area. To change the area
            you need to upload another shapefile.
            """
        ),
    )

    class Meta:
        model = models.Garea
        exclude = ()


@admin.register(models.Garea)
class GareaAdmin(admin.ModelAdmin):
    form = GareaForm
    list_display = ["id", "name", "code", "category"]
    list_filter = ["category"]
    search_fields = ("id", "name", "code")

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path("bulk_add/", self.admin_site.admin_view(self.bulk_add))]
        return new_urls + urls

    def bulk_add(self, request):
        if request.method == "POST":
            return self._bulk_post(request)
        else:
            return self._get_template_response(request, GareaUploadForm())

    def _bulk_post(self, request):
        form = GareaUploadForm(request.POST, request.FILES)
        if form.is_valid():
            return self._process_uploaded_form(request, form)
        else:
            return self._get_template_response(request, form)

    def _process_uploaded_form(self, request, form):
        try:
            category = models.GareaCategory.objects.get(id=request.POST["category"])
            nnew, nold = self._process_uploaded_shapefile(
                category, request.FILES["file"]
            )
        except IntegrityError as e:
            messages.add_message(request, messages.ERROR, str(e))
        else:
            messages.add_message(
                request,
                messages.INFO,
                _(
                    "Replaced {} existing objects in category {} with {} new objects"
                ).format(nold, category.descr, nnew),
            )
        return HttpResponseRedirect("")

    def _get_template_response(self, request, form):
        return TemplateResponse(
            request, "admin/enhydris/garea/bulk_add.html", {"form": form}
        )

    @transaction.atomic
    def _process_uploaded_shapefile(self, category, file):
        zipfile = ZipFile(file)
        shapefilename = [x for x in zipfile.namelist() if x.lower()[-4:] == ".shp"][0]
        with tempfile.TemporaryDirectory() as tmpdir:
            zipfile.extractall(path=tmpdir)
            shapefile = os.path.join(tmpdir, shapefilename)
            layer = DataSource(shapefile)[0]
            delete_result = models.Garea.objects.filter(category=category).delete()
            try:
                nold = delete_result[1]["enhydris.Garea"]
            except KeyError:
                nold = 0
            nnew = 0
            layer = DataSource(shapefile)[0]
            for feature in layer:
                garea = self._get_garea(feature, category)
                garea.save()
                nnew += 1
        return nnew, nold

    def _get_garea(self, feature, category):
        garea = models.Garea()
        if isinstance(feature.geom.geos, MultiPolygon):
            garea.geom = feature.geom.geos
        else:
            garea.geom = MultiPolygon(feature.geom.geos)
        garea.name = self._get_feature_attr(feature, "Name")
        garea.code = self._get_feature_attr(feature, "Code", allow_empty=True) or ""
        garea.category = category
        return garea

    def _get_feature_attr(self, feature, attr, allow_empty=False):
        try:
            value = feature.get(attr)
        except IndexError:
            value = None
        if value or allow_empty:
            return value
        raise MissingAttribute(
            'Feature with fid={} does not have a "{}" attribute'.format(
                feature.fid, attr
            )
        )
