# Copyright (c) 2024, Zaviago.lts and contributors
# For license information, please see license.txt

import os
import frappe
from frappe.model.document import Document
import pyotp
from base64 import b32encode


class OTPSettings(Document):

    def send_otp(self, phone, country_code, otp_secret=None):
        """Send OTP to user."""
        '''params:
            phone: phone number
            country_code: country code
            otp_secret: user secret key for OTP
        '''
        if not otp_secret:
            otp_secret = b32encode(os.urandom(10)).decode("utf-8")
        token = int(pyotp.TOTP(otp_secret).now())

        otp_settings = self
        if otp_settings.with_country_code:
            phone = f"{country_code}{phone}"
        headers = get_headers("request", otp_settings)
        use_json = headers.get("Content-Type") == "application/json"
        args = {
            otp_settings.message_parameter: None,
            otp_settings.receiver_parameter: phone
        }

        for d in [*otp_settings.get("parameters"), *otp_settings.get("parameters_when_requesting")]:
            if not d.header:
                args[d.parameter] = d.value

        res = send_request(
            f'''{otp_settings.otp_gateway_host.rstrip(
                '/')}/{otp_settings.api_route_request.lstrip('/')}''',
            args,
            headers,
            otp_settings.use_post_when_requesting,
            use_json
        )

        if otp_settings.referencesupport_property:
            tmp_id = extract_prop(res, otp_settings.referencesupport_property)
        else:
            tmp_id = phone

        cache_otp(phone, token, tmp_id)

        return {
            "ref": tmp_id,
            "otp_secret": otp_secret
        }

    def verify_otp(self, phone, country_code, otp):
        """Verify OTP."""
        '''params:
            phone: phone number
            country_code: country code
            otp: OTP
        '''
        otp_settings = self
        if otp_settings.with_country_code:
            phone = f"{country_code}{phone}"

        cached_otp = frappe.cache().get_value(
            f"phone_verification_otp:{phone}")

        if not cached_otp:
            return frappe.throw("OTP expired or invalid. Please request a new one.")

        if cached_otp["otp"] == otp:
            return True

        headers = get_headers("verify", otp_settings)
        use_json = headers.get("Content-Type") == "application/json"
        args = {
            otp_settings.otp_parameter: otp,
        }

        if otp_settings.referencesupporting_parameter:
            args[otp_settings.referencesupporting_parameter] = cached_otp["ref"]

        for d in [*otp_settings.get("parameters"), *otp_settings.get("parameters_when_verifying")]:
            if not d.header:
                args[d.parameter] = d.value

        res = send_request(
            f'''{otp_settings.otp_gateway_host.rstrip(
                '/')}/{otp_settings.api_route_verification.lstrip('/')}''',
            args,
            get_headers("verify", otp_settings),
            otp_settings.use_post_when_verifying,
            use_json
        )

        if otp_settings.validation_property:
            is_valid = extract_prop(res, otp_settings.validation_property)
        else:
            is_valid = True

        if type(is_valid) is bool and is_valid or "success" in is_valid.lower():
            frappe.cache().delete(f"phone_verification_otp:{phone}")
            return True
        else:
            return False

def cache_otp(phone, otp=None, ref=None):
    """Cache OTP for verification."""
    frappe.cache().set_value(f"phone_verification_otp:{phone}", {
        "otp": otp,
        "ref": ref
    }, expires_in_sec=int(frappe.get_doc("OTP Settings", "OTP Settings").otp_validity_in_mins * 60))


def extract_prop(dict, prop):
    nested_props = prop.split('.')
    for nested_prop in nested_props:
        if type(dict) is list:
            dict = dict[nested_prop]
        else:
            dict = dict.get(nested_prop)
        if not dict:
            return None
    return dict


def get_headers(event=None, otp_settings=None):
    if not otp_settings:
        otp_settings = frappe.get_doc("OTP Settings", "OTP Settings")

    headers = {"Accept": "text/plain, text/html, */*"}
    if event == "request":
        header_table_field = "parameters_when_requesting"
    elif event == "verify":
        header_table_field = "parameters_when_verifying"
    else:
        header_table_field = "parameters"

    for d in [*otp_settings.get("parameters"), *otp_settings.get(header_table_field)]:
        if d.header == 1:
            headers.update({d.parameter: d.value})

    return headers


def send_request(gateway_url, params, headers=None, use_post=False, use_json=False):
    import requests

    if not headers:
        headers = get_headers()
    kwargs = {"headers": headers}

    if use_json:
        kwargs["json"] = params
    elif use_post:
        kwargs["data"] = params
    else:
        kwargs["params"] = params

    if use_post:
        response = requests.post(gateway_url, **kwargs)
    else:
        response = requests.get(gateway_url, **kwargs)
    response.raise_for_status()
    return response.json()
