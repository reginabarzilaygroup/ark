import argparse
import json
import requests
import tempfile
import tkinter as tk
from tkinter import filedialog as fd

from PIL import ImageTk, Image

from utils import dicom_to_image_dcmtk


class App:
    def __init__(self, api):
        self.api = api

        self.window = tk.Tk()
        self.init_window()
        self.i_img = 0
        self.filenames = []
        self.imgs = []
        self.data = {
            "predictions": {
                "Year 1": None,
                "Year 2": None,
                "Year 3": None,
                "Year 4": None,
                "Year 5": None
            },
            'metadata': {
                "patientID": None
            }
        }

        self.img_frame = tk.Frame(self.window, bd=2, relief='groove',)
        self.img_btn_frame = tk.Frame(self.window, height=40)
        self.data_frame = tk.Frame(self.window, width=150)
        self.upload_frame = tk.Frame(self.window, width=150, height=80)
        self.build_frames()

        self.img = tk.Canvas(self.img_frame, width=400, height=400)
        self.build_img_widget()

        self.data_text = tk.Text(self.data_frame, height=8, width=20, bd=2, relief='groove', state='disabled', font=('Arial', 15), wrap='word')
        self.build_data_widget()
        self.show_data()

        self.left_btn = tk.Button(self.img_btn_frame, width=5, text='<<', font=('Arial', 15), command=self.prev_img)
        self.mid_text = tk.Label(self.img_btn_frame,  width=12, bg='gray', fg='white', relief='sunken', text=str(self.i_img), font=('Arial', 15))
        self.right_btn = tk.Button(self.img_btn_frame, width=5, text='>>', font=('Arial', 15), command=self.next_img)
        self.build_img_button_widget()

        self.file_list = tk.Text(self.upload_frame, height=4, width=20, bd=2, relief='groove', state='disabled', font=('Arial', 15), wrap='none')
        self.open_btn = tk.Button(self.upload_frame, width=10, text='Open Files...', font=('Arial', 15), command=self.open_files)
        self.upload_btn = tk.Button(self.upload_frame, width=5, text='Upload', font=('Arial', 15), command=self.upload_files)
        self.build_upload_wdiget()

    def run(self):
        self.window.mainloop()

    def init_window(self):
        self.window.geometry('800x600')
        self.window.minsize(800, 600)
        self.window.maxsize(800, 600)

        self.window.rowconfigure(0, weight=5)
        self.window.rowconfigure(1, weight=1)

        for i in range(3):
            self.window.columnconfigure(i, weight=1)

    def build_frames(self):
        self.img_frame.grid(row=0, column=0, rowspan=2, columnspan=3, sticky='nsew', padx=20, pady=20)
        self.img_frame.rowconfigure(0, weight=1)
        self.img_frame.columnconfigure(0, weight=1)

        self.data_frame.grid(row=0, column=3, rowspan=2, sticky='nsew', padx=20, pady=20)
        self.img_frame.rowconfigure(0, weight=1)
        self.img_frame.columnconfigure(0, weight=1)

        self.img_btn_frame.grid(row=2, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)
        self.img_btn_frame.rowconfigure(0, weight=1)
        self.img_btn_frame.columnconfigure(0, weight=1)
        self.img_btn_frame.columnconfigure(2, weight=1)

        self.upload_frame.grid(row=1, column=3, rowspan=2, sticky='sew', padx=20, pady=5)
        self.upload_frame.rowconfigure(0, weight=1)
        self.upload_frame.rowconfigure(1, weight=1)
        self.upload_frame.columnconfigure(0, weight=1)

    def build_img_widget(self):
        self.img.grid(row=0, column=0, sticky='nsew')

    def build_data_widget(self):
        self.data_text.grid(row=0, column=0)

    def build_img_button_widget(self):
        self.left_btn.grid(row=0, column=0, sticky='e', pady=10)
        self.mid_text.grid(row=0, column=1, padx=20, pady=10)
        self.right_btn.grid(row=0, column=2, sticky='w', pady=10)

    def build_upload_wdiget(self):
        self.file_list.grid(row=0, column=0, columnspan=2, sticky='ew')
        self.open_btn.grid(row=1, column=0, sticky='ne', padx=5, pady=10)
        self.upload_btn.grid(row=1, column=1, sticky='nw', padx=5, pady=10)

    def prev_img(self):
        if self.i_img > 1:
            self.i_img -= 1
            self.show_img()

    def next_img(self):
        if self.i_img < len(self.imgs):
            self.i_img += 1
            self.show_img()

    def show_img(self):
        img = self.imgs[self.i_img-1]
        self.img.create_image(20, 20, anchor='nw', image=img)
        self.mid_text.config(text='{} / {}'.format(self.i_img, len(self.imgs)))

    def show_data(self):
        text = " Patient ID: {}\n\nPredictions:\n     Year 1: {}\n     Year 2: {}\n     Year 3: {}\n     Year 4: {}\n     Year 5: {}".format(
            self.data['metadata']['patientID'], self.data['predictions']['Year 1'], self.data['predictions']['Year 2'],
            self.data['predictions']['Year 3'], self.data['predictions']['Year 4'], self.data['predictions']['Year 5']
        )
        print(text)
        self.data_text.configure(state='normal')
        self.data_text.delete("1.0", tk.END)
        self.data_text.insert(tk.END, text)
        self.data_text.configure(state='disabled')

    def set_file_list(self, text):
        self.file_list.configure(state='normal')
        self.file_list.delete("1.0", tk.END)
        self.file_list.insert(tk.END, text)
        self.file_list.configure(state='disabled')

    def open_files(self):
        files = fd.askopenfiles(
            parent=self.window,
            title='Open a File',
            initialdir='./',
            filetypes=[('text files', '*.dcm')]
        )

        self.filenames = [file.name for file in files]
        text = '\n'.join([fn.split('/')[-1] for fn in self.filenames])
        self.set_file_list(text)

        images = []
        for fn in self.filenames:
            image_path = tempfile.NamedTemporaryFile(suffix='.png').name
            image = dicom_to_image_dcmtk(fn, image_path)
            image = image.resize((400, 400), Image.ANTIALIAS)
            images.append(ImageTk.PhotoImage(image=image))

        self.imgs = images
        self.i_img = 1
        self.show_img()

    def upload_files(self):
        self.api.get_files(self.filenames)
        self.data = self.api.consume_mirai()
        self.show_data()


class API:
    def __init__(self, api_root, port):
        self.api_root = api_root
        self.port = port

        self.files = []

    def get_files(self, files):
        """Builds the file array for an HTTP form request.
        """
        dicom_files = []
        for file in files:
            if file.endswith('.dcm'):
                dicom_files.append(('dicom', open(file, 'rb')))

        self.files = dicom_files

    def consume_mirai(self):
        files_endpoint = "{}/dicom/files".format(self.api_root)
        data = {"metadata": {"patientID": "001"}}  # required data input, but can be empty

        r = requests.post(url=files_endpoint, data={'data': json.dumps(data)}, files=self.files)

        return r.json()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', default="http://localhost")
    parser.add_argument('-p', default=5000)

    args = parser.parse_args()

    api_url = "{}:{}".format(args.server, args.p)
    api = API(api_url, args.p)
    app = App(api)
    app.run()
    # app.get_files([
    #     './mirai_demo_data/ccl1.dcm', './mirai_demo_data/ccr1.dcm',
    #     './mirai_demo_data/mlol2.dcm', './mirai_demo_data/mlor2.dcm'
    # ])
    # print(app.consume_mirai())
