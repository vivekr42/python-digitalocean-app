from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "🚀 Hello from Flask App on DigitalOcean with CI/CD!, this website is a demo created for farooq. here we have deployed python app usinging github actions."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
