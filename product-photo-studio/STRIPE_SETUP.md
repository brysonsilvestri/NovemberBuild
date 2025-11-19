# Stripe Integration Setup Guide

This document explains how the Stripe checkout integration works and how to verify it's configured correctly.

## Overview

The application uses Stripe Checkout for subscription billing with three tiers:
- **Starter**: $6/month or $60/year ($5/month)
- **Creator**: $11/month or $220/year ($18.33/month) - includes 50% off first month for monthly plan
- **Enterprise**: $99/month or $990/year ($82.50/month)

## How It Works

### 1. User Flow

1. User visits `/pricing` and selects a plan
2. User clicks "Get Started" → redirected to `/signup-plan?plan=X&billing=Y`
3. User creates account via `/api/signup` endpoint
4. Backend creates Stripe Checkout session with appropriate price ID
5. User completes payment on Stripe
6. User redirected back to `/post-checkout?session_id=XXX`
7. Webhook `checkout.session.completed` activates subscription and allocates credits

### 2. Price ID Mapping

The application maps plan + billing cycle to Stripe price IDs:

```python
# From app.py lines 275-279
price_id_map = {
    'starter': STRIPE_PRICE_ID_STARTER if billing == 'monthly' else STRIPE_PRICE_ID_STARTER_ANNUAL,
    'creator': STRIPE_PRICE_ID_CREATOR if billing == 'monthly' else STRIPE_PRICE_ID_CREATOR_ANNUAL,
    'enterprise': STRIPE_PRICE_ID_ENTERPRISE if billing == 'monthly' else STRIPE_PRICE_ID_ENTERPRISE_ANNUAL,
}
```

### 3. Webhook Handling

The webhook endpoint `/stripe/webhook` handles:
- `checkout.session.completed` - Initial subscription activation
- `customer.subscription.updated` - Plan changes
- `customer.subscription.deleted` - Cancellations
- `invoice.payment_succeeded` - Monthly credit resets

## Verification Steps

### Step 1: Run the Verification Script

```bash
python verify_stripe_config.py
```

This will check:
- All price IDs are properly formatted
- No duplicate price IDs
- Display expected pricing structure

### Step 2: Verify Against Stripe Dashboard

