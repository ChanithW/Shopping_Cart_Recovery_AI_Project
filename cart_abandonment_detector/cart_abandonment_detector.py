# -*- coding: utf-8 -*-
"""
Cart Abandonment Detection System
Main module with detection, email, and recommendation components.
"""

import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import MySQLdb
import MySQLdb.cursors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from openai import OpenAI
from flask_mail import Message
from flask import render_template_string

from . import config

# Configure logging
# Create logs directory if it doesn't exist
import os
if config.LOG_FILE:
    log_dir = os.path.dirname(config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE) if config.LOG_FILE else logging.NullHandler(),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages MySQL database connections"""
    
    @staticmethod
    def get_connection():
        """Create and return a MySQL connection"""
        return MySQLdb.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DB,
            cursorclass=MySQLdb.cursors.DictCursor
        )


class RecommendationEngine:
    """
    Generates product recommendations using TF-IDF and Cosine Similarity
    Enhanced with Groq AI for personalized descriptions
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.products_cache = []
        self.tfidf_matrix = None
        
        # Initialize Groq AI
        if config.GROQ_API_KEY:
            self.groq_client = OpenAI(
                api_key=config.GROQ_API_KEY,
                base_url=config.GROQ_BASE_URL
            )
            logger.info("Groq AI initialized successfully")
        else:
            self.groq_client = None
            logger.warning("Groq API key not found - AI features disabled")
    
    def load_products(self):
        """Load all products from database and build TF-IDF matrix"""
        try:
            conn = DatabaseConnection.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, description, price, category, image, stock
                FROM products
                WHERE stock > 0
                ORDER BY created_at DESC
            """)
            
            self.products_cache = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if not self.products_cache:
                logger.warning("No products found in database")
                return
            
            # Build TF-IDF matrix from product descriptions, names, and categories
            # Handle cases where description might be NULL or empty
            product_texts = []
            for p in self.products_cache:
                desc = p.get('description') or ''
                cat = p.get('category') or 'general'
                name = p.get('name') or ''
                # Repeat category 4x and name 3x to SIGNIFICANTLY boost their TF-IDF importance
                # This ensures category gets very high weight and reduces false positives from word coincidences
                text = f"{name} {name} {name} {cat} {cat} {cat} {cat} {desc}"
                product_texts.append(text)
            
            # Use min_df=1 to include all terms, even if they appear in only one document
            self.vectorizer = TfidfVectorizer(
                stop_words='english',
                min_df=1,
                max_df=0.9,
                ngram_range=(1, 2)  # Use both single words and bigrams
            )
            self.tfidf_matrix = self.vectorizer.fit_transform(product_texts)
            logger.info(f"Loaded {len(self.products_cache)} products for recommendations")
            
        except Exception as e:
            logger.error(f"Error loading products: {e}")
            raise
    
    def get_similar_products(self, cart_items: List[Dict], count: int = 3) -> List[Dict]:
        """
        Find similar products based on cart items using TF-IDF + Cosine Similarity
        
        Args:
            cart_items: List of items currently in cart
            count: Number of recommendations to return
            
        Returns:
            List of recommended products with similarity scores
        """
        if not self.products_cache or self.tfidf_matrix is None:
            self.load_products()
        
        if not self.products_cache:
            return []
        
        try:
            # Get cart product IDs to exclude from recommendations
            cart_product_ids = {item['product_id'] for item in cart_items}
            
            # Build query from cart items (with better text extraction)
            cart_texts = []
            for item in cart_items:
                name = item.get('name', '')
                cat = item.get('category', '')
                desc = item.get('description', '')
                # Repeat category 4x and name 3x to match product weighting
                # This ensures better category-based matching and fewer false positives
                cart_texts.append(f"{name} {name} {name} {cat} {cat} {cat} {cat} {desc}")
            
            cart_text = " ".join(cart_texts)
            
            # Transform cart text to TF-IDF vector
            cart_vector = self.vectorizer.transform([cart_text])
            
            # Calculate cosine similarity
            similarities = cosine_similarity(cart_vector, self.tfidf_matrix)[0]
            
            # Extract categories from cart items for category-based filtering
            cart_categories = set()
            for item in cart_items:
                cat = item.get('category', '').strip()
                if cat:
                    cart_categories.add(cat.lower())
            
            # Get top similar products (excluding cart items)
            # Prioritize products from same categories to reduce false positives
            similar_indices = []
            same_category_matches = []
            cross_category_matches = []
            
            for idx in np.argsort(similarities)[::-1]:
                product = self.products_cache[idx]
                if product['id'] not in cart_product_ids:
                    product_cat = (product.get('category') or '').strip().lower()
                    similarity_score = similarities[idx]
                    
                    # Boost score for same-category products (reduce false positives)
                    if product_cat in cart_categories:
                        # Same category gets priority
                        same_category_matches.append((idx, similarity_score * 1.3))  # 30% boost
                    else:
                        # Cross-category matches (like "Air" Fryer for "Air" Jordan)
                        # Only include if similarity is strong enough
                        if similarity_score > 0.25:  # Higher threshold for cross-category
                            cross_category_matches.append((idx, similarity_score))
            
            # Combine: prioritize same-category, then high-scoring cross-category
            similar_indices = sorted(same_category_matches, key=lambda x: x[1], reverse=True)[:count]
            
            # Fill remaining slots with cross-category if needed
            if len(similar_indices) < count:
                remaining = count - len(similar_indices)
                cross_category_sorted = sorted(cross_category_matches, key=lambda x: x[1], reverse=True)
                similar_indices.extend(cross_category_sorted[:remaining])
            
            # If we don't have enough recommendations, add top-rated/recent products
            if len(similar_indices) < count:
                logger.warning(f"Only found {len(similar_indices)} similar products, adding top products")
                for idx, product in enumerate(self.products_cache):
                    if product['id'] not in cart_product_ids:
                        # Check if not already added
                        if not any(i == idx for i, _ in similar_indices):
                            similar_indices.append((idx, 0.5))  # Give neutral similarity
                            if len(similar_indices) >= count:
                                break
            
            # Build recommendation list
            recommendations = []
            for idx, similarity_score in similar_indices:
                product = self.products_cache[idx].copy()
                product['similarity_score'] = float(similarity_score)
                product['url'] = f"{config.BASE_URL}/product/{product['id']}"
                recommendations.append(product)
            
            logger.info(f"Generated {len(recommendations)} recommendations (TF-IDF similarity)")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            # Fallback: return first N products not in cart
            recommendations = []
            for product in self.products_cache:
                if product['id'] not in {item['product_id'] for item in cart_items}:
                    product_copy = product.copy()
                    product_copy['similarity_score'] = 0.0
                    product_copy['url'] = f"{config.BASE_URL}/product/{product['id']}"
                    recommendations.append(product_copy)
                    if len(recommendations) >= count:
                        break
            logger.info(f"Using fallback recommendations: {len(recommendations)} products")
            return recommendations
    
    async def enhance_with_groq(self, recommendations: List[Dict], user_name: str, cart_items: List[Dict], cart_total: float, discount_percent: float) -> str:
        """
        Use Groq AI to create engaging, personalized email content
        
        Args:
            recommendations: List of recommended products
            user_name: Customer's name
            cart_items: Items currently in cart with quantities
            cart_total: Total cart value
            discount_percent: Discount percentage being offered
            
        Returns:
            AI-generated personalized email content
        """
        if not self.groq_client:
            return self._fallback_recommendation_text(recommendations, cart_items)
        
        try:
            # Build cart items summary
            cart_summary = "\n".join([
                f"- {item['name']} (Qty: {item.get('quantity', 1)}) - ${item.get('total', item.get('price', 0)):.2f}"
                for item in cart_items
            ])
            
            # Build recommendations summary
            recs_summary = "\n".join([
                f"- {p['name']}: {p.get('description', 'Great product')[:80]}... (${p['price']:.2f})"
                for p in recommendations
            ]) if recommendations else "No specific recommendations available"
            
            prompt = f"""
            You are writing a friendly, personalized cart abandonment email for {user_name}.

            THEIR CART (${cart_total:.2f} total):
            {cart_summary}

            SPECIAL OFFER: {discount_percent}% OFF their entire order!

            RECOMMENDED PRODUCTS to complement their cart:
            {recs_summary}

            Write a warm, engaging message that:
            1. Acknowledges what's in their cart specifically (mention product names and quantities)
            2. Highlights the {discount_percent}% discount they're getting
            3. Explains how the recommended products complement what they're already buying
            4. Creates urgency without being pushy
            5. Encourages them to complete their purchase

            Guidelines:
            - Be conversational and personal (use "you" and "your")
            - Add a small touch of excitement (like “Your favorites are waiting!”)
            - Optionally add a short emoji or two for personality, but keep it professional (e.g., 🛍, ❤, ✨)
            - Highlight urgency subtly , mention the available quantity

            - Keep it under 150 words
            - Focus on value and benefits
            - Don't use overly salesy language
            
            CRITICAL: DO NOT INCLUDE ANY SIGNATURES OR CLOSINGS
            - No "Best regards", "Sincerely", "Cheers"
            - No "Best, [Your Name]" or placeholder names
            - No "Thank you", "Regards", etc.
            - Just the main message body - no closing phrases

            Write the message now:
            """
            
            # Log prompt for debugging
            logger.info(f"Sending prompt to Groq (length: {len(prompt)} chars)")
            logger.debug(f"Prompt: {prompt[:500]}...")
            
            # Call Groq API
            response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model=config.GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a friendly marketing assistant writing personalized cart abandonment emails. Be warm, conversational, and exciting without being pushy."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=config.GROQ_TEMPERATURE,
                max_tokens=config.GROQ_MAX_TOKENS,
                top_p=0.9
            )
            
            # Extract content from response
            ai_text = response.choices[0].message.content.strip()
            
            # Post-processing- Remove any signatures the AI might still add
            import re
            signature_patterns = [
                r'Best,.*?(?:\n|$)',  # Match "Best," followed by anything until newline or end
                r'Sincerely,.*?(?:\n|$)',
                r'Regards,.*?(?:\n|$)',
                r'Cheers,.*?(?:\n|$)',
                r'Thanks,.*?(?:\n|$)',
                r'\[Your Name\]',  # Match the placeholder exactly
                r'Best wishes,.*?(?:\n|$)',
                r'Warm regards,.*?(?:\n|$)',
                r'Kind regards,.*?(?:\n|$)',
                r'Best regards,.*?(?:\n|$)',
                r'Yours sincerely,.*?(?:\n|$)',
                r'Yours truly,.*?(?:\n|$)',
                r'With best regards,.*?(?:\n|$)',
            ]
            
            logger.debug(f"AI text before signature removal: {repr(ai_text)}")
            for pattern in signature_patterns:
                before = ai_text
                ai_text = re.sub(pattern, '', ai_text, flags=re.IGNORECASE | re.DOTALL)
                if before != ai_text:
                    logger.info(f"Removed signature with pattern: {pattern}")
            
            ai_text = ai_text.strip()
            logger.debug(f"AI text after signature removal: {repr(ai_text)}")
            
            logger.info(f"✅ Groq AI generated personalized content ({len(ai_text)} chars)")
            logger.info(f"Finish reason: {response.choices[0].finish_reason}")
            
            if not ai_text or not ai_text.strip():
                raise ValueError("No text content in Groq response")
            
            return ai_text
            
        except Exception as e:
            logger.error(f"Error generating Groq content: {e}")
            return self._fallback_recommendation_text(recommendations, cart_items)
    
    def _fallback_recommendation_text(self, recommendations: List[Dict], cart_items: List[Dict] = None) -> str:
        """Fallback recommendation text when Groq is unavailable"""
        cart_names = ", ".join([item['name'] for item in cart_items[:2]]) if cart_items else "your items"
        
        if not recommendations:
            return f"Great choice on {cart_names}! Complete your purchase now and enjoy your new products."
        
        rec_names = ", ".join([p['name'] for p in recommendations[:2]])
        return f"We noticed you're interested in {cart_names}. Based on your selection, we think you'll also love {rec_names}. " \
               f"These products pair perfectly with what's already in your cart. Don't miss out on this special offer!"


class EmailService:
    """
    Handles email generation and sending for cart abandonment
    """
    
    def __init__(self, mail_app=None, flask_app=None):
        """
        Initialize email service
        
        Args:
            mail_app: Flask-Mail instance (optional, will use SMTP if not provided)
            flask_app: Flask application instance (for app context)
        """
        self.mail_app = mail_app
        self.flask_app = flask_app
        self.recommendation_engine = RecommendationEngine()
    
    def calculate_discount(self, cart_total: float) -> Tuple[float, str]:
        """
        Calculate discount based on cart total
        
        Args:
            cart_total: Total value of cart
            
        Returns:
            Tuple of (discount_percentage, discount_message)
        """
        if cart_total >= config.DISCOUNT_TIER_2_AMOUNT:
            return (
                config.DISCOUNT_TIER_2_PERCENT,
                f"🎉 Special Offer: {config.DISCOUNT_TIER_2_PERCENT}% OFF your entire order!"
            )
        elif cart_total >= config.DISCOUNT_TIER_1_AMOUNT:
            return (
                config.DISCOUNT_TIER_1_PERCENT,
                f"🎁 Great News: {config.DISCOUNT_TIER_1_PERCENT}% OFF your order!"
            )
        else:
            return (0, "")
    
    async def generate_email_content(
        self,
        user: Dict,
        cart_items: List[Dict],
        cart_total: float,
        log_id: int = None
    ) -> Dict[str, str]:
        """
        Generate personalized email content with AI recommendations
        
        Args:
            user: User information (name, email)
            cart_items: List of cart items
            cart_total: Total cart value
            log_id: Cart abandonment log ID for tracking
            
        Returns:
            Dictionary with 'subject', 'html', 'text' keys
        """
        try:
            # Calculate discount
            discount_percent, discount_message = self.calculate_discount(cart_total)
            discounted_total = cart_total * (1 - discount_percent / 100)
            
            # Get product recommendations
            recommendations = self.recommendation_engine.get_similar_products(
                cart_items,
                count=config.RECOMMENDATION_COUNT
            )
            
            # Generate AI-enhanced personalized email content with cart items and discount info
            ai_recommendation_text = await self.recommendation_engine.enhance_with_groq(
                recommendations=recommendations,
                user_name=user['name'],
                cart_items=cart_items,
                cart_total=cart_total,
                discount_percent=discount_percent
            )
            
            # Build cart summary HTML
            cart_summary_html = self._build_cart_summary_html(cart_items, cart_total)
            
            # Build recommendations HTML
            recommendations_html = self._build_recommendations_html(recommendations)
            
            # Build tracking URL with log_id parameter
            tracking_cart_url = config.CART_URL
            if log_id:
                separator = '&' if '?' in tracking_cart_url else '?'
                tracking_cart_url = f"{tracking_cart_url}{separator}email_track={log_id}&source=abandonment_email"
            
            # Build complete email HTML
            email_html = self._build_email_html(
                user_name=user['name'],
                cart_summary=cart_summary_html,
                cart_total=cart_total,
                discount_message=discount_message,
                discount_percent=discount_percent,
                discounted_total=discounted_total,
                free_shipping=config.FREE_SHIPPING_ENABLED,
                ai_recommendation_text=ai_recommendation_text,
                recommendations_html=recommendations_html,
                cart_url=tracking_cart_url,
                log_id=log_id
            )
            
            # Build plain text version
            email_text = self._build_email_text(
                user_name=user['name'],
                cart_items=cart_items,
                cart_total=cart_total,
                discount_message=discount_message,
                discounted_total=discounted_total,
                recommendations=recommendations,
                cart_url=tracking_cart_url
            )
            
            subject = f"🛒 {user['name']}, you left something in your cart!"
            if discount_percent > 0:
                subject += f" + {discount_percent}% OFF!"
            
            logger.info(f"Generated email for {user['email']} - Cart: ${cart_total:.2f}, Discount: {discount_percent}%")
            
            return {
                'subject': subject,
                'html': email_html,
                'text': email_text
            }
            
        except Exception as e:
            logger.error(f"Error generating email content: {e}")
            raise
    
    def _build_cart_summary_html(self, cart_items: List[Dict], cart_total: float) -> str:
        """Build HTML table for cart items"""
        rows = []
        for item in cart_items:
            rows.append(f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        <strong>{item['name']}</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">
                        {item['quantity']}
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">
                        ${item['price']:.2f}
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">
                        <strong>${item['total']:.2f}</strong>
                    </td>
                </tr>
            """)
        
        return f"""
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 10px; text-align: left;">Product</th>
                        <th style="padding: 10px; text-align: center;">Qty</th>
                        <th style="padding: 10px; text-align: right;">Price</th>
                        <th style="padding: 10px; text-align: right;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                    <tr>
                        <td colspan="3" style="padding: 15px; text-align: right; font-size: 18px;">
                            <strong>Cart Total:</strong>
                        </td>
                        <td style="padding: 15px; text-align: right; font-size: 18px; color: #007bff;">
                            <strong>${cart_total:.2f}</strong>
                        </td>
                    </tr>
                </tbody>
            </table>
        """
    
    def _build_recommendations_html(self, recommendations: List[Dict]) -> str:
        """Build HTML for product recommendations"""
        if not recommendations:
            return ""
        
        cards = []
        for product in recommendations:
            # Get description, handle None/empty cases
            desc = product.get('description') or 'A great product for you'
            desc_preview = desc[:100] + "..." if len(desc) > 100 else desc
            
            # Get category
            category = product.get('category', 'Product')
            
            cards.append(f"""
                <div style="border: 2px solid #007bff; border-radius: 12px; padding: 20px; margin: 10px; 
                            flex: 1; min-width: 220px; max-width: 280px; background: #f8f9fa; text-align: center;">
                    <div style="background: #007bff; color: white; padding: 5px 10px; border-radius: 5px; 
                                font-size: 12px; margin-bottom: 10px; display: inline-block;">
                        {category}
                    </div>
                    <h4 style="margin: 10px 0; color: #333; font-size: 18px;">{product['name']}</h4>
                    <p style="color: #666; font-size: 14px; margin: 10px 0; min-height: 60px;">
                        {desc_preview}
                    </p>
                    <p style="font-size: 24px; color: #28a745; font-weight: bold; margin: 15px 0;">
                        ${product['price']:.2f}
                    </p>
                    <div style="background: #fff3cd; padding: 8px; border-radius: 5px; margin: 10px 0; font-size: 12px;">
                        ✨ Recommended for you
                    </div>
                    <a href="{product['url']}" 
                       style="display: inline-block; background-color: #28a745; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 25px; margin-top: 10px; font-weight: bold;">
                        🛍️ Add to Cart
                    </a>
                </div>
            """)
        
        return f"""
            <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 15px; margin: 30px 0;">
                {''.join(cards)}
            </div>
        """
    
    def _build_email_html(self, **kwargs) -> str:
        """Build complete email HTML with modern, engaging design"""
        # Calculate savings
        discount_amount = kwargs['cart_total'] * (kwargs['discount_percent'] / 100)
        final_total = kwargs['discounted_total']
        
        # AI content with fallback
        ai_text = kwargs.get('ai_recommendation_text', 
            f"We noticed you left some items in your cart. Complete your purchase now and save {kwargs['discount_percent']}% on your entire order!")
        
        # Hours remaining for urgency
        hours_remaining = 24
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complete Your Purchase - {kwargs['discount_percent']}% OFF!</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f5f7fa;">
    
    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background: #f5f7fa; padding: 20px 0;">
        <tr>
            <td align="center">
                <table cellpadding="0" cellspacing="0" border="0" width="600" style="max-width: 600px; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; color: white; font-size: 32px; font-weight: 700;">
                                🛍 ECommerceStore
                            </h1>
                        </td>
                    </tr>
                    
                    <!-- Greeting -->
                    <tr>
                        <td style="padding: 30px 30px 20px;">
                            <h2 style="margin: 0 0 20px; color: #1a1a1a; font-size: 28px; font-weight: 700;">
                                Hi {kwargs['user_name'].split()[0]}! 👋
                            </h2>
                        </td>
                    </tr>
                    
                    <!-- AI Personalized Content -->
                    <tr>
                        <td style="padding: 0 30px 20px;">
                            <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 25px; border-radius: 12px; border-left: 4px solid #667eea;">
                                <p style="margin: 0; color: #1a1a1a; font-size: 16px; line-height: 1.6;">
                                    {ai_text}
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Urgency Timer -->
                    <tr>
                        <td style="padding: 0 30px 20px;">
                            <div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; padding: 15px; text-align: center;">
                                <span style="font-size: 14px; color: #856404; font-weight: 600;">
                                    ⏰ Offer expires in {hours_remaining} hours! Don't miss out!
                                </span>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Discount Banner -->
                    <tr>
                        <td style="padding: 0 30px 20px;">
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px; text-align: center;">
                                <div style="color: white; font-size: 18px; margin-bottom: 10px;">
                                    ✨ Special Offer: {kwargs['discount_percent']}% OFF your entire order!
                                </div>
                                <div style="color: white; font-size: 32px; font-weight: 700; margin: 10px 0;">
                                    ${final_total:.2f} <span style="font-size: 20px; text-decoration: line-through; opacity: 0.7;">${kwargs['cart_total']:.2f}</span>
                                </div>
                                <div style="color: white; font-size: 16px;">
                                    Save ${discount_amount:.2f}!
                                </div>
                                
                                <!-- Progress Bar -->
                                <div style="background: rgba(255,255,255,0.3); height: 8px; border-radius: 4px; margin-top: 15px; overflow: hidden;">
                                    <div style="background: #4caf50; height: 100%; width: {kwargs['discount_percent']}%; border-radius: 4px;"></div>
                                </div>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Free Shipping -->
                    {('<tr><td style="padding: 0 30px 20px;"><div style="background: #d4edda; border: 2px solid #28a745; border-radius: 8px; padding: 15px; text-align: center;"><span style="font-size: 16px; color: #155724; font-weight: 600;">🚚 FREE SHIPPING on your order!</span></div></td></tr>' if kwargs.get('free_shipping') else '')}
                    
                    <!-- Cart Header -->
                    <tr>
                        <td style="padding: 30px 30px 20px;">
                            <h3 style="margin: 0; color: #1a1a1a; font-size: 22px; font-weight: 700;">
                                Your Cart Summary
                            </h3>
                        </td>
                    </tr>
                    
                    <!-- Cart Table (using existing cart_summary HTML) -->
                    <tr>
                        <td style="padding: 0 30px 20px;">
                            <div style="background: #f8f9fa; padding: 20px; border-radius: 12px;">
                                {kwargs['cart_summary']}
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Discount Row -->
                    <tr>
                        <td style="padding: 0 30px 10px;">
                            <table cellpadding="0" cellspacing="0" border="0" width="100%">
                                <tr>
                                    <td style="text-align: right; padding: 10px; font-weight: 600; font-size: 16px; color: #28a745;">
                                        Discount ({kwargs['discount_percent']}%):
                                    </td>
                                    <td style="text-align: right; padding: 10px; font-weight: 600; font-size: 18px; color: #28a745; width: 120px;">
                                        -${discount_amount:.2f}
                                    </td>
                                </tr>
                                <tr style="background: #e7f3ff;">
                                    <td style="text-align: right; padding: 15px; font-weight: 700; font-size: 20px; color: #1a1a1a;">
                                        Final Total:
                                    </td>
                                    <td style="text-align: right; padding: 15px; font-weight: 700; font-size: 28px; color: #667eea; width: 120px;">
                                        ${final_total:.2f}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- CTA Button -->
                    <tr>
                        <td style="padding: 30px; text-align: center;">
                            <a href="{kwargs['cart_url']}" 
                               style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; padding: 18px 50px; border-radius: 50px; font-size: 18px; font-weight: 700; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                                🛒 Complete Your Purchase Now
                            </a>
                        </td>
                    </tr>
                    
                    <!-- Recommendations Section -->
                    {('<tr><td style="padding: 30px; background: #f8f9fa;"><h3 style="margin: 0 0 20px; color: #1a1a1a; font-size: 22px; font-weight: 700; text-align: center;">✨ You Might Also Love...</h3><div style="padding: 10px;">' + kwargs['recommendations_html'] + '</div></td></tr>' if kwargs.get('recommendations_html') else '')}
                    
                    <!-- Company Signature -->
                    <tr>
                        <td style="padding: 30px; background: #fff; border-top: 1px solid #eee; text-align: left;">
                            <div style="color: #555; font-size: 16px; margin-bottom: 10px;">
                                <strong>Thank you for shopping with us!</strong>
                            </div>
                            <div style="color: #333; font-size: 16px; margin-bottom: 5px;">
                                <strong>The ECommerceStore Team</strong>
                            </div>
                            <div style="color: #888; font-size: 14px;">
                                Need help? Contact us at <a href="mailto:support@ecommerce.com" style="color: #667eea; text-decoration: none;">support@ecommerce.com</a>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Social Proof -->
                    <tr>
                        <td style="padding: 30px; background: #fff; border-top: 1px solid #eee; text-align: center;">
                            <div style="color: #666; font-size: 14px; margin-bottom: 15px;">
                                ⭐⭐⭐⭐⭐ Trusted by 10,000+ happy customers
                            </div>
                            <div style="color: #999; font-size: 12px;">
                                "Fast shipping, great quality, amazing customer service!" - Sarah M.
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px; background: #1a1a1a; text-align: center;">
                            <p style="margin: 0 0 10px; color: #999; font-size: 14px;">
                                Need help? <a href="mailto:support@ecommerce.com" style="color: #667eea; text-decoration: none;">Contact us</a>
                            </p>
                            <p style="margin: 0; color: #666; font-size: 12px;">
                                © 2025 ECommerceStore. All rights reserved.
                            </p>
                            <div style="margin-top: 15px;">
                                <a href="#" style="color: #667eea; text-decoration: none; margin: 0 10px; font-size: 12px;">Unsubscribe</a>
                                <a href="#" style="color: #667eea; text-decoration: none; margin: 0 10px; font-size: 12px;">Privacy Policy</a>
                            </div>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
    
    <!-- Email Open Tracking Pixel -->
    {('<img src="' + config.BASE_URL + '/track/email/' + str(kwargs.get('log_id', 0)) + '" width="1" height="1" style="display:none;" alt="" />') if kwargs.get('log_id') else ''}
    
