# GEMINI PERSONALIZATION FIX

## Issue Identified
Gemini is blocking content with `finish_reason=2` (RECITATION) - it thinks marketing emails are copyrighted templates.

## Solution
The prompt is too detailed and resembles common email templates, triggering Gemini's recitation filter.

## Quick Fix
Modify the `enhance_with_gemini()` method in `cart_abandonment_detector.py` (lines 208-360):

### Replace the prompt generation section (lines 237-267) with:

```python
# Simplified prompt to avoid recitation detection
cart_items_text = ', '.join([f"{item['name']} ({item.get('quantity', 1)}x)" for item in cart_items])
recs_text = ', '.join([p['name'] for p in recommendations[:3]])

prompt = f"""Write a brief personal message for {user_name}.

Cart: {cart_items_text} - ${cart_total:.2f}  
Discount: {discount_percent}%
Suggestions: {recs_text}

Create 2-3 sentences that mention their items, the discount, and how suggestions complement their purchase."""
```

## Why This Works
1. **Shorter prompt** (< 200 chars vs 1500+ chars)
2. **No marketing keywords** (removed "cart abandonment", "email", "call-to-action")
3. **Direct request** (not asking to emulate a specific format)
4. **Factual info only** (items, discount, suggestions)

## Current Status
- Simple prompts: ✅ WORKING (147 chars generated)
- Complex prompts: ❌ BLOCKED (finish_reason=2, 0 chars)

## Alternative Solution
If recitation continues to be an issue, consider:
1. Use a different model (GPT-4 via OpenAI doesn't have this restriction)
2. Disable Gemini and use enhanced template system
3. Use Gemini only for product descriptions, not full emails

## Test Command
```bash
cd "C:\AI_Agent_LLM&NLP\Ecom_platform\ecom\cart_abandonment_detector"
python debug_gemini.py  # Tests simple prompt (working)
python test_detector.py  # Tests full system (currently blocked)
```
