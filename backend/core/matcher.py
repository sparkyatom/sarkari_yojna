# """
# core/matcher.py
# Eligibility engine — matches a user's profile against all active schemes.
# Returns schemes sorted by closest deadline first.
# """
# from django.db.models import Q
# from django.utils import timezone


# def get_eligible_schemes(user):
#     """
#     Given a UserProfile instance, return a queryset of Scheme objects
#     that the user is eligible for, sorted by last_date ascending.
#     """
#     from schemes.models import Scheme

#     today = timezone.now().date()
#     qs    = Scheme.objects.filter(status='active', last_date__gte=today)

#     # ── 1. Caste / Category filter ──────────────────────────────
#     # FIX: original code had broken Q() chaining with inline `if` expressions
#     # that caused TypeError due to Python operator-precedence misparse.
#     # The malformed block ran first and could crash before _filter_by_category
#     # had a chance to replace it. Now we call _filter_by_category directly.
#     user_cat = user.category  # 'general', 'sc', 'st', 'obc'
#     if user_cat:
#         qs = _filter_by_category(qs, user_cat)

#     # ── 2. Income filter ─────────────────────────────────────────
#     user_max_income = user.get_max_income()
#     if user_max_income is not None:
#         # Scheme's max_income must be >= user's min income OR no limit set
#         qs = qs.filter(
#             Q(max_income__isnull=True) |
#             Q(max_income__gte=_get_user_min_income(user))
#         )

#     # ── 3. State filter ──────────────────────────────────────────
#     if user.state:
#         qs = qs.filter(
#             Q(eligible_state='all') | Q(eligible_state=user.state)
#         )

#     # ── 4. Occupation filter ─────────────────────────────────────
#     if user.occupation:
#         qs = qs.filter(
#             Q(eligible_occupation='all') | Q(eligible_occupation=user.occupation)
#         )

#     # ── 5. Gender filter ─────────────────────────────────────────
#     if user.gender:
#         qs = qs.filter(
#             Q(eligible_gender='all') | Q(eligible_gender=user.gender)
#         )

#     return qs.order_by('last_date')


# def _filter_by_category(qs, user_cat):
#     """
#     Returns schemes whose eligible_category includes the user's caste category.
#     Handles compound categories like 'sc_st' and 'sc_st_obc'.
#     """
#     category_map = {
#         'sc':      ['all', 'sc', 'sc_st', 'sc_st_obc'],
#         'st':      ['all', 'st', 'sc_st', 'sc_st_obc'],
#         'obc':     ['all', 'obc', 'sc_st_obc'],
#         'general': ['all', 'general'],
#     }
#     allowed = category_map.get(user_cat, ['all'])
#     return qs.filter(eligible_category__in=allowed)


# def _get_user_min_income(user):
#     """Return the lower bound of the user's income range."""
#     if not user.income_range:
#         return 0
#     parts = user.income_range.split('-')
#     try:
#         return int(parts[0])
#     except (ValueError, IndexError):
#         return 0


"""
core/matcher.py

Eligibility engine — matches a user's profile against schemes.
Returns schemes sorted by closest deadline first.
"""

from django.db.models import Q
from django.utils import timezone


def get_eligible_schemes(user):
    """
    Given a UserProfile instance, return schemes the user is eligible for.
    """

    from schemes.models import Scheme

    today = timezone.now().date()

    # ── BASE QUERY ─────────────────────────────────────
    qs = Scheme.objects.filter(
        status='active',
        last_date__gte=today   # remove expired schemes
    )

    # ── 1. CATEGORY (CASTE) FILTER ─────────────────────
    # SAFE VERSION (will NOT break results)
    if user.category:
        qs = qs.filter(
            Q(eligible_category='all') |
            Q(eligible_category__icontains=user.category)
        )

    # ── 2. INCOME FILTER (FIXED LOGIC) ─────────────────
    if user.income_range:
        user_min = _get_user_min_income(user)

        qs = qs.filter(
            Q(max_income__isnull=True) |      # no limit
            Q(max_income__gte=user_min)       # scheme supports user income
        )

    # ── 3. STATE FILTER ────────────────────────────────
    if user.state:
        # Normalize slug-like states (e.g. 'andhra_pradesh') to human form ('andhra pradesh')
        user_state = str(user.state).replace('_', ' ').strip().lower()
        qs = qs.filter(
            Q(eligible_state='all') |
            Q(eligible_state__icontains=user_state)
        )

    # ── 4. OCCUPATION FILTER ───────────────────────────
    if user.occupation:
        qs = qs.filter(
            Q(eligible_occupation='all') |
            Q(eligible_occupation__icontains=user.occupation)
        )

    # ── 5. GENDER FILTER ───────────────────────────────
    if user.gender:
        qs = qs.filter(
            Q(eligible_gender='all') |
            Q(eligible_gender__icontains=user.gender)
        )

    # ── FINAL SORT ─────────────────────────────────────
    return qs.order_by('last_date')


# ─────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────

def _get_user_min_income(user):
    """
    Extract lower bound from income range string.
    Example: "250000-500000" → 250000
    """
    if not user.income_range:
        return 0

    try:
        return int(user.income_range.split('-')[0])
    except (ValueError, IndexError):
        return 0