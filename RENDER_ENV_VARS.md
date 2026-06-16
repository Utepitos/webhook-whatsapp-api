Render environment variables for EduRuta AI

Copy/paste checklist for Render -> Environment Variables:

Required
- NODE_ENV=production
- VERIFY_TOKEN=your_webhook_verify_token_here
- FLOWISE_URL=https://your-flowise-instance.com
- FLOWISE_FLOW_ID=your_flowise_chatflow_id
- WHATSAPP_TOKEN=your_whatsapp_token_here
- WHATSAPP_PHONE_ID=your_phone_number_id_here

Optional
- FLOWISE_API_KEY=your_flowise_api_key_here
- FLOWISE_TIMEOUT_MS=15000
- REDIS_URL=redis://:password@host:port

Notes
- Do not commit real secrets to git.
- If your Flowise instance does not require auth, leave FLOWISE_API_KEY empty or omit it in Render.
- If you use Redis later for sessions, add REDIS_URL and update session storage accordingly.
