# Stripe Payment Integration Setup Guide

This guide will walk you through setting up Stripe for the IoT Security Platform.

## 📋 Prerequisites

- A Stripe account (sign up at https://stripe.com)
- Access to your `.env` file

---

## Step 1: Create Stripe Account

1. Go to https://stripe.com
2. Click "Sign up" and create your account
3. Complete the account verification process
4. You'll start in **Test Mode** (perfect for development)

---

## Step 2: Get API Keys

1. Log in to your Stripe Dashboard
2. Click on "Developers" in the left sidebar
3. Click on "API keys"
4. You'll see two keys:
   - **Publishable key** (starts with `pk_test_...`)
   - **Secret key** (starts with `sk_test_...`) - Click "Reveal test key"

5. Copy these keys and add them to your `.env` file:

```env
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
```

---

## Step 3: Create Products and Prices

### Option A: Using Stripe Dashboard (Recommended)

1. In Stripe Dashboard, go to **Products** → **Add product**

2. **Create Pro Plan**:
   - **Name**: IoT Security Pro
   - **Description**: Professional IoT security monitoring with advanced features
   - **Pricing**:
     - **Price**: £4.99
     - **Billing period**: Monthly
     - **Currency**: GBP
   - Click "Save product"
   - **Copy the Price ID** (starts with `price_...`)

3. **Create Business Plan**:
   - **Name**: IoT Security Business
   - **Description**: Enterprise IoT security with teams, audit logs, and unlimited devices
   - **Pricing**:
     - **Price**: £9.99
     - **Billing period**: Monthly
     - **Currency**: GBP
   - Click "Save product"
   - **Copy the Price ID** (starts with `price_...`)

4. Add the Price IDs to your `.env` file:

```env
STRIPE_PRICE_PRO=price_your_pro_price_id_here
STRIPE_PRICE_BUSINESS=price_your_business_price_id_here
```

### Option B: Using Stripe CLI (Advanced)

```bash
# Install Stripe CLI: https://stripe.com/docs/stripe-cli

# Create Pro product and price
stripe products create \
  --name="IoT Security Pro" \
  --description="Professional IoT security monitoring"

stripe prices create \
  --product=prod_XXX \
  --unit-amount=499 \
  --currency=gbp \
  --recurring[interval]=month

# Create Business product and price
stripe products create \
  --name="IoT Security Business" \
  --description="Enterprise IoT security"

stripe prices create \
  --product=prod_YYY \
  --unit-amount=999 \
  --currency=gbp \
  --recurring[interval]=month
```

---

## Step 4: Set Up Webhooks

Webhooks allow Stripe to notify your app when payments succeed or subscriptions change.

### Development (Local Testing)

1. Install Stripe CLI: https://stripe.com/docs/stripe-cli

2. Run the webhook forwarder:
```bash
stripe listen --forward-to localhost:8000/api/payments/webhook
```

3. Copy the webhook signing secret (starts with `whsec_...`)

4. Add to `.env`:
```env
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

### Production

1. In Stripe Dashboard, go to **Developers** → **Webhooks**
2. Click **Add endpoint**
3. **Endpoint URL**: `https://www.pro-alert.co.uk/api/payments/webhook` (or your real `APP_BASE_URL` host, same origin as the app)
4. **Events to send**:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. Click **Add endpoint**
6. Copy the **Signing secret** (starts with `whsec_...`)
7. Add to your production `.env`:
```env
STRIPE_WEBHOOK_SECRET=whsec_your_production_webhook_secret_here
```

---

## Step 5: Configure Customer Portal

The Customer Portal allows users to manage their subscriptions, update payment methods, and view invoices.

1. In Stripe Dashboard, go to **Settings** → **Billing** → **Customer portal**
2. Click **Activate test link** (for test mode)
3. Configure settings:
   - ✅ **Allow customers to update payment methods**
   - ✅ **Allow customers to update billing information**
   - ✅ **Allow customers to view invoices**
   - ✅ **Allow customers to cancel subscriptions**
4. Click **Save changes**

---

## Step 6: Test the Integration

### Test Cards

Use these test card numbers in Test Mode:

- **Successful payment**: `4242 4242 4242 4242`
- **Requires authentication**: `4000 0025 0000 3155`
- **Declined**: `4000 0000 0000 9995`

**Expiry**: Any future date (e.g., 12/34)
**CVC**: Any 3 digits (e.g., 123)
**ZIP**: Any 5 digits (e.g., 12345)

### Testing Flow

1. Start your server:
```bash
python -m uvicorn main:app --reload
```

2. Go to http://localhost:8000/pricing

3. Click "Upgrade to Pro"

4. Use test card `4242 4242 4242 4242`

5. Complete checkout

6. Verify:
   - User's plan updated in database
   - Subscription appears in Stripe Dashboard
   - Webhook events received

---

## Step 7: Go Live (Production)

When you're ready to accept real payments:

1. **Complete Stripe Account Verification**:
   - In Stripe Dashboard, complete all required business information
   - Provide bank account details for payouts
   - Submit identity verification documents if required

2. **Switch to Live Mode**:
   - Toggle from "Test mode" to "Live mode" in Stripe Dashboard
   - Get your **Live API keys** (start with `pk_live_...` and `sk_live_...`)
   - Create **Live products and prices** (same as test mode)
   - Set up **Live webhooks**

3. **Update Production `.env`**:
```env
STRIPE_SECRET_KEY=sk_live_your_live_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_publishable_key
STRIPE_PRICE_PRO=price_live_pro_price_id
STRIPE_PRICE_BUSINESS=price_live_business_price_id
STRIPE_WEBHOOK_SECRET=whsec_live_webhook_secret
```

4. **Redirects**: Checkout success/cancel and Customer Portal return URLs use **`APP_BASE_URL`** from the environment (see `get_public_app_base_url()` in `core/config.py`). Set `APP_BASE_URL=https://www.yourdomain.com` on Railway with no trailing slash.

---

## 🔒 Security Best Practices

1. **Never commit API keys to Git**:
   - Keep `.env` in `.gitignore`
   - Use environment variables in production

2. **Always verify webhook signatures**:
   - The code already does this in `routes/payments.py`

3. **Use HTTPS in production**:
   - Stripe requires HTTPS for webhooks

4. **Monitor for fraud**:
   - Enable Stripe Radar (included free)
   - Review suspicious transactions

---

## 📊 Monitoring

### Stripe Dashboard

Monitor your business in real-time:
- **Home**: Revenue, customers, recent payments
- **Payments**: All payment transactions
- **Customers**: Customer list and details
- **Subscriptions**: Active and cancelled subscriptions
- **Disputes**: Handle chargebacks

### Logs

Check webhook delivery:
- **Developers** → **Webhooks** → Click your endpoint
- View successful and failed webhook attempts
- Retry failed webhooks manually

---

## 💰 Pricing

### Stripe Fees

- **2.9% + 30¢** per successful card charge
- **0.5%** additional for international cards
- **No monthly fees** (pay as you go)

### Example Revenue

If you charge £4.99 for Pro plan:
- Stripe fee: £0.24
- Your revenue: £4.75 (95.2%)

If you charge £9.99 for Business plan:
- Stripe fee: £0.42
- Your revenue: £9.57 (95.8%)

---

## 🆘 Troubleshooting

### Webhook not receiving events

1. Check webhook endpoint is publicly accessible
2. Verify webhook secret in `.env` matches Stripe Dashboard
3. Check server logs for errors
4. Use Stripe CLI to test locally: `stripe listen --forward-to localhost:8000/api/payments/webhook`

### Payment succeeds but subscription not activated

1. Check webhook events in Stripe Dashboard
2. Verify `checkout.session.completed` event is being sent
3. Check server logs for webhook processing errors
4. Ensure database connection is working

### Customer Portal not working

1. Verify Customer Portal is activated in Stripe Dashboard
2. Check that user has `stripe_customer_id` in database
3. Ensure user has an active subscription

---

## 📚 Additional Resources

- **Stripe Documentation**: https://stripe.com/docs
- **Stripe API Reference**: https://stripe.com/docs/api
- **Stripe Testing**: https://stripe.com/docs/testing
- **Stripe CLI**: https://stripe.com/docs/stripe-cli
- **Stripe Support**: https://support.stripe.com

---

## ✅ Checklist

Before going live, ensure:

- [ ] Stripe account fully verified
- [ ] Live API keys configured
- [ ] Products and prices created in Live mode
- [ ] Webhooks configured for production URL
- [ ] Customer Portal activated
- [ ] Test payments completed successfully
- [ ] Webhook events processed correctly
- [ ] Error handling tested
- [ ] HTTPS enabled on production server
- [ ] `.env` file secured (not in Git)
- [ ] Monitoring and alerts set up

---

**Need Help?**

- Stripe Support: https://support.stripe.com
- Stripe Discord: https://stripe.com/discord
- Our Support: [Your support email]
