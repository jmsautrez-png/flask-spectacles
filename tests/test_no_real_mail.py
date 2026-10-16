"""Garde-fou : la suite de tests n'envoie jamais de vrai e-mail (le .env local contient les identifiants SMTP)."""

import smtplib

import pytest


def test_flask_mail_is_suppressed_during_tests(app):
    from flask_mail import Message

    with app.app_context(), app.mail.record_messages() as outbox:
        app.mail.send(Message("test", recipients=["destinataire@example.test"], body="corps"))
    assert len(outbox) == 1


def test_direct_smtp_connections_are_refused():
    with pytest.raises(RuntimeError):
        smtplib.SMTP("localhost", 25)
    with pytest.raises(RuntimeError):
        smtplib.SMTP_SSL("localhost", 465)
