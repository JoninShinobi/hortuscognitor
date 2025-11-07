from django.urls import path
from . import views

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list'),
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('<slug:slug>/book/', views.book_course, name='book_course'),
    path('<slug:slug>/payment/', views.payment_selection, name='payment_selection'),
    path('api/create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),
]