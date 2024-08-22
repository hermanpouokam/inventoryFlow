from .models import (Product, Category, Supplier,ClientCategory, Client,Enterprise,
                     PaymentInfo, Plan,EnterpriseDetails,SellPrice,ProductBill,Bill,Variant,
                     SalesPoint, Employee,EmployeeDebt,Packaging,RecordedPackaging,PackageProductBill,
                     PackagingHistory
                     )
from django.contrib.auth import get_user_model
from datetime import timedelta,datetime
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.db.models import F
from django.shortcuts import get_object_or_404

User = get_user_model()

class EnterpriseDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnterpriseDetails
        fields = ['enterprise', 'balance', 'created_at', 'last_update']

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'description', 'price', 'duration']

class EnterpriseSerializer(serializers.ModelSerializer):
    plan_id = serializers.IntegerField(write_only=True)
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Enterprise
        fields = ['id', 'name', 'address', 'phone', 'email', 'created_at', 'last_update', 'plan_id', 'plan']

    def create(self, validated_data):
        plan_id = validated_data.pop('plan_id')
        plan = Plan.objects.get(id=plan_id)
        
        # Create the Enterprise instance
        enterprise = Enterprise.objects.create(**validated_data)
        
        # Associate the plan with the enterprise
        enterprise.plan = plan
        enterprise.save()

        # Create PaymentInfo
        PaymentInfo.objects.create(
            enterprise=enterprise,
            plan=plan,
            amount=plan.price,
            payment_method='Default',  # Set the default payment method or get it from the request
            next_due_date=datetime.now() + timedelta(days=plan.duration),
        )
        
        # # Handle EnterpriseDetails
        # details_data = validated_data.pop('details', None)
        # if details_data:
        #     EnterpriseDetails.objects.create(enterprise=enterprise, **details_data)
        # else:
        #     EnterpriseDetails.objects.create(enterprise=enterprise)

        return enterprise

class SalesPointSerializer(serializers.ModelSerializer):
    enterprise = serializers.PrimaryKeyRelatedField(read_only=True, required=False)

    class Meta:
        model = SalesPoint
        fields = ['id', 'name', 'enterprise', 'balance', 'address', 'created_at', 'last_update']

    def validate(self, data):
        user = self.context['request'].user
        if not user.user_type == 'admin':
            raise serializers.ValidationError("Unauthorized user.")
        return data
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        validated_data['enterprise'] = user.enterprise

        return super().create(validated_data)


class CategorySerializer(serializers.ModelSerializer):
    enterprise = serializers.PrimaryKeyRelatedField(read_only=True,required=False)
    sales_point_details = SalesPointSerializer(source='sales_point',read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'created_at', 'enterprise', 'ab_name', 'sales_point', 'sales_point_details']
    
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        # Set enterprise and sales_point based on signed-in user's details
        validated_data['enterprise'] = user.enterprise
        if user.user_type == 'admin':
            sales_point = validated_data.get('sales_point')
            if not sales_point:
                raise serializers.ValidationError({'sales_point': 'This field is required for admin users.'})
        else:
            validated_data['sales_point'] = user.sales_point

        return super().create(validated_data)
        
class SupplierSerializer(serializers.ModelSerializer):
    enterprise = serializers.PrimaryKeyRelatedField(read_only=True,required=False)
    sales_point_details = SalesPointSerializer(source='sales_point',read_only=True)
    
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'email', 'created_at', 'sales_point', 'sales_point_details', 'enterprise','sales_point', 'contact', 'ab_name']
    
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        # Set enterprise and sales_point based on signed-in user's details
        validated_data['enterprise'] = user.enterprise
        if user.user_type == 'admin':
            sales_point = validated_data.get('sales_point')
            if not sales_point:
                raise serializers.ValidationError({'sales_point': 'This field is required for admin users.'})
        else:
            validated_data['sales_point'] = user.sales_point

        return super().create(validated_data)

class SellPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellPrice
        fields = ['id', 'product', 'price', 'created_at', 'last_update']

class ProductVariantSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = Variant
        fields = ['id', 'name', 'quantity', 'product']

class EmployeeSerializer(serializers.ModelSerializer):
    sales_point_details = SalesPointSerializer(source='sales_point',read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'name', 'surname', 'salary', 'monthly_salary', 'role', 'enterprise', 'sales_point', 'sales_point_details', 'is_deliverer']

