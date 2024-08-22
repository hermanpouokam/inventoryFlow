from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.utils import timezone
from django.db.models import F
import random
import string

class Plan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class Enterprise(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, related_name='enterprises')  # Add this line

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Check if this is a new instance
        super().save(*args, **kwargs)  # Save the Enterprise instance first

        if is_new:
            # Create a Sales Point for the new Enterprise
            SalesPoint.objects.create(
                enterprise=self,
                name=f"{self.name}",  # Customize as needed
                address=self.address  # Provide default values or customize
            )

    def __str__(self):
        return self.name
    
class SalesPoint(models.Model):
    name = models.CharField(max_length=200)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name
    
class Category(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    ab_name = models.CharField(max_length=50,null=True)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name='Category',null=True,blank=True)  # New field
    sales_point = models.ForeignKey(SalesPoint, on_delete=models.CASCADE, null=True, blank=True)  # New field
    
    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(null=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    contact = models.TextField(null=True)
    ab_name = models.CharField(max_length=50,null=True, blank=True)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name='Supplier',null=True,blank=True)  # New field
    sales_point = models.ForeignKey(SalesPoint, on_delete=models.CASCADE, null=True, blank=True)  # New field

    def __str__(self):
        return self.name

class Packaging(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    full_quantity = models.PositiveIntegerField(default=0)
    empty_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sales_point = models.ForeignKey('SalesPoint', on_delete=models.CASCADE)
    enterprise = models.ForeignKey('Enterprise', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Packaging'

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    product_code = models.CharField(max_length=200,null=True)
    quantity = models.IntegerField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_beer = models.BooleanField(default=False)
    with_variant = models.BooleanField(default=False)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name='Prduct',null=True,blank=True)  # New field
    sales_point = models.ForeignKey(SalesPoint, on_delete=models.CASCADE, null=True, blank=True)  # New field
    package = models.ForeignKey(Packaging, on_delete=models.SET_NULL, null=True, blank=True)  # New field

    def __str__(self):
        return self.name
    
    @property
    def total_quantity(self):
        if self.with_variant:
            return sum(variant.quantity for variant in self.variants.all())
        return self.quantity

class Variant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.name} (Variant of {self.product.name}"

class SellPrice(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sell_prices')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.price}"

class ClientCategory(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    sales_point = models.ForeignKey(SalesPoint, on_delete=models.CASCADE, null=True, blank=True)  # New field
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name='client_category',null=True,blank=True)  # New field

    def __str__(self):
        return self.name

def generate_client_code(name, surname, number):
    initials = ""
    if name and surname:
        initials = f"{name[0]}{surname[0]}".upper()
    elif name:
        initials = f"{name[0]}X".upper()
    elif surname:
        initials = f"X{surname[0]}".upper()
    else:
        initials = "XX"

    number_part = "".join(filter(str.isdigit, str(number)))[:4] if number else "0000"

    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

    return f"{initials}{number_part}{random_part}"

class Client(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100,null=True,blank=True)
    number = models.CharField(max_length=100,null=True,blank=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=100,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    code = models.CharField(max_length=8, unique=True, editable=False)
    client_category = models.ForeignKey(ClientCategory, on_delete=models.CASCADE)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name='Client',null=True,blank=True)  # New field
    sales_point = models.ForeignKey(SalesPoint, on_delete=models.CASCADE, null=True, blank=True) 
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_client_code(self.name, self.surname, self.number)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} {self.surname}"

    
class PaymentInfo(models.Model):
    enterprise = models.OneToOneField(Enterprise, on_delete=models.CASCADE, related_name='payment_info')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE) 
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    next_due_date = models.DateTimeField()
    payment_method = models.CharField(max_length=50) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.enterprise.name} - {self.plan_name} - {self.amount}"
    
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
    ]

    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100,unique=True)
    number = models.CharField(max_length=15, blank=True, null=True)
    password = models.CharField(max_length=128)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.SET_NULL, related_name='users', null=True, blank=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='employee')
    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    sales_point = models.ForeignKey(SalesPoint, on_delete=models.CASCADE, null=True, blank=True)  # New field

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['name', 'surname']

    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_groups',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions',
        blank=True
    )

    def __str__(self):
        return f"{self.name} {self.surname}"

class EnterpriseDetails(models.Model):
    enterprise = models.OneToOneField(Enterprise, on_delete=models.CASCADE, related_name='details')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Details for {self.enterprise.name}"
    
