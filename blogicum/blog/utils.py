from django.core.paginator import Paginator

def paginate_queryset(queryset, page_number, per_page=10):
    """
    Пагинация для queryset
    """
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page_number)