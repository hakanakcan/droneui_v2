from pathlib import Path
import json
import mysql.connector
import os
import cv2
from ultralytics import YOLO
from tkinter import Tk, Canvas, Button, PhotoImage, filedialog, Label, Frame

renk_kodlari = {
    "construction-machine": (0, 255, 255),
    "rescue-team": (255, 255, 0),
    "collapsed": (0, 0, 255),
    "solid": (0, 255, 0),
    "damaged": (0, 128, 255),
    "tilted": (0, 64, 255),
}

def getAddress(longitude, latitude):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Hakanakcan123",
        database="project_1",
        charset='utf8'
    )

    if mydb.is_connected():
        print("Baglanti basarili!")

    mycursor = mydb.cursor()

    mycursor.execute("SELECT Mahalle FROM mahallerler WHERE Longitude_1 <= %s AND Longitude_end >= %s AND Latitude_1 <= %s AND Latitude_end >= %s LIMIT 1", 
                     (longitude, longitude, latitude, latitude))
    
    mahalle_row = mycursor.fetchone()
    if mahalle_row:
        mahalle_adi = mahalle_row[0]
        print("Mahalle:", mahalle_adi)
        mycursor.execute("SELECT cok_agir_hasarli, agir_hasarli,orta_hasarli,hafif_hasarli FROM hasar_tahminleri WHERE mahalle_adi = %s", (mahalle_adi,))
        hasar_tahminleri = mycursor.fetchall()
        mycursor.execute("SELECT can_kaybi_sayisi, agir_yarali_sayisi,hastanede_tedavi_sayisi,hafif_yarali_sayisi FROM yaralanma_tahminleri WHERE mahalle_adi = %s", (mahalle_adi,))
        yaralanma_tahminleri = mycursor.fetchall()
        
        return mahalle_adi, hasar_tahminleri, yaralanma_tahminleri
    else:
        print("Mahalle bulunamadi.")

    mycursor.close()
    mydb.close()

def browse_video_file():
    file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi"), ("All files", "*.*")])
    if file_path:
        process_video_file(file_path)
    print("Selected video file:", file_path)

def browse_location_file():
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    return file_path

def process_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)

    flight_array = []
    data_list = data['exchange']['message']['flight_logging']['flight_logging_items']
    
    for row in data_list:
        flight_array.append(row)

    general_lon = 0.0
    general_lat = 0.0

    for row in flight_array:
        first_three_elements = row[1:3] 
        general_lon += row[1]
        general_lat += row[2]
        
    general_lon = general_lon/len(flight_array)
    general_lat = general_lat/len(flight_array)
    result = getAddress(general_lon, general_lat)
    print(result)
    display_results(result)