class PackagingSerializer(serializers.ModelSerializer):
    enterprise = serializers.PrimaryKeyRelatedField(queryset=Enterprise.objects.all(), required=False)
    sales_point = serializers.PrimaryKeyRelatedField(queryset=SalesPoint.objects.all(), required=False)
    sales_point_details = SalesPointSerializer(source='sales_point',read_only=True)
    supplier_details = SalesPointSerializer(source='supplier',read_only=True)

    class Meta:
        model = Packaging
        fields = ['id', 'name', 'price', 'supplier', 'sales_point_details', 'supplier_details', 'full_quantity', 'empty_quantity', 'created_at', 'updated_at', 'sales_point', 'enterprise']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        validated_data['enterprise'] = user.enterprise
        if user.user_type == 'admin':
            sales_point = validated_data.get('sales_point')
            if not sales_point:
                raise serializers.ValidationError({'sales_point': 'This field is required for admin users.'})
        else:
            validated_data['sales_point'] = user.sales_point

        return super().create(validated_data)
    
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    enterprise = serializers.PrimaryKeyRelatedField(required=False,read_only=True)
    supplier = SupplierSerializer(read_only=True)
    sell_prices = SellPriceSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    total_quantity = serializers.ReadOnlyField()
    sales_point = serializers.PrimaryKeyRelatedField(queryset=SalesPoint.objects.all())
    sales_point_details = SalesPointSerializer(source='sales_point',read_only=True)
    category_details = CategorySerializer(source='category',read_only=True)
    package_details = PackagingSerializer(source='package',read_only=True)

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(), source='supplier', write_only=True
    )
    package_id = serializers.PrimaryKeyRelatedField(
        queryset=Packaging.objects.all(), source='package', write_only=True, required=False
    )

    class Meta:
        model = Product
        fields = ['id', 'name', 'enterprise', 'total_quantity', 'sales_point', 'sales_point_details', 'category_details' ,'package', 'package_details',
        'quantity', 'created_at', 'with_variant', 'last_update', 'category', 'category_id', 'supplier', 'product_code','sell_prices', 'supplier_id', 
        'price', 'is_beer','variants', 'package_id']
    
    def validate(self, data):
        if data.get('is_beer'):
            package = data.get('package')
            if not package:
                raise serializers.ValidationError({"package": "Package must be provided if the product is beer."})
            
            # Check if quantity is less than or equal to the empty_quantity of the selected packaging
            quantity = data.get('quantity')
            if quantity > package.empty_quantity:
                raise serializers.ValidationError({"quantity": "Quantity cannot be greater than the empty quantity of the selected packaging."})

        
        category = data.get('category')
        sales_point = data.get('sales_point')
        if category and sales_point and category.sales_point != sales_point:
            raise serializers.ValidationError({"category": "Category does not belong to the sales point."})
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        # Set the enterprise from the signed-in user
        validated_data['enterprise'] = user.enterprise

        # Check and assign sales_point based on the user type
        if user.user_type == 'admin':
            sales_point = validated_data.get('sales_point')
            if not sales_point:
                raise serializers.ValidationError({'sales_point': 'This field is required for admin users.'})
        else:
            validated_data['sales_point'] = user.sales_point

        # Handle packaging adjustments for beer products
        if validated_data.get('is_beer'):
            package = validated_data['package']
            quantity = validated_data['quantity']
            full_quantity_before = package.full_quantity
            empty_quantity_before = package.empty_quantity
            if package.empty_quantity >= quantity:
                package.empty_quantity -= quantity
                package.full_quantity += quantity
                package.save()
            else:
                raise serializers.ValidationError({"quantity": "Quantity cannot be greater than the empty quantity of the selected packaging."})

        product = super().create(validated_data)
        if validated_data.get('is_beer'):
            PackagingHistory.objects.create(
                packaging=package,
                product=product,
                action=f'create',
                quantity_changed=quantity,
                full_quantity_before=full_quantity_before,
                empty_quantity_before=empty_quantity_before,
                full_quantity_after=package.full_quantity,
                empty_quantity_after=package.empty_quantity,
                performed_by=user,
                sales_point=product.sales_point
            )
            
        return product


class ClientCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientCategory
        fields = ['id', 'name', 'created_at', 'enterprise', 'sales_point', 'last_update']


class ClientSerializer(serializers.ModelSerializer):
    client_category = serializers.PrimaryKeyRelatedField(queryset=ClientCategory.objects.all())
    sales_point = serializers.PrimaryKeyRelatedField(queryset=SalesPoint.objects.all(), required=False)
    sales_point_details = SalesPointSerializer(source='sales_point', read_only=True)
    client_category_details = SalesPointSerializer(source='client_category', read_only=True)
    enterprise = serializers.PrimaryKeyRelatedField(queryset=Enterprise.objects.all(), required=False)

    class Meta:
        model = Client 
        fields = ['id', 'name', 'surname', 'number', 'address', 'balance', 'email', 'client_category_details', 'sales_point', 'sales_point_details', 'created_at', 'last_update', 'code', 'client_category', 'enterprise']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        # Set enterprise and sales_point based on signed-in user's details
        validated_data['enterprise'] = user.enterprise
        if user.user_type == 'admin':
            sales_point = validated_data.get('sales_point')
            if not sales_point:
                raise serializers.ValidationError({'sales_point': 'This field is required for admin users.'})
        else:
            validated_data['sales_point'] = user.sales_point

        return super().create(validated_data)

class PaymentInfoSerializer(serializers.ModelSerializer):
    plan = PlanSerializer()

    class Meta:
        model = PaymentInfo
        fields = '__all__'

    def create(self, validated_data):
        plan_data = validated_data.pop('plan')
        plan = Plan.objects.create(**plan_data)
        payment_info = PaymentInfo.objects.create(plan=plan, **validated_data)
        return payment_info
    
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'surname', 'username','email', 'password', 'enterprise', 'number', 'user_type','created_at', 'last_update']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            name=validated_data['name'],
            surname=validated_data['surname'],
            user_type=validated_data.get('user_type', 'employee')
        )
        return user

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password', 'email')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'], validated_data['email'], validated_data['password'])
        return user

class UpdateUserEnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['enterprise']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        if username and password:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise serializers.ValidationError('User does not exist.')

            if not user.check_password(password):
                raise serializers.ValidationError('Invalid username or password.')

            if not user.is_active:
                raise serializers.ValidationError('User is inactive.')

            refresh = self.get_token(user)
            enterprise_data = None
            if user.enterprise:
                enterprise_serializer = EnterpriseSerializer(user.enterprise)
                enterprise_data = enterprise_serializer.data
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'name': user.name,
                    'surname': user.surname,
                    'enterprise': enterprise_data
                }
            }
        else:
            raise serializers.ValidationError('Must include "username" and "password".')

        return super().validate(attrs)

