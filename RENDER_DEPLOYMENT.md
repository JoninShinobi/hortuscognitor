# Render Deployment Guide for Hortus Cognitor

## Prerequisites
- GitHub repository with the latest code
- Render account
- Stripe account with live keys

## Deployment Steps

### 1. Create PostgreSQL Database
1. Go to Render Dashboard
2. Create a new PostgreSQL database
3. Note the database connection details

### 2. Create Web Service
1. Create new Web Service from GitHub repo
2. Configure the following settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn hortus_cognitor.wsgi:application`
   - **Python Version**: 3.11.x

### 3. Environment Variables (Required)
Set these in Render's Environment Variables section:

```
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=False
DATABASE_URL=postgresql://... (from your Render PostgreSQL database)

# Stripe Configuration (REQUIRED for payments)
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_... (get from Stripe Dashboard)
STRIPE_HORTUS_ACCOUNT_ID=acct_...

# Domain configuration
ALLOWED_HOSTS=your-app.onrender.com,your-domain.com
```

### 4. Stripe Webhook Setup
1. In Stripe Dashboard, go to Webhooks
2. Add endpoint: `https://your-app.onrender.com/courses/webhooks/stripe/`
3. Select events: `payment_intent.succeeded`, `payment_intent.payment_failed`
4. Copy the webhook secret to `STRIPE_WEBHOOK_SECRET`

### 5. Database Migration
After first deployment, run in Render shell:
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## Security Notes
- All sensitive keys are stored in environment variables
- No hardcoded secrets in the codebase
- `.env` files are ignored by git

## Testing
1. Check payment flow works with test data
2. Verify admin panel access
3. Test contact form submission
4. Confirm static files are served correctly

## Post-Deployment
1. Set up custom domain (optional)
2. Configure SSL certificate
3. Test all payment flows thoroughly
4. Monitor application logs for any issues