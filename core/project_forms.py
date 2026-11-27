from django import forms

from .models import KENYAN_COUNTIES, Project


class ProjectForm(forms.ModelForm):
    county = forms.ChoiceField(
        choices=[('', 'Select a county')] + [
            (county, county) for county in KENYAN_COUNTIES
        ],
    )

    class Meta:
        model = Project
        fields = (
            'title',
            'county',
            'location',
            'implementing_agency',
            'description',
            'status',
            'start_date',
            'expected_completion',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_completion': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        expected_completion = cleaned_data.get('expected_completion')

        if start_date and expected_completion and expected_completion < start_date:
            self.add_error(
                'expected_completion',
                'Expected completion must be on or after the start date.',
            )

        return cleaned_data
