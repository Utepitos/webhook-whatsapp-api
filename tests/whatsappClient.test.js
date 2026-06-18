const { extractMessage } = require('../src/whatsappClient');

const validPayload = {
  entry: [{
    changes: [{
      value: {
        messages: [{
          from: '573001234567',
          id: 'wamid.abc123',
          type: 'text',
          text: { body: '¡Hola!' },
        }],
      },
    }],
  }],
};

describe('extractMessage', () => {
  test('extracts all fields from a valid WhatsApp Cloud API payload', () => {
    expect(extractMessage(validPayload)).toEqual({
      from: '573001234567',
      text: '¡Hola!',
      type: 'text',
      messageId: 'wamid.abc123',
    });
  });

  test('returns null when the messages array is empty', () => {
    const body = { entry: [{ changes: [{ value: { messages: [] } }] }] };
    expect(extractMessage(body)).toBeNull();
  });

  test('returns null for an empty entry array', () => {
    expect(extractMessage({ entry: [] })).toBeNull();
  });

  test.each([null, {}, { entry: 'not-an-array' }, undefined])(
    'returns null for malformed input: %p',
    (input) => {
      expect(extractMessage(input)).toBeNull();
    }
  );

  test('returns empty string for text when the message has no text field', () => {
    const payload = JSON.parse(JSON.stringify(validPayload));
    delete payload.entry[0].changes[0].value.messages[0].text;
    expect(extractMessage(payload).text).toBe('');
  });

  test('passes through non-text message types correctly', () => {
    const payload = JSON.parse(JSON.stringify(validPayload));
    payload.entry[0].changes[0].value.messages[0].type = 'image';
    expect(extractMessage(payload).type).toBe('image');
  });
});
