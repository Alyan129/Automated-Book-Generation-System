"""
Notification Service for Email and MS Teams.
Sends notifications on key workflow events.
"""
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from src.core.config import config
from src.utils.logger import logger


class NotificationService:
    """Service for sending notifications"""
    
    def __init__(self):
        """Initialize notification service"""
        self.email_configured = bool(config.SMTP_USERNAME and config.SMTP_PASSWORD)
        self.teams_configured = bool(config.TEAMS_WEBHOOK_URL)
        
        if self.email_configured:
            logger.info("Email notifications enabled")
        if self.teams_configured:
            logger.info("MS Teams notifications enabled")
    
    def send_email(self, subject: str, body: str, to_email: Optional[str] = None) -> bool:
        """
        Send email notification.
        
        Args:
            subject: Email subject
            body: Email body (can be HTML)
            to_email: Recipient email (defaults to config.NOTIFICATION_EMAIL)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.email_configured:
            logger.warning("Email not configured, skipping email notification")
            return False
        
        try:
            recipient = to_email or config.NOTIFICATION_EMAIL
            if not recipient:
                logger.warning("No recipient email configured")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = config.SMTP_USERNAME
            msg['To'] = recipient
            
            # Attach HTML body
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
                server.starttls()
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def send_teams_message(self, title: str, text: str, color: str = "0078D4") -> bool:
        """
        Send MS Teams notification via webhook.
        
        Args:
            title: Message title
            text: Message text
            color: Theme color (hex without #)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.teams_configured:
            logger.warning("MS Teams not configured, skipping Teams notification")
            return False
        
        try:
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": title,
                "themeColor": color,
                "title": title,
                "text": text
            }
            
            response = requests.post(
                config.TEAMS_WEBHOOK_URL,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info(f"Teams message sent: {title}")
                return True
            else:
                logger.error(f"Teams webhook failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Teams message: {e}")
            return False
    
    def notify_outline_ready(self, book_title: str, book_id: str):
        """Notify that outline is ready for review"""
        subject = f"📝 Outline Ready: {book_title}"
        body = f"""
        <html>
            <body>
                <h2>Outline Generated</h2>
                <p>The outline for "<strong>{book_title}</strong>" has been generated and is ready for review.</p>
                <p><strong>Book ID:</strong> {book_id}</p>
                <p>Please review the outline and provide feedback if needed.</p>
            </body>
        </html>
        """
        
        self.send_email(subject, body)
        self.send_teams_message(
            "Outline Ready for Review",
            f"The outline for '{book_title}' has been generated.",
            "0078D4"
        )
    
    def notify_waiting_for_chapter_notes(self, book_title: str, chapter_number: int):
        """Notify that system is waiting for chapter notes"""
        subject = f"⏸️ Waiting for Notes: {book_title} - Chapter {chapter_number}"
        body = f"""
        <html>
            <body>
                <h2>Chapter Awaiting Review</h2>
                <p>Chapter {chapter_number} of "<strong>{book_title}</strong>" is ready for review.</p>
                <p>The system is waiting for your feedback before proceeding to the next chapter.</p>
            </body>
        </html>
        """
        
        self.send_email(subject, body)
        self.send_teams_message(
            "Chapter Awaiting Review",
            f"Chapter {chapter_number} of '{book_title}' needs review.",
            "FFA500"
        )
    
    def notify_final_draft_ready(self, book_title: str, book_id: str, output_path: str):
        """Notify that final draft is compiled"""
        subject = f"✅ Book Complete: {book_title}"
        body = f"""
        <html>
            <body>
                <h2>Book Generation Complete!</h2>
                <p>The final draft of "<strong>{book_title}</strong>" has been compiled successfully.</p>
                <p><strong>Book ID:</strong> {book_id}</p>
                <p><strong>Output Location:</strong> {output_path}</p>
                <p>The book is ready for final review and distribution.</p>
            </body>
        </html>
        """
        
        self.send_email(subject, body)
        self.send_teams_message(
            "Book Generation Complete",
            f"'{book_title}' has been compiled successfully!",
            "28A745"
        )
    
    def notify_error(self, book_title: str, error_message: str):
        """Notify about an error"""
        subject = f"❌ Error: {book_title}"
        body = f"""
        <html>
            <body>
                <h2>Generation Error</h2>
                <p>An error occurred during generation of "<strong>{book_title}</strong>".</p>
                <p><strong>Error:</strong> {error_message}</p>
                <p>Please check the logs for more details.</p>
            </body>
        </html>
        """
        
        self.send_email(subject, body)
        self.send_teams_message(
            "Generation Error",
            f"Error in '{book_title}': {error_message}",
            "DC3545"
        )
    
    def notify_paused(self, book_title: str, reason: str):
        """Notify that generation is paused"""
        subject = f"⏸️ Paused: {book_title}"
        body = f"""
        <html>
            <body>
                <h2>Generation Paused</h2>
                <p>Generation of "<strong>{book_title}</strong>" has been paused.</p>
                <p><strong>Reason:</strong> {reason}</p>
            </body>
        </html>
        """
        
        self.send_email(subject, body)
        self.send_teams_message(
            "Generation Paused",
            f"'{book_title}' paused: {reason}",
            "FFC107"
        )
