Post-deploy checklist for Render

1. Open the Render service logs.
2. Confirm the app started with no runtime errors.
3. Check the health endpoint:
   - GET /health should return {"status":"ok"}
4. Verify the webhook endpoint:
   - GET /webhook with the correct verification flow should return the challenge.
5. Send a test message through WhatsApp Cloud API.
6. Confirm the app logs show:
   - incoming message received
   - Flowise request sent
   - response returned to WhatsApp
7. If the response is slow, increase FLOWISE_TIMEOUT_MS slightly.
8. If webhook verification fails, re-check VERIFY_TOKEN.
9. If Flowise requests fail, confirm FLOWISE_URL, FLOWISE_FLOW_ID, and FLOWISE_API_KEY.
10. If WhatsApp messages are not delivered, confirm WHATSAPP_TOKEN and WHATSAPP_PHONE_ID.

Quick curl checks

Health:
```bash
curl -X GET https://<your-service>.onrender.com/health
```

Chat endpoint:
```bash
curl -X POST https://<your-service>.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"test-1","message":"Hola, tengo 18 años y soy de Boyacá"}'
```

Webhook verification reminder
- Render public URL + /webhook must be configured in Meta/WhatsApp Cloud API.
- The verify token in Meta must match VERIFY_TOKEN in Render exactly.
