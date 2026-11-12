from django import template
from django.http import QueryDict


register = template.Library()


@register.simple_tag
def url_tag(cale, parametri, tag, elimina=False):
    parametri = parametri.copy() if parametri else QueryDict(mutable=True)
    taguri = parametri.pop("tag", [])
    if elimina:
        taguri = [valoare for valoare in taguri if valoare != tag]
    elif tag not in taguri:
        taguri.append(tag)
    if taguri:
        parametri.setlist("tag", taguri)
    return f"{cale}?{parametri.urlencode()}" if parametri else cale
