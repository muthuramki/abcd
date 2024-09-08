from django.shortcuts import render

# Create your views here.
def resume_view(request):
    return render(request, 'ramki.html')

