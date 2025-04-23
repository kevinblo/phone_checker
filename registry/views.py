from django.shortcuts import render
from .forms import LookupForm
from .models import PhoneCode
from rest_framework.decorators import api_view
from rest_framework.response import Response


def lookup_view(request):
    result = None
    form = LookupForm(request.GET or None)
    if form.is_valid():
        msisdn = form.cleaned_data['msisdn']
        number = int(msisdn)
        code = str(number)[1:4]
        digits = str(number)[4:]
        result = PhoneCode.objects.filter(code=code, start__lte=digits, end__gte=digits).first()
    return render(request, 'lookup.html', {'form': form, 'result': result})


@api_view(['GET'])
def lookup_number(request):
    msisdn = request.GET.get('msisdn')
    try:
        number = int(msisdn)
        code = str(number)[1:4]
        digits = str(number)[4:]
        result = PhoneCode.objects.filter(code=code, start__lte=digits, end__gte=digits).first()
        if result:
            return Response({
                "msisdn": msisdn,
                "operator": result.operator,
                "region": result.region,
                "code": code,
            })
        return Response({"error": "Number not found in registry"}, status=404)
    except:
        return Response({"error": "Invalid MSISDN format"}, status=400)
