from chalice import Chalice
from multiprocessing import Process, Pipe
import cv2

app = Chalice(app_name='SaveBears-GlacierChecking')


@app.route('/')
def index():
    data = []

    process_list = []
    parent_connections = []

    for i in range(4):
        # Lambda only supports Pipe, not Queue or Pool
        parent_conn, child_conn = Pipe()
        parent_connections.append(parent_conn)

        process = Process(target=glacier_checking, args=(i * 10, (i + 1) * 10, child_conn))
        process.start()
        process_list.append(process)

    for process in process_list:
        process.join()

    for parent_connection in parent_connections:
        data.append(parent_connection.recv())

    return data


def glacier_checking(prev, now, conn):
    status = dict()

    mp4 = cv2.VideoCapture(
        "https://storage.googleapis.com/earthengine-timelapse/2020/curated/mp4/src/columbia-glacier-alaska.mp4")

    width = mp4.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = mp4.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print("Video resolution: %sx%s" % (int(width), int(height)))

    frame_count = int(mp4.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_count < now:
        now = frame_count - 1

    mp4.set(cv2.CAP_PROP_POS_FRAMES, now)
    (valid, image) = mp4.read()  # current frame

    # to reduce calculation time but not effective
    image = cv2.resize(image, dsize=(1280, 720), interpolation=cv2.INTER_AREA)

    now_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # mean pixel intensity of current frame
    now_mean = now_image.mean()

    mp4.set(cv2.CAP_PROP_POS_FRAMES, prev)
    (valid, image) = mp4.read()  # current frame

    # to reduce calculation time but not effective
    image = cv2.resize(image, dsize=(1280, 720), interpolation=cv2.INTER_AREA)

    past_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # mean pixel intensity of current frame
    past_mean = past_image.mean()

    # Calculate diff between last frame and current frame
    difference = past_mean - now_mean
    abs_difference = abs(difference)

    start_year = 1984 + prev
    end_year = 1984 + now
    image_name = str(start_year) + str(end_year)

    changed_image = cv2.subtract(past_image, now_image)
    # cv2.imwrite(image_name + '.jpg', changed_image)

    print("Detected movement of size %s" % abs_difference)

    ratio = int((abs_difference / past_mean) * 100)

    if difference > 0:
        status['Glacier'] = "Retreated"
        status['Changed Ratio'] = ratio
    else:
        status['Glacier'] = "Recovered"
        status['Changed Ratio'] = ratio

    mp4.release()

    conn.send(status)
    conn.close()