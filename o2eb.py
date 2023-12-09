"""
"   List conversion from observation.org to ebird.org
"
"   Author: Xavier Mayeur
"   Date: December 2023
"
"
"""
import re
import tkinter as tk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
from tkinter import ttk
from PIL import ImageTk, Image
from os.path import dirname, basename, join, abspath
from os import getcwd
from obs2ebird import import_obs, export_to_ebird
from datetime import date
from get_config import get_config, write_config_file

config = get_config()

__dir__ = dirname(__file__)


class O2ebGui(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.db_in = None
        self.win_width = 1000
        self.win_height = 700
        self.selected_files = []
        self.db = tk.StringVar()
        self.dbname = tk.StringVar()
        self.mysql_host = tk.StringVar()
        self.mysql_port = tk.StringVar()
        self.sqlite_db = config['sqlite']['db']
        self.mysql_db = config['mysql']['db']
        self.mysql_host.set(config['mysql']['host'])
        self.mysql_port.set(config['mysql']['port'])
        self.lbl_url = None
        self.in_url = None
        self.lbl_port = None
        self.in_port = None
        self.option_row = 0

        self.choice = tk.StringVar()
        self.choice.set(config['default']['db_dialect'])
        self.top = None

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

        # Define menus for settings editing
        self.menu = tk.Menu(self)
        self.config(menu=self.menu)
        self.main_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label='Edit', menu=self.main_menu)
        self.main_menu.add_command(label="Settings", command=self.settings)

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
                                  foreground='green')
        self.lbl_list.grid(column=0, row=row, sticky=tk.W, padx=50, pady=10)

        row += 1
        # define an input field to capture observation file to import
        # val = self.register(self.check_files_exist)
        self.file_names = tk.StringVar()
        self.inp = ttk.Entry(self.frm, textvariable=self.file_names, justify=tk.LEFT, width=34)
        self.inp.grid(column=0, row=row, sticky=tk.W, padx=50, pady=0)
        self.inp.update()
        self.inp.focus()

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
        self.file_folder.set(f"Current folder: {abspath(getcwd())}")
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

        row += 1
        # Label for eBird.org list file
        self.lbl_list2 = ttk.Label(self.frm,
                                   text="Enter eBird.org list file or select using folder button",
                                   foreground='green')
        self.lbl_list2.grid(column=0, row=row, sticky=tk.W, padx=50, pady=10)

        row += 1
        # define an input field to capture observation file to export
        # val = self.register(self.check_files_exist)
        self.e_file_name = tk.StringVar()
        self.e_inp = ttk.Entry(self.frm, textvariable=self.e_file_name, justify=tk.LEFT, width=34)
        self.e_inp.grid(column=0, row=row, sticky=tk.W, padx=50, pady=0)
        self.e_inp.update()

        self.btn_folder2 = ttk.Button(
            self.frm,
            width=0,
            image=_img,
            command=self.select_file
        )
        self.btn_folder2.image = _img
        self.btn_folder2.grid(column=0, row=row, padx=self.e_inp.winfo_width() - 40)

        # Add labels and entries for from/to dates
        row += 1
        # Label for eBird.org list file
        self.lbl_dates = ttk.Label(self.frm,
                                   text="From / to date (yyyy-mm-dd)",
                                   foreground='green')
        self.lbl_dates.grid(column=0, row=row, sticky=tk.W, padx=50, pady=10)

        row += 1
        val = (self.register(self.val_date), '%P')
        inval = (self.register(self.invalid_date),)
        self.from_date = tk.StringVar()
        self.from_date.set("2020-01-01")
        self.from_inp = ttk.Entry(self.frm, textvariable=self.from_date, justify=tk.LEFT, width=10,
                                  validatecommand=val, validate='focusout', invalidcommand=inval)
        self.from_inp.grid(column=0, row=row, sticky=tk.W, padx=50, pady=0)
        self.from_inp.update()

        self.lbl_to = ttk.Label(self.frm,
                                text="to",
                                foreground='green')
        self.lbl_to.grid(column=0, row=row, sticky=tk.W, padx=self.from_inp.winfo_width() + 50, pady=0)
        self.lbl_to.update()
        self.to_date = tk.StringVar()
        self.to_inp = ttk.Entry(self.frm, textvariable=self.to_date, justify=tk.LEFT, width=10,
                                validatecommand=val, validate='focusout', invalidcommand=inval)
        self.to_inp.grid(column=0, row=row, sticky=tk.W, padx=170, pady=0)
        self.to_inp.update()

        # create a processing button
        self.btn_export = ttk.Button(self.frm,
                                     text="GENERATE eBIRD FILE",
                                     command=self.export)
        self.btn_export.grid(column=0, row=row, sticky=tk.E)

        row += 1
        # status label
        self.export_status = tk.StringVar()
        self.export_status.set('')
        self.style.configure('Status.TLabel', foreground='green')
        self.lbl_export_status = ttk.Label(self.frm, textvariable=self.export_status, style='Status.TLabel')
        self.lbl_export_status.grid(column=0, row=row, sticky=tk.E, padx=0, pady=0)

    def settings(self):
        """

        Manage the config file data as per:
        mysql:
          host: xxx
          port: xxx
          db: xxx

        sqlite:
          db: xxx

        default:
          db_dialect: [mysql | sqlite]


        :return:
        """
        # create top window
        self.top = tk.Toplevel(self.frm)
        top_width = 520
        top_height = 230
        self.top.geometry(f"{top_width}x{top_height}")
        self.top.grid_propagate(True)

        row = 0
        lbl1 = ttk.Label(self.top, text='Database', foreground='green')
        lbl1.grid(row=row, sticky=tk.W, padx=20, pady=10)
        row += 1
        rb_sqlite = ttk.Radiobutton(self.top, text='sqlite', variable=self.choice,
                                    value='sqlite', command=self.db_selected)
        rb_mysql = ttk.Radiobutton(self.top, text='mysql', variable=self.choice,
                                   value='mysql', command=self.db_selected)
        rb_sqlite.grid(row=row, sticky=tk.W, padx=20)
        row += 1
        rb_mysql.grid(row=row, sticky=tk.W, padx=20)

        row += 2
        lbl2 = ttk.Label(self.top, text='Name of the database:', foreground='green')
        lbl2.grid(row=row, sticky=tk.W, padx=20)
        row += 1

        self.db_in = ttk.Entry(self.top, textvariable=self.dbname, justify=tk.LEFT, width=50)
        self.db_in.bind("<FocusOut>", self.set_dbname)
        self.db_in.grid(row=row, padx=20)
        self.db_in.update()

        row += 1
        self.option_row = row
        self.lbl_url = ttk.Label(self.top, text="host url", foreground='green')
        self.lbl_url.grid(row=row, padx=20, sticky=tk.W)
        self.lbl_url.update()
        self.in_url = ttk.Entry(self.top, textvariable=self.mysql_host, justify=tk.LEFT, width=15)
        self.in_url.grid(row=row, sticky=tk.W, padx=20 + self.lbl_url.winfo_width())
        row += 1
        self.lbl_port = ttk.Label(self.top, text="port     ", foreground='green')
        self.lbl_port.grid(row=row, padx=20, sticky=tk.W)
        self.lbl_port.update()
        self.in_port = ttk.Entry(self.top, textvariable=self.mysql_port, justify=tk.LEFT, width=15)
        self.in_port.grid(row=row, sticky=tk.W, padx=20 + self.lbl_port.winfo_width())

        if config['default']['db_dialect'] == 'sqlite':
            self.dbname.set(self.sqlite_db)
            rb_sqlite.invoke()
        else:
            self.dbname.set(self.mysql_db)
            rb_mysql.invoke()

        if config['default']['db_dialect'] == 'sqlite':
            self.lbl_url.grid_forget()
            self.lbl_port.grid_forget()
            self.in_port.grid_forget()
            self.in_url.grid_forget()

        row += 1
        btn_cancel = ttk.Button(self.top, text='Cancel', command=self.top.withdraw)
        btn_cancel.grid(row=row, sticky=tk.E)
        btn_cancel.update()
        ttk.Button(self.top, text='Save', command=self.save_config).grid(row=row, sticky=tk.E,
                                                                         padx=btn_cancel.winfo_width() + 20)

    def set_dbname(self, event):
        selection = self.choice.get()
        if selection == 'sqlite':
            self.sqlite_db = self.db_in.get()
        else:
            self.mysql_db = self.db_in.get()
            
    def save_config(self):
        global config
        _config = {
            "mysql": {
                "host": self.mysql_host.get(),
                "port": self.mysql_port.get(),
                "db": self.mysql_db
            },
            "sqlite": {"db": self.sqlite_db},
            "default": {"db_dialect": self.db.get()}
        }
        write_config_file(_config)
        config = _config.copy()
        self.sqlite_db = config['sqlite']['db']
        self.mysql_db = config['mysql']['db']
        self.mysql_host.set(config['mysql']['host'])
        self.mysql_port.set(config['mysql']['port'])
        self.choice.set(config['default']['db_dialect'])
        self.top.withdraw()

    def db_selected(self):
        selection = self.choice.get()
        self.db.set(selection)
        if selection == 'sqlite':
            self.lbl_url.grid_forget()
            self.lbl_port.grid_forget()
            self.in_port.grid_forget()
            self.in_url.grid_forget()
            self.dbname.set(self.sqlite_db)
        else:
            self.lbl_url.grid(row=self.option_row, padx=20, sticky=tk.W)
            self.in_url.grid(row=self.option_row, sticky=tk.W, padx=20 + self.lbl_url.winfo_width())
            self.lbl_port.grid(row=self.option_row+1, padx=20, sticky=tk.W)
            self.in_port.grid(row=self.option_row+1, sticky=tk.W, padx=20 + self.lbl_port.winfo_width())
            self.dbname.set(self.mysql_db)

    @staticmethod
    def get_image(image_path: str, size=tuple(), keep_proportion=True):
        _img = Image.open(join(__dir__, image_path))
        w, h = size
        factor = w / _img.width if keep_proportion else 1
        _img = _img.resize((w, int(_img.height * factor)), Image.LANCZOS)
        return ImageTk.PhotoImage(_img)

    @staticmethod
    def val_date(my_date):
        matches = re.findall(r'(\d{4})-(\d{2})-(\d{2})', my_date, re.DOTALL)
        if len(matches) != 0:
            _year, _mm, _dd = matches[0]
            try:
                date(int(_year), int(_mm), int(_dd))
                return True
            except TypeError:
                return False
        return False

    @staticmethod
    def invalid_date():
        showinfo(title='Date entry',
                 message='Please enter a valid data in format yyyy-mm-dd', icon='error')

    def select_files(self):
        """
        Selects one or more CSV files using a file dialog box.

        Returns:
            None

        """
        filetypes = (('CSV file', '*.csv'),)
        self.selected_files = fd.askopenfiles(
            title='Select files',
            initialdir='./obs_data',
            filetypes=filetypes
        )
        if len(self.selected_files) != 0:
            _text = ', '.join([basename(x.name) for x in self.selected_files])
            self.file_folder.set(f"Current folder: {dirname(self.selected_files[0].name)}")
            self.inp.delete(0, tk.END)
            self.inp.insert(0, _text)
            self.btn_upload.focus()

    def select_file(self):
        """
        Selects one or more CSV files using a file dialog box.

        Returns:
            None

        """
        filetypes = (('CSV file', '*.csv'),)
        self.selected_files = fd.askopenfile(
            title='Select file',
            initialdir='./ebird_data',
            filetypes=filetypes
        )
        if self.selected_files is not None:
            _text = self.selected_files.name
            self.e_inp.delete(0, tk.END)
            self.e_inp.insert(0, _text)
            self.from_inp.focus()

    def upload(self):
        if self.inp.get() == '':
            return "Error: no file name has been provided"

        _folder = self.file_folder.get()
        if ':' in _folder:
            _folder = _folder.split(":")[1].strip()
        status = import_obs(self.inp.get(), folder=_folder)
        self.upload_status.set('File(s) processed' if status is None else f'Error: {status}')

    def export(self):
        _file = self.e_inp.get()
        if _file == '':
            return "Error: no file name has been provided"
        _from = self.from_inp.get()
        _to = self.to_inp.get()
        if _to == '':
            _to = None
        status = export_to_ebird(_file, _from, _to)
        self.export_status.set('File processed' if status is None else f'Error: {status}')
        return status


def main():
    gui = O2ebGui()
    gui.mainloop()


if __name__ == "__main__":
    main()
