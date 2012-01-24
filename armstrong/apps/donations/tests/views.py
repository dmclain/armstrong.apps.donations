from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import Client
import os
from unittest import expectedFailure

from ._utils import TestCase

from .. import forms
from .. import models


class BaseDonationFormViewTestCase(TestCase):
    view_name = "donations_form"

    @property
    def url(self):
        # TODO: move this into armstrong.dev
        return reverse(self.view_name)

    def setUp(self):
        self.client = Client()
        # TODO: make this based off of class name and move into armstrong.dev
        settings.TEMPLATE_DIRS = (
            os.path.join(os.path.dirname(__file__), "_templates"),
        )
        self.client

    def assert_in_context(self, response, name):
        # TODO: move this into armstrong.dev
        self.assertTrue(name in response.context,
                msg="%s was not in the context")

    def assert_type_in_context(self, response, name, expected_type):
        self.assert_in_context(response, name)
        self.assertEqual(response.context[name].__class__, expected_type,
                msg="%s in the context, but does not have a class of %s" % (
                        name, expected_type.__name__))

    def assert_value_in_context(self, response, name, expected_value):
        self.assert_in_context(response, name)
        self.assertEqual(response.context[name], expected_value,
                msg="%s in the context, but not equal to '%s'" % (
                        name, expected_value))

    def get_response(self):
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code, msg="sanity check")
        return response


# TODO: move to armstrong.dev
def get_response(func):
    from functools import wraps
    @wraps(func)
    def inner(self):
        func(self, self.get_response())
    return inner


class DonationFormViewGetTestCase(BaseDonationFormViewTestCase):
    @get_response
    def test_adds_form_action_url_to_context(self, response):
        self.assert_value_in_context(response, "form_action_url", "")

    @get_response
    def test_adds_donor_form_to_context(self, response):
        self.assert_type_in_context(response, "donor_form", forms.DonorForm)

    @get_response
    def test_adds_address_formset_to_context(self, response):
        self.assert_type_in_context(response, "address_formset",
                forms.DonorAddressFormset)

class DonationFormViewPostTestCase(BaseDonationFormViewTestCase):
    @property
    def random_post_data(self):
        donor_name = self.random_donor_name
        address_kwargs = self.random_address_kwargs
        address_formset = self.get_data_as_formset(address_kwargs)
        data = {
            "name": donor_name,
        }
        data.update(address_formset)
        return data

    def test_saves_donation_on_post_with_minimal_information(self):
        donor_name = self.random_donor_name
        random_amount = self.random_amount
        data = {
            "name": donor_name,
            "amount": random_amount,
        }
        data.update(self.get_data_as_formset())

        # sanity check
        self.assertRaises(models.Donor.DoesNotExist,
                models.Donor.objects.get, name=donor_name)
        self.client.post(self.url, data)
        donor = models.Donor.objects.get(name=donor_name)
        self.assertEqual(donor.name, donor_name)

    def test_saves_address_if_present(self):
        donor_name = self.random_donor_name
        address_kwargs = self.random_address_kwargs
        address_formset = self.get_data_as_formset(address_kwargs)
        data = {
            "name": donor_name,
        }
        data.update(address_formset)

        self.client.post(self.url, data)
        address = models.DonorAddress.objects.get(**address_kwargs)
        donor = models.Donor.objects.get(name=donor_name)
        self.assertEqual(address, donor.address)
        self.assertEqual(None, donor.mailing_address)

    def test_saves_mailing_address_if_present(self):
        donor_name = self.random_donor_name
        address_kwargs = self.random_address_kwargs
        mailing_address_kwargs = self.random_address_kwargs
        address_formset = self.get_data_as_formset([
            address_kwargs,
            mailing_address_kwargs,
        ])
        data = {
            "name": donor_name,
        }
        data.update(address_formset)

        self.assertEqual(0, len(models.DonorAddress.objects.all()),
            msg="sanity check")
        self.client.post(self.url, data)
        self.assertEqual(2, len(models.DonorAddress.objects.all()))
        address = models.DonorAddress.objects.get(**address_kwargs)
        mailing_address = models.DonorAddress.objects.get(
                **mailing_address_kwargs)
        self.assertNotEqual(address, mailing_address)

        donor = models.Donor.objects.get(name=donor_name)
        self.assertEqual(address, donor.address)
        self.assertEqual(mailing_address, donor.mailing_address)


    def test_saves_mailing_address_if_same_as_billing_is_checked(self):
        data = self.random_post_data
        data["mailing_same_as_billing"] = u"1"
        self.client.post(self.url, data)
        donor = models.Donor.objects.get(name=data["name"])
        self.assertEqual(donor.address, donor.mailing_address)

    @expectedFailure
    def test_saves_donation_information(self):
        self.fail()

    @expectedFailure
    def test_displays_errors_on_donor_validation_error(self):
        self.fail()

    @expectedFailure
    def test_displays_errors_on_address_validation_error(self):
        self.fail()

    @expectedFailure
    def test_redirects_to_success_url_on_success(self):
        self.fail()

    @expectedFailure
    def test_displays_errors_when_payment_method_authorization_fails(self):
        self.fail()
