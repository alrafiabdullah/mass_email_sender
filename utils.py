"""
Utility functions for Mass Email Sender application
"""

import re
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import polars as pl


def load_csv(file_path):
    """
    Load CSV file using polars and parse email, first_name, last_name columns

    Args:
        file_path: Path to CSV file

    Returns:
        List of dictionaries with email, first_name, last_name

    Raises:
        ValueError: If required columns are missing
    """
    try:
        # Read CSV with polars
        df = pl.read_csv(file_path)

        # Check for required columns (case-insensitive)
        columns_lower = [col.lower() for col in df.columns]

        # Map to find actual column names
        email_col = None
        first_name_col = None
        last_name_col = None

        for col in df.columns:
            col_lower = col.lower()
            if "email" in col_lower or col_lower == "e-mail":
                email_col = col
            elif (
                "first" in col_lower and "name" in col_lower or col_lower == "firstname"
            ):
                first_name_col = col
            elif "last" in col_lower and "name" in col_lower or col_lower == "lastname":
                last_name_col = col

        # Check if all required columns found
        missing = []
        if not email_col:
            missing.append("email")
        if not first_name_col:
            missing.append("first_name")
        if not last_name_col:
            missing.append("last_name")

        if missing:
            raise ValueError(
                f"Missing required columns: {', '.join(missing)}\n"
                f"Available columns: {', '.join(df.columns)}"
            )

        # Convert to list of dictionaries
        recipients = []
        for row in df.iter_rows(named=True):
            email = str(row[email_col]).strip()
            first_name = str(row[first_name_col]).strip()
            last_name = str(row[last_name_col]).strip()

            # Validate email format
            if email and is_valid_email(email):
                recipients.append(
                    {"email": email, "first_name": first_name, "last_name": last_name}
                )

        return recipients

    except Exception as e:
        raise Exception(f"Failed to load CSV: {str(e)}")


def is_valid_email(email):
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_email_settings(settings):
    """
    Validate email settings

    Returns:
        tuple: (is_valid, error_message)
    """
    provider = settings.get("provider", "smtp")

    if provider == "ses":
        # Validate AWS SES settings
        if not settings.get("aws_access_key"):
            return False, "AWS Access Key ID is required"

        if not settings.get("aws_secret_key"):
            return False, "AWS Secret Access Key is required"

        if not settings.get("aws_region"):
            return False, "AWS Region is required"

        if not settings.get("sender_email"):
            return False, "Sender email is required"

        if not is_valid_email(settings.get("sender_email")):
            return False, "Invalid sender email format"
    else:
        # Validate SMTP settings
        if not settings.get("smtp_server"):
            return False, "SMTP server is required"

        if not settings.get("smtp_port"):
            return False, "SMTP port is required"

        if not settings.get("sender_email"):
            return False, "Sender email is required"

        if not is_valid_email(settings.get("sender_email")):
            return False, "Invalid sender email format"

        if not settings.get("sender_password"):
            return False, "Sender password is required"

    return True, None


def format_email_body(template, recipient):
    """
    Replace template variables with recipient data

    Args:
        template: Email body template with {variables}
        recipient: Dictionary with email, first_name, last_name

    Returns:
        Formatted email body with greeting prepended
    """
    # Add greeting at the beginning
    greeting = f"Dear {recipient['first_name']} {recipient['last_name']},\n\n"

    # Combine greeting with template body
    body = greeting + template

    # Replace any remaining template variables
    body = body.replace("{email}", recipient["email"])
    body = body.replace("{first_name}", recipient["first_name"])
    body = body.replace("{last_name}", recipient["last_name"])
    return body


