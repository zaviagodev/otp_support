## Otp Support

allows users to use otp specific APIs from various providers like sms2pro, msg91.

## Pre-requisites

- **OTP Settings** doctype should be created and configured with the required fields.

# OTP Settings API Documentation

The `OTPSettings` class provides methods to send and verify One-Time Passwords (OTPs). Below is the documentation for the available methods.

## Methods

### `send_otp`

Send an OTP to a user.

#### Parameters

- `phone` (str): The phone number to send the OTP to.
- `country_code` (str): The country code of the phone number.
- `otp_secret` (str, optional): The user's secret key for OTP. If not provided, a new secret key will be generated.

#### Returns

- `dict`: A dictionary containing the reference ID (`ref`) and the OTP secret (`otp_secret`).

#### Example

```python
otp_settings = frappe.get_doc("OTP Settings")
response = otp_settings.send_otp(phone="1234567890", country_code="1")
print(response)
```

### `verify_otp`

Verify an OTP sent to a user.

#### Parameters

- `phone` (str): The phone number to verify the OTP for.
- `country_code` (str): The country code of the phone number.
- `otp` (str): The OTP to verify.

#### Returns

- `bool`: `True` if the OTP is valid, `False` otherwise.

#### Example

```python
otp_settings = frappe.get_doc("OTP Settings")
response = otp_settings.verify_otp(phone="1234567890", country_code="1", otp="123456")
print(response)
```

#### License

mit
