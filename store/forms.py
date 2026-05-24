from django import forms
from .models import Order, Service

class CreateOrderForm(forms.ModelForm):
    service = forms.ModelChoiceField(queryset=Service.objects.all(), empty_label="Select a service", widget=forms.Select(attrs={'class': 'input', 'id':'id_service'}))
    quantity = forms.IntegerField(min_value=50,max_value=100000, widget=forms.NumberInput(attrs={'class': 'input', 'id':'id_quantity'}))
    target_link = forms.URLField(widget=forms.URLInput(attrs={'class': 'input', 'id':'id_target_link'}))
    class Meta:
        model = Order
        fields = ['service', 'quantity', 'target_link']
        exclude = ['user', 'total_price']  # user will be set in the view based on the logged-in user