def process_video_file(video_path):
    BASE_DIR = 'C:/Users/Hakca/OneDrive/Belgeler/Projetest'
    VIDEOS_DIR = os.path.join(BASE_DIR, 'videos')
    RUNS_DIR = os.path.join(BASE_DIR, 'runs')

    video_path_out = os.path.join(VIDEOS_DIR, 'processed_video.mp4')

    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    H, W, _ = frame.shape
    out = cv2.VideoWriter(video_path_out, cv2.VideoWriter_fourcc(*'MP4V'), int(cap.get(cv2.CAP_PROP_FPS)), (W, H))

    model_path = os.path.join(RUNS_DIR, 'detect', 'yolov8_96acc', 'weights', 'last.pt')

    model = YOLO(model_path)

    threshold = 0.5

    while ret:
        results = model(frame)[0]

        for result in results.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = result

            if score > threshold:
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), renk_kodlari[results.names[int(class_id)]], 4)
                cv2.putText(frame, results.names[int(class_id)].upper(), (int(x1), int(y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.3, renk_kodlari[results.names[int(class_id)]], 3, cv2.LINE_AA)

        out.write(frame)
        ret, frame = cap.read()

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"Processed video saved to {video_path_out}")

def display_results(results):
    mahalle_adi, hasar_tahminleri, yaralanma_tahminleri = results

    for widget in results_frame.winfo_children():
        widget.destroy()

    headers = ["Kategori", "Değer"]
    for i, header in enumerate(headers):
        label = Label(results_frame, text=header, font=("Inter", 12, "bold"), bg="#FFFFFF")
        label.grid(row=0, column=i, padx=10, pady=5)

    Label(results_frame, text="Mahalle Adı", font=("Inter", 12), bg="#FFFFFF").grid(row=1, column=0, padx=10, pady=5)
    Label(results_frame, text=mahalle_adi, font=("Inter", 12), bg="#FFFFFF").grid(row=1, column=1, padx=10, pady=5)

    hasar_labels = ["Çok Ağır Hasarlı", "Ağır Hasarlı", "Orta Hasarlı", "Hafif Hasarlı"]
    for i, hasar in enumerate(hasar_tahminleri[0], start=5):
        Label(results_frame, text=hasar_labels[i-5], font=("Inter", 12), bg="#FFFFFF").grid(row=i, column=0, padx=10, pady=5)
        Label(results_frame, text=hasar, font=("Inter", 12), bg="#FFFFFF").grid(row=i, column=1, padx=10, pady=5)

    yaralanma_labels = ["Can Kaybı Sayısı", "Ağır Yaralı Sayısı", "Hastanede Tedavi Sayısı", "Hafif Yaralı Sayısı"]
    for i, yaralanma in enumerate(yaralanma_tahminleri[0], start=9):
        Label(results_frame, text=yaralanma_labels[i-9], font=("Inter", 12), bg="#FFFFFF").grid(row=i, column=0, padx=10, pady=5)
        Label(results_frame, text=yaralanma, font=("Inter", 12), bg="#FFFFFF").grid(row=i, column=1, padx=10, pady=5)

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"C:/Users/Hakca/OneDrive/Masaüstü/pythonstuff/UI-For-Drone-Project/assets/frame0")

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

window = Tk()
window.geometry("850x700")
window.configure(bg="#FFFFFF")

canvas = Canvas(
    window,
    bg="#FFFFFF",
    height=768,
    width=1024,
    bd=0,
    highlightthickness=0,
    relief="ridge"
)
canvas.place(x=0, y=0)

image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
image_1 = canvas.create_image(
    512.0,
    384.0,
    image=image_image_1
)

def on_button_1_click():
    location = browse_location_file()
    if location:
        process_json_file(location)

button_image_1 = PhotoImage(file=relative_to_assets("button_1.png"))
button_1 = Button(
    image=button_image_1,
    borderwidth=0,
    highlightthickness=0,
    command=on_button_1_click,
    relief="flat"
)
button_1.place(x=8.0, y=300.0, width=155.0, height=30.0)

canvas.create_text(
    260.0,
    23.0,
    anchor="nw",
    text="Collapsed Building Analysis",
    fill="#FFFFFF",
    font=("Inter BlackItalic", 30 * -1)
)

button_image_2 = PhotoImage(file=relative_to_assets("button_2.png"))
button_2 = Button(
    image=button_image_2,
    borderwidth=0,
    highlightthickness=0,
    command=browse_video_file,
    relief="flat"
)
button_2.place(x=8.0, y=600.0, width=100.0, height=30.0)

results_frame = Frame(window, bg="#FFFFFF")
results_frame.place(x=350, y=170, anchor="nw")

canvas.create_text(
    430.0,
    120.0,
    anchor="nw",
    text="Estimated Results",
    fill="#FFFFFF",
    font=("Inter BlackItalic", 24 * -1)
)

button_image_4 = PhotoImage(file=relative_to_assets("button_4.png"))
button_4 = Button(
    image=button_image_4,
    borderwidth=0,
    highlightthickness=0,
    command=browse_video_file,
    relief="flat"
)
button_4.place(x=8.0, y=200.0, width=154.52996826171875, height=30.0)

window.resizable(False, False)
window.mainloop()
