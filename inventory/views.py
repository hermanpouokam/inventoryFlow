from rest_framework import viewsets
from .models import (Product, Category, Supplier,ClientCategory, Client,
                     Enterprise,PaymentInfo,Plan,User,SellPrice,Bill,Variant,
                     SalesPoint,Employee,EmployeeDebt,Packaging,RecordedPackaging,ProductBill,
                     PackagingHistory
                     )
from .serializers import (ProductSerializer, CategorySerializer, SupplierSerializer, ClientCategorySerializer, ClientSerializer,
                          EnterpriseSerializer, PaymentInfoSerializer,PlanSerializer,UserSerializer,CustomTokenObtainPairSerializer,SellPriceSerializer,BillSerializer,ProductVariantSerializer,
                          SalesPointSerializer,EmployeeSerializer,DelivererUpdateSerializer,UpdateDeliveredBillSerializer,EmployeeDebtSerializer,PayDebtSerializer,
                          PackagingSerializer,RecordedPackagingSerializer,ProductBillSerializer,
                          PackagingHistorySerializer
                          )
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenRefreshView,TokenObtainPairView
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.views import APIView
from django_filters import rest_framework as filters
from django.db.models import F
from rest_framework import serializers
from django.core.exceptions import PermissionDenied,ValidationError
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ClientFilter, CustomerBillFilter, SalesPointCategoryFilterBackend,SalesPointSupplierFilterBackend,SalesPointCategorySupplierFilterBackend
import pdfkit
from django.http import HttpResponse,JsonResponse
from django.template.loader import get_template
from django.utils.dateparse import parse_datetime

User = get_user_model()

class IsAdminOrManager(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.user.user_type == 'admin' or request.user.user_type == 'manager'
        )

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrManager]
    

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.user_type == 'admin':
            sales_point_ids = self.request.query_params.get('sales_points', None)
            if sales_point_ids:
                sales_point_ids = sales_point_ids.split(',')
                sales_points = SalesPoint.objects.filter(id__in=sales_point_ids)
                if not sales_points.exists():
                    raise ValidationError("One or more provided sales points do not exist.")
                return queryset.filter(sales_point__in=sales_points)
            else:
                return queryset
        else:
            return queryset.filter(sales_point=user.sales_point)

class UserProductsView(APIView):
    permission_classes = [IsAuthenticated]

    # if user.user_type == 'admin':
    #         return Product.objects.all()
    #     else:
    #         sales_point_ids = user.enterprise.sales_points.values_list('id', flat=True)
    #         return Product.objects.filter(sales_point__in=sales_point_ids)
    
    def get(self, request):
        user = request.user
        enterprise = user.enterprise

        if not enterprise:
            return Response({'detail': 'User does not belong to any enterprise.'}, status=status.HTTP_400_BAD_REQUEST)

        if user.user_type == 'admin':
            products = Product.objects.filter(enterprise=enterprise)
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            sales_point_id = user.sales_point
            products = Product.objects.filter(enterprise=enterprise,sales_point=sales_point_id)
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        sales_point_ids = self.request.query_params.get('sales_points', None)
        if sales_point_ids:
            sales_point_ids = sales_point_ids.split(',')
            sales_points = SalesPoint.objects.filter(id__in=sales_point_ids)
            if not sales_points.exists():
                raise ValidationError("One or more provided sales points do not exist.")
            queryset = queryset.filter(sales_point__in=sales_points)
        
        return queryset

