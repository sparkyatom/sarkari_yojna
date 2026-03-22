"""
schemes/models.py
The Scheme model — stores every government scheme
"""
from django.db import models


class Scheme(models.Model):
    CATEGORY_CHOICES = [
        ('agriculture', 'Agriculture'),
        ('education',   'Education'),
        ('housing',     'Housing'),
        ('health',      'Health'),
        ('women',       'Women & Child'),
        ('employment',  'Employment'),
        ('social',      'Social Security'),
        ('finance',     'Finance & Loans'),
    ]

    STATUS_CHOICES = [
        ('active',  'Active'),
        ('draft',   'Draft'),
        ('expired', 'Expired'),
    ]

    PERIOD_CHOICES = [
        ('per_year',        'Per Year'),
        ('per_month',       'Per Month'),
        ('one_time',        'One-time'),
        ('per_installment', 'Per Installment'),
    ]

    GENDER_CHOICES = [
        ('all',    'All Genders'),
        ('male',   'Male Only'),
        ('female', 'Female Only'),
    ]

    ELIGIBLE_CAT_CHOICES = [
        ('all',        'All Categories'),
        ('sc',         'SC Only'),
        ('st',         'ST Only'),
        ('obc',        'OBC Only'),
        ('sc_st',      'SC + ST'),
        ('sc_st_obc',  'SC + ST + OBC'),
        ('general',    'General Only'),
    ]

    OCCUPATION_CHOICES = [
        ('all',          'All Occupations'),
        ('farmer',       'Farmer'),
        ('labour',       'Labour'),
        ('student',      'Student'),
        ('self_employed','Self-Employed'),
        ('business',     'Business'),
        ('teacher',      'Teacher'),
        ('other',        'Other'),
    ]

    # ─── Basic info ───
    name        = models.CharField(max_length=300)
    ministry    = models.CharField(max_length=300)
    category    = models.CharField(max_length=30, choices=CATEGORY_CHOICES, db_index=True)
    description = models.TextField()
    official_url = models.URLField(blank=True, null=True)
    icon        = models.CharField(max_length=10, default='📋')   # emoji

    # ─── Eligibility ───
    eligible_category  = models.CharField(max_length=20, choices=ELIGIBLE_CAT_CHOICES, default='all', db_index=True)
    eligible_occupation= models.CharField(max_length=30, choices=OCCUPATION_CHOICES, default='all')
    eligible_gender    = models.CharField(max_length=10, choices=GENDER_CHOICES, default='all')
    eligible_state     = models.CharField(max_length=50, default='all')  # 'all' or state slug
    min_income         = models.PositiveIntegerField(default=0)           # annual, in rupees
    max_income         = models.PositiveIntegerField(null=True, blank=True)  # null = no limit

    # ─── Benefit ───
    benefit_amount  = models.PositiveIntegerField()           # in rupees
    benefit_period  = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='per_year')

    # ─── Documents (stored as newline-separated string) ───
    required_documents = models.TextField(blank=True, default='')

    # ─── Dates ───
    last_date   = models.DateField(db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    # ─── Status ───
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', db_index=True)

    class Meta:
        db_table = 'schemes'
        ordering = ['last_date']   # closest deadline first

    def __str__(self):
        return self.name

    def get_documents_list(self):
        return [d.strip() for d in self.required_documents.split('\n') if d.strip()]

    def set_documents_list(self, docs_list):
        self.required_documents = '\n'.join(docs_list)
