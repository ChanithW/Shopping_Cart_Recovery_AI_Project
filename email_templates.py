# Email Templates for Customer Communication
# This module contains predefined email templates for common customer interactions

EMAIL_TEMPLATES = {
    'welcome': {
        'subject': 'Welcome to Our Store!',
        'message': '''Thank you for joining our store community!

We're excited to have you as a valued customer. Here's what you can expect:

✅ Quality products at competitive prices
✅ Fast and reliable shipping
✅ Excellent customer support
✅ Exclusive offers and promotions

Browse our latest collection and discover amazing deals just for you.

If you have any questions or need assistance, please don't hesitate to reach out to us.'''
    },
    
    'order_follow_up': {
        'subject': 'How was your recent purchase?',
        'message': '''We hope you're enjoying your recent purchase from our store!

Your satisfaction is our top priority, and we'd love to hear about your experience.

Could you take a moment to:
• Let us know if everything arrived as expected
• Share any feedback about the product quality
• Rate your shopping experience with us

If you encountered any issues or have concerns, please contact us immediately so we can make it right.

Thank you for choosing our store. We look forward to serving you again!'''
    },
    
    'promotion': {
        'subject': '🎉 Exclusive Offer Just for You!',
        'message': '''Great news! We have a special offer exclusively for our valued customers.

🏷️ SPECIAL DISCOUNT: 15% OFF on your next purchase
📅 Valid until: [End Date]
💳 Use code: VALUED15 at checkout

Browse our featured products:
• Latest electronics and gadgets
• Fashion and accessories
• Home and garden essentials
• And much more!

This exclusive offer is our way of saying thank you for being a loyal customer.

Shop now and save big!'''
    },
    
    'support': {
        'subject': 'We\'re Here to Help!',
        'message': '''Thank you for reaching out to us regarding your inquiry.

Our customer support team has received your message and we want to assist you as quickly as possible.

What we can help you with:
• Order status and tracking information
• Product questions and recommendations
• Returns and exchanges
• Account and billing inquiries
• Technical support

We typically respond within 24 hours during business days. For urgent matters, you can also contact us directly.

Your satisfaction is important to us, and we're committed to resolving any concerns you may have.'''
    },
    
    'birthday': {
        'subject': '🎂 Happy Birthday! Special Gift Inside',
        'message': '''Happy Birthday from all of us at the store!

🎉 We hope your special day is filled with joy, laughter, and wonderful surprises!

As a birthday gift from us to you, please enjoy:
🎁 20% OFF your next purchase
🚚 FREE shipping on any order
✨ Access to exclusive birthday deals

Your birthday discount code: BIRTHDAY20
Valid for the next 7 days - because birthdays deserve to be celebrated all week long!

Browse our latest arrivals and treat yourself to something special. You deserve it!

Wishing you a fantastic year ahead filled with happiness and amazing shopping experiences.'''
    },
    
    'restock_notification': {
        'subject': '📦 Good News! Your Requested Item is Back in Stock',
        'message': '''Great news! The item you were waiting for is now back in stock.

We know how disappointing it can be when your desired product is unavailable, so we wanted to let you know as soon as it became available again.

⚡ Limited quantities available
🛒 Order now to secure your item
🚚 Fast shipping available

Don't wait too long - popular items like this tend to sell out quickly!

You can complete your purchase by visiting our website or clicking the link below.

Thank you for your patience, and we look forward to fulfilling your order.'''
    },
    
    'feedback_request': {
        'subject': 'Your Opinion Matters - Quick Survey',
        'message': '''We value your feedback and would love to hear from you!

As one of our valued customers, your opinion helps us improve our products and services to better serve you and our community.

We'd appreciate if you could spare 2-3 minutes to share:
📝 Your overall shopping experience
⭐ Product quality and satisfaction
🚚 Delivery and packaging feedback
💬 Any suggestions for improvement

Your honest feedback helps us:
• Enhance our product selection
• Improve customer service
• Develop better shopping experiences
• Maintain high quality standards

As a thank you for your time, you'll receive a 10% discount code after completing the survey.

Thank you for helping us serve you better!'''
    },
    
    'seasonal': {
        'subject': '🍂 Seasonal Collection Now Available!',
        'message': '''The new season is here, and so is our amazing seasonal collection!

Discover the latest trends and must-have items perfect for this time of year:

🛍️ New Arrivals:
• Seasonal fashion and accessories
• Home décor and essentials
• Seasonal electronics and gadgets
• Special holiday items

🏷️ Launch Special: 25% OFF on all seasonal items
📅 Limited time offer - don't miss out!

Whether you're updating your wardrobe, redecorating your space, or looking for the perfect gift, our seasonal collection has something special for everyone.

Shop early for the best selection and enjoy exclusive launch prices.

Happy shopping!'''
    },
    
    'custom': {
        'subject': '',
        'message': 'Write your custom message here...'
    }
}

def get_template(template_name):
    """Get email template by name"""
    return EMAIL_TEMPLATES.get(template_name, EMAIL_TEMPLATES['custom'])

def get_all_templates():
    """Get all available email templates"""
    return EMAIL_TEMPLATES

def get_template_list():
    """Get list of template names and subjects for dropdown"""
    templates = []
    for key, template in EMAIL_TEMPLATES.items():
        if key == 'custom':
            templates.append({
                'key': key,
                'name': 'Custom Message',
                'subject': template['subject']
            })
        else:
            # Convert key to readable name
            name = key.replace('_', ' ').title()
            templates.append({
                'key': key,
                'name': name,
                'subject': template['subject']
            })
    return templates