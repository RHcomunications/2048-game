import wx
from game_ui import VentanaJuego

if __name__ == "__main__":
    app = wx.App()
    VentanaJuego(None, "2048 Accesible")
    app.MainLoop()
