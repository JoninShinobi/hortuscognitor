#!/usr/bin/env python3
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hortus_cognitor.settings')
django.setup()

from courses.models import PricingTier

# Get all pricing tiers
tiers = PricingTier.objects.all()

for tier in tiers:
    # Remove all newlines and extra spaces, keeping single spaces
    cleaned = ' '.join(tier.description.split())

    print(f"\nTier: {tier.get_tier_display()}")
    print(f"Before: {repr(tier.description)}")
    print(f"After: {repr(cleaned)}")

    # Update the description
    tier.description = cleaned
    tier.save()

print("\n✓ All pricing tier descriptions have been cleaned!")