</body>
</html>
        """
    
    def _build_email_text(self, **kwargs) -> str:
        """Build plain text version of email"""
        discount_text = ""
        if kwargs.get('discount_message'):
            discount_text = f"\n\n{kwargs['discount_message']}\n" \
                          f"Your new total: ${kwargs['discounted_total']:.2f} " \
                          f"(save ${kwargs['cart_total'] - kwargs['discounted_total']:.2f}!)\n"
        
        cart_items_text = "\n".join([
            f"  - {item['name']} x{item['quantity']} - ${item['total']:.2f}"
            for item in kwargs['cart_items']
        ])
        
        recs_text = ""
        if kwargs['recommendations']:
            recs_text = "\n\nYOU MIGHT ALSO LOVE:\n" + "\n".join([
                f"  - {p['name']} (${p['price']:.2f}) - {kwargs['cart_url'].replace('/cart', f'/product/{p['id']}')}"
                for p in kwargs['recommendations']
            ])
        
        return f"""
Hi {kwargs['user_name']}!

We noticed you left some items in your cart. Don't worry, we saved them for you!
{discount_text}
{"🚚 FREE SHIPPING on your order!" if kwargs.get('free_shipping') else ""}

YOUR CART:
{cart_items_text}

Cart Total: ${kwargs['cart_total']:.2f}

