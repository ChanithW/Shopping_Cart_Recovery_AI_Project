"""
Minimal test to debug Gemini response structure
"""
import os
import sys
import asyncio

# Set up path
sys.path.insert(0, os.path.dirname(__file__))

import google.generativeai as genai
import config

# Configure Gemini
genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel(config.GEMINI_MODEL)

async def test_gemini():
    print("\n=== Testing Gemini Response Structure ===\n")
    
    # Simple prompt
    prompt = "Write a friendly 2-sentence message encouraging someone to complete their purchase of a laptop."
    
    print(f"Sending prompt: {prompt[:100]}...")
    
    # Generate content
    response = await asyncio.to_thread(
        model.generate_content,
        prompt,
        generation_config={'temperature': 0.7, 'max_output_tokens': 200}
    )
    
    print(f"\nResponse type: {type(response)}")
    print(f"Has 'text' attribute: {hasattr(response, 'text')}")
    print(f"Has 'candidates' attribute: {hasattr(response, 'candidates')}")
    print(f"Has 'prompt_feedback' attribute: {hasattr(response, 'prompt_feedback')}")
    
    # Check prompt feedback
    if hasattr(response, 'prompt_feedback'):
        pf = response.prompt_feedback
        print(f"\nPrompt Feedback:")
        print(f"  - block_reason: {getattr(pf, 'block_reason', 'NONE')}")
        print(f"  - safety_ratings: {getattr(pf, 'safety_ratings', 'NONE')}")
    
    # Check candidates
    if hasattr(response, 'candidates') and response.candidates:
        print(f"\nCandidates: {len(response.candidates)}")
        candidate = response.candidates[0]
        
        print(f"  Candidate 0:")
        print(f"    - finish_reason: {getattr(candidate, 'finish_reason', 'UNKNOWN')}")
        print(f"    - has safety_ratings: {hasattr(candidate, 'safety_ratings')}")
        
        if hasattr(candidate, 'safety_ratings'):
            print(f"    - safety_ratings:")
            for rating in candidate.safety_ratings:
                print(f"        * {rating.category}: {rating.probability}")
        
        # Check parts
        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
            parts = candidate.content.parts
            print(f"    - parts count: {len(parts)}")
            
            for i, part in enumerate(parts):
                print(f"      Part {i}:")
                print(f"        - type: {type(part)}")
                print(f"        - has 'text': {hasattr(part, 'text')}")
                
                if hasattr(part, 'text'):
                    text = part.text
                    print(f"        - text length: {len(text)}")
                    print(f"        - text preview: {text[:100]}")
    
    # Try to get text
    print("\n=== Attempting Text Extraction ===")
    
    try:
        text = response.text
        print(f"SUCCESS via response.text: {len(text)} chars")
        print(f"Text: {text}")
    except Exception as e:
        print(f"FAILED response.text: {str(e)[:150]}")
        
        # Try alternatives
        try:
            parts_text = "".join([p.text for p in response.candidates[0].content.parts if hasattr(p, 'text')])
            print(f"SUCCESS via parts: {len(parts_text)} chars")
            print(f"Text: {parts_text}")
        except Exception as e2:
            print(f"FAILED parts extraction: {e2}")

if __name__ == '__main__':
    asyncio.run(test_gemini())
