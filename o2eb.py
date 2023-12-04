"""
"   List conversion from observation.org to ebird.org
"
"   Author: Xavier Mayeur
"   Date: December 2023
"
"
"""
import tkinter as tk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
from tkinter import ttk
from PIL import ImageTk, Image


def select_file():
    """
    Selects one or more CSV files using a file dialog box.

    Returns:
        None

    """
    filetypes = (('CSV file', '*.csv'),)
    filenames = fd.askopenfiles(
        title='Select files',
        initialdir='./obs_data',
        filetypes=filetypes
    )

    showinfo(
        title='Selected files',
        message=', '.join([f.name for f in filenames])
    )


def define_root_windows(win_width=1000, win_height=400, background_image=None):
    """
    :param win_width: (int) The width of the root window. Default is 1000.
    :param win_height: (int) The height of the root window. Default is 400.
    :param background_image: (str) The path to the background image for the root window. Default is None.
    :return: (tkinter.Tk) The root window.

    This method creates and configures the root window for the Observation to eBird list conversion application.
    The root window is the main window of the application.

    Example usage:
        root = define_root_windows(1200, 600, "images/background.jpg")
        root.mainloop()
    """
    master = tk.Tk()
    master.title("Observation to eBird list conversion")
    master.geometry(f"{win_width}x{win_height}")

    if background_image is not None:
        _img = Image.open(background_image)
        _factor = win_width / _img.width
        new_h = int(_img.height * _factor)
        new_w = win_width
        _img = _img.resize((new_w, new_h), Image.LANCZOS)
        _img = _img.crop((0, int(new_h * 0.25), new_w, int(new_h * 75)))
        img = ImageTk.PhotoImage(_img)
        lbl1 = tk.Label(image=img)
        lbl1.image = img
        lbl1.place(x=0, y=0)

    return master


def new_image_frame(root, image=None, **kwargs):
    _frm = ttk.Frame(root, **kwargs)
    _frm.grid_propagate(0)
    _frm.grid()
    w = kwargs['width']
    if image is not None:
        # open and resize the image
        img = Image.open(image)
        _factor = w / img.width
        new_h = int(img.height * _factor)
        img = img.resize((w, new_h), Image.LANCZOS)
        img = ImageTk.PhotoImage(img)
        lbl1 = ttk.Label(_frm, image=img)
        lbl1.image = img
        # lbl1.place(x=0, y=0)
        lbl1.grid(column=0, row=0)
    return _frm


def main():
    win_width = 1000
    win_height = 400
    root = define_root_windows(win_width=win_width, win_height=win_height)
    frm = new_image_frame(root=root,
                    image='images/background.jpg',
                    width=win_width,
                    height=win_height,
                    padding=10)
    # frm = ttk.Frame(root, padding=10, width=win_width, height=200)
    # frm.grid_propagate(0)
    # frm.grid()

    ttk.Label(frm, text="Hello World!").grid(column=0, row=1)
    ttk.Button(
        frm,
        text='Open a File',
        command=select_file
    ).grid(column=0, row=2)

    # open_button.pack(expand=True)

    ttk.Button(frm, text="Quit", command=root.destroy).grid(column=0, row=3)

    root.mainloop()


if __name__ == "__main__":
    main()