class Bill(models.Model):
    BILL_STATES = [
        ('created', 'Created'),
        ('pending', 'Pending'),
        ('success', 'Success'),
    ]

    bill_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Client, on_delete=models.SET_NULL,null=True,blank=True)
    enterprise = models.ForeignKey('Enterprise', on_delete=models.CASCADE, related_name='bills')
    created_at = models.DateTimeField(auto_now_add=True)
    customer_name = models.CharField(max_length=255, null=True, blank=True)
    delivery_date = models.DateTimeField(default=timezone.now)
    state = models.CharField(max_length=10, choices=BILL_STATES, default='created')
    sales_point = models.ForeignKey(SalesPoint, on_delete=models.CASCADE, null=True, blank=True)  # New field
    deliverer = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='bills')
    paid = models.DecimalField(max_digits=20, decimal_places=2,null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.bill_number:
            self.bill_number = self.generate_bill_number()
        
        # Ensure that customer is None if customer_id is 0
        if self.customer_id is None:
            self.customer = None
            self.customer_name = self.customer_name or "Anonymous"
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        for product_bill in self.product_bills.all():
            if product_bill.is_variant:
                # If the product bill is a variant, increase the variant's quantity
                Variant.objects.filter(pk=product_bill.variant_id).update(quantity=F('quantity') + product_bill.quantity)
            else:
                # If the product bill is a standard product, increase the product's quantity
                Product.objects.filter(pk=product_bill.product.id).update(quantity=F('quantity') + product_bill.quantity)
            if product_bill.product.is_beer:
                try:
                    package_product_bill = PackageProductBill.objects.get(product_bill=product_bill)
                    packaging = package_product_bill.packaging

                    # Restore the packaging quantities
                    packaging.full_quantity += package_product_bill.quantity
                    packaging.empty_quantity -= package_product_bill.quantity - package_product_bill.record

                    if packaging.full_quantity < 0:
                        packaging.full_quantity = 0

                    if packaging.empty_quantity < 0:
                        packaging.empty_quantity = 0

                    packaging.save()

                    # Delete the PackageProductBill instance
                    package_product_bill.delete()
                except PackageProductBill.DoesNotExist:
                    pass
        # Call the superclass delete method
        super().delete(*args, **kwargs)

    def generate_bill_number(self):
        last_bill = Bill.objects.filter(enterprise=self.enterprise).order_by('id').last()
        if not last_bill:
            return 'BILL-0001'
        bill_number = last_bill.bill_number
        bill_int = int(bill_number.split('-')[1])
        new_bill_int = bill_int + 1
        new_bill_number = f'BILL-{new_bill_int:04d}'
        return new_bill_number
    
class ProductBill(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='product_bills')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    sell_price = models.ForeignKey(SellPrice, on_delete=models.SET_NULL,null=True, blank=True)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_variant = models.BooleanField(default=False)
    variant_id = models.IntegerField(null=True, blank=True)

    @property
    def price(self):
        return self.sell_price.price
    
    def delete(self, *args, **kwargs):
        if self.is_variant:
            variant = Variant.objects.get(pk=self.variant_id)
            product_instance = variant.product
        else:
            product_instance = self.product

        if product_instance.is_beer:
            packaging = product_instance.package
            if packaging:
                package_product_bill = PackageProductBill.objects.get(product_bill=self)
                packaging.empty_quantity -= package_product_bill.quantity - package_product_bill.record 
                packaging.full_quantity += package_product_bill.quantity
                if packaging.empty_quantity < 0:
                    packaging.empty_quantity = 0
                packaging.save()
                package_product_bill.delete()

        super().delete(*args, **kwargs)
    
class Employee(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100,null=True)
    salary = models.DecimalField(max_digits=20, decimal_places=2)
    monthly_salary = models.DecimalField(max_digits=20, decimal_places=2,default=0)
    role = models.CharField(max_length=20)
    sales_point = models.ForeignKey(SalesPoint, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    enterprise = models.ForeignKey(Enterprise, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    is_deliverer = models.BooleanField(default=False)
     
    def save(self, *args, **kwargs):
        if not self.monthly_salary:
            self.monthly_salary = self.salary
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class EmployeeDebt(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('paid', 'Paid')], default='pending')

    def __str__(self):
        return f"Debt of {self.amount} for {self.employee.name}"



class RecordedPackaging(models.Model):
    customer = models.ForeignKey('Client', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    bill = models.ForeignKey('Bill', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    repay = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    packaging = models.ForeignKey('Packaging', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Recorded Packaging'
        verbose_name_plural = 'Recorded Packaging'

    def __str__(self):
        return f"{self.customer} - {self.packaging} - {self.quantity}"

class PackageProductBill(models.Model):
    product_bill = models.OneToOneField(ProductBill, on_delete=models.CASCADE, related_name='package_product_bill')
    packaging = models.ForeignKey(Packaging, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    record  = models.PositiveIntegerField(default=0)
    class Meta:
        verbose_name = 'Package Product Bill'
        verbose_name_plural = 'Package Product Bills'

    def __str__(self):
        return f"Packaging for {self.product_bill}"

class PackagingHistory(models.Model):
    packaging = models.ForeignKey(Packaging, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=255)
    quantity_changed = models.PositiveIntegerField()
    full_quantity_before = models.PositiveIntegerField()
    empty_quantity_before = models.PositiveIntegerField()
    full_quantity_after = models.PositiveIntegerField()
    empty_quantity_after = models.PositiveIntegerField()
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    sales_point = models.ForeignKey(SalesPoint, on_delete=models.SET_NULL, null=True, blank=True)
    bill =  models.ForeignKey(Bill, on_delete=models.SET_NULL, null=True, blank=True)
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} on {self.packaging} (Product: {self.product}) by {self.performed_by} at {self.timestamp}"