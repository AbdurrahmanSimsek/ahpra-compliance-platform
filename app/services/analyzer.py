import anthropic
from flask import current_app
from app import db
from app.models import Page, Violation
import re

class AhpraComplianceAnalyzer:
    def __init__(self):
        self.api_key = current_app.config['ANTHROPIC_API_KEY']
        self.model = current_app.config['ANTHROPIC_MODEL']
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Ahpra guidelines system prompt
        self.system_prompt = """
        Act as Ahpra Compliance Specialist Assistant. Meticulously evaluate text against Ahpra Guidelines to ensure strict compliance. 
        Assess text paragraph-by-paragraph, identifying sentences that potentially violate Ahpra Guidelines.
        For each violation, please provide:
        1. The exact problematic sentence
        2. The specific Ahpra guideline section violated (e.g., Section 8.3f)
        3. A justification explaining why it violates the guideline
        4. A revised, compliant version of the text
        
        The Compliance Guard ensures compliance with specific Ahpra Guidelines sections, including:
        Section 8.3f: Avoids implying psychological, social, or transformative benefits without evidence.
        Section 9.2: Avoids claims of psychological or social benefits without linking to acceptable evidence.
        Section 7.6a: Avoids trivializing cosmetic surgery through terms that minimize its invasiveness.
        Section 9.1a: Avoids advertising cosmetic surgery in a way that creates unrealistic expectations of outcomes.
        Section 7.6f: Avoids idealizing cosmetic surgery through images, words, or marketing techniques that trivialize the procedure.
        
        Also check for compliance with these additional sections:
        1. Practitioner Responsibility:
        1.1: Advertising must not exploit vulnerabilities or insecurities to increase demand.
        1.2: Advertising must not target individuals who may not be suitable candidates due to psychological issues.
        1.3: Practitioners must acknowledge the potential conflict between financial gain and their duty of care.
        1.4: Advertising must clearly and honestly present cost information, including the total cost.
        
        2. Titles and Claims about Training, Qualifications, Registration, Experience, and Competence:
        2.1-2.6: Only qualified practitioners with specialist registration may use relevant specialist titles. Information about qualifications and experience must be accurate, honest, and clear.
        
        3. Financial and Other Incentives:
        3.1: Advertising must not offer incentives to encourage cosmetic surgery.
        
        4. Testimonials:
        4.1-4.7: Testimonials are prohibited in cosmetic surgery advertising.
        
        7. Risk, Recovery, and Idealizing Cosmetic Surgery:
        7.1-7.3: Advertising must provide accurate and realistic information about risks.
        7.4-7.5: Advertising must include realistic information about recovery.
        7.6: Advertising must not trivialize cosmetic surgery.
        
        8. Body Image and Promotion for Wellbeing and Improved Mental Health:
        8.1-8.3: Advertising must not exploit unrealistic body image expectations or promote unrealistic body image ideals.
        
        9. Realistic Expectations of Outcomes:
        9.1-9.2: Advertising must not create unrealistic expectations of outcomes and claims about benefits must be supported by evidence.
        
        Provide your analysis in JSON format as follows:
        {
            "violations": [
                {
                    "text": "[The non-compliant text]",
                    "guideline": "[Section reference]",
                    "justification": "[Explanation of violation]",
                    "revision": "[Compliant revision]"
                }
            ],
            "compliance_score": [score between 0-100]
        }
        """
    
    def analyze_page(self, page_id):
        """Analyze a page for Ahpra compliance"""
        page = Page.query.get(page_id)
        if not page:
            raise ValueError(f"Page with ID {page_id} not found")
        
        # Analyze the page content
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,  # Lower temperature for more consistent results
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": page.text_content}
                ]
            )
            
            # Parse the response to extract violations and compliance score
            result = self._parse_analysis_response(response.content)
            
            # Calculate compliance score (adjust logic as needed)
            compliance_score = result.get('compliance_score', 0)
            
            # Update page with analysis results
            page.compliance_score = compliance_score
            page.analyzed = True
            
            # Create violation records
            for violation in result.get('violations', []):
                new_violation = Violation(
                    page=page,
                    text_content=violation['text'],
                    guideline_reference=violation['guideline'],
                    justification=violation['justification'],
                    suggested_revision=violation['revision']
                )
                db.session.add(new_violation)
            
            db.session.commit()
            return result
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def _parse_analysis_response(self, response_text):
        """Parse the AI response to extract violations and compliance score"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                import json
                result = json.loads(json_match.group(0))
                return result
            
            # Fallback to manual parsing if JSON extraction fails
            violations = []
            compliance_score = 100  # Default to 100% if no violations found
            
            # Extract violations using regex patterns
            violation_blocks = re.finditer(r'Quote:\s*"([^"]+)"\s*Violated Guideline:\s*([^\n]+)\s*Justification:\s*([^\n]+)\s*Compliant Revision:\s*"([^"]+)"', response_text)
            
            for block in violation_blocks:
                violations.append({
                    'text': block.group(1),
                    'guideline': block.group(2),
                    'justification': block.group(3),
                    'revision': block.group(4)
                })
            
            # Adjust compliance score based on number of violations
            if violations:
                compliance_score = max(0, 100 - (len(violations) * 10))  # Deduct 10 points per violation
            
            return {
                'violations': violations,
                'compliance_score': compliance_score
            }
            
        except Exception as e:
            print(f"Error parsing analysis response: {str(e)}")
            return {
                'violations': [],
                'compliance_score': 0,
                'error': str(e)
            }
