from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Course, CourseSession, Instructor, Booking, PricingTier, PaymentPlan, CoursePayment, StripePaymentRecord, SiteSettings

class CourseSessionInline(TabularInline):
    model = CourseSession
    extra = 1
    fields = ['session_number', 'date', 'start_time', 'end_time']

@admin.register(Course)
class CourseAdmin(ModelAdmin):
    list_display = ['title', 'start_date', 'duration', 'price', 'max_participants', 'is_active']
    list_filter = ['is_active', 'start_date']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_date'
    inlines = [CourseSessionInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'subtitle', 'slug', 'is_active')
        }),
        ('Hero Section', {
            'fields': ('hero_image',),
            'description': 'Hero background image for course pages. Recommended size: 1920x1080px (16:9 aspect ratio).'
        }),
        ('Course Details', {
            'fields': ('description', 'what_you_will_experience', 'course_structure')
        }),
        ('Logistics', {
            'fields': ('location', 'accessibility')
        }),
        ('Target Audience & Benefits', {
            'fields': ('who_this_is_for', 'what_you_will_gain')
        }),
        ('Scheduling & Pricing', {
            'fields': ('start_date', 'duration', 'max_participants', 'price')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Automatically managed timestamps.'
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']

    # Media removed - using Django Unfold's global styles instead

@admin.register(CourseSession)
class CourseSessionAdmin(ModelAdmin):
    list_display = ['course', 'session_number', 'date', 'start_time', 'end_time']
    list_filter = ['course', 'date']
    search_fields = ['course__title']
    date_hierarchy = 'date'

    fieldsets = (
        ('Session Information', {
            'fields': ('course', 'session_number', 'date', 'start_time', 'end_time')
        }),
    )

@admin.register(Instructor)
class InstructorAdmin(ModelAdmin):
    list_display = ['name', 'photo_preview', 'course_count']
    search_fields = ['name', 'bio']
    filter_horizontal = ['courses']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'photo')
        }),
        ('Biography', {
            'fields': ('bio',),
            'description': 'Detailed biography to display on course pages.'
        }),
        ('Courses', {
            'fields': ('courses',),
            'description': 'Select which courses this instructor teaches.'
        })
    )
    
    def photo_preview(self, obj):
        if obj.photo:
            return f'<img src="{obj.photo.url}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover;">'
        return "No photo"
    photo_preview.allow_tags = True
    photo_preview.short_description = "Photo"
    
    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = "Courses"
    
@admin.register(Booking)
class BookingAdmin(ModelAdmin):
    list_display = ['full_name', 'email', 'course', 'created_at']
    list_filter = ['course', 'created_at']
    search_fields = ['full_name', 'email', 'course__title']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Booking Details', {
            'fields': ('course', 'message', 'created_at')
        })
    )


class PricingTierInline(TabularInline):
    model = PricingTier
    extra = 0
    fields = ['tier', 'price', 'sessions', 'description']
    readonly_fields = []


@admin.register(PricingTier)
class PricingTierAdmin(ModelAdmin):
    list_display = ['course', 'tier', 'price', 'price_per_session', 'sessions']
    list_filter = ['tier', 'course']
    search_fields = ['course__title', 'description']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'tier', 'price', 'sessions')
        }),
        ('Description', {
            'fields': ('description',),
            'description': 'Detailed description explaining who this pricing tier is for.'
        })
    )


@admin.register(PaymentPlan)
class PaymentPlanAdmin(ModelAdmin):
    list_display = ['name', 'deposit_percentage', 'deposit_deadline', 'final_payment_deadline', 'is_active']
    list_filter = ['name', 'is_active']
    
    fieldsets = (
        ('Plan Details', {
            'fields': ('name', 'deposit_percentage', 'is_active')
        }),
        ('Payment Deadlines', {
            'fields': ('deposit_deadline', 'final_payment_deadline'),
            'description': 'Set the deadlines for deposit and final payments.'
        })
    )


class StripePaymentRecordInline(TabularInline):
    model = StripePaymentRecord
    extra = 0
    readonly_fields = ['payment_type', 'stripe_payment_intent_id', 'amount', 'currency', 'status', 'created_at', 'processed_at']
    can_delete = False


@admin.register(CoursePayment)
class CoursePaymentAdmin(ModelAdmin):
    list_display = ['booking', 'pricing_tier', 'payment_plan', 'status', 'total_amount', 'next_payment_due', 'is_overdue']
    list_filter = ['status', 'pricing_tier__tier', 'payment_plan__name', 'created_at']
    search_fields = ['booking__full_name', 'booking__email', 'booking__course__title']
    date_hierarchy = 'created_at'
    readonly_fields = ['total_amount', 'deposit_amount', 'final_amount', 'created_at', 'updated_at', 'is_overdue', 'next_payment_due']
    inlines = [StripePaymentRecordInline]
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('booking', 'pricing_tier', 'payment_plan', 'status')
        }),
        ('Stripe Integration', {
            'fields': ('stripe_customer_id', 'stripe_payment_intent_id'),
            'classes': ('collapse',)
        }),
        ('Payment Amounts', {
            'fields': ('total_amount', 'deposit_amount', 'final_amount'),
            'classes': ('collapse',),
            'description': 'Amounts are automatically calculated based on pricing tier and payment plan.'
        }),
        ('Payment Tracking', {
            'fields': ('deposit_paid_at', 'final_paid_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Status Information', {
            'fields': ('is_overdue', 'next_payment_due'),
            'classes': ('collapse',),
            'description': 'Automatically calculated status information.'
        })
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('booking', 'pricing_tier', 'payment_plan')


@admin.register(StripePaymentRecord)
class StripePaymentRecordAdmin(ModelAdmin):
    list_display = ['course_payment', 'payment_type', 'amount', 'status', 'created_at']
    list_filter = ['payment_type', 'status', 'currency', 'created_at']
    search_fields = ['course_payment__booking__full_name', 'stripe_payment_intent_id']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('course_payment', 'payment_type', 'amount', 'currency', 'status')
        }),
        ('Stripe Details', {
            'fields': ('stripe_payment_intent_id',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    """
    Admin interface for site-wide settings.
    Allows Hannah to manage notification emails and other global settings.
    """

    fieldsets = (
        ('Email Notifications', {
            'fields': ('booking_notification_emails',),
            'description': (
                'Configure who receives email notifications when bookings are made. '
                'You can enter multiple email addresses separated by commas. '
                'For example: hannah@hortuscognitor.co.uk, admin@hortuscognitor.co.uk'
            )
        }),
    )

    def has_add_permission(self, request):
        """Prevent adding more than one settings instance"""
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of settings"""
        return False