class PackageProductBillSerializer(serializers.ModelSerializer):
    packaging_details = PackagingSerializer(source='packaging', read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = PackageProductBill
        fields = ['id', 'packaging', 'packaging_details', 'quantity', 'record', 'total_amount']

    def get_total_amount(self, obj):
        return obj.record * obj.packaging.price

class ProductBillSerializer(serializers.ModelSerializer):
    price = serializers.ReadOnlyField(source='sell_price.price')
    is_variant = serializers.BooleanField()
    product_details = serializers.SerializerMethodField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    total_amount = serializers.SerializerMethodField()
    benefit = serializers.SerializerMethodField()
    package_product_bill = PackageProductBillSerializer(read_only=True)
    record_package = serializers.IntegerField(required=False, default=0)

    class Meta:
        model = ProductBill
        fields = ['id', 'product', 'variant_id', 'sell_price', 'quantity', 'created_at', 'price',
                   'is_variant', 'product_details', 'total_amount', 'benefit', 'package_product_bill', 'record_package']

    def get_product_details(self, obj):
        if obj.is_variant and obj.variant_id:
            try:
                variant = Variant.objects.get(pk=obj.variant_id)
                product = variant.product
                return {
                    'id': product.id,
                    'name': f"{product.name} - {variant.name}",
                    'product_code': product.product_code,
                    'quantity': variant.quantity,
                    'created_at': product.created_at,
                    'last_update': product.last_update,
                    'category': product.category.name,
                    'supplier': product.supplier.name,
                    'price': product.price,
                    'is_beer': product.is_beer,
                    'enterprise': product.enterprise.name
                }
            except Variant.DoesNotExist:
                raise serializers.ValidationError({'product': 'Product variant does not exist.'})
        else:
            try:
                product = Product.objects.get(pk=obj.product.id)
                return {
                    'id': product.id,
                    'name': product.name,
                    'product_code': product.product_code,
                    'quantity': product.quantity,
                    'created_at': product.created_at,
                    'last_update': product.last_update,
                    'category': product.category.name,
                    'supplier': product.supplier.name,
                    'price': product.price,
                    'is_beer': product.is_beer,
                    'enterprise': product.enterprise.name
                }
            except Product.DoesNotExist:
                raise serializers.ValidationError({'product': 'Product does not exist.'})
            
    def get_total_amount(self, obj):
        return obj.quantity * obj.sell_price.price

    def get_benefit(self, obj):
        product_price = self.get_product_details(obj)['price']
        return (obj.sell_price.price - product_price) * obj.quantity

    def validate(self, data):
        product = data['product']
        is_variant = data['is_variant']
        variant_id = data.get('variant_id')

        if is_variant:
            if not variant_id:
                raise serializers.ValidationError({'variant_id': 'Variant ID is required for variant products.'})
            if not Variant.objects.filter(pk=variant_id).exists():
                raise serializers.ValidationError({'variant_id': 'Product variant does not exist.'})
        else:
            if not Product.objects.filter(pk=product.id).exists():
                raise serializers.ValidationError({'product': 'Product does not exist.'})

        sell_price = data['sell_price']
        if not SellPrice.objects.filter(pk=sell_price.id).exists():
            raise serializers.ValidationError({'sell_price': 'Sell price does not exist.'})

        return data

    def create(self, validated_data):
        is_variant = validated_data.pop('is_variant')
        product = validated_data['product']
        variant_id = validated_data.get('variant_id')
        
        if is_variant:
            variant = Variant.objects.get(pk=variant_id)
            if variant.quantity < validated_data['quantity']:
                raise serializers.ValidationError({'quantity': 'Insufficient quantity for variant.'})
            variant.quantity -= validated_data['quantity']
            variant.save()
        else:
            if product.quantity < validated_data['quantity']:
                raise serializers.ValidationError({'quantity': 'Insufficient quantity for product.'})
            product.quantity -= validated_data['quantity']
            product.save()

        product_bill = ProductBill.objects.create(**validated_data)
        return product_bill
    
class BillSerializer(serializers.ModelSerializer):
    product_bills = ProductBillSerializer(many=True)
    customer_name = serializers.CharField(required=False, allow_blank=True)
    customer_details = ClientSerializer(source='customer', read_only=True)
    sales_point = serializers.PrimaryKeyRelatedField(queryset=SalesPoint.objects.all())
    sales_point_details = SalesPointSerializer(source='sales_point', read_only=True)
    deliverer_details = EmployeeSerializer(source='deliverer', read_only=True)
    total = serializers.SerializerMethodField()
    total_bill_amount = serializers.SerializerMethodField()

    class Meta:
        model = Bill
        fields = ['id', 'bill_number', 'customer', 'sales_point', 'deliverer', 'deliverer_details',
                  'total', 'sales_point_details', 'customer_details', 'sales_point', 'paid',
                  'customer_name', 'created_at', 'delivery_date', 'state', 'product_bills', 'total_bill_amount', 'deliverer',
                  'deliverer_details']

    def validate(self, attrs):
        user = self.context['request'].user
        customer_id = attrs.get('customer')

        if user.user_type == 'admin':
            if customer_id is None:
                sales_point = attrs.get('sales_point')
                customer = attrs.get('sales_point')
                if not sales_point:
                    raise serializers.ValidationError({'sales_point': 'This field is required for admin users when customer is 0.'})
                if not attrs.get('customer_name'):
                    raise serializers.ValidationError({'customer_name': 'Customer name is required if customer is 0.'})
            else:
                customer = get_object_or_404(Client, pk=customer_id.id)
                attrs['sales_point'] = customer.sales_point
                attrs['customer_name'] = f"{customer.name} {customer.surname}"
        else:
            attrs['sales_point'] = user.sales_point

        return attrs

    def get_total(self, obj):
        return sum(pb.quantity * pb.price for pb in obj.product_bills.all())
    
    def get_total_bill_amount(self, obj):
        total = 0
        for pb in obj.product_bills.all():
            total += pb.quantity * pb.price
            package_product_bill = getattr(pb, 'package_product_bill', None)
            if package_product_bill:
                total += package_product_bill.record * package_product_bill.packaging.price
        return total

    def create(self, validated_data):
        product_bills_data = validated_data.pop('product_bills')
        request = self.context.get('request')
        enterprise = request.user.enterprise
        bill = Bill.objects.create(**validated_data)

        for product_bill_data in product_bills_data:
            product_id = product_bill_data['product']
            sell_price = product_bill_data['sell_price']
            quantity = product_bill_data['quantity']
            is_variant = product_bill_data['is_variant']
            variant_id = product_bill_data.get('variant_id')
            record_package = product_bill_data.get('record_package',0)

            if is_variant:
                if Variant.objects.filter(id=variant_id).exists():
                    variant = Variant.objects.get(id=variant_id)
                    if variant.quantity >= quantity:
                        variant.quantity -= quantity
                        variant.save()

                        product_instance = variant.product
                        if product_instance.is_beer:
                            empty_quantity_needed = quantity
                            packaging = product_instance.package
                            if packaging:
                                if record_package > empty_quantity_needed:
                                    raise serializers.ValidationError({'record_package': f"Packaging to record can't be greater than needed packaging for product {product_instance.name}"})
                                else:
                                    record_quantity = empty_quantity_needed - record_package
                                    ProductBillInstance = ProductBill.objects.create(
                                        bill=bill,
                                        product=product_instance,
                                        sell_price=sell_price,
                                        quantity=quantity,
                                        is_variant=True,
                                        variant_id=variant_id
                                    )
                                    PackageProductBill.objects.create(
                                        product_bill=ProductBillInstance,
                                        packaging=packaging,
                                        quantity=empty_quantity_needed,
                                        record=record_package
                                    )
                                    packaging.full_quantity -= empty_quantity_needed
                                    packaging.empty_quantity += record_quantity
                                    if packaging.full_quantity < 0:
                                        packaging.full_quantity = 0
                                    packaging.save()
                        else:
                            ProductBill.objects.create(
                                        bill=bill,
                                        product=product_instance,
                                        sell_price=sell_price,
                                        quantity=quantity,
                                        is_variant=True,
                                        variant_id=variant_id
                                    )
                    else:
                        raise serializers.ValidationError({'quantity': f"Not enough quantity for the variant product. {variant.name}"})
                else:
                    raise serializers.ValidationError({'variant_id': 'Product variant does not exist.'})
            else:
                if Product.objects.filter(id=product_id.id).exists():
                    product_instance = Product.objects.get(id=product_id.id)
                    if product_instance.quantity >= quantity:
                        product_instance.quantity -= quantity
                        product_instance.save()

                        if product_instance.is_beer:
                            empty_quantity_needed = quantity
                            packaging = product_instance.package
                            if packaging:
                                if record_package > empty_quantity_needed:
                                    raise serializers.ValidationError({'record_package': f"Packaging to record can't be greater than needed packaging for product {product_instance.name}"})
                                else:
                                    record_quantity = empty_quantity_needed - record_package
                                    ProductBillInstance = ProductBill.objects.create(
                                        bill=bill,
                                        product=product_instance,
                                        sell_price=sell_price,
                                        quantity=quantity,
                                        is_variant=False
                                    )
                                    PackageProductBill.objects.create(
                                        product_bill=ProductBillInstance,
                                        packaging=packaging,
                                        quantity=empty_quantity_needed,
                                        record=record_package
                                    )
                                    packaging.empty_quantity += record_package
                                    packaging.full_quantity -= empty_quantity_needed
                                    if packaging.full_quantity < 0:
                                        packaging.full_quantity = 0
                                    packaging.save()
                        else:
                            ProductBillInstance = ProductBill.objects.create(
                                        bill=bill,
                                        product=product_instance,
                                        sell_price=sell_price,
                                        quantity=quantity,
                                        is_variant=False
                                    )
                    else:
                        raise serializers.ValidationError({'quantity': f"c. {product_instance.name}"})
                else:
                    raise serializers.ValidationError({'product': 'Product does not exist.'})

        return bill

    def update(self, instance, validated_data):
        product_bills_data = validated_data.pop('product_bills')
        instance.delivery_date = validated_data.get('delivery_date', instance.delivery_date)
        instance.state = validated_data.get('state', instance.state)
        instance.save()

        new_product_bill_ids = []

        for product_bill_data in product_bills_data:
            product_bill_id = product_bill_data.get('id')
            updated_quantity = product_bill_data.get('quantity')
            record_package = product_bill_data.get('record_package', 0)

            if product_bill_id:
                product_bill = ProductBill.objects.get(id=product_bill_id)
                current_quantity = product_bill.quantity
                quantity_diff = updated_quantity - current_quantity

                if product_bill.is_variant:
                    variant = Variant.objects.get(pk=product_bill.variant_id)
                    if variant.quantity < quantity_diff:
                        raise serializers.ValidationError({
                            'quantity': f'Insufficient quantity for variant. Available: {variant.quantity}'
                        })
                    variant.quantity -= quantity_diff
                    variant.save()
                    product_instance = variant.product
                else:
                    product = Product.objects.get(pk=product_bill.product.id)
                    if product.quantity < quantity_diff:
                        raise serializers.ValidationError({
                            'quantity': f'Insufficient quantity for product. Available: {product.quantity}'
                        })
                    product.quantity -= quantity_diff
                    product.save()
                    product_instance = product

                if product_instance.is_beer:
                    empty_quantity_needed = updated_quantity
                    packaging = product_instance.package
                    if packaging:
                        if record_package > empty_quantity_needed:
                            raise serializers.ValidationError({'record_package': f"Packaging to record can't be greater than needed packaging for product {product_instance.name}"})
                        else:
                            record_quantity = empty_quantity_needed - record_package
                            package_product_bill = PackageProductBill.objects.get(product_bill=product_bill.id)
                            old_record_package = package_product_bill.record
                            old_quantity = package_product_bill.quantity

                            package_product_bill.quantity = empty_quantity_needed
                            package_product_bill.record = record_package
                            package_product_bill.save()

                            packaging.full_quantity += old_quantity - empty_quantity_needed
                            packaging.empty_quantity += old_record_package - record_package
                            if packaging.full_quantity < 0:
                                packaging.full_quantity = 0
                            packaging.save()

                product_bill.product = product_bill_data.get('product', product_bill.product)
                product_bill.variant_id = product_bill_data.get('variant_id', product_bill.variant_id)
                product_bill.sell_price = product_bill_data.get('sell_price', product_bill.sell_price)
                product_bill.quantity = product_bill_data.get('quantity', product_bill.quantity)
                product_bill.is_variant = product_bill_data.get('is_variant', product_bill.is_variant)
                product_bill.save()
                new_product_bill_ids.append(product_bill.id)
            else:
                if product_bill_data['is_variant']:
                    variant = Variant.objects.get(pk=product_bill_data['variant_id'])
                    if variant.quantity < product_bill_data['quantity']:
                        raise serializers.ValidationError({
                            'quantity': f'Insufficient quantity for variant. Available: {variant.quantity}'
                        })
                    variant.quantity -= product_bill_data['quantity']
                    variant.save()
                    product_instance = variant.product
                else:
                    product = Product.objects.get(pk=product_bill_data['product'].id)
                    if product.quantity < product_bill_data['quantity']:
                        raise serializers.ValidationError({
                            'quantity': f'Insufficient quantity for product. Available: {product.quantity}'
                        })
                    product.quantity -= product_bill_data['quantity']
                    product.save()
                    product_instance = product

                new_product_bill = ProductBill.objects.create(bill=instance, **product_bill_data)
                new_product_bill_ids.append(new_product_bill.id)

                if product_instance.is_beer:
                    empty_quantity_needed = new_product_bill.quantity
                    packaging = product_instance.package
                    if packaging:
                        if packaging.full_quantity >= empty_quantity_needed:
                            if record_package > empty_quantity_needed:
                                raise serializers.ValidationError({'record_package': f"Packaging to record can't be greater than needed packaging for product {product_instance.name}"})
                            else:
                                record_quantity = empty_quantity_needed - record_package
                                PackageProductBill.objects.create(
                                    product_bill=new_product_bill,
                                    packaging=packaging,
                                    quantity=empty_quantity_needed,
                                    record=record_package
                                )
                                packaging.empty_quantity += record_quantity
                                packaging.full_quantity -= empty_quantity_needed
                                if packaging.full_quantity < 0:
                                    packaging.full_quantity = 0
                                packaging.save()
                        else:
                            raise serializers.ValidationError({'quantity': f"Insufficient quantity for packaging {packaging.name}. Available: {packaging.full_quantity}"})

        for product_bill in instance.product_bills.exclude(id__in=new_product_bill_ids):
            if product_bill.is_variant:
                variant = Variant.objects.get(pk=product_bill.variant_id)
                variant.quantity += product_bill.quantity
                variant.save()
            else:
                product = Product.objects.get(pk=product_bill.product.id)
                product.quantity += product_bill.quantity
                product.save()

            if product_bill.product.is_beer:
                packaging = product_bill.product.package
                if packaging:
                    package_product_bill = PackageProductBill.objects.get(product_bill=product_bill.id)
                    packaging.full_quantity += package_product_bill.quantity
                    packaging.empty_quantity -= package_product_bill.record
                    if packaging.full_quantity < 0:
                        packaging.full_quantity = 0
                    packaging.save()

            product_bill.delete()

        return instance
    
    def create_packaging_history(self, bill, product_instance, packaging, quantity, record_package, user, action, variant=None):
        PackagingHistory.objects.create(
            packaging=packaging,
            product=product_instance,
            action=action,
            quantity_changed=quantity,
            full_quantity_before=packaging.full_quantity + quantity,
            empty_quantity_before=packaging.empty_quantity - (quantity - record_package),
            full_quantity_after=packaging.full_quantity,
            empty_quantity_after=packaging.empty_quantity,
            performed_by=user,
            bill=bill,
            variant=variant
        )

class DelivererUpdateSerializer(serializers.ModelSerializer):
    deliverer = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.filter(is_deliverer=True), required=False, allow_null=True)

    class Meta:
        model = Bill
        fields = ['deliverer', 'state']

    def validate(self, data):
        state = data.get('state')
        deliverer = data.get('deliverer')

        # If state is 'pending' and deliverer is provided, check if the deliverer is valid
        if state == 'pending' and deliverer:
            if not deliverer.is_deliverer:
                raise serializers.ValidationError({'deliverer': 'Selected employee is not a deliverer.'})

        return data

class UpdateDeliveredBillSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        model = Bill
        fields = ['amount']
    
class EmployeeDebtSerializer(serializers.ModelSerializer):
    employee_details = EmployeeSerializer(source='employee',read_only=True)
    
    class Meta:
        model = EmployeeDebt
        fields = ['id','employee_details', 'employee', 'amount',  'created_at',  'updated_at', 'status']

class PayDebtSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)

    def validate(self, data):
        debt = self.context['debt']
        if data['amount'] <= 0:
            raise serializers.ValidationError("Payment amount must be greater than zero.")
        if data['amount'] > debt.amount:
            raise serializers.ValidationError("Payment amount exceeds debt amount.")
        return data


class RecordedPackagingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordedPackaging
        fields = ['id', 'customer', 'quantity', 'bill', 'created_at', 'updated_at', 'repay', 'packaging']

class PackagingHistoryFilterSerializer(serializers.Serializer):
    sales_point = serializers.PrimaryKeyRelatedField(queryset=SalesPoint.objects.all(), required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)

class PackagingHistorySerializer(serializers.ModelSerializer):
    packaging = serializers.PrimaryKeyRelatedField(read_only=True)
    product = serializers.PrimaryKeyRelatedField(read_only=True, required=False)
    performed_by = serializers.PrimaryKeyRelatedField(read_only=True)
    sales_point = serializers.PrimaryKeyRelatedField(read_only=True, required=False)

    class Meta:
        model = PackagingHistory
        fields = [
            'id',
            'packaging',
            'product',
            'action',
            'quantity_changed',
            'full_quantity_before',
            'empty_quantity_before',
            'full_quantity_after',
            'empty_quantity_after',
            'performed_by',
            'timestamp',
            'sales_point'
        ]