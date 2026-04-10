from openai import OpenAI

client = OpenAI(
  api_key="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"
)

completion = client.chat.completions.create(
  model="gpt-4o-mini",
  store=True,
  messages=[
    {"role": "user", "content": input("Enter prompt")}
  ]
)

print(completion.choices[0].message);
