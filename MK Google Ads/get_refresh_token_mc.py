"""Run once to get a refresh token covering both Google Ads + Merchant Center."""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/adwords",
    "https://www.googleapis.com/auth/content",
]

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes=SCOPES)
credentials = flow.run_local_server(port=8080, open_browser=True, prompt="consent")

print("\n=== COPY THIS REFRESH TOKEN ===")
print(credentials.refresh_token)
print("================================\n")
