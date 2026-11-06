import re
from categories.models import Category
from .models import CategorizationRule

DEFAULT_CATEGORIES_CONFIG = [
    {
        'name': 'Food & Dining',
        'type': 'expense',
        'color': '#f97316',
        'keywords': [
            'foodmandu', 'bhoj', 'himalayan java', 'bakery', 'cafe', 'coffee',
            'restaurant', 'khaja', 'kitchen', 'burger', 'pizza', 'momo', 'bar',
            'bakes', 'sweets', 'eatery', 'canteen', 'chiyaghar', 'tea', 'foodpanda',
            'kfc', 'dining', 'lunch', 'dinner', 'breakfast', 'hotel'
        ],
    },
    {
        'name': 'Transportation',
        'type': 'expense',
        'color': '#06b6d4',
        'keywords': [
            'pathao', 'indrive', 'tootle', 'sajha', 'fuel', 'petrol', 'pump',
            'diesel', 'oil', 'transport', 'cab', 'taxi', 'rides', 'parking',
            'toll', 'bus', 'air'
        ],
    },
    {
        'name': 'Groceries & Shopping',
        'type': 'expense',
        'color': '#8b5cf6',
        'keywords': [
            'bhatbhateni', 'bbsm', 'big mart', 'salesberry', 'daraz', 'supermarket',
            'mart', 'kirana', 'store', 'department', 'clothing', 'pasal', 'retail',
            'shopping', 'fashion', 'mall'
        ],
    },
    {
        'name': 'Utilities & Bills',
        'type': 'expense',
        'color': '#3b82f6',
        'keywords': [
            'nea', 'electricity', 'khanepani', 'water', 'ncell', 'ntc', 'nepal telecom',
            'telecom', 'subisu', 'worldlink', 'vianet', 'dishhome', 'internet',
            'recharge', 'bill', 'topup', 'cable'
        ],
    },
    {
        'name': 'Healthcare',
        'type': 'expense',
        'color': '#ec4899',
        'keywords': [
            'pharmacy', 'hospital', 'medical', 'pharma', 'clinic', 'health',
            'lab', 'dental', 'care', 'medicine', 'doctor', 'diagnostic'
        ],
    },
    {
        'name': 'Entertainment',
        'type': 'expense',
        'color': '#eab308',
        'keywords': [
            'qfx', 'ini', 'cinemas', 'movies', 'fube', 'entertainment', 'theatre',
            'netflix', 'game', 'gaming', 'concert', 'ticket'
        ],
    },
    {
        'name': 'Education',
        'type': 'expense',
        'color': '#10b981',
        'keywords': [
            'school', 'college', 'tuition', 'books', 'university', 'academy',
            'library', 'fee', 'fees', 'course', 'exam'
        ],
    },
    {
        'name': 'Salary & Income',
        'type': 'income',
        'color': '#22c55e',
        'keywords': [
            'salary', 'deposit', 'remittance', 'bonus', 'interest', 'dividend',
            'freelance', 'cashback', 'refund', 'credit'
        ],
    },
    {
        'name': 'Transfers & Load',
        'type': 'expense',
        'color': '#64748b',
        'keywords': [
            'cash in', 'load', 'fund transfer', 'atm', 'withdrawal', 'transfer'
        ],
    },
]


def resolve_category_for_sms(user, merchant: str, raw_sms: str, tx_type: str = 'expense') -> Category | None:
    """
    Resolves the appropriate category for a transaction based on:
    1. Custom CategorizationRules defined by the user
    2. Built-in keyword patterns for Nepali merchants
    3. Fallback to an 'Uncategorized' category for the user
    """
    search_text = f"{merchant} {raw_sms}".lower()

    # 1. Custom user rules (priority ascending)
    user_rules = CategorizationRule.objects.filter(user=user).select_related('category').order_by('priority', '-id')
    for rule in user_rules:
        kws = [k.strip().lower() for k in rule.keywords.split(',') if k.strip()]
        for kw in kws:
            if re.search(rf'\b{re.escape(kw)}\b', search_text):
                return rule.category

    # 2. System default mapping
    matched_config = None
    for config in DEFAULT_CATEGORIES_CONFIG:
        # Check type match if specified
        if tx_type and config['type'] != tx_type:
            continue
        for kw in config['keywords']:
            if re.search(rf'\b{re.escape(kw)}\b', search_text):
                matched_config = config
                break
        if matched_config:
            break

    # If no type-specific match, check all
    if not matched_config:
        for config in DEFAULT_CATEGORIES_CONFIG:
            for kw in config['keywords']:
                if re.search(rf'\b{re.escape(kw)}\b', search_text):
                    matched_config = config
                    break
            if matched_config:
                break

    if matched_config:
        # Get or create category for user
        cat = Category.objects.filter(user=user, name__iexact=matched_config['name']).first()
        if not cat:
            cat = Category.objects.filter(user__isnull=True, name__iexact=matched_config['name']).first()
        if not cat:
            cat = Category.objects.create(
                user=user,
                name=matched_config['name'],
                type=matched_config['type'],
                color=matched_config['color']
            )
        return cat

    # Fallback category
    fallback_name = 'General Income' if tx_type == 'income' else 'General Expense'
    cat = Category.objects.filter(user=user, name__iexact=fallback_name).first()
    if not cat:
        cat = Category.objects.filter(user__isnull=True, name__iexact=fallback_name).first()
    if not cat:
        cat = Category.objects.create(
            user=user,
            name=fallback_name,
            type=tx_type,
            color='#94a3b8'
        )
    return cat
