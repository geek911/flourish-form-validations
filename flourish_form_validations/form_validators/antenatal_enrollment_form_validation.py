from django import forms
from django.apps import apps as django_apps
from django.core.exceptions import ValidationError
from edc_constants.constants import YES, POS, NEG, IND, NO, DWTA
from edc_form_validators import FormValidator
from flourish_caregiver.helper_classes import EnrollmentHelper

from .crf_form_validator import FormValidatorMixin


class AntenatalEnrollmentFormValidator(FormValidatorMixin,
                                       FormValidator):

    antenatal_enrollment_model = 'flourish_caregiver.antenatalenrollment'

    child_consent_model = 'flourish_caregiver.caregiverchildconsent'

    @property
    def antenatal_enrollment_cls(self):
        return django_apps.get_model(self.antenatal_enrollment_model)

    @property
    def child_consent_cls(self):
        return django_apps.get_model(self.child_consent_model)

    def clean(self):

        super().clean()

        self.subject_identifier = self.cleaned_data.get('subject_identifier')

        self.required_if(
            YES,
            field='knows_lmp',
            field_required='last_period_date'
        )

        self.required_if(
            YES,
            field='rapid_test_done',
            field_required='rapid_test_date'
        )

        self.required_if(
            YES,
            field='rapid_test_done',
            field_required='rapid_test_result'
        )

        self.validate_against_consent_datetime(
            self.cleaned_data.get('report_datetime'),)

        self.validate_current_hiv_status()
        # self.validate_week32_result()

        enrollment_helper = EnrollmentHelper(
            instance_antenatal=self.antenatal_enrollment_cls(
                **self.cleaned_data),
            exception_cls=forms.ValidationError)

        try:
            enrollment_helper.enrollment_hiv_status
        except ValidationError:
            raise forms.ValidationError(
                'Unable to determine maternal hiv status at enrollment.')

        enrollment_helper.raise_validation_error_for_rapidtest()

    def validate_current_hiv_status(self):
        if (self.cleaned_data.get('week32_test') == NO and
                self.cleaned_data.get('current_hiv_status') in [POS, NEG, IND]):
            message = {'current_hiv_status':
                       'Participant has never tested for HIV. Current HIV '
                       'status is unknown.'}
            self._errors.update(message)
            raise ValidationError(message)
        elif (self.cleaned_data.get('week32_test') == YES and
              self.cleaned_data.get('current_hiv_status') not in
              [POS, NEG, IND, DWTA]):
            message = {'current_hiv_status':
                       'Participant has previously tested for HIV. Current '
                       'HIV status cannot be unknown or never tested.'}
            self._errors.update(message)
            raise ValidationError(message)
