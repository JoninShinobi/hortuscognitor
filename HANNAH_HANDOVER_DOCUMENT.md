# Hortus Cognitor Website - Admin Guide

**Welcome to your new website!** 🌱

This document contains everything you need to know to manage your Hortus Cognitor website and course bookings.

---

## 🔐 Your Login Details

### Website Admin Panel
- **URL**: https://hortuscognitor.co.uk/admin
- **Username**: `HannahWatkins`
- **Password**: `zR8$vN4mQ#wL9pX@Kt6!Yj2yF`

⚠️ **IMPORTANT**: Please save these credentials somewhere safe (like a password manager). Change the password if you prefer - you can do this in the admin panel under "Change password".

---

## 📧 Your Professional Email

You now have a professional email address for your business:

**Email**: `hannah@hortuscognitor.co.uk`

### How Emails Work

Your email is handled through SendGrid (an email service), which means:

1. **Incoming emails**: When someone emails hannah@hortuscognitor.co.uk, you'll receive it at your personal email address
2. **Outgoing emails**: When the website sends emails (booking confirmations, contact forms), they come from hannah@hortuscognitor.co.uk

### What Emails You'll Receive

**1. Contact Form Submissions**
- When someone fills out the contact form on your website
- You'll get an email with their name, email, phone, and message
- Contains a link to view the submission in your admin panel

**2. Course Booking Notifications**
- When someone books a course and completes payment
- Includes all their details and which pricing tier they selected
- Shows payment status (deposit paid or fully paid)
- Contains a link to view the booking in your admin panel

**3. Payment Confirmations** (what customers receive)
- Customers automatically receive a confirmation email when they pay
- This includes course details, what they paid, and what comes next

---

## 🎯 Using the Admin Panel

### Accessing the Admin Panel

1. Go to https://hortuscognitor.onrender.com/admin/
2. Enter your username: `HannahWatkins`
3. Enter your password: `zR8$vN4mQ#wL9pX@Kt6!Yj2yF`
4. Click "Log in"

### What You Can Do

#### 📚 **Courses**
- View all your courses
- Edit course details, dates, descriptions
- Change pricing
- Update course images
- Add individual session dates and times

#### 👥 **Bookings**
View all course bookings and contact form submissions:
- See who has booked courses
- Check payment status (pending, deposit paid, fully paid)
- View contact form messages
- See phone numbers and emails for all enquiries

#### 💳 **Course Payments**
Track all payments:
- See who has paid deposits vs. full amounts
- Check payment deadlines
- View pricing tier selections (Basic/Standard/Solidarity)
- Monitor outstanding payments

#### 💰 **Pricing Tiers**
Manage your three-tier pricing system:
- **Basic Tier** (Meeting Basic Needs): £225
- **Standard Tier** (Regular Income): £325
- **Solidarity Tier** (Financially Secure): £475

You can adjust these prices anytime.

#### 📅 **Payment Plans**
Manage payment options:
- **Pay in Full**: One payment before the course
- **Two Installments**: 50% deposit, then 50% final payment

#### 📧 **Site Settings**
- Configure which email addresses receive booking notifications
- You can add multiple emails separated by commas
- Example: `hannah@hortuscognitor.co.uk, assistant@hortuscognitor.co.uk`

---

## 💰 Payment System (Stripe)

Your website uses Stripe to accept payments securely.

### Current Status
✅ Stripe test mode is working
❌ **Action Required**: You need to connect your bank account to Stripe to receive actual payments

### How to Connect Your Bank Account

1. You'll need to complete "Stripe Onboarding" - Aaron will help you with this
2. This connects your bank account so money from course bookings goes directly to you
3. Stripe takes a small fee per transaction (standard payment processing fee)
4. Money is deposited to your bank account within a few business days

### Payment Flow

1. Customer selects a pricing tier (Basic/Standard/Solidarity)
2. Customer chooses payment plan (Full or Installments)
3. Customer enters their details and clicks "Proceed to Payment"
4. They're taken to Stripe's secure checkout page
5. After payment:
   - Customer receives confirmation email
   - You receive booking notification email
   - Booking appears in your admin panel

---

## 📅 Course Sessions Feature

Your courses now support multiple session dates!

### How to Add Session Dates

1. Go to **Courses** in admin panel
2. Click on your course (e.g., "Growing a Regenerative Movement")
3. Scroll to **Course Sessions**
4. Click "Add another Course session"
5. Enter:
   - Session number (1, 2, 3, etc.)
   - Date
   - Start time
   - End time
