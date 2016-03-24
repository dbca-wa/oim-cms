"""
sqlalchemy events
"""

import datetime

from sqlalchemy import event
from sqlalchemy.orm import Session


def fix_datetime_fields(session):
    """
    Transform date strings into proper datetime objects before committing

    This function is called just before sqlalchemy's session commits
    changes to djangopycsw's database. Since `djangopycsw.models` declares
    that the datetime fields should use a `models.DatetimeField` but pycsw
    is expecting to treat these as strings, we must catch the session before
    data is committed to the database and alter the types of the fields.
    """

    new_records = session.new
    for record in new_records:
        record.date = datetime.datetime.strptime(record.date, "%Y-%m-%d")
        record.insert_date = datetime.datetime.strptime(
            record.insert_date, "%Y-%m-%dT%H:%M:%SZ")
        record.temporal_extent_begin = datetime.datetime.strptime(
            record.temporal_extent_begin, "%Y-%m-%dT%H:%M:%SZ")
        record.temporal_extent_end = datetime.datetime.strptime(
            record.temporal_extent_end, "%Y-%m-%dT%H:%M:%SZ")


event.listen(Session, "before_commit", fix_datetime_fields)
