import anthropic
from flask import current_app
from app import db
from app.models import Page, HTMLFix

class HTMLSemanticFixer:
    def __init__(self):
        self.api_key = current_app.config['ANTHROPIC_API_KEY']
        self.model = current_app.config['ANTHROPIC_MODEL']
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # System prompt for HTML semantic improvements
        self.system_prompt = """
        Act as an expert HTML semantics specialist with deep knowledge of Ahpra guidelines and SEO best practices.
        
        Your task is to analyze the provided HTML content and improve its semantic structure while ensuring it remains
        compliant with Ahpra (Australian Health Practitioner Regulation Agency) guidelines.
        
        For each HTML document:
        1. Identify poor semantic HTML structure (e.g., excessive <div> tags, improper heading hierarchy, missing semantic elements)
        2. Convert non-semantic tags to appropriate semantic elements (e.g., <div> to <section>, <article>, <nav>, etc.)
        3. Ensure proper heading hierarchy (h1 → h2 → h3) is maintained
        4. Add appropriate ARIA attributes where beneficial
        5. Improve accessibility features (alt text for images, proper form labels, etc.)
        6. Maintain and enhance the content's compliance with Ahpra guidelines
        
        Return your response in JSON format with the following structure:
        {
            "original_html": "[The original HTML]",
            "fixed_html": "[The improved semantic HTML]",
            "justification": "[Detailed explanation of changes made and benefits]"
        }
        """
    
    def generate_html_fix(self, page_id):
        """Generate improved semantic HTML for a page"""
        page = Page.query.get(page_id)
        if not page:
            raise ValueError(f"Page with ID {page_id} not found")
        
        if not page.html_content:
            raise ValueError("Page has no HTML content to fix")
        
        try:
            # Send the HTML content to Claude for analysis and improvement
            response = self.client.messages.create(
                model=self.model,
                max_tokens=6000,
                temperature=0.3,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": page.html_content}
                ]
            )
            
            # Parse the response to extract the fixed HTML and justification
            result = self._parse_fix_response(response.content, page.html_content)
            
            # Create or update HTMLFix record
            html_fix = HTMLFix.query.filter_by(page_id=page.id).first()
            if not html_fix:
                html_fix = HTMLFix(
                    page=page,
                    original_html=page.html_content,
                    fixed_html=result['fixed_html'],
                    justification=result['justification']
                )
                db.session.add(html_fix)
            else:
                html_fix.original_html = page.html_content
                html_fix.fixed_html = result['fixed_html']
                html_fix.justification = result['justification']
            
            db.session.commit()
            return result
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def _parse_fix_response(self, response_text, original_html):
        """Parse the AI response to extract the fixed HTML and justification"""
        try:
            # Try to extract JSON from the response
            import re
            import json
            
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group(0))
                return {
                    'original_html': result.get('original_html', original_html),
                    'fixed_html': result.get('fixed_html', ''),
                    'justification': result.get('justification', '')
                }
            
            # Fallback to basic extraction if JSON parsing fails
            fixed_html = original_html  # Default to original if extraction fails
            justification = "Unable to extract proper HTML improvements from the response."
            
            # Look for HTML code blocks
            html_match = re.search(r'```html\n([\s\S]*?)\n```', response_text)
            if html_match:
                fixed_html = html_match.group(1)
            
            # Extract justification (any text after the HTML block)
            just_match = re.search(r'```html[\s\S]*?\n```\n\n([\s\S]*)', response_text)
            if just_match:
                justification = just_match.group(1)
            
            return {
                'original_html': original_html,
                'fixed_html': fixed_html,
                'justification': justification
            }
            
        except Exception as e:
            print(f"Error parsing HTML fix response: {str(e)}")
            return {
                'original_html': original_html,
                'fixed_html': original_html,
                'justification': f"Error parsing response: {str(e)}",
                'error': str(e)
            }
