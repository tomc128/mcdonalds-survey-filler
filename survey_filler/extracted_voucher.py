from datetime import datetime


class ExtractedVoucher:
    def __init__(self, coupon_code: str, coupon_expiry: datetime, raw_data: str | None = None):
        self.coupon_code = coupon_code
        self.coupon_expiry = coupon_expiry
        self.raw_data = raw_data

    def __str__(self):
        return f'Voucher code: {self.coupon_code}, expires on: {self.coupon_expiry}. Raw data: {self.raw_data}'
