import requests
import json

API_URL = "https://kong-proxy.yc.amvera.ru/api/v1/models/deepseek"

API_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJtVmV0T3hCQlJhcWNpZHdnYUJROEF4UjcwMkk4QmtrRjRseXJWazFKU1BjIn0.eyJleHAiOjE4NjM3NzEyMjEsImlhdCI6MTc2OTE2MzIyMSwiYXV0aF90aW1lIjoxNzY5MTYyMDAyLCJqdGkiOiIzZmQyNWM3MC1kYzIyLTQ5ZmItOTMwNy1hMjNiNmJiYmMyNmQiLCJpc3MiOiJodHRwczovL2lkLmFtdmVyYS5ydS9hdXRoL3JlYWxtcy9hbXZlcmEiLCJhdWQiOlsiYWNjb3VudCIsImtvbmctMSJdLCJzdWIiOiI2ZTBjYWU2OC04MjU2LTRkMTItOWNiNy1mMDdhNjMyYzhiNDUiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJhbXZlcmEtYXBpIiwic2lkIjoiYjYwMjg2MzAtMzBhNS00OTJlLWFiODYtNGY0OWI2ZmFmZmUzIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyIvKiJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImRlZmF1bHQtcm9sZXMtYW12ZXJhIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgZW1haWwgcGhvbmUgcHJvZmlsZSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJkYW5pbGt5bmkiLCJlbWFpbCI6Imlua2Vycm9yNjlAZ21haWwuY29tIn0.RIiSXrbihfpcRsu23iCapqThP9r5Qtr1nUN9HHjLnRhf1JDhfzcf_V5Kh9h4v4KHuN72uAUSCtyd7vzI-QjDMqHaYZFbubZC66g14RZaEKtZISqUQunQ6XGiBGSho3rd8PjM5ig42AbE61NxELB2cE9PnV6siJ1DZ5wxzwtgRLQqz_-Y4s-M5XuJSyMGXl5qmvGlUkxtbSBi9DNKx0o7_wZ8o0dkrqKl0-7qlME5EKqqxmTCl6v4Cnlq_0A1fywCy7QHtLCOmWaQayE8bTbGNGCfhhPchGzQJK_aMc0jG_7VdvkHjvPjkXvosN3-c0y5kJG9vVCjKDOGBIiqyq80Lg"

headers = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "X-Auth-Token": f"Bearer {API_TOKEN}"
}

messages = [
    {
        "role": "system",
        "text": "Ты полезный ассистент."
    }
]

print("DeepSeek V3 чат запущен")
print("exit = выход\n")

while True:
    user_input = input("Ты: ")

    if user_input.lower() == "exit":
        break

    messages.append({
        "role": "user",
        "text": user_input
    })

    payload = {
        "model": "deepseek-V3",
        "messages": messages,
        "temperature": 0.7,
        "max_completion_tokens": 500
    }

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        print(f"\nSTATUS: {response.status_code}")

        data = response.json()

        if response.status_code != 200:
            print("\nОшибка API:")
            continue

        assistant_text = data["choices"][0]["message"]["content"]

        print(f"\nDeepSeek: {assistant_text}\n")

        messages.append({
            "role": "assistant",
            "text": assistant_text
        })

    except Exception as e:
        print("\nОшибка:")
        print(e)