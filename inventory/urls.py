from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (ProductViewSet, CategoryViewSet, SupplierViewSet, ClientCategoryViewSet, ClientViewSet,
                    EnterpriseViewSet,PaymentInfoViewSet,PlanViewSet,UserViewSet,RegisterUserView,RegisterEnterpriseView,SelectPlanView,
                    LoginView,CustomTokenRefreshView,CustomTokenObtainPairView,BillListView,
                    SellPriceListView,BillCreateView,UserProductsView,UserCustomersView,VariantCreateView,
                    BillDetailView,SalesPointCreateView, SalesPointUpdateView, SalesPointDeleteView,EmployeeViewSet,
                    DelivererUpdateViewSet,UpdateDeliveredBillView,EmployeeDebtViewSet,PayDebtView,SalesPointListView,
                    CustomerBillListView,generate_pdf,RecordedPackagingViewSet,PackagingViewSet,TokenVerifyView,
                    ProductListView,ProductBillListView,PackagingHistoryListView
                    )

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'client-categories', ClientCategoryViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'enterprises', EnterpriseViewSet)  
router.register(r'payment-info', PaymentInfoViewSet)
router.register(r'plans', PlanViewSet)
router.register(r'payment-info', PaymentInfoViewSet)
router.register(r'plans', PlanViewSet)
router.register(r'users', UserViewSet)
router.register(r'sell-prices', SellPriceListView)
router.register(r'variants', VariantCreateView)
router.register(r'employees', EmployeeViewSet)
router.register(r'employeedebts', EmployeeDebtViewSet)
router.register(r'recorded-packagings', RecordedPackagingViewSet)
router.register(r'packagings', PackagingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register-user/', RegisterUserView.as_view(), name='register-user'),
    path('register-enterprise/', RegisterEnterpriseView.as_view(), name='register-enterprise'),
    path('select-plan/', SelectPlanView.as_view(), name='select-plan'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('user-products/', UserProductsView.as_view(), name='user-products'),
    path('user-customers/', UserCustomersView.as_view(), name='user-customers'),
    path('create-bill/', BillCreateView.as_view(), name='create-bill'),
    path('bills/', BillListView.as_view(), name='bill-list'),
    path('bills/<int:pk>/', BillDetailView.as_view(), name='bill-detail'),
    path('sales-points/', SalesPointCreateView.as_view(), name='sales-point-create'),
    path('sales-points/<int:pk>/', SalesPointUpdateView.as_view(), name='sales-point-update'),
    path('sales-points/<int:pk>/delete/', SalesPointDeleteView.as_view(), name='sales-point-delete'),
    path('bills/<int:pk>/update-deliverer/', DelivererUpdateViewSet.as_view({'put': 'update_deliverer'}), name='update-deliverer'),
    path('bills/<int:pk>/update-delivered/', UpdateDeliveredBillView.as_view(), name='update-delivered-bill'),
    path('employeedebts/<int:pk>/pay/', PayDebtView.as_view(), name='pay-debt'),
    path('sales-points-list/', SalesPointListView.as_view(), name='sales-point-list'),
    path('bills/customer/', CustomerBillListView.as_view(), name='customer-bill-list'),
    path('api/bills/<int:bill_id>/generate-pdf/', generate_pdf, name='generate_pdf'),
    path('verify-token/', TokenVerifyView.as_view(), name='verify_token'),
    path('products-list/', ProductListView.as_view(), name='product-list'),
    path('product-bills/', ProductBillListView.as_view(), name='product_bill_list'),
    path('packaging-history/', PackagingHistoryListView.as_view(), name='packaging-history-list'),


]    
