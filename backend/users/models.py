"""
users/models.py
Custom user model extending AbstractBaseUser with all scheme-eligibility fields
"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserProfileManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)
        return self.create_user(username, password, **extra_fields)


class UserProfile(AbstractBaseUser, PermissionsMixin):
    # ─── Auth fields ───
    username    = models.CharField(max_length=80, unique=True)
    email       = models.EmailField(blank=True, null=True)
    mobile      = models.CharField(max_length=15, blank=True, null=True)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    is_admin    = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # ─── Personal fields ───
    full_name     = models.CharField(max_length=200)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_pic   = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    GENDER_CHOICES = [('male', 'Male'), ('female', 'Female'), ('other', 'Other')]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)

    # ─── Eligibility fields (used for scheme matching) ───
    CATEGORY_CHOICES = [('general', 'General'), ('sc', 'SC'), ('st', 'ST'), ('obc', 'OBC')]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')

    MARITAL_CHOICES = [('single', 'Single'), ('married', 'Married'),
                       ('divorced', 'Divorced'), ('widowed', 'Widowed')]
    marital_status = models.CharField(max_length=20, choices=MARITAL_CHOICES, blank=True, null=True)

    aadhaar = models.CharField(max_length=12, blank=True, null=True)

    # Income range stored as string: "0-100000", "100000-250000", "500000+" etc.
    income_range = models.CharField(max_length=30, blank=True, null=True)

    OCCUPATION_CHOICES = [
        ('farmer', 'Farmer'), ('labour', 'Labour'), ('self_employed', 'Self-Employed'),
        ('business', 'Business'), ('teacher', 'Teacher'), ('student', 'Student'),
        ('govt_employee', 'Govt Employee'), ('private_employee', 'Private Employee'),
        ('other', 'Other'),
    ]
    occupation = models.CharField(max_length=30, choices=OCCUPATION_CHOICES, blank=True, null=True)

    STATE_CHOICES = [
        ('andhra_pradesh', 'Andhra Pradesh'), ('telangana', 'Telangana'),
        ('tamil_nadu', 'Tamil Nadu'), ('karnataka', 'Karnataka'),
        ('kerala', 'Kerala'), ('maharashtra', 'Maharashtra'),
        ('gujarat', 'Gujarat'), ('rajasthan', 'Rajasthan'),
        ('madhya_pradesh', 'Madhya Pradesh'), ('uttar_pradesh', 'Uttar Pradesh'),
        ('bihar', 'Bihar'), ('west_bengal', 'West Bengal'), ('other', 'Other'),
    ]
    state = models.CharField(max_length=30, choices=STATE_CHOICES, blank=True, null=True)

    HAS_LAND_CHOICES = [('no', 'No'), ('yes_less_2ha', 'Yes < 2ha'), ('yes_more_2ha', 'Yes > 2ha')]
    has_land = models.CharField(max_length=20, choices=HAS_LAND_CHOICES, default='no')

    father_name = models.CharField(max_length=200, blank=True, null=True)
    mother_name = models.CharField(max_length=200, blank=True, null=True)
    family_size = models.PositiveSmallIntegerField(default=1)

    objects = UserProfileManager()
    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table   = 'user_profiles'
        verbose_name = 'User Profile'

    def __str__(self):
        return f"{self.full_name} ({self.username})"

    def get_max_income(self):
        """Return upper bound of income_range for eligibility matching.
        Handles formats: '0-100000', '100000-250000', '500000+', '500000'
        FIX: original code had int('+') crash when range ended with '+'.
        """
        if not self.income_range:
            return None
        val = str(self.income_range).strip()
        # Handle "500000+" style — open-ended upper bound
        if val.endswith('+'):
            return 9_999_999
        # Handle "min-max" range — return the max (right side)
        if '-' in val:
            parts = val.split('-')
            try:
                return int(parts[-1])
            except (ValueError, IndexError):
                return None
        # Plain single number
        try:
            return int(val)
        except ValueError:
            return None