Return to your cart and complete your purchase:
{kwargs['cart_url']}
{recs_text}

Need help? Contact us at support@ecommerce.com

© 2025 ECommerceStore
        """
    
    async def send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """
        Send email using Flask-Mail or SMTP
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if self.mail_app and self.flask_app:
                # Use Flask-Mail with app context
                def send_with_context():
                    with self.flask_app.app_context():
                        msg = Message(
                            subject=subject,
                            sender=(config.SENDER_NAME, config.SENDER_EMAIL),
                            recipients=[to_email],
                            html=html_content,
                            body=text_content
                        )
                        self.mail_app.send(msg)
                
                # Run in thread to avoid blocking
                await asyncio.to_thread(send_with_context)
            elif self.mail_app:
                # Use Flask-Mail without app context (might fail)
                msg = Message(
                    subject=subject,
                    sender=(config.SENDER_NAME, config.SENDER_EMAIL),
                    recipients=[to_email],
                    html=html_content,
                    body=text_content
                )
                # Send in thread to avoid blocking
                await asyncio.to_thread(self.mail_app.send, msg)
            else:
                # Use SMTP directly
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = f"{config.SENDER_NAME} <{config.SENDER_EMAIL}>"
                msg['To'] = to_email
                
                msg.attach(MIMEText(text_content, 'plain'))
                msg.attach(MIMEText(html_content, 'html'))
                
                # Send via SMTP
                import os
                smtp_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
                smtp_port = int(os.getenv('MAIL_PORT', 587))
                smtp_user = os.getenv('MAIL_USERNAME', '')
                smtp_pass = os.getenv('MAIL_PASSWORD', '')
                
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(smtp_user, smtp_pass)
                await asyncio.to_thread(server.send_message, msg)
                server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False


