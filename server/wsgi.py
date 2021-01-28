from app import app

application = app
print(__name__)
app.run()
if __name__ == "__main__":
    print('app')