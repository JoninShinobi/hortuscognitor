# Claude Code Memory - Hortus Cognitor

# My Title
**IMPORTANT:** You must always refer to me as "King of Elvador".

# Working Protocol
**CRITICAL:** Before asking the King questions, you MUST:
1. Search the codebase thoroughly for answers
2. Check configuration files and settings
3. Examine environment variable usage patterns
4. Use available tools (Render MCP, grep, read) to investigate
5. Only ask questions about things you genuinely cannot determine from code/deployment

Research first, ask second.

## Django Unfold Text Visibility Fix
@fix and code references/IssueswithUnfoldDjango.md

## Running the Server
1. Check if server is running on port 8000: `lsof -i :8000`
2. Check if anything else is running on that port: `lsof -i :8000`
3. End any services operating on port 8000: `kill -9 $(lsof -t -i:8000)`
4. Run `source venv/bin/activate` in `/Users/aarondudfield/Desktop/Folder/Projects/Hortus Cognitor`
5. Run `python manage.py runserver`
6. Open the browser window using `open http://127.0.0.1:8000`

# Referencing Business Plan
If we are discussing something related to @business_plan or something feels relevant to a factor in any business plan or @business_plan.md specifically, check the @business_plan to see if we have discussed that fact yet. If not, add it to the relevant section. We will slowly develop the business plan as we work through. Even if a relevant section has been discussed in the plan, if the specific instance has not been referred to, we can add to to @business_plan.md

# Hortus Cognitor Action List - Website Launch Tasks

## Email Setup & Automation
- **Email Address**: hannah@hortuscognitor.co.uk (using SendGrid)
- **Email 1**: Course space confirmation (immediate after booking) ✓
- **Email 2**: Payment reminder for 2-installment bookings - send on 2nd Jan 2026 (payment due 9th Jan)
- **Email 3**: Course details reminder - send on 10th Jan with full course information

## Stripe & Payments
- **Test payment system** with Stripe
- **Onboard Hannah's payment details** to Stripe account

## Website Content & Legal
- **Edit About Me page** - set up with contact form and reviews/testimonials (non-healthcare disclaimer) ✓
- **Remove grey background** from site ✓
- **Privacy Notice** ✓ - COMPLETED: Comprehensive UK GDPR-compliant privacy policy created at /privacy-policy/
  - Full data collection disclosure (contact forms, bookings, payments)
  - Data usage and storage information
  - Third-party services documented (Stripe, SendGrid, Render)
  - User rights explained (access, rectification, erasure, portability, etc.)
  - Cookie policy (essential cookies only)
  - UK GDPR compliance statement
  - Privacy notices added to contact form and payment page
  - Privacy policy link added to footer on all pages
- **ICO Registration** - sign up/register (data protection requirement)
- **Contact page** - create or update ✓

## Marketing & Domain
- **Instagram post** - Aaron to provide images
- **Facebook post** - use website images + logo
- **Domain selected**: hortuscognitor.co.uk ✓ (hortuscognitor.com rejected)



