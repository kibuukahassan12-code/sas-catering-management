import threading, time, webbrowser, sys, os, socket



def start_flask():

    try:

        from app import create_app

        app = create_app()

        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

    except Exception:

        import app as raw_app_module

        raw_app_module.app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)



def start_gui():

    try:

        import webview, pystray

        from PIL import Image, ImageDraw

    except Exception:

        webbrowser.open("http://127.0.0.1:5000")

        return



    def icon_image():

        img = Image.new('RGBA', (64,64), (0,0,0,0))

        d = ImageDraw.Draw(img)

        d.ellipse((8,8,56,56), fill=(255,140,0,255))

        d.rectangle((20,28,44,36), fill=(255,255,255,255))

        return img



    def menu_show(icon, item):

        try:

            win.show()

        except:

            webbrowser.open("http://127.0.0.1:5000")



    def menu_quit(icon, item):

        icon.stop()

        os._exit(0)



    win = webview.create_window("SAS Management System", "http://127.0.0.1:5000", width=1200, height=800)

    icon = pystray.Icon("sas", icon_image(), "SAS Management System",

        menu=pystray.Menu(

            pystray.MenuItem("Show", menu_show),

            pystray.MenuItem("Quit", menu_quit)

        )

    )



    threading.Thread(target=icon.run, daemon=True).start()

    webview.start()



def wait_for_server(timeout=25):

    start = time.time()

    while time.time() - start < timeout:

        try:

            socket.create_connection(("127.0.0.1", 5000), 1).close()

            return True

        except:

            time.sleep(0.3)

    return False



if __name__ == "__main__":

    threading.Thread(target=start_flask, daemon=True).start()

    if not wait_for_server():

        webbrowser.open("http://127.0.0.1:5000")

    start_gui()

