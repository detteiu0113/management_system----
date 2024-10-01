from datetime import date
from .choices import SPECIAL_TIME_CHOICES, TIME_CHOICES

class FiscalYearMixin:
    def get_fiscal_year_boundaries(self, input_date):
        year = input_date.year

        # Determine fiscal year start and end dates
        fiscal_year_start = date(year, 3, 1)
        if input_date < fiscal_year_start:
            fiscal_year_start = date(year - 1, 3, 1)
        fiscal_year_end = date(year, 2, 28 if year % 4 != 0 or (year % 100 == 0 and year % 400 != 0) else 29)
        if input_date >= fiscal_year_start:
            fiscal_year_end = date(year + 1, 2, 28 if (year + 1) % 4 != 0 or ((year + 1) % 100 == 0 and (year + 1) % 400 != 0) else 29)

        return fiscal_year_start, fiscal_year_end
    
class SpecialTimeSaveMixin:
    def save(self, *args, **kwargs):
        if self.time in [time[0] for time in SPECIAL_TIME_CHOICES]:
            self._meta.get_field('time').choices = TIME_CHOICES + SPECIAL_TIME_CHOICES
        super().save(*args, **kwargs)
