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
from obs2ebird import import_obs


class O2ebGui(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.win_width = 1000
        self.win_height = 700
        self.input_files = []

        self.title("Observation to eBird list conversion")
        self.geometry(f"{self.win_width}x{self.win_height}")
        self.style = ttk.Style()

        # Define the frame
        self.frm = ttk.Frame(self,
                             width=self.win_width,
                             height=self.win_height,
                             padding=0)
        self.frm.grid_propagate(False)
        self.frm.grid()

        row = 0
        # set an image on the top of the frame
        self.img = self.get_image('./images/background.jpg', (self.win_width, self.win_height), True)
        self.lbl_img = ttk.Label(self.frm, image=self.img)
        self.lbl_img.image = self.img
        # lbl1.place(x=0, y=0)
        self.lbl_img.grid(column=0, row=row, columnspan=2)

        row += 1
        # Label with invite to enter observation list file(s)
        self.lbl_list = ttk.Label(self.frm,
                                  text="Enter Observation.org list file(s) or select using folder button",
                                  foreground='yellow')
        self.lbl_list.grid(column=0, row=row, sticky=tk.W, padx=50, pady=10)

        row += 1
        # define an input field to capture observation file to import
        # val = self.register(self.check_files_exist)
        self.file_names = tk.StringVar()
        self.inp = ttk.Entry(self.frm, textvariable=self.file_names, justify=tk.LEFT, width=34)
        self.inp.grid(column=0, row=row, sticky=tk.W, padx=50, pady=0)
        self.inp.update()
        self.inp.focus()

        # validatecommand=val('%P', validate='focusout')

        # define a button to select files to import, with a folder icon
        _img = self.get_image('./images/folder.png', (30, 30), True)
        self.btn_folder = ttk.Button(
            self.frm,
            width=0,
            image=_img,
            command=self.select_files
        )
        self.btn_folder.image = _img
        self.btn_folder.grid(column=0, row=row, padx=self.inp.winfo_width() - 40)

        row += 1
        # display the current directory
        self.file_folder = tk.StringVar()
        self.file_folder.set(f"Current folder: {os.path.abspath(os.getcwd())}")
        self.lbl_folder = ttk.Label(self.frm, textvariable=self.file_folder)
        self.lbl_folder.grid(column=0, row=row, sticky=tk.W, padx=50, pady=0)
        _img = self.get_image('./images/folder.png', (30, 30), True)

        # create a processing button
        self.btn_upload = ttk.Button(self.frm,
                                     text="IMPORT LIST(S)",
                                     command=self.upload)
        self.btn_upload.grid(column=0, row=row, sticky=tk.E)
        # self.btn_quit = ttk.Button(self.frm, text="Quit", command=self.destroy)
        # self.btn_quit.grid(column=1, row=3)

        row += 1
        # status label
        self.upload_status = tk.StringVar()
        self.upload_status.set('')
        self.style.configure('Status.TLabel', foreground='green')
        self.lbl_upload_status = ttk.Label(self.frm, textvariable=self.upload_status, style='Status.TLabel')
        self.lbl_upload_status.grid(column=0, row=row, sticky=tk.E, padx=0, pady=0)
        # Insert separator line
        row += 1

        # SEPARATOR
        self.style.configure('TSeparator', background='yellow')
        sep = ttk.Separator(self.frm, orient=tk.HORIZONTAL, style='TSeparator')
        sep.grid(column=0, row=row, columnspan=2, sticky=tk.EW, pady=10)

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
        self.input_files = fd.askopenfiles(
            title='Select files',
            initialdir='./obs_data',
            filetypes=filetypes
        )
        if len(self.input_files) != 0:
            _text = ', '.join([os.path.basename(x.name) for x in self.input_files])
            self.file_folder.set(f"Current folder: {os.path.dirname(self.input_files[0].name)}")
            self.inp.delete(0, tk.END)
            self.inp.insert(0, _text)
            self.btn_upload.focus()

    def upload(self):
        if self.inp.get() == '':
            return "Error: no file name has been provided"

        _folder = self.file_folder.get()
        if ':' in _folder:
            _folder = _folder.split(":")[1].strip()
        status = import_obs(self.inp.get(), folder=_folder)
        self.upload_status.set('File(s) processed' if status is None else f'Error: {status}')


def main():
    gui = O2ebGui()
    gui.mainloop()


if __name__ == "__main__":
    main()
