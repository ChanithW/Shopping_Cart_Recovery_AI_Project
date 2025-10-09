# Email Configuration Setup

This document explains how to configure email sending functionality for the E-Commerce platform.

## Email Configuration Options

The system now supports actual email sending using Flask-Mail with SMTP. You can configure it using environment variables.

### Method 1: Gmail Configuration (Recommended)

1. **Create a Gmail App Password:**
   - Go to your Google Account settings
   - Enable 2-Factor Authentication if not already enabled
   - Go to Security > App passwords
   - Generate an app password for "Mail"
   - Copy the 16-character password

2. **Set Environment Variables:**
   Create a `.env` file in the project root or set these environment variables:

   ```bash
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USE_SSL=False
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-16-char-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   ```

### Method 2: Outlook/Hotmail Configuration

```bash
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=your-email@outlook.com
```

### Method 3: Custom SMTP Server

```bash
MAIL_SERVER=your-smtp-server.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-username
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=noreply@yourstore.com
```

## Testing Email Configuration

1. Restart your Flask application after setting environment variables
2. Go to Admin > Customers
3. Click the email icon next to any customer
4. Send a test email

## Current Status

- ✅ Email interface is fully functional
- ✅ Form validation works
- ✅ HTML email templates included
- ✅ Fallback to simulation mode if not configured
- ✅ Comprehensive error handling and logging

## Troubleshooting

### Common Issues:

1. **"Email simulated (not configured)"**: Environment variables not set
2. **Authentication failed**: Wrong username/password or need app password
3. **Connection timeout**: Check MAIL_SERVER and MAIL_PORT settings
4. **SSL/TLS errors**: Verify MAIL_USE_TLS and MAIL_USE_SSL settings

### Security Notes:

- Never commit email credentials to version control
- Use app passwords instead of regular passwords when available
- Consider using environment-specific configuration files
- For production, consider using dedicated email services like SendGrid, AWS SES, or Mailgun

## Example .env File

```bash
# Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_db_password
MYSQL_DB=ecommerce

# Email Configuration (Gmail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=yourstore@gmail.com
MAIL_PASSWORD=abcd-efgh-ijkl-mnop
MAIL_DEFAULT_SENDER=yourstore@gmail.com

# Application Configuration
SECRET_KEY=your-secret-key-here
```

## Email Template Features

The system sends professionally formatted HTML emails with:
- Store branding header
- Properly formatted message content
- Professional footer
- Responsive design
- Plain text fallback

Once configured, customers will receive beautifully formatted emails directly from your store's email address!