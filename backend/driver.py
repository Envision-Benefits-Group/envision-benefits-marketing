import os
import warnings

import gunicorn.app.base
from dotenv import load_dotenv

warnings.filterwarnings("ignore")

# Load environment variables from .env file
load_dotenv()

# Get the current working directory
cwd = os.getcwd()

# Check if logs directory exists, if not create it
logs_dir = os.path.join(cwd, "logs")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Check if app.log exists, if not create it
app_log = os.path.join(logs_dir, "app.log")
if not os.path.exists(app_log):
    with open(app_log, "w") as f:
        f.write("")


class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app_import_path, options=None):
        self.options = options or {}
        self.application = app_import_path
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


if __name__ == "__main__":
    environment = os.getenv("ENVIRONMENT", "PROD").upper()

    if environment == "DEV":
        import uvicorn

        print("Running in DEV mode with Uvicorn and reload enabled.")
        # Ensure src.main:app is the correct path to your FastAPI app instance
        uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        print("Running in PROD mode with Gunicorn.")
        options = {
            "bind": "0.0.0.0:8000",
            "workers": 3,  # Consider making this configurable via env var
            "worker_class": "uvicorn.workers.UvicornWorker",
            "proxy_protocol": True,
            "forwarded_allow_ips": "*",
            # Log to both file and stdout
            "accesslog": "-",  # '-' means log to stdout
            "errorlog": "-",  # '-' means log to stdout
            "capture_output": True,  # Capture stdout/stderr of workers
        }
        StandaloneApplication("src.main:app", options).run()
