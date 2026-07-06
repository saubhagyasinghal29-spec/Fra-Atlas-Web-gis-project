from rest_framework.pagination import CursorPagination


class TimestampCursorPagination(CursorPagination):
    ordering = "-created_at"
    page_size = 50
    max_page_size = 1000
