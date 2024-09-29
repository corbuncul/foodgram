from rest_framework.pagination import PageNumberPagination

from recipes.constants import MAX_PAGE_SIZE, PAGE_SIZE


class UserRecipePagination(PageNumberPagination):

    page_size = PAGE_SIZE
    page_query_param = 'page'
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGE_SIZE