class ClientCategoryViewSet(viewsets.ModelViewSet):
    queryset = ClientCategory.objects.all()
    serializer_class = ClientCategorySerializer
    permission_classes = [IsAdminOrManager]

    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data.copy()

        if user.user_type == 'admin':
            # Admin must provide sales point in the request
            if 'sales_point' not in data:
                return Response({"detail": "Admin must provide a sales point."}, status=status.HTTP_400_BAD_REQUEST)
        elif user.user_type == 'manager':
            # Manager uses their own sales point
            if not user.sales_point:
                return Response({"detail": "Manager must have an assigned sales point."}, status=status.HTTP_400_BAD_REQUEST)
            data['sales_point'] = user.sales_point.id
        else:
            return Response({"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SalesPointCategoryFilterBackend]
    # filterset_class = ClientFilter

    # def get_queryset(self):
    #     user = self.request.user
    #     queryset = Client.objects.filter(enterprise=user.enterprise)

    #     if user.user_type == 'admin':
    #         # Admin can filter by sales_point and client_category
    #         sales_point = self.request.query_params.get('sales_point')
    #         client_category = self.request.query_params.get('category')
    #         if sales_point:
    #             queryset = queryset.filter(sales_point__id=sales_point)
    #         if client_category:
    #             queryset = queryset.filter(client_category__id=client_category)
    #     elif user.user_type == 'manager':
    #         # Manager can only filter by client_category
    #         sales_point = user.sales_point
    #         queryset = queryset.filter(sales_point=sales_point)
    #         client_category = self.request.query_params.get('category')
    #         if client_category:
    #             queryset = queryset.filter(client_category__id=client_category)
    #     else:
    #         # Non-admin, non-manager users can only see their own sales point's clients
    #         sales_point = user.sales_point
    #         queryset = queryset.filter(sales_point=sales_point)

    #     return queryset
    
class EnterpriseViewSet(viewsets.ModelViewSet):
    queryset = Enterprise.objects.all()
    serializer_class = EnterpriseSerializer
    permission_classes = [IsAuthenticated]

class PaymentInfoViewSet(viewsets.ModelViewSet):
    queryset = PaymentInfo.objects.all()
    serializer_class = PaymentInfoSerializer
    permission_classes = [IsAuthenticated]

class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class UserCustomersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        enterprise = user.enterprise

        if not enterprise:
            return Response({'detail': 'User does not belong to any enterprise.'}, status=status.HTTP_400_BAD_REQUEST)

        client = Client.objects.filter(enterprise=enterprise)
        serializer = ClientSerializer(client, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RegisterUserView(generics.CreateAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            response = JsonResponse({
                'message': 'User registered successfully.',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'username': user.username,
                    'surname': user.surname,
                    'email': user.email,
                    'user_type': user.user_type,
                    'enterprise': user.enterprise
                },
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
            response.set_cookie(
                'access_token',
                str(refresh.access_token),
                httponly=True,
                secure=True,  
                samesite='Lax'
            )
            response.set_cookie(
                'refresh_token',
                str(refresh),
                httponly=True,
                secure=True,  
                samesite='Lax'
            )
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class RegisterEnterpriseView(generics.CreateAPIView):
    queryset = Enterprise.objects.all()
    serializer_class = EnterpriseSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Save the enterprise instance
        enterprise = serializer.save()
        user = self.request.user

        if user.enterprise is not None:
            raise ValidationError({"detail": "User is already associated with an enterprise."})
        
        # Associate the user with the newly created enterprise
        user.enterprise = enterprise
        user.save()
        
        return user

class SelectPlanView(generics.CreateAPIView):
    queryset = PaymentInfo.objects.all()
    serializer_class = PaymentInfoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        enterprise = user.enterprise
        payment_info = serializer.save(enterprise=enterprise)

        return Response(PaymentInfoSerializer(payment_info).data, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        refresh = RefreshToken.for_user(user)
        response = JsonResponse({
            'message': 'User registered successfully.',
            'user': {
                'id': user.id,
                'name': user.name,
                'username': user.username,
                'surname': user.surname,
                'email': user.email,
                'user_type': user.user_type,
                'enterprise': user.enterprise
            },
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
        response.set_cookie(
            'access_token',
            str(refresh.access_token),
            httponly=True,
            secure=True,  
            samesite='Lax'
        )
        response.set_cookie(
            'refresh_token',
            str(refresh),
            httponly=True,
            secure=True,  
            samesite='Lax'
        )
    
        return response
    
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CustomTokenRefreshView(TokenRefreshView):
    pass

class SellPriceListView(viewsets.ModelViewSet):
    queryset = SellPrice.objects.all()
    serializer_class = SellPriceSerializer
    permission_classes = [AllowAny]

class SellPriceDetailView(viewsets.ModelViewSet):
    queryset = SellPrice.objects.all()
    serializer_class = SellPriceSerializer

class BillCreateView(generics.CreateAPIView):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        enterprise = user.enterprise
       
        serializer.save(enterprise=enterprise)

class VariantCreateView(viewsets.ModelViewSet):
    queryset = Variant.objects.all()
    permission_classes = [AllowAny]
    serializer_class = ProductVariantSerializer

class BillFilter(filters.FilterSet):
    start_date = filters.DateTimeFilter(field_name="created_at", lookup_expr='gte')
    end_date = filters.DateTimeFilter(field_name="created_at", lookup_expr='lte')
    customer = filters.NumberFilter(field_name="customer")
    state = filters.CharFilter(field_name="state")
    sales_point = filters.NumberFilter(field_name="sales_point")

    class Meta:
        model = Bill
        fields = ['start_date', 'end_date', 'customer', 'state','sales_point']

class BillListView(generics.ListCreateAPIView):
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = BillFilter

    def perform_create(self, serializer):
        user = self.request.user
        if user.user_type != 'admin':
            # Use the authenticated user's sales point
            serializer.save(enterprise=user.enterprise, sales_point=user.sales_point)
        else:
            # Admin must provide sales_point
            sales_point = self.request.data.get('sales_point')
            if not sales_point:
                raise serializers.ValidationError({'sales_point': 'This field is required for admin users.'})
            serializer.save(enterprise=user.enterprise, sales_point=sales_point)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Iterate through all associated product bills
        for product_bill in instance.product_bills.all():
            if product_bill.is_variant:
                # If the product bill is a variant, increase the variant's quantity
                Variant.objects.filter(pk=product_bill.variant.id).update(quantity=F('quantity') + product_bill.quantity)
            else:
                # If the product bill is a standard product, increase the product's quantity
                Product.objects.filter(pk=product_bill.product.id).update(quantity=F('quantity') + product_bill.quantity)

        # Perform the deletion
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'admin':
            return Bill.objects.filter(enterprise=user.enterprise)
        else:
            sales_point = user.enterprise.sales_point
            return Bill.objects.filter(enterprise=user.enterprise,sales_point=sales_point)
        
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Update stock quantities
        for product_bill_data in request.data.get('product_bills', []):
            product = product_bill_data['product']
            quantity = product_bill_data['quantity']
            is_variant = product_bill_data['is_variant']
            variant_id = product_bill_data.get('variant_id')

            if is_variant:
                variant = Variant.objects.get(pk=variant_id)
                variant.quantity = F('quantity') - quantity
                variant.save()
            else:
                product_instance = Product.objects.get(pk=product)
                product_instance.quantity = F('quantity') - quantity
                product_instance.save()

        return Response(serializer.data)

class BillDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Perform the deletion
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class SalesPointCreateView(generics.CreateAPIView):
    queryset = SalesPoint.objects.all()
    serializer_class = SalesPointSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Check if user is admin
        user = self.request.user
        if user.user_type != 'admin':
            raise PermissionDenied('Only admins can create sales points.')
        
        # Save the SalesPoint with the enterprise of the signed-in user
        serializer.save(enterprise=user.enterprise)
    
class SalesPointListView(generics.ListAPIView):
    serializer_class = SalesPointSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Ensure the user is authenticated and has an enterprise associated with them
        if user.user_type == 'admin' and user.enterprise:
            # Return sales points related to the user's enterprise
            return SalesPoint.objects.filter(enterprise=user.enterprise)
        
        # Return an empty queryset if the user is not authenticated or has no associated enterprise
        return SalesPoint.objects.none()

class SalesPointUpdateView(generics.UpdateAPIView):
    queryset = SalesPoint.objects.all()
    serializer_class = SalesPointSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        user = self.request.user
        if user.user_type != 'admin':
            raise PermissionDenied('Only admins can update sales points.')
        serializer.save()

class SalesPointDeleteView(generics.DestroyAPIView):
    queryset = SalesPoint.objects.all()
    serializer_class = SalesPointSerializer
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        user = self.request.user
        if user.user_type != 'admin':
            raise PermissionDenied('Only admins can delete sales points.')
        instance.delete()

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['sales_point']

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'admin':
            return Employee.objects.filter(sales_point__enterprise=user.enterprise)
        elif user.user_type == 'manager':
            return Employee.objects.filter(sales_point=user.sales_point)
        else:
            return Employee.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.user_type in ['admin', 'manager']:
            if user.user_type != 'admin':
                # Use the authenticated user's sales point
                serializer.save(sales_point=user.sales_point)
            else:
                # Admin must provide sales_point
                sales_point = self.request.data.get('sales_point')
                if not sales_point:
                    raise serializers.ValidationError({'sales_point': 'This field is required for admin users.'})
                serializer.save()
        else:
            raise PermissionDenied('Only admins and managers can create employee.')
    
class DelivererUpdateViewSet(viewsets.ViewSet):

    def update_deliverer(self, request, pk=None):
        try:
            bill = Bill.objects.get(pk=pk)
        except Bill.DoesNotExist:
            return Response({'detail': 'Bill not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DelivererUpdateSerializer(bill, data=request.data, partial=True)
        
        if serializer.is_valid():
            # Explicitly handle state and deliverer updates
            state = serializer.validated_data.get('state')
            deliverer = serializer.validated_data.get('deliverer')

            if state == 'pending':
                bill.state = 'pending'
            if deliverer is not None:
                bill.deliverer = deliverer
            elif 'deliverer' in request.data and request.data['deliverer'] is None:
                bill.deliverer = None

            bill.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateDeliveredBillView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        bill_id = kwargs.get('pk')
        bill = get_object_or_404(Bill, pk=bill_id)

        # Ensure the bill is in 'pending' state before updating
        if bill.state != 'pending':
            return Response({"detail": "Bill must be in 'pending' state to update."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate and update the amount
        serializer = UpdateDeliveredBillSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['amount']
        reduce_from_balance = serializer.validated_data['reduce_from_balance']
        use_balance_as_paid = serializer.validated_data['use_balance_as_paid']

        # Calculate total_amount dynamically if not stored
        total_amount = sum(pb.quantity * pb.price for pb in bill.product_bills.all())

        if amount < 0:
            return Response({"detail": "Amount cannot be less than 0."}, status=status.HTTP_400_BAD_REQUEST)

        if amount > total_amount:
            return Response({"detail": "Amount cannot be greater than the total amount."}, status=status.HTTP_400_BAD_REQUEST)

        sales_point = bill.sales_point
        if sales_point:
            # Use transaction.atomic to ensure balance is updated correctly
            with transaction.atomic():
                # Update sales point balance if required
                if reduce_from_balance:
                    sales_point.balance += amount
                    sales_point.save()

                # Update client's balance if applicable
                client = bill.client
                if reduce_from_balance and client.balance < amount:
                    if use_balance_as_paid:
                        bill.paid = client.balance
                        client.balance = 0
                    else:
                        bill.paid = amount
                        client.balance -= amount
                elif reduce_from_balance:
                    bill.paid = amount
                    client.balance -= amount
                else:
                    bill.paid = amount

                client.save()

                # Update the bill's state
                bill.state = 'delivered'  # Update to the correct state
                bill.save()

        return Response({"detail": "Bill updated and sales point balance adjusted."}, status=status.HTTP_200_OK)

class EmployeeDebtViewSet(viewsets.ModelViewSet):
    queryset = EmployeeDebt.objects.none()
    serializer_class = EmployeeDebtSerializer
    permission_classes = [IsAuthenticated]
    
    # Placeholder queryset to satisfy DRF's requirements

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'admin':
            # Return all debts for admin users
            return EmployeeDebt.objects.all()
        elif user.user_type == 'manager':
            # Return debts associated with the manager's sales point
            sales_point = user.sales_point_set.first()  # Adjust this according to your actual model relationship
            if sales_point:
                return EmployeeDebt.objects.filter(employee__sales_point=sales_point)
            else:
                # If manager has no sales point, return an empty queryset or handle it as needed
                return EmployeeDebt.objects.none()
        else:
            # Employee does not have permission to view debts
            return EmployeeDebt.objects.none()

    def list(self, request, *args, **kwargs):
        user = self.request.user
        if user.user_type == 'employee':
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        user = self.request.user
        if user.user_type == 'employee':
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        return super().retrieve(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        user = self.request.user
        if user.user_type == 'employee':
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        user = self.request.user
        if user.user_type == 'employee':
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        if user.user_type == 'employee':
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

class PayDebtView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        debt_id = kwargs.get('pk')
        debt = get_object_or_404(EmployeeDebt, pk=debt_id)
        serializer = PayDebtSerializer(data=request.data, context={'debt': debt})
        serializer.is_valid(raise_exception=True)
        payment_amount = serializer.validated_data['amount']

        employee = debt.employee
        employee_salary = employee.monthly_salary

        with transaction.atomic():
            if payment_amount > employee_salary:
                # Reduce debt amount by the employee's salary
                remaining_debt = payment_amount - employee_salary
                debt.amount = remaining_debt
                employee.monthly_salary = 0  # All salary is used for debt
            else:
                # Reduce debt amount by the payment amount
                debt.amount -= payment_amount
                employee.monthly_salary -= payment_amount
            
            # Update debt status if fully paid
            if debt.amount <= 0:
                debt.status = 'paid'
                debt.amount = 0
            debt.save()
            employee.save()

        return Response({"detail": "Debt payment processed successfully."}, status=status.HTTP_200_OK)

class CustomerBillListView(generics.ListAPIView):
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomerBillFilter

    def get_queryset(self):
        user = self.request.user
        queryset = Bill.objects.filter(enterprise=user.enterprise)

        if user.user_type not in ['admin','manager']:
            # Non-admin users can only see bills related to their sales point
            raise ValidationError("You don't have permission to access")
        
        return queryset
    
def generate_pdf(request, bill_id):
    # Fetch bill data and template
    bill = get_object_or_404(Bill, pk=bill_id)
    template = get_template('bill_template.html')
    context = {'bill': bill}
    html = template.render(context)
    
    # Generate PDF from HTML
    pdf = pdfkit.from_string(html, False)
    
    # Create HTTP response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=bill_{bill_id}.pdf'
    
    return response

class PackagingViewSet(viewsets.ModelViewSet):
    queryset = Packaging.objects.all()
    serializer_class = PackagingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SalesPointSupplierFilterBackend]

class RecordedPackagingViewSet(viewsets.ModelViewSet):
    queryset = RecordedPackaging.objects.all()
    serializer_class = RecordedPackagingSerializer
    permission_classes = [IsAuthenticated]

class TokenVerifyView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        try:
            token = request.data.get('token')
            if not token:
                return Response({'detail': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

            decoded_token = AccessToken(token)
            return Response({'detail': 'Token is valid'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'code': str(e), 'detail': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SalesPointCategorySupplierFilterBackend]

class ProductBillListView(generics.ListAPIView):
    queryset = ProductBill.objects.all()
    serializer_class = ProductBillSerializer

class PackagingHistoryListView(generics.ListAPIView):
    serializer_class = PackagingHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        sales_point = self.request.query_params.get('sales_point')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        queryset = PackagingHistory.objects.all()

        if user.user_type == 'admin':
            if sales_point:
                queryset = queryset.filter(sales_point=sales_point)
            if user.enterprise:
                queryset = queryset.filter(packaging__enterprise=user.enterprise)

        else:  # Non-admin users
            queryset = queryset.filter(sales_point=user.sales_point)

        if start_date:
            start_date = parse_datetime(start_date)
            queryset = queryset.filter(timestamp__gte=start_date)
        
        if end_date:
            end_date = parse_datetime(end_date)
            queryset = queryset.filter(timestamp__lte=end_date)

        return queryset.order_by('-timestamp')