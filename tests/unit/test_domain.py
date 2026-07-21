from uuid import uuid4

import pytest

from backend.domain.entities import Application
from backend.domain.entities.application import ApplicationStatus
from backend.domain.values.address import Address
from backend.core.exceptions import ApplicationAlreadySubmittedError, InvalidStateTransitionError


class TestApplicationEntity:
    def test_create_application(self):
        app = Application(applicant_id=uuid4())
        assert app.status == ApplicationStatus.DRAFT
        assert app.id is not None

    def test_submit_changes_status(self):
        app = Application(applicant_id=uuid4())
        app.submit()
        assert app.status == ApplicationStatus.SUBMITTED

    def test_cannot_submit_from_wrong_status(self):
        app = Application(applicant_id=uuid4())
        app.submit()
        with pytest.raises(ApplicationAlreadySubmittedError):
            app.submit()

    def test_cannot_approve_from_draft(self):
        app = Application(applicant_id=uuid4())
        with pytest.raises(InvalidStateTransitionError):
            app.approve()

    def test_full_lifecycle(self):
        app = Application(applicant_id=uuid4())
        app.submit()
        app.start_processing("wf_123")
        assert app.status == ApplicationStatus.PROCESSING
        assert app.workflow_id == "wf_123"
        app.approve()
        assert app.status == ApplicationStatus.APPROVED
        assert app.completed_at is not None

    def test_decline_after_processing(self):
        app = Application(applicant_id=uuid4())
        app.submit()
        app.start_processing("wf_456")
        app.decline()
        assert app.status == ApplicationStatus.DECLINED
        assert app.completed_at is not None


class TestAddress:
    def test_create_address(self):
        addr = Address(
            street="123 Main St",
            city="Dubai",
            emirate="Dubai",
            country="UAE",
            po_box="12345",
        )
        assert str(addr) is not None
        assert addr.country == "UAE"
        assert addr.po_box == "12345"
