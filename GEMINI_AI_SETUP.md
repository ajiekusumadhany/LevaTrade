# Gemini AI Setup Guide

## Overview
The trading bot integrates with Google's Gemini AI to provide intelligent market analysis, entry/exit reasoning, and interactive chat capabilities.

## Getting Gemini API Keys

### Step 1: Access Google AI Studio
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Accept the terms of service if prompted

### Step 2: Create API Keys
1. Click "Create API Key"
2. Choose "Create API key in new project" or select existing project
3. Copy the generated API key
4. **Important**: Save the key immediately as you won't be able to see it again

### Step 3: Create Multiple Keys (Recommended)
For better rate limit handling, create 2-3 API keys:
1. Repeat Step 2 to create additional keys
2. You can create keys in the same project or different projects
3. Each key has its own rate limits, allowing for rotation

## Configuration

### Add Keys to .env File
```bash
# Multiple Gemini API keys for rotation (recommended)
GEMINI_API_KEYS=AIzaSyD1234567890abcdef,AIzaSyD0987654321fedcba,AIzaSyD1122334455667788

# Single key (basic setup)
GEMINI_API_KEYS=AIzaSyD1234567890abcdef

# Optional: Customize AI behavior
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=500
```

### Key Rotation Benefits
- **Automatic failover**: If one key hits rate limits, automatically switches to next key
- **Higher throughput**: Multiple keys = higher combined rate limits
- **Reliability**: System continues working even if one key fails

## Rate Limits (as of 2024)

### Gemini 2.0 Flash
- **Free tier**: 15 requests per minute, 1,500 requests per day
- **Paid tier**: Higher limits based on billing

### Best Practices
1. **Use 3+ API keys** for active trading bots
2. **Monitor usage** in Google AI Studio console
3. **Upgrade to paid tier** for production use
4. **Implement caching** for repeated queries (future enhancement)

## Features Enabled by Gemini AI

### 1. Entry Reasoning
- Analyzes market conditions when opening positions
- Explains technical indicators and market context
- Provides risk assessment and expected outcomes

### 2. Exit Reasoning
- Explains why positions were closed (TP/SL hit)
- Analyzes market journey from entry to exit
- Provides lessons learned and performance review

### 3. Interactive Chat
- Ask questions about your trading performance
- Get real-time market analysis
- Query specific positions or symbols
- System analytics and insights

### 4. Mode-Aware Analysis
- **Dry Run Mode**: Analyzes simulation data
- **Real Trading Mode**: Analyzes live trading data
- Separate performance tracking and insights

## Example Chat Queries

```
"What's my current performance?"
"Analyze my BTCUSDT position"
"Why did my last trade hit stop loss?"
"What's the market sentiment right now?"
"Show me my recent trading activity"
"How is my win rate in simulation vs real trading?"
```

## Troubleshooting

### Common Issues

#### 1. "GEMINI_API_KEYS not found"
- Check your .env file has the correct variable name
- Ensure no spaces around the = sign
- Restart the bot after adding keys

#### 2. "No valid Gemini API keys found"
- Check for typos in API keys
- Ensure keys are separated by commas (no spaces)
- Verify keys are active in Google AI Studio

#### 3. Rate limit errors
- Add more API keys to .env file
- Check usage in Google AI Studio
- Consider upgrading to paid tier

#### 4. "AI response unavailable"
- Check internet connection
- Verify API keys are still valid
- Check Google AI Studio for service status

### Testing Your Setup

Run the test script to verify your Gemini AI integration:

```bash
python -c "
import asyncio
from gemini_ai_system import get_gemini_analyst

async def test():
    analyst = get_gemini_analyst()
    if analyst:
        response = await analyst.chat_with_market_data('Hello, test message')
        print('✅ Gemini AI working:', response[:50] + '...')
    else:
        print('❌ Gemini AI not working')

asyncio.run(test())
"
```

## Security Notes

1. **Keep API keys secret**: Never commit them to version control
2. **Use .env file**: Store keys in environment variables only
3. **Rotate keys regularly**: Generate new keys periodically
4. **Monitor usage**: Watch for unexpected API calls
5. **Restrict key access**: Use Google Cloud IAM if available

## Cost Optimization

1. **Start with free tier**: Test with free API keys first
2. **Monitor usage**: Track requests in Google AI Studio
3. **Optimize prompts**: Shorter prompts = lower costs
4. **Cache responses**: Avoid repeated identical queries
5. **Use appropriate models**: Balance cost vs capability

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your API keys in Google AI Studio
3. Test with a simple query first
4. Check bot logs for detailed error messages

For Google AI Studio support:
- [Google AI Studio Documentation](https://ai.google.dev/docs)
- [Gemini API Documentation](https://ai.google.dev/api)