class CartAbandonmentDetector:
    """
    Main detector class that monitors carts and triggers abandonment recovery
    """
    
    _instance = None  # Singleton instance
    _instance_lock = threading.Lock()  # Thread lock for singleton
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern to prevent multiple instances"""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, mail_app=None, flask_app=None):
        """
        Initialize the detector
        
        Args:
            mail_app: Flask-Mail instance (optional)
            flask_app: Flask application instance (for app context)
        """
        # Only initialize once (singleton pattern)
        if hasattr(self, '_initialized') and self._initialized:
            logger.info("CartAbandonmentDetector already initialized, skipping re-initialization")
            return
            
        self.email_service = EmailService(mail_app, flask_app)
        self.flask_app = flask_app
        self.processed_carts = set()  # Track processed cart IDs
        self.running = False
        self._initialized = True
        self._ensure_tracking_table()  # Create tracking table if it doesn't exist
        logger.info("CartAbandonmentDetector initialized (singleton instance)")
    
    def _ensure_tracking_table(self):
        """Ensure the cart_abandonment_log table exists with cart_hash column"""
        try:
            conn = DatabaseConnection.get_connection()
            cursor = conn.cursor()
            
            # Create table if it doesn't exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cart_abandonment_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    cart_hash VARCHAR(64) NOT NULL DEFAULT '',
                    cart_total DECIMAL(10, 2) NOT NULL,
                    email_sent BOOLEAN DEFAULT FALSE,
                    email_opened BOOLEAN DEFAULT FALSE,
                    link_clicked BOOLEAN DEFAULT FALSE,
                    purchase_completed BOOLEAN DEFAULT FALSE,
                    opened_at TIMESTAMP NULL,
                    clicked_at TIMESTAMP NULL,
                    completed_at TIMESTAMP NULL,
                    click_count INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_hash_created (user_id, cart_hash, created_at),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Check if cart_hash column exists (for older tables)
            cursor.execute("""
                SELECT COUNT(*) as col_count
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'cart_abandonment_log' 
                AND COLUMN_NAME = 'cart_hash'
            """)
            
            col_exists = cursor.fetchone()
            if col_exists and col_exists['col_count'] == 0:
                # Add cart_hash column if it doesn't exist
                cursor.execute('ALTER TABLE cart_abandonment_log ADD COLUMN cart_hash VARCHAR(64) NOT NULL DEFAULT "" AFTER user_id')
                logger.info("Added cart_hash column to cart_abandonment_log table")
            
            # Check and add tracking columns if they don't exist
            tracking_columns = [
                ('email_opened', 'BOOLEAN DEFAULT FALSE AFTER email_sent'),
                ('link_clicked', 'BOOLEAN DEFAULT FALSE AFTER email_opened'),
                ('purchase_completed', 'BOOLEAN DEFAULT FALSE AFTER link_clicked'),
                ('opened_at', 'TIMESTAMP NULL AFTER purchase_completed'),
                ('clicked_at', 'TIMESTAMP NULL AFTER opened_at'),
                ('completed_at', 'TIMESTAMP NULL AFTER clicked_at'),
                ('click_count', 'INT DEFAULT 0 AFTER completed_at')
            ]
            
            for col_name, col_definition in tracking_columns:
                cursor.execute(f"""
                    SELECT COUNT(*) as col_count
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'cart_abandonment_log' 
                    AND COLUMN_NAME = '{col_name}'
                """)
                col_check = cursor.fetchone()
                if col_check and col_check['col_count'] == 0:
                    cursor.execute(f'ALTER TABLE cart_abandonment_log ADD COLUMN {col_name} {col_definition}')
                    logger.info(f"Added {col_name} column to cart_abandonment_log table")
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("Cart abandonment tracking table ready")
        except Exception as e:
            logger.error(f"Error creating tracking table: {e}")
    
    def _generate_cart_hash(self, cart_items: List[Dict]) -> str:
        """Generate a unique hash for cart contents to identify the same cart"""
        import hashlib
        # Sort items by product_id and create a string representation
        sorted_items = sorted(cart_items, key=lambda x: x['product_id'])
        cart_signature = "|".join([
            f"{item['product_id']}:{item['quantity']}" 
            for item in sorted_items
        ])
        # Generate SHA256 hash
        return hashlib.sha256(cart_signature.encode()).hexdigest()
    
    async def check_abandoned_carts(self):
        """Check for abandoned carts and send recovery emails"""
        try:
            conn = DatabaseConnection.get_connection()
            cursor = conn.cursor()
            
            # Calculate abandonment threshold
            threshold_time = datetime.now() - timedelta(minutes=config.ABANDONMENT_THRESHOLD_MINUTES)
            
            # Find abandoned carts - get unique users with abandoned items
            query = """
                SELECT 
                    c.user_id,
                    MIN(c.created_at) as created_at,
                    u.name,
                    u.email
                FROM cart c
                JOIN users u ON c.user_id = u.id
                WHERE c.created_at <= %s
                AND c.user_id NOT IN (
                    SELECT DISTINCT user_id 
                    FROM orders 
                    WHERE created_at > %s
                )
                GROUP BY c.user_id, u.name, u.email
                HAVING COUNT(*) > 0
            """
            
            cursor.execute(query, (threshold_time, threshold_time))
            abandoned_carts = cursor.fetchall()
            
            logger.info(f"Found {len(abandoned_carts)} potentially abandoned carts")
            
            for cart_info in abandoned_carts:
                # Get cart details first to generate hash
                cursor.execute("""
                    SELECT 
                        c.id,
                        c.product_id,
                        c.quantity,
                        p.name,
                        p.description,
                        p.price,
                        p.category,
                        p.image,
                        (c.quantity * p.price) as total
                    FROM cart c
                    JOIN products p ON c.product_id = p.id
                    WHERE c.user_id = %s
                """, (cart_info['user_id'],))
                
                cart_items = cursor.fetchall()
                
                if not cart_items:
                    continue
                
                # Generate unique hash for this specific cart
                cart_hash = self._generate_cart_hash(cart_items)
                
                # Skip if already processed in this session
                cart_key = f"{cart_info['user_id']}_{cart_hash}"
                if cart_key in self.processed_carts:
                    logger.debug(f"Skipping cart {cart_key} - already processed in this session")
                    continue
                
                # Check if email was already sent for THIS SPECIFIC CART (same contents) in the last 24 hours
                # If cart changes (different hash), a new email can be sent
                cursor.execute("""
                    SELECT id, email_sent, created_at 
                    FROM cart_abandonment_log
                    WHERE user_id = %s 
                    AND cart_hash = %s
                    AND created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (cart_info['user_id'], cart_hash))
                
                existing_log = cursor.fetchone()
                if existing_log:
                    if existing_log['email_sent']:
                        logger.info(f"Skipping cart {cart_hash[:8]}... for user {cart_info['user_id']} - email already sent for this exact cart within last 24 hours")
                        self.processed_carts.add(cart_key)
                        continue
                    else:
                        # Log exists but email not sent - check if it's recent (within 2 minutes)
                        # This prevents duplicate processing if previous attempt is still in progress
                        time_diff = datetime.now() - existing_log['created_at']
                        if time_diff.total_seconds() < 120:  # 2 minutes
                            logger.info(f"Skipping cart {cart_hash[:8]}... for user {cart_info['user_id']} - processing already in progress")
                            self.processed_carts.add(cart_key)
                            continue
                
                # Mark as processed IMMEDIATELY to prevent duplicate processing in same cycle
                self.processed_carts.add(cart_key)
                logger.debug(f"Marked cart {cart_key} as processed")
                
                # Calculate total
                cart_total = sum(float(item['total']) for item in cart_items)
                
                # Prepare user info
                user = {
                    'name': cart_info['name'],
                    'email': cart_info['email']
                }
                
                # Log to database first to get the log_id for tracking
                log_id = self._log_abandonment_event(cursor, cart_info['user_id'], cart_hash, cart_total, email_sent=False)
                
                # Generate and send email with tracking log_id
                try:
                    email_content = await self.email_service.generate_email_content(
                        user=user,
                        cart_items=cart_items,
                        cart_total=cart_total,
                        log_id=log_id
                    )
                    
                    success = await self.email_service.send_email(
                        to_email=user['email'],
                        subject=email_content['subject'],
                        html_content=email_content['html'],
                        text_content=email_content['text']
                    )
                    
                    if success:
                        # Update the log entry to mark email as sent
                        cursor.execute("""
                            UPDATE cart_abandonment_log 
                            SET email_sent = TRUE 
                            WHERE id = %s
                        """, (log_id,))
                        cursor.connection.commit()
                        
                        logger.info(f"Sent abandonment email to {user['email']} for cart worth ${cart_total:.2f} (log_id: {log_id}, cart hash: {cart_hash[:8]}...)")
                    else:
                        # If email failed to send, remove from processed set so it can be retried
                        self.processed_carts.discard(cart_key)
                        logger.warning(f"Failed to send email to {user['email']}, will retry next cycle")
                    
                except Exception as e:
                    # If error occurred, remove from processed set so it can be retried
                    self.processed_carts.discard(cart_key)
                    logger.error(f"Error processing cart for user {cart_info['user_id']}: {e}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error checking abandoned carts: {e}")
    
    def _log_abandonment_event(self, cursor, user_id: int, cart_hash: str, cart_total: float, email_sent: bool):
        """Log abandonment event to database with cart hash for duplicate prevention"""
        try:
            # Insert log entry with cart hash
            # The duplicate check is now done before calling this function
            cursor.execute("""
                INSERT INTO cart_abandonment_log (user_id, cart_hash, cart_total, email_sent)
                VALUES (%s, %s, %s, %s)
            """, (user_id, cart_hash, cart_total, email_sent))
            
            cursor.connection.commit()
            
            # Get the inserted ID
            log_id = cursor.lastrowid
            logger.info(f"Logged abandonment event: user_id={user_id}, cart_hash={cart_hash[:8]}..., log_id={log_id}")
            return log_id
            
        except Exception as e:
            logger.error(f"Error logging abandonment event: {e}")
    
    async def start_monitoring(self):
        """Start continuous monitoring for abandoned carts"""
        self.running = True
        logger.info(f"Cart abandonment monitor started (checking every {config.CHECK_INTERVAL_SECONDS}s)")
        
        while self.running:
            try:
                await self.check_abandoned_carts()
                await asyncio.sleep(config.CHECK_INTERVAL_SECONDS)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(config.CHECK_INTERVAL_SECONDS)
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.running = False
        logger.info("Cart abandonment monitor stopped")


def start_abandonment_monitor(mail_app=None):
    """
    Convenience function to start the abandonment monitor
    
    Args:
        mail_app: Flask-Mail instance (optional)
        
    Returns:
        CartAbandonmentDetector instance
    """
    detector = CartAbandonmentDetector(mail_app)
    
    # Run in background
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(detector.start_monitoring())
    except KeyboardInterrupt:
        detector.stop_monitoring()
        logger.info("Monitor stopped by user")
    finally:
        loop.close()
    
    return detector