1. Log into [Stripe Dashboard](https://dashboard.stripe.com/)
2. Navigate to **Products** → **Pricing**
3. For each plan tier, verify:

   **Starter Plan:**
   - Monthly price: $6.00/month
     - API ID: Should match `STRIPE_PRICE_ID_STARTER`
   - Annual price: $60.00/year
     - API ID: Should match `STRIPE_PRICE_ID_STARTER_ANNUAL`

   **Creator Plan:**
   - Monthly price: $11.00/month
     - API ID: Should match `STRIPE_PRICE_ID_CREATOR`
   - Annual price: $220.00/year
     - API ID: Should match `STRIPE_PRICE_ID_CREATOR_ANNUAL`

   **Enterprise Plan:**
   - Monthly price: $99.00/month
     - API ID: Should match `STRIPE_PRICE_ID_ENTERPRISE`
   - Annual price: $990.00/year
     - API ID: Should match `STRIPE_PRICE_ID_ENTERPRISE_ANNUAL`

### Step 3: Verify Creator Coupon

1. Navigate to **Coupons** in Stripe Dashboard
2. Find coupon with ID `L5UtC6vm` (or your custom ID)
3. Verify settings:
   - Percent off: 50%
   - Duration: Once (first payment only)
   - Status: Active

### Step 4: Test the Integration

1. Set test mode in Stripe: Use `sk_test_...` keys
2. Visit `/pricing` page
3. Click "Get Started" on any plan
4. Complete signup flow
5. Use Stripe test card: `4242 4242 4242 4242`
6. Verify redirect to app after checkout
7. Check webhook logs in Stripe Dashboard

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required Stripe variables
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxxx

# App base URL for redirects
APP_BASE_URL=http://localhost:5000

# Price IDs (verify these match your Stripe account!)
STRIPE_PRICE_ID_STARTER=price_1SIDgmAEzseiAJU6m8OBsmEE
STRIPE_PRICE_ID_CREATOR=price_1SIDnMAEzseiAJU6DaZmPwBf
STRIPE_PRICE_ID_ENTERPRISE=price_1SIDsNAEzseiAJU6BNb5geHN
STRIPE_PRICE_ID_STARTER_ANNUAL=price_1SIDgmAEzseiAJU6vsEva7Fe
STRIPE_PRICE_ID_CREATOR_ANNUAL=price_1SIDp0AEzseiAJU6mC23jEBO
STRIPE_PRICE_ID_ENTERPRISE_ANNUAL=price_1SIDr3AEzseiAJU6vAFIkUe9

# Creator 50% off coupon
STRIPE_CREATOR_COUPON=L5UtC6vm
```

### Webhook Setup

1. In Stripe Dashboard, go to **Developers** → **Webhooks**
2. Click **Add endpoint**
3. Set endpoint URL: `https://your-domain.com/stripe/webhook`
4. Select events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
5. Copy the webhook signing secret to `STRIPE_WEBHOOK_SECRET` in `.env`

## Code Structure

### Key Files

- **`app.py`** (lines 28-44): Stripe configuration and price IDs
- **`app.py`** (lines 226-313): `/api/signup` endpoint - creates checkout sessions
- **`app.py`** (lines 450-501): `/upgrade` endpoint - upgrade flow
- **`app.py`** (lines 559-651): Webhook handler
- **`templates/pricing.html`**: Pricing page with plan cards and checkout links
- **`templates/signup_plan.html`**: Tier-specific signup pages

### Price ID Usage

```python
# 1. Define price IDs (app.py:33-38)
STRIPE_PRICE_ID_STARTER = os.getenv("STRIPE_PRICE_ID_STARTER", "price_...")
STRIPE_PRICE_ID_CREATOR = os.getenv("STRIPE_PRICE_ID_CREATOR", "price_...")
# ... etc

# 2. Map to tiers (app.py:90-97)
PRICE_ID_TO_TIER = {
    STRIPE_PRICE_ID_STARTER: 'starter',
    STRIPE_PRICE_ID_CREATOR: 'creator',
    # ... etc
}

# 3. Create checkout session (app.py:275-306)
price_id_map = {
    'starter': STRIPE_PRICE_ID_STARTER if billing == 'monthly' else STRIPE_PRICE_ID_STARTER_ANNUAL,
    # ... etc
}
price_id = price_id_map.get(plan)
session = stripe.checkout.Session.create(
    line_items=[{"price": price_id, "quantity": 1}],
    # ... etc
)

# 4. Webhook processes subscription (app.py:569-620)
price_id = session['line_items']['data'][0]['price']['id']
tier = PRICE_ID_TO_TIER.get(price_id)
user.plan_tier = tier
user.credits_remaining = PLAN_CREDITS[tier]
```

## Troubleshooting

### Issue: Checkout redirects to wrong price

**Solution:** Verify price IDs in `.env` match Stripe Dashboard

### Issue: Subscription created but credits not allocated

**Solution:**
1. Check webhook is configured in Stripe
2. Verify `STRIPE_WEBHOOK_SECRET` is correct
3. Check webhook logs in Stripe Dashboard for errors
4. Ensure `PRICE_ID_TO_TIER` mapping includes the price ID

### Issue: Creator 50% off not applying

**Solution:**
1. Verify `STRIPE_CREATOR_COUPON` is set in `.env`
2. Check coupon exists and is active in Stripe Dashboard
3. Ensure coupon ID matches exactly (case-sensitive)
4. Verify coupon duration is "Once"

### Issue: Annual billing shows wrong price

**Solution:**
1. Verify annual price IDs are different from monthly
2. Check pricing page JavaScript `toggleBilling()` function
3. Ensure `.env` has correct annual price IDs

## Testing Checklist

- [ ] All 6 price IDs configured in `.env`
- [ ] Price IDs match Stripe Dashboard
- [ ] Webhook endpoint configured in Stripe
- [ ] Webhook secret set in `.env`
- [ ] Creator coupon exists and is active
- [ ] Test monthly checkout flow (all 3 tiers)
- [ ] Test annual checkout flow (all 3 tiers)
- [ ] Verify credits allocated after checkout
- [ ] Test webhook events fire correctly
- [ ] Verify Creator discount applies
- [ ] Test subscription upgrade/downgrade
- [ ] Test subscription cancellation

## Support

For issues with Stripe integration:
1. Check webhook logs in Stripe Dashboard
2. Review application logs for errors
3. Run `python verify_stripe_config.py` to verify configuration
4. Consult [Stripe Documentation](https://stripe.com/docs/billing/subscriptions/checkout)
