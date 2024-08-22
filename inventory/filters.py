import django_filters
from .models import Client,Bill
from django.utils import timezone
from rest_framework.filters import BaseFilterBackend

class ClientFilter(django_filters.FilterSet):
    sales_point = django_filters.NumberFilter(field_name="sales_point__id")
    client_category = django_filters.NumberFilter(field_name="client_category__id")

    class Meta:
        model = Client
        fields = ['sales_point', 'client_category']
    
class CustomerBillFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="created_at", lookup_expr='gte', method='filter_start_date')
    end_date = django_filters.DateFilter(field_name="created_at", lookup_expr='lte', method='filter_end_date')
    customer_code = django_filters.CharFilter(field_name='customer__code', method='filter_customer_code')

    class Meta:
        model = Bill
        fields = ['start_date', 'end_date', 'customer_code']

    def filter_start_date(self, queryset, name, value):
        if not value:
            value = timezone.now().date()
        return queryset.filter(created_at__gte=value)

    def filter_end_date(self, queryset, name, value):
        if not value:
            value = timezone.now().date()
        return queryset.filter(created_at__lte=value)

    def filter_customer_code(self, queryset, name, value):
        try:
            customer = Client.objects.get(code=value)
            return queryset.filter(customer=customer)
        except Client.DoesNotExist:
            return queryset.none()

class SalesPointCategorySupplierFilterBackend(BaseFilterBackend):
     
     def filter_queryset(self, request, queryset, view):
        sales_point_ids = request.query_params.getlist('sales_point')
        category_ids = request.query_params.getlist('category')
        supplier_ids = request.query_params.getlist('supplier')

        if sales_point_ids:
            queryset = queryset.filter(sales_point__id__in=sales_point_ids)
        if category_ids:
            queryset = queryset.filter(category__id__in=category_ids)
        if supplier_ids:
            queryset = queryset.filter(supplier__id__in=supplier_ids)

        return queryset

class SalesPointSupplierFilterBackend(BaseFilterBackend):
     
     def filter_queryset(self, request, queryset, view):
        sales_point_ids = request.query_params.getlist('sales_point')
        supplier_ids = request.query_params.getlist('supplier')

        if sales_point_ids:
            queryset = queryset.filter(sales_point__id__in=sales_point_ids)
        if supplier_ids:
            queryset = queryset.filter(supplier__id__in=supplier_ids)

        return queryset
    
class SalesPointCategoryFilterBackend(BaseFilterBackend):
     
     def filter_queryset(self, request, queryset, view):
        sales_point_ids = request.query_params.getlist('sales_point')
        category_ids = request.query_params.getlist('category')

        if sales_point_ids:
            queryset = queryset.filter(sales_point__id__in=sales_point_ids)
        if category_ids:
            queryset = queryset.filter(category__id__in=category_ids)


        return queryset