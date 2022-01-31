from re import sub
from turtle import pd
from django.apps import apps as django_apps
from django.core.exceptions import ValidationError
from edc_form_validators.form_validator import FormValidator
from .crf_form_validator import CRFFormValidator
from flourish_caregiver.models import UltraSound

class ObstericalHistoryFormValidator(CRFFormValidator, FormValidator):
    ultrasound_model = 'flourish_caregiver.ultrasound'

    @property
    def ultrasound_model_cls(self):
        return django_apps.get_model(self.ultrasound_model)

    
    def clean(self):
        self.subject_identifier = self.cleaned_data.get(
            'maternal_visit').subject_identifier
        
        self.validate_ultra_sound_exist(cleaned_data=self.cleaned_data)
        self.validate_prev_pregnancies(cleaned_data=self.cleaned_data)
        self.validate_children_deliv(cleaned_data=self.cleaned_data)

        return super().clean()

    def validate_ultra_sound_exist(self, cleaned_data = None):


        maternal_visit = cleaned_data.get('maternal_visit')
        subject_identifier = maternal_visit.subject_identifier
        visit_code = maternal_visit.visit_code
        ultrasound_crf_exist =  self.ultrasound_model_cls.objects.filter(
                maternal_visit__subject_identifier=subject_identifier, 
            maternal_visit__visit_code=visit_code).exists()

        if not ultrasound_crf_exist:
            raise ValidationError('Please fill the ultrasound CRF first')

        
        

    def validate_children_deliv(self, cleaned_data=None):
        if None not in [cleaned_data.get('children_deliv_before_37wks'),
                        cleaned_data.get('children_deliv_aftr_37wks'),
                        cleaned_data.get('lost_before_24wks'),
                        cleaned_data.get('lost_after_24wks')]:

            sum_deliv_37_wks = \
                (cleaned_data.get('children_deliv_before_37wks') +
                 cleaned_data.get('children_deliv_aftr_37wks'))
            sum_lost_24_wks = (cleaned_data.get('lost_before_24wks') +
                               cleaned_data.get('lost_after_24wks'))
            total_children = cleaned_data.get('prev_pregnancies') - sum_lost_24_wks
            if (cleaned_data.get('prev_pregnancies')
                    and (sum_deliv_37_wks not in [total_children, total_children - 1])):
                raise ValidationError('The sum of Q9 and Q10 must be equal to (Q3 - (Q5 + Q6))'
                                      ' or (Q3-1 - (Q5 + Q6)) if currently pregnant. Please '
                                      'correct.')

    def validate_prev_pregnancies(self, cleaned_data=None):
        # These fields can never be None because there are required on the form
        prev_pregnancies = cleaned_data.get('prev_pregnancies')
        pregs_24wks_or_more = cleaned_data.get('pregs_24wks_or_more')
        lost_before_24wks = cleaned_data.get('lost_before_24wks')

        if prev_pregnancies > 1:
            if pregs_24wks_or_more < lost_before_24wks:
                message = {'pregs_24wks_or_more':
                           'Sum of pregnancies more than 24 weeks should NOT be'
                           ' less than those lost'}
                self._errors.update(message)
                raise ValidationError(message)
