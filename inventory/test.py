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
                  'customer_name', 'created_at', 'delivery_date', 'state', 'product_bills', 'deliverer',
                  'deliverer_details', 'total_bill_amount']

    def validate(self, attrs):
        user = self.context['request'].user
        customer_id = attrs.get('customer')
        customer_name = attrs.get('customer_name')

        # Admin-specific validation
        if user.user_type == 'admin':
            if customer_id == 0:
                attrs['customer'] = None
                if not attrs.get('sales_point'):
                    raise serializers.ValidationError({'sales_point': 'This field is required for admin users when customer is 0.'})
                if not customer_name:
                    raise serializers.ValidationError({'customer_name': 'Customer name is required if customer is 0.'})
            elif customer_id is not None:
                try:
                    customer = Client.objects.get(pk=customer_id.id)
                    attrs['sales_point'] = customer.sales_point
                    attrs['customer_name'] = f"{customer.name} {customer.surname}"
                except Client.DoesNotExist:
                    raise serializers.ValidationError({'customer': 'Invalid customer ID.'})
        else:
            attrs['sales_point'] = user.sales_point

        return attrs


    def get_total(self, obj):
        return sum(pb.quantity * pb.price for pb in obj.product_bills.all())

    def get_total_bill_amount(self, obj):
        total = 0
        for pb in obj.product_bills.all():
            total += pb.quantity * pb.price
            if pb.package_product_bill:
                total += pb.package_product_bill.record * pb.package_product_bill.packaging.price
        return total

    def create(self, validated_data):
        product_bills_data = validated_data.pop('product_bills')
        request = self.context.get('request')
        enterprise = request.user.enterprise
        bill = Bill.objects.create(**validated_data)
        print(f"DEBUG: validated_data in create method: {validated_data}")

        if validated_data.get('customer') == 0:
            validated_data['customer'] = None

        for product_bill_data in product_bills_data:
            product_id = product_bill_data['product']
            sell_price = product_bill_data['sell_price']
            quantity = product_bill_data['quantity']
            is_variant = product_bill_data['is_variant']
            variant_id = product_bill_data.get('variant_id')
            record_package = product_bill_data.get('record_package', 0)

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
                                    packaging.empty_quantity += record_quantity
                                    packaging.full_quantity -= empty_quantity_needed
                                    if packaging.full_quantity < 0:
                                        packaging.full_quantity = 0
                                    packaging.save()
                    else:
                        raise serializers.ValidationError({'quantity': f"c. {product_instance.name}"})
                else:
                    raise serializers.ValidationError({'product': 'Product does not exist.'})

        return bill
