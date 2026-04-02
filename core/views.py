from django.shortcuts import redirect, render
from django.views import View
from django.conf import settings



class HomeView(View):
    __template_name = 'index.html'

    def get(self, request):
        context = {
            'BACKEND_URL': settings.BACKEND_URL,
        }
        return render(request, self.__template_name, context)


class SellerView(View):
    __template_name = 'seller.html'

    def get(self, request):
        context = {
            'BACKEND_URL': settings.BACKEND_URL,
        }
        return render(request, self.__template_name, context)

class AuthView(View):
    __template_name = 'auth.html'

    def get(self, request):
        # JWT token frontend (localStorage) da tekshiriladi
        # Django session auth bu yerda ishlatilmaydi
        context = {
            'BACKEND_URL': settings.BACKEND_URL,
        }
        return render(request, self.__template_name, context)