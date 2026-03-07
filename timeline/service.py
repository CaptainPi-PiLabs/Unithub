from timeline.builders import get_orbat_timeline, get_personal_timeline


class TimelineService:

    @staticmethod
    def get_orbat_timeline(user=None, section=None, start_date=None, end_date=None):
        return get_orbat_timeline(user, section, start_date, end_date)

    @staticmethod
    def get_personal_timeline(user=None, section=None, start_date=None, end_date=None):
        return get_personal_timeline(user, start_date, end_date)