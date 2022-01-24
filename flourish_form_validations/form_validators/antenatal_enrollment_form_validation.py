from dateutil.relativedelta import relativedelta
from django import forms
from django.core.exceptions import ValidationError
from edc_constants.constants import YES, POS, NEG, IND, NO, DWTA
from edc_form_validators import FormValidator
from flourish_caregiver.helper_classes import EnrollmentHelper

from .crf_form_validator import CRFFormValidator
from .form_validator_mixin import FlourishFormValidatorMixin


class AntenatalEnrollmentFormValidator(CRFFormValidator,
                                       FlourishFormValidatorMixin,
                                       FormValidator):

    def clean(self):

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

        self.validate_last_period_date(cleaned_data=self.cleaned_data)

        id = self.instance.id if self.instance else None

        self.validate_against_consent_datetime(
            self.cleaned_data.get('report_datetime'),
            id=id)

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

    def validate_last_period_date(self, cleaned_data=None):
        last_period_date = cleaned_data.get('last_period_date')
        report_datetime = cleaned_data.get('report_datetime')

        if last_period_date and (
                last_period_date < (
                report_datetime.date() - relativedelta(weeks=16))):
            message = {'last_period_date':
                           'LMP cannot be less than 16 weeks of report datetime. '
                           f'Got LMP as {last_period_date} and report datetime as '
                           f'{report_datetime}'}
            self._errors.update(message)
            raise ValidationError(message)

        elif last_period_date and (
                last_period_date > (
                    report_datetime.date() - relativedelta(weeks=30))):
            message = {'last_period_date':
                           'LMP cannot be more than 30 weeks of report datetime. '
                           f'Got LMP as {last_period_date} and report datetime as '
                           f'{report_datetime}'}
            self._errors.update(message)
            raise ValidationError(message)
