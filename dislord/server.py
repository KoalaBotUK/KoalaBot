from .client import ApplicationClient

try:
    from flask import Flask, request
    app = Flask(__name__)
except ImportError:
    Flask = None
    request = None

    class FakeFlask:
        @staticmethod
        def route(self, *args, **kwargs): # noqa
            def decorator(func):
                return func
            return decorator

        def run(self, *args, **kwargs):
            raise RuntimeError("flask library needed in order to use server")

    app = FakeFlask()

__application_client: ApplicationClient


@app.route("/", methods=["POST"])
async def interactions_endpoint():
    raw_request = request.json
    signature = request.headers.get('X-Signature-Ed25519')
    timestamp = request.headers.get('X-Signature-Timestamp')
    print(f"👉 Request: {raw_request}")
    response = __application_client.verified_interact(raw_request, signature, timestamp).as_server_response()
    print(f"🫴 Response: {response}")
    return response


def start_server(application_client, **kwargs):
    global __application_client
    __application_client = application_client
    app.run(**kwargs)



