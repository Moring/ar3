from __future__ import annotations

from typing import Iterable, Sequence

from django.db.models import Q, QuerySet

from .models import File


def _normalize_category_values(categories: Iterable) -> Sequence[str]:
    normalized = []
    for item in categories:
        if not item:
            continue
        if hasattr(item, "slug"):
            normalized.append(item.slug)
        else:
            normalized.append(str(item))
    return normalized


def select_docs(categories: Iterable = None, tags: Iterable = None) -> QuerySet[File]:
    categories = categories or []
    tags = tags or []
    category_slugs = _normalize_category_values(categories)
    tag_names = [getattr(tag, "name", str(tag)) for tag in tags if tag]

    if not category_slugs and not tag_names:
        return File.objects.none()

    query = Q()
    if category_slugs:
        query |= Q(category__slug__in=category_slugs)
    if tag_names:
        query |= Q(tags__name__in=tag_names)
    return File.objects.filter(query).distinct()
