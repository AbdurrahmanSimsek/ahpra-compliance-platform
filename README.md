# Ahpra Compliance Audit & Content Improvement Platform

A comprehensive platform for auditing medical websites for Ahpra (Australian Health Practitioner Regulation Agency) guideline compliance and providing semantic HTML improvements.

## Features

- **Website Crawling**: Automatically crawls and extracts content from medical websites
- **AI-Powered Compliance Analysis**: Identifies non-compliant content according to Ahpra guidelines
- **Semantic HTML Improvements**: Suggests structural HTML improvements for better SEO and accessibility
- **Comprehensive Reports**: Generates detailed compliance reports for website owners
- **Credit System**: Pay-as-you-go system with initial free page analysis
- **Scheduled Rechecks**: Optional recurring compliance checks

## Running on Replit

This application is designed to run easily on Replit. To get started:

1. Fork this GitHub repository
2. Create a new Replit project by importing from GitHub
3. Set up your environment variables in Replit's Secrets tab:
   - `SECRET_KEY`: A secure random string
   - `ANTHROPIC_API_KEY`: Your Claude API key
   - `STRIPE_PUBLIC_KEY`: Your Stripe public key (for payments)
   - `STRIPE_SECRET_KEY`: Your Stripe secret key

4. Click the Run button in Replit

The application will automatically initialize the database and set up default credit packages on first run.

## Local Development

### Requirements

- Python 3.8+
- SQLite (for development)

### Setup

1. Clone the repository

```bash
git clone https://github.com/yourusername/ahpra-compliance-platform.git
cd ahpra-compliance-platform
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with these variables:

```
SECRET_KEY=your-secure-random-key
ANTHROPIC_API_KEY=your-anthropic-api-key
STRIPE_PUBLIC_KEY=your-stripe-test-key
STRIPE_SECRET_KEY=your-stripe-test-secret
BASE_URL=http://localhost:5000
```

4. Run the application

```bash
python app.py
```

The application will be available at http://localhost:5000

## API Keys Required

To fully use this application, you'll need:

1. **Anthropic API Key**: For AI-powered compliance analysis using Claude
   - Sign up at [Anthropic](https://www.anthropic.com/)

2. **Stripe API Keys**: For handling payments and credit purchases
   - Sign up at [Stripe](https://stripe.com/)
   - Use test keys for development

## License

[MIT License](LICENSE)
