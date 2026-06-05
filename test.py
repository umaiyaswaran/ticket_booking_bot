from google import genai

client = genai.Client(api_key="AQ.Ab8RN6KSd-YNXeIETUq2D-NxlL0n2-ACv356ubDwAm9IbdfDSw")

models = client.models.list()
for m in models:
    print(m.name)