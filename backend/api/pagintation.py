from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """
    Кастомный пагинатор с атрибутом для вывода количества страниц.
    """
    page_size_query_param = 'limit'
