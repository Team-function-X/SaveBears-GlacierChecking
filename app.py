from chalice import Chalice
import cv2

app = Chalice(app_name='SaveBears-GlacierChecking')


@app.route('/')
def index():
    result = GlacierChecking()
    return result


def GlacierChecking():
    status = dict()
    
    mp4 = cv2.VideoCapture("https://storage.googleapis.com/earthengine-timelapse/2020/curated/mp4/src/columbia-glacier-alaska.mp4")
            
    width  = mp4.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = mp4.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print ("Video resolution: %sx%s" % (int(width), int(height)))

    # total frame of video
    frame_count = mp4.get(cv2.CAP_PROP_FRAME_COUNT)
    
    mp4.set(cv2.CAP_PROP_POS_FRAMES, frame_count-1)
    (valid, image) = mp4.read() # current frame

    now_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # mean pixel intensity of current frame
    now_mean = now_image.mean()


    mp4.set(cv2.CAP_PROP_POS_FRAMES, 0)
    (valid, image) = mp4.read() # current frame

    past_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # mean pixel intensity of current frame
    past_mean = past_image.mean()


    # Calculate diff between last frame and current frame
    difference = past_mean-now_mean
    abs_difference = abs(difference)
        
    changed_image = cv2.subtract(past_image, now_image)
    #cv2.imwrite('changed.jpg',changed_image)

    print ("Detected movement of size %s" % abs_difference)
    
    ratio = int((abs_difference / past_mean) * 100)
    
    if difference > 0:
      status['Glacier'] = "Retreated"
      status['Changed Ratio'] = ratio
    else:
      status['Glacier'] = "Recovered"
      status['Changed Ratio'] = ratio

    mp4.release()
    
    return status
    