6. Click "Save"

### Where Sessions Appear
- On the course detail page
- In a "View Course Dates" dropdown for students
- Shows exact dates and times for each session

---

## 👥 Understanding Spaces Left

The course detail page automatically shows "Spaces Left" based on:
- **Max Participants**: 15 (you can change this)
- **Confirmed Bookings**: Only counts people who have paid (deposit or full)

This updates automatically - no manual tracking needed!

---

## 📋 Automated Reminder Emails

### What's Set Up

**Email 1: Course Confirmation** ✅ Working
- Sent immediately when someone pays
- Confirms their booking and payment

**Email 2: Payment Reminder** (Code ready, needs scheduling)
- For people paying in installments
- Should send on 2nd January 2026
- Reminds them final payment is due 9th January 2026

**Email 3: Course Details Reminder** (Code ready, needs scheduling)
- Should send on 10th January 2026
- Includes full course details and what to bring/expect

📝 *Note: Emails 2 and 3 need to be scheduled - this will be done before the course start date*

---

## 🔒 Security & Data Protection

### What's Protected
✅ All payments go through Stripe (PCI compliant - highest security standard)
✅ Customer data is encrypted
✅ Rate limiting prevents spam and abuse
✅ Secure admin login with strong password
✅ All forms validate user input for safety

### Still To Do
- **Privacy Notice**: Create a privacy policy page
- **ICO Registration**: Register with the UK Information Commissioner's Office (legally required for processing customer data)

---

## 🌐 Your Website URLs

- **Main Website**: https://hortuscognitor.onrender.com/
- **Admin Panel**: https://hortuscognitor.onrender.com/admin/
- **Domain**: hortuscognitor.co.uk (selected and ready to connect)

---

## 📞 Getting Help

### If You Need to...

**Change Course Details**
1. Admin Panel → Courses → Click on course → Edit → Save

**Check Who Has Booked**
1. Admin Panel → Bookings → View all bookings

**See Payment Status**
1. Admin Panel → Course Payments → Check status column

**Update Prices**
1. Admin Panel → Pricing Tiers → Click tier → Change price → Save

**Change Notification Email**
1. Admin Panel → Site Settings → Update "Booking notification emails" → Save

---

## ✅ Quick Checklist Before Launch

- [ ] Test the payment system with real card (small amount)
- [ ] Connect your bank account to Stripe (onboarding)
- [ ] Verify you're receiving booking notification emails
- [ ] Check course details are correct on the website
- [ ] Ensure pricing tiers are set correctly
- [ ] Add all course session dates
- [ ] Create Privacy Notice page
- [ ] Register with ICO
- [ ] Share website on social media

---

## 🎨 Marketing Launch

**What's Ready**
- Website is live and functional
- Payment system works (in test mode)
- Email notifications working
- Professional domain ready: hortuscognitor.co.uk

**What's Needed**
- Instagram post (Aaron to provide images)
- Facebook post (use website images + logo)
- Switch Stripe from test mode to live mode
- Connect bank account to Stripe

---

## 💡 Tips for Managing Bookings

1. **Check admin panel daily** during booking period
2. **Payment statuses**:
   - `pending`: No payment received yet
   - `deposit_paid`: First 50% paid (for installments)
   - `fully_paid`: All payment received
3. **Contact form submissions** appear in the Bookings section (they have no course attached)
4. **Export data**: You can export booking lists from the admin panel if needed

---

## 🔄 If Something Goes Wrong

**Can't log in?**
- Check you're using `HannahWatkins` (case-sensitive)
- Try copying the password exactly as written
- Clear your browser cache

**Not receiving emails?**
- Check your spam folder
- Verify in Admin Panel → Site Settings that your email is listed

**Payment not working?**
- Check if Stripe onboarding is complete
- Verify you're not in test mode (should use live Stripe keys)

**Need technical help?**
- Contact Aaron for any technical issues
- All code and documentation is on GitHub
- Render dashboard for server management

---

## 📱 Contact Information

**Your Professional Email**: hannah@hortuscognitor.co.uk
**Website**: https://hortuscognitor.co.uk
**Admin**: https://hortuscognitor.co.uk

---

**This website is ready for you to start taking bookings!** 🎉

The only critical step remaining before going fully live is connecting your bank account to Stripe so you can receive payments. Everything else is working and ready to go.

Good luck with your course! 🌱
