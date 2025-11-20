#!/usr/bin/env python3
"""
Stripe Configuration Verification Script

This script helps verify that your Stripe price IDs are correctly configured.
It will check:
1. That all required price IDs are set
2. That the price IDs follow Stripe's format
3. That the mapping between price IDs and tiers is consistent

Usage:
    python verify_stripe_config.py

You can also use this to fetch price details from Stripe (requires API key):
    python verify_stripe_config.py --fetch
"""

import os
import sys

# Try to load environment variables from .env if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, will just use environment variables
    pass

# Expected price IDs from app.py defaults
DEFAULT_PRICE_IDS = {
    'STRIPE_PRICE_ID_STARTER': 'price_1SIDgmAEzseiAJU6m8OBsmEE',
    'STRIPE_PRICE_ID_CREATOR': 'price_1SIDnMAEzseiAJU6DaZmPwBf',
    'STRIPE_PRICE_ID_ENTERPRISE': 'price_1SIDsNAEzseiAJU6BNb5geHN',
    'STRIPE_PRICE_ID_STARTER_ANNUAL': 'price_1SIDgmAEzseiAJU6vsEva7Fe',
    'STRIPE_PRICE_ID_CREATOR_ANNUAL': 'price_1SIDp0AEzseiAJU6mC23jEBO',
    'STRIPE_PRICE_ID_ENTERPRISE_ANNUAL': 'price_1SIDr3AEzseiAJU6vAFIkUe9',
}

# Expected pricing from pricing.html
EXPECTED_PRICING = {
    'starter': {
        'monthly': {'price': 6.00, 'credits': 60000, 'images': 120},
        'annual': {'price': 5.00, 'annual_total': 60.00, 'credits': 60000, 'images': 120},
    },
    'creator': {
        'monthly': {'price': 11.00, 'first_month_discount': '50%', 'credits': 200000, 'images': 400},
        'annual': {'price': 18.33, 'annual_total': 220.00, 'credits': 200000, 'images': 400},
    },
    'enterprise': {
        'monthly': {'price': 99.00, 'credits': 800000, 'images': 1600},
        'annual': {'price': 82.50, 'annual_total': 990.00, 'credits': 800000, 'images': 1600},
    }
}


def check_price_id_format(price_id):
    """Verify price ID follows Stripe's format"""
    if not price_id.startswith('price_'):
        return False, "Price ID must start with 'price_'"
    if len(price_id) < 20:
        return False, "Price ID seems too short"
    return True, "OK"


def verify_configuration():
    """Verify that Stripe configuration is complete and consistent"""
    print("=" * 70)
    print("STRIPE CONFIGURATION VERIFICATION")
    print("=" * 70)
    print()

    errors = []
    warnings = []

    # Check each price ID
    print("1. Checking Price IDs:")
    print("-" * 70)
    for key, default_value in DEFAULT_PRICE_IDS.items():
        actual_value = os.getenv(key, default_value)
        is_using_default = actual_value == default_value

        # Check format
        is_valid, message = check_price_id_format(actual_value)

        status = "✓" if is_valid else "✗"
        env_status = "(using default)" if is_using_default else "(from .env)"

        print(f"{status} {key}")
        print(f"  Value: {actual_value} {env_status}")
        print(f"  Status: {message}")

        if not is_valid:
            errors.append(f"{key}: {message}")

        if is_using_default:
            warnings.append(f"{key} is using default value - verify this is correct for your Stripe account")

        print()

    # Check for duplicate price IDs
    print("\n2. Checking for Duplicate Price IDs:")
    print("-" * 70)
    price_ids = [os.getenv(key, default) for key, default in DEFAULT_PRICE_IDS.items()]
    duplicates = set([pid for pid in price_ids if price_ids.count(pid) > 1])

    if duplicates:
        print("✗ Found duplicate price IDs:")
        for dup in duplicates:
            keys_with_dup = [k for k, v in DEFAULT_PRICE_IDS.items()
                           if os.getenv(k, v) == dup]
            print(f"  - {dup}")
            print(f"    Used by: {', '.join(keys_with_dup)}")
            errors.append(f"Duplicate price ID: {dup}")
    else:
        print("✓ No duplicate price IDs found")

    print()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if errors:
        print(f"\n❌ Found {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✓ No errors found")

    if warnings:
        print(f"\n⚠️  {len(warnings)} warning(s):")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("\n✓ No warnings")

    print("\n" + "=" * 70)
    print("EXPECTED PRICING (from pricing.html)")
    print("=" * 70)

    for plan, pricing in EXPECTED_PRICING.items():
        print(f"\n{plan.upper()}:")
        print(f"  Monthly: ${pricing['monthly']['price']}/mo ({pricing['monthly']['images']} images)")
        if 'first_month_discount' in pricing['monthly']:
            print(f"    Discount: {pricing['monthly']['first_month_discount']} off first month")
        print(f"  Annual:  ${pricing['annual']['price']}/mo (billed ${pricing['annual']['annual_total']}/year, {pricing['annual']['images']} images)")

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("""
To verify these price IDs match your Stripe account:

1. Log into your Stripe Dashboard: https://dashboard.stripe.com/

2. Go to Products > Pricing

3. For each plan, verify the price ID matches:
   - Click on the price
   - Check the "API ID" field
   - Compare with the values shown above

4. Verify the prices match:
   - Starter Monthly: $6.00/month
   - Starter Annual: $60.00/year ($5.00/month)
   - Creator Monthly: $11.00/month (with 50% off first month coupon)
   - Creator Annual: $220.00/year ($18.33/month)
   - Enterprise Monthly: $99.00/month
   - Enterprise Annual: $990.00/year ($82.50/month)

5. If any price IDs are incorrect, create a .env file with:
   STRIPE_PRICE_ID_STARTER=price_xxxxx
   STRIPE_PRICE_ID_CREATOR=price_xxxxx
   STRIPE_PRICE_ID_ENTERPRISE=price_xxxxx
   STRIPE_PRICE_ID_STARTER_ANNUAL=price_xxxxx
   STRIPE_PRICE_ID_CREATOR_ANNUAL=price_xxxxx
   STRIPE_PRICE_ID_ENTERPRISE_ANNUAL=price_xxxxx

6. Verify Creator monthly plan has a 50% off coupon:
   - Coupon ID should be in .env as: STRIPE_CREATOR_COUPON=L5UtC6vm
   - Verify this coupon exists in Stripe Dashboard > Coupons
""")

    return len(errors) == 0


def fetch_stripe_prices():
    """Fetch actual price details from Stripe API"""
    try:
        import stripe
    except ImportError:
        print("Error: stripe module not installed. Run: pip install stripe")
        return

    stripe_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe_key:
        print("Error: STRIPE_SECRET_KEY not set in environment")
        return

    stripe.api_key = stripe_key

    print("\n" + "=" * 70)
    print("FETCHING PRICE DETAILS FROM STRIPE")
    print("=" * 70)

    for key, default_value in DEFAULT_PRICE_IDS.items():
        price_id = os.getenv(key, default_value)
        print(f"\n{key}:")
        print(f"  ID: {price_id}")

        try:
            price = stripe.Price.retrieve(price_id)
            product = stripe.Product.retrieve(price.product)

            amount = price.unit_amount / 100 if price.unit_amount else 0
            interval = price.recurring.get('interval') if price.recurring else 'one-time'

            print(f"  ✓ Product: {product.name}")
            print(f"  ✓ Amount: ${amount:.2f}")
            print(f"  ✓ Interval: {interval}")
            print(f"  ✓ Active: {price.active}")

        except stripe.error.InvalidRequestError as e:
            print(f"  ✗ Error: {e.user_message}")
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")


if __name__ == '__main__':
    if '--fetch' in sys.argv:
        fetch_stripe_prices()
    else:
        success = verify_configuration()
        sys.exit(0 if success else 1)
