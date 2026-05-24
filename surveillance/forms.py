from django import forms
from .models import CaseReport, AlertThreshold, District, Disease
from django.utils import timezone


class CaseReportForm(forms.ModelForm):
    class Meta:
        model = CaseReport
        fields = [
            'disease', 'district', 'ward', 'case_count',
            'onset_date', 'report_date', 'status', 'severity',
            'symptoms', 'lab_confirmed', 'hospitalized', 'deaths', 'notes'
        ]
        widgets = {
            'onset_date': forms.DateInput(attrs={'type': 'date'}),
            'report_date': forms.DateInput(attrs={'type': 'date'}),
            'symptoms': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        # checkboxes
        for f in ['lab_confirmed', 'hospitalized']:
            self.fields[f].widget.attrs['class'] = 'form-check-input'
        self.fields['report_date'].initial = timezone.now().date()


class AlertThresholdForm(forms.ModelForm):
    class Meta:
        model = AlertThreshold
        fields = ['disease', 'district', 'cases_per_week', 'is_active']
        widgets = {
            'cases_per_week': forms.NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['is_active'].widget.attrs['class'] = 'form-check-input'
        self.fields['district'].required = False
        self.fields['district'].help_text = 'Leave blank to apply nationwide'


class CaseFilterForm(forms.Form):
    disease = forms.ModelChoiceField(
        queryset=Disease.objects.all(), required=False,
        empty_label='All diseases',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    district = forms.ModelChoiceField(
        queryset=District.objects.select_related('province').all(), required=False,
        empty_label='All districts',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All statuses')] + CaseReport.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