def send_emails_smtp(
    recipients, subject, body_template, settings, progress_callback=None
):
    """
    Send emails via SMTP
    """
    # Connect to SMTP server
    try:
        if settings["use_tls"]:
            server = smtplib.SMTP(settings["smtp_server"], settings["smtp_port"])
            server.starttls()
        else:
            server = smtplib.SMTP(settings["smtp_server"], settings["smtp_port"])

        server.login(settings["sender_email"], settings["sender_password"])

    except Exception as e:
        raise Exception(f"Failed to connect to SMTP server: {str(e)}")

    # Send emails
    total = len(recipients)
    failed = []

    try:
        for i, recipient in enumerate(recipients):
            try:
                # Create message
                msg = MIMEMultipart()
                msg["From"] = settings["sender_email"]
                msg["To"] = recipient["email"]
                msg["Subject"] = subject

                # Format body with recipient data
                body = format_email_body(body_template, recipient)
                msg.attach(MIMEText(body, "plain"))

                # Send email
                server.send_message(msg)

                # Update progress
                if progress_callback:
                    progress_callback.emit(
                        i + 1, total, f"Sent to {recipient['email']} ({i+1}/{total})"
                    )

                # Small delay to avoid overwhelming server
                time.sleep(0.5)

            except Exception as e:
                failed.append(f"{recipient['email']}: {str(e)}")
                if progress_callback:
                    progress_callback.emit(
                        i + 1, total, f"Failed: {recipient['email']}"
                    )

    finally:
        server.quit()

    # Report any failures
    if failed:
        raise Exception(
            f"Failed to send to {len(failed)} recipients:\n"
            + "\n".join(failed[:5])
            + (f"\n... and {len(failed) - 5} more" if len(failed) > 5 else "")
        )


def send_emails_ses(
    recipients, subject, body_template, settings, progress_callback=None
):
    """
    Send emails via AWS SES
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        raise Exception(
            "boto3 is required for AWS SES. Install it with: pip install boto3"
        )

    # Create SES client
    try:
        ses_client = boto3.client(
            "ses",
            region_name=settings["aws_region"],
            aws_access_key_id=settings["aws_access_key"],
            aws_secret_access_key=settings["aws_secret_key"],
        )
    except Exception as e:
        raise Exception(f"Failed to create AWS SES client: {str(e)}")

    # Send emails
    total = len(recipients)
    failed = []

    for i, recipient in enumerate(recipients):
        try:
            # Format body with recipient data
            body = format_email_body(body_template, recipient)

            # Send email via SES
            response = ses_client.send_email(
                Source=settings["sender_email"],
                Destination={"ToAddresses": [recipient["email"]]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
                },
            )

            # Update progress
            if progress_callback:
                progress_callback.emit(
                    i + 1, total, f"Sent to {recipient['email']} ({i+1}/{total})"
                )

            # Small delay to respect SES rate limits
            time.sleep(0.1)

        except ClientError as e:
            error_msg = e.response["Error"]["Message"]
            failed.append(f"{recipient['email']}: {error_msg}")
            if progress_callback:
                progress_callback.emit(i + 1, total, f"Failed: {recipient['email']}")
        except Exception as e:
            failed.append(f"{recipient['email']}: {str(e)}")
            if progress_callback:
                progress_callback.emit(i + 1, total, f"Failed: {recipient['email']}")

    # Report any failures
    if failed:
        raise Exception(
            f"Failed to send to {len(failed)} recipients:\n"
            + "\n".join(failed[:5])
            + (f"\n... and {len(failed) - 5} more" if len(failed) > 5 else "")
        )


def send_emails(recipients, subject, body_template, settings, progress_callback=None):
    """
    Send emails to all recipients using the configured provider

    Args:
        recipients: List of recipient dictionaries
        subject: Email subject
        body_template: Email body template with variables
        settings: Settings dictionary (SMTP or AWS SES)
        progress_callback: Optional callback function for progress updates
    """
    provider = settings.get("provider", "smtp")

    if provider == "ses":
        send_emails_ses(recipients, subject, body_template, settings, progress_callback)
    else:
        send_emails_smtp(
            recipients, subject, body_template, settings, progress_callback
        )
