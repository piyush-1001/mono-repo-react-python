"""Regex pattern constants."""

import re

EMAIL_PATTERN = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
PHONE_PATTERN = r"^[6-9]\d{9}$"
SKU_PATTERN = r"^[A-Z]{2,4}-\d{4,6}$"
CATEGORY_CODE_PATTERN = r"^[A-Z0-9][A-Z0-9-]{1,19}$"
PASSWORD_PATTERN = r"^(?=.*[A-Za-z])(?=.*\d).{8,64}$"
SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
SEMVER_PATTERN = r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$"

email_re = re.compile(EMAIL_PATTERN)
phone_re = re.compile(PHONE_PATTERN)
sku_re = re.compile(SKU_PATTERN)
category_code_re = re.compile(CATEGORY_CODE_PATTERN)
password_re = re.compile(PASSWORD_PATTERN)
