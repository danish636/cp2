from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission, AbstractBaseUser, PermissionsMixin
import json

class UserManager(BaseUserManager):

    use_in_migration = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is Required')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff = True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser = True')

        return self.create_user(email, password, **extra_fields)



class User(AbstractBaseUser, PermissionsMixin):
    account_made_at = models.DateTimeField(auto_now=True,null=True,blank=True) 
    email = models.EmailField(max_length=50, unique=True)
    username = models.CharField(max_length=500)
    password = models.CharField(max_length=500)
    firstName = models.CharField(max_length=50,blank=True,null=True)
    middleName = models.CharField(max_length=50,blank=True,null=True)  
    lastName = models.CharField(max_length=50,blank=True,null=True)
    bod = models.DateField(blank=True,null=True)
    mobile = models.IntegerField(blank=True,null=True)
    prime_user = models.BooleanField(default = False)
    addressLine1 = models.CharField(max_length=100,blank=True,null=True)
    addressLine2 = models.CharField(max_length=50,blank=True,null=True)
    pincode = models.CharField(max_length=50,blank=True,null=True)
    city = models.CharField(max_length=50,blank=True,null=True)
    state = models.CharField(max_length=50,blank=True,null=True)
    status = models.IntegerField(default = 0, blank=True)
    country = models.CharField(max_length=50,blank=True,null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    subscription_id = models.CharField(max_length=50, blank=True, null=True)
    is_subscribed = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)


    USERNAME_FIELD = 'email'
    objects = UserManager()

    def __str__(self):
        return self.email


class Course(models.Model):
    course_id = models.IntegerField()
    course_name = models.CharField(max_length=255)
    author = models.CharField(max_length=50)
    course_description = models.TextField()
    chapter_name = models.CharField(max_length=255)
    image = models.URLField(max_length=1000)
    materials = models.JSONField()
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Company(models.Model):
    symbol = models.CharField(max_length=255, null=True)
    companyName = models.CharField(max_length=255, null=True)
    exchange = models.CharField(max_length=255, null=True)
    industry = models.CharField(max_length=255, null=True)
    website = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    ceo = models.CharField(max_length=255, null=True)
    securityName = models.CharField(max_length=255, null=True)
    issueType = models.CharField(max_length=255, null=True)
    sector = models.CharField(max_length=255, null=True)
    primarySicCode = models.CharField(max_length=255, null=True)
    employees = models.CharField(max_length=255, null=True)
    address = models.CharField(max_length=255, null=True)
    address2 = models.CharField(max_length=255, null=True)
    state = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=255, null=True)
    zip_code = models.CharField(max_length=255, null=True)
    country = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    tags = models.TextField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.tags:
            self.tags = json.loads(self.tags)
        super().save(*args, **kwargs)


class UserPortfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    portfolio_name = models.CharField(max_length=255)
    portfolio_id = models.CharField(max_length = 200)
    reinvesting_dividends = models.BooleanField(default=False)
    currency = models.CharField(max_length=255)
    portfolio_description = models.TextField()
    ticker_values = models.JSONField()
    portfolio_slug = models.CharField(max_length=255)
    header_title = models.CharField(max_length=255)
    header_description = models.CharField(max_length=255)
    image_url = models.ImageField(upload_to='images', null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_published = models.BooleanField(default=False)
    without_login = models.BooleanField(default=False)
    paid_user = models.BooleanField(default=False)
    is_free = models.BooleanField(default=False)
    
    show_ticker = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.ticker_values:
            self.ticker_values = json.loads(self.ticker_values)
        super().save(*args, **kwargs)


class UserDcfCalculatorFilter(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dcf_calculator_filter_name = models.CharField(max_length=250)
    filter_values = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.filter_values:
            self.filter_values = json.loads(self.filter_values)
        super().save(*args, **kwargs)


class UserScreenerFilter(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    screener_name = models.CharField(max_length=250)
    filter_values = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.filter_values:
            self.filter_values = json.loads(self.filter_values)
        super().save(*args, **kwargs)



class Customer(models.Model):
    customer_id = models.CharField(max_length=250)
    plan_id = models.IntegerField(null=True)
    user_id = models.IntegerField()
    payment_type = models.CharField(max_length=250, null=True)
    discount_coupon = models.CharField(max_length=250, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.customer_id


class UserPortfolioPublish(models.Model):
    portfolio_id = models.IntegerField(null=True)
    image = models.ImageField(upload_to="./Images/", null=True, blank=True)
    meta_title = models.CharField(max_length=255)
    meta_description = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    portfolio_publish_status = models.BooleanField(default=False)
    portfolio_publish_slug = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.portfolio_id

class TempTokenModel(models.Model):
    email = models.CharField(max_length=50)
    token = models.CharField(max_length=16)

    def __str__(self):
        return self.email + " : " + self.token