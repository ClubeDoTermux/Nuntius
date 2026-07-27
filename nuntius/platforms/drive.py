class DriveClient:
    def __init__(self, credentials_path: str = ""):
        self.creds_path = credentials_path
        self._service = None

    @property
    def service(self):
        if self._service is None:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            creds = None
            token_path = self.creds_path.replace("credentials.json", "token.json")

            try:
                creds = Credentials.from_authorized_user_file(token_path)
            except Exception:
                pass

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.creds_path,
                        ["https://www.googleapis.com/auth/drive"],
                    )
                    creds = flow.run_local_server(port=0)
                with open(token_path, "w") as f:
                    f.write(creds.to_json())

            self._service = build("drive", "v3", credentials=creds)
        return self._service

    def list_files(self, page_size: int = 10):
        results = self.service.files().list(
            pageSize=page_size, fields="files(id, name, mimeType)"
        ).execute()
        return [f"{f['name']} ({f['mimeType']})" for f in results.get("files", [])]

    def read_file(self, file_id: str):
        from googleapiclient.http import MediaIoBaseDownload
        import io

        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return fh.getvalue().decode("utf-8", errors="replace")
