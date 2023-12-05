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
# from tkinter.messagebox import showinfo
from tkinter import ttk
from PIL import ImageTk, Image
import os


class O2ebGui(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.win_width = 1000
        self.win_height = 400
        self.filenames = []

        self.title("Observation to eBird list conversion")
        self.geometry(f"{self.win_width}x{self.win_height}")

        # Define the frame
        self.frm = ttk.Frame(self,
                             width=self.win_width,
                             height=self.win_height,
                             padding=0)
        self.frm.grid_propagate(True)
        self.frm.grid()

        # set an image on the top of the frame
        self.img = self.get_image('./images/background.jpg', (self.win_width, self.win_height), True)
        self.lbl_img = ttk.Label(self.frm, image=self.img)
        self.lbl_img.image = self.img
        # lbl1.place(x=0, y=0)
        self.lbl_img.grid(column=0, row=0, columnspan=2)

        # display the current directory
        self.folder_txt = tk.StringVar()
        self.folder_txt.set(f"Current folder: {os.path.abspath(os.getcwd())}")
        self.lbl_folder = ttk.Label(self.frm, textvariable=self.folder_txt)
        self.lbl_folder.grid(column=0, row=1, sticky=tk.W, padx=50, pady=10)
        _img = self.get_image('./images/folder.png', (30, 30), True)

        # define an input field to capture observation file to import
        # val = self.register(self.check_files_exist)
        self.input = tk.StringVar()
        self.inp = ttk.Entry(self.frm, textvariable=self.input, justify=tk.LEFT, width=34)
        self.inp.grid(column=0, row=2, sticky=tk.W, padx=50, pady=0)
        self.inp.update()

        # validatecommand=val('%P', validate='focusout')

        # define a button to select files to import
        self.btn_folder = ttk.Button(
            self.frm,
            width=0,
            image=_img,
            command=self.select_files
        )
        self.btn_folder.image = _img
        self.btn_folder.grid(column=0, row=2, padx=self.inp.winfo_width()-40)

        # self.btn_quit = ttk.Button(self.frm, text="Quit", command=self.destroy)
        # self.btn_quit.grid(column=1, row=3)

#    def check_files_exist(self, filepath):
#        return True

    @staticmethod
    def get_image(image_path: str, size=tuple(), keep_proportion=True):
        _img = Image.open(image_path)
        w, h = size
        factor = w / _img.width if keep_proportion else 1
        _img = _img.resize((w, int(_img.height * factor)), Image.LANCZOS)
        return ImageTk.PhotoImage(_img)

    def select_files(self):
        """
        Selects one or more CSV files using a file dialog box.

        Returns:
            None

        """
        filetypes = (('CSV file', '*.csv'),)
        self.filenames = fd.askopenfiles(
            title='Select files',
            initialdir='./obs_data',
            filetypes=filetypes
        )
        _text = ', '.join([os.path.basename(x.name) for x in self.filenames])
        self.folder_txt.set(f"Current folder: {os.path.dirname(self.filenames[0].name)}")
        self.inp.delete(0, tk.END)
        self.inp.insert(0, _text)



def main():
    gui = O2ebGui()
    gui.mainloop()


if __name__ == "__main__":
    main()
