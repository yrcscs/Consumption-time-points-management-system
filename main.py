import webbrowser
from threading import Timer
from app import create_app

app = create_app()
browser_opened = False

def open_browser():
    global browser_opened
    if not browser_opened:
        webbrowser.open_new('http://127.0.0.1:5555/')
        browser_opened = True

if __name__ == '__main__':
    Timer(1, open_browser).start()  # 在1秒后打开浏览器
    app.run(debug=True, port=5555)