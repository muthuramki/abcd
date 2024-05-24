"""
URL configuration for ocr project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from inte.views import upload_invoice, push_to_sap, login_view, back_login_view, forgot_password_view

urlpatterns = [
    path('', upload_invoice, name='upload_invoice'),
    path('push-to-sap/', push_to_sap, name='push_to_sap'),
    path('login.html', login_view, name='login'),
    path('forgot-password.html',forgot_password_view, name='forgot_password'),
    path('login.html', back_login_view, name='back_to_login'),
    
]