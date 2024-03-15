# Dependencies
import streamlit as st
from bs4 import BeautifulSoup
import requests
import google.generativeai as genai
from PIL import Image
import datetime

# Define url to the website
web_monkey = 'https://jigokudani-yaenkoen.co.jp'

# Define the API KEY to access Gemini models
genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])

# Define the prompt to be used for Gemini Pro Vision
prompt = """
Analyze the provided image. The goal is to detect the presence of monkeys.
If there are monkeys in the image, respond True.
Otherwise, respond False.
You should format your response as a binary.

Example 1: True
Example 2: False
"""

# Dictionnary used to convert the selected timeslot
dict_time = {'8am': '08', '9am': '09', '10am': '10', '11am': '11', '12pm': '12',
             '1pm': '13', '2pm': '14', '3pm': '15', '4pm': '16', '5pm': '17'}


def curr_month():
    """
    Returns the current month on call.
    :return: current month as int.
    """
    curr_mth = datetime.datetime.now().month

    return curr_mth


def which_cam_up():
    """
    This function checks if the cameras are working or not,
    by checking if there is content for the first photo of the day.
    :return: 'live' is livecam is up, 'live2' if the other one is up,
              None is neither is working.
    """
    # TODO: remove and uncomment when fixed                              -- CURRENT --
    url_live1 = '{}/livecam/monkey/main.htm'.format(web_monkey)
    #url_live1 = '{}/livecam/monkey/index.htm'.format(web_monkey)
    url_live2 = '{}/livecam2/video.php'.format(web_monkey)
    # Check if livecam feed is down
    if requests.get(url_live1).content == b'':
        # Check if livecam2 feed is down
        if requests.get(url_live2).content == b'':
            which_cam = None
        else:
            which_cam = 'live2'
    else:
        which_cam = 'live1'

    return which_cam


def get_image_live1(day, time):
    """
    This function retrieves the image(s) for the selected day and time.
    :param day: 'day0' for today, 'day1' for yesterday
    :param time: '08', '09', ..., '17'
    :return: the url(s) to the image(s),
             the number of image(s) retrieved (should be 1 ideally).
    """
    # Start by completing the url
    # TODO: remove and uncomment when fixed                              -- CURRENT --
    url_ = '{}/livecam/monkey/main.htm'.format(web_monkey)
    #url_ = '{}/livecam/monkey/{}/{}/main.htm'.format(web_monkey, day, time)

    # Extract contents from the url, as a text
    htmldata = requests.get(url_).text

    # Scrap using BeautifulSoup
    soup = BeautifulSoup(htmldata, 'html.parser')

    # Find the title
    title_tags = soup.title.string

    # If there is a photo, the title should be 'JIGOKUDANI-YAENKOEN SVGA-LIVECAM'
    title_bin = title_tags == 'JIGOKUDANI-YAENKOEN SVGA-LIVECAM'

    # Find all the images
    img_tags = soup.find_all('img')

    # Get the url
    #base_ = '{}/livecam/monkey/{}/{}/'.format(web_monkey, day, time)
    base_ = '{}/livecam/monkey/'.format(web_monkey)
    url_imgs = [base_ + img['src'] for img in img_tags]
    num_imgs = len(url_imgs)

    return url_imgs, num_imgs, title_bin


# TODO: find a way to complete function
def get_image_live2():
    """
    This function retrieves the gif for the livecam2.
    :return: the url(s) to the gif,
             the presence of the correct title as a binary.
    """
    # Start by completing the url
    url_ = '{}/livecam2/video.php'.format(web_monkey)

    # Extract contents from the url, as a text
    htmldata = requests.get(url_).text

    # Scrap using BeautifulSoup
    soup = BeautifulSoup(htmldata, 'html.parser')

    # Find all the links
    content = soup.find_all('link')

    # Find all the images
    #img_tags = soup.find_all('img')

    # Get the url
    #base_ = '{}/livecam/monkey/{}/{}/'.format(web_monkey, day, time)
    #url_imgs = [base_ + img['src'] for img in img_tags]
    #num_imgs = len(url_imgs)

    #return url_imgs
    return content


@st.cache_resource
def load_gemini_vision():
    """
    This function loads Gemini Pro Vision if available.
    :return: the model, or None
    """
    model = None
    # First, make sure Gemini Pro Vision is still available
    for m in genai.list_models():
        if m.name == 'models/gemini-pro-vision':
            model = genai.GenerativeModel('gemini-pro-vision')

    return model


def average_on_responses(list_):
    """
    THe goal of this function is to average on the 3 responses from the model.
    If at least 2 times out of 3 the model answered True (meaning it detected monkeys at least 2 times),
    then return True. Otherwise, return False.
    :param list_: List of the 3 responses from the model
    :return: bool_
    """
    # Counts the number of times the model answered True
    count_True = sum([x == 'True' for x in list_])
    # Counts the number of times the model answered False
    count_False = sum([x == 'False' for x in list_])
    # Check that the sum of both is equal to the length of the list
    check_ = (count_True + count_False) == len(list_)
    # If the models answered at least 2 times (out of 3)
    if count_True > 1:
        bool_ = True
    else:
        bool_ = False

    return check_, bool_


def main():
    st.title("Welcome to a Jigokudani Yaen-Koen monkey detector!")
    st.warning("There is currently an issue with the page indexing the photos for the \
               current day and the day before. Timeslot selection are disabled.")
    st.markdown('---')
    st.write('')

    # Check which camera is working:
    cam = which_cam_up()

    # If livecam1 available
    if cam == 'live1':
        # Load model
        with st.spinner(text="Gemini model loading..."):
            model = load_gemini_vision()
            if model is not None:
                st.info('Gemini Pro Vision successfully connected!')
            else:
                st.warning('Gemini Pro Vision unavailable, working on a fix...')
    # TODO: uncomment when get_image_live2() gets fixed
    # Else, if livecam2 available
    #elif cam == 'live2':
        # Load model
        #with st.spinner(text="Gemini model loading..."):
            #model = load_gemini_vision()
            #if model is not None:
                #st.info('Gemini Pro Vision successfully connected!')
            #else:
                #st.warning('Gemini Pro Vision unavailable, working on a fix...')
    # Else, if no cam feed
    else:
        model = None
        st.error('The cameras are down at the moment, please try again later.')

    st.write('')
    # Initialize variable to display the correct body
    if 'body_button' not in st.session_state:
        st.session_state.body_button = 'Home'

    # Define columns to split the buttons
    col1, col2, col3 = st.columns(3)
    # On button click, change the value of the variable
    # If model unavailable, disable the buttons for detection
    with col1:
        if st.button('Homepage', type='primary'):
            st.session_state.body_button = 'Home'
    with col2:
        if (cam is not None) and (model is not None):
            if st.button('Detect for today', type='primary'):
                st.session_state.body_button = 'Today'
        else:
            st.button('Detect for today', disabled=True)
    with col3:
        if (cam is not None) and (model is not None):
            if st.button('Detect for yesterday', type='primary'):
                st.session_state.body_button = 'Yest'
        else:
            st.button('Detect for yesterday', disabled=True)

    # Show the correct body according to the button clicked
    st.write('')
    st.write('')
    # Homepage
    if st.session_state.body_button == 'Home':
        st.write("""
        This app helps in knowing if monkeys have been sighted recently at
        Jigokudani Yaen-Koen at a glance.\n
        Here's the link to the official [website](http://www.jigokudani-yaenkoen.co.jp).\n
        Winter Season and Summer Season have different opening times:\n
        - Winter Season (Nov-Mar): 9am - 4pm
        - Summer Season (Apr-Oct): 8.30am - 5pm\n
        This app is currently designed for Winter Season only.
        """)
    # Menu for Today
    elif st.session_state.body_button == 'Today':
        # If livecam1 up:
        if cam == 'live1':
            select_day = 'day0'
            # TODO: enable back when issue fixed by website (index.htm)
            # Check if Winter
            #if curr_month() in [1, 2, 3, 11, 12]:
                #selected_time_today = st.selectbox('Select the timeslot:',
                                                   #['9am', '10am', '11am', '12pm',
                                                    #'1pm', '2pm', '3pm', '4pm'],
                                                   #index=None,
                                                   #placeholder='Please select...',
                                                   #key='time_today')
            # Else, Summer
            #else:
                #selected_time_today = st.selectbox('Select the timeslot:',
                                                   #['8am', '9am', '10am', '11am', '12pm',
                                                    #'1pm', '2pm', '3pm', '4pm', '5pm'],
                                                   #index=None,
                                                   #placeholder='Please select...',
                                                   #key='time_today')
            st.write('')
            today_button = st.button('Run the summary')
            if today_button:
                st.write('')
                # TODO: enable back when issue fixed by website (index.htm)
                #if selected_time_today:
                    #url_imgs, num_imgs, title_bin = get_image_live1(day=select_day,
                                                                    #time=dict_time[selected_time_today])
                #else:
                    #st.warning('No timeslot selected, showing for 9am.')
                    #url_imgs, num_imgs, title_bin = get_image_live1(day=select_day, time='09')
                url_imgs, num_imgs, title_bin = get_image_live1(day=select_day, time='09')
                # If there is a "live" photo:
                if title_bin:
                    if num_imgs == 1:
                        st.success('Correctly fetched the image.')
                    else:
                        st.warning('Fetched more than one image, proceed with caution on the output!')
                    # Run the model against the provided image
                    with st.spinner("Analyzing the photo..."):
                        response_1 = model.generate_content(
                            [prompt, Image.open(requests.get(url_imgs[0], stream=True).raw)])
                        response_2 = model.generate_content(
                            [prompt, Image.open(requests.get(url_imgs[0], stream=True).raw)])
                        response_3 = model.generate_content(
                            [prompt, Image.open(requests.get(url_imgs[0], stream=True).raw)])
                    check_, avg_resp = average_on_responses([response_1.text.strip(),
                                                             response_2.text.strip(),
                                                             response_3.text.strip()])
                    # If avg_resp is True there are monkeys in the photo
                    if avg_resp:
                        st.write('There were monkeys at the selected time!')
                    # Else, if check_ is True there are no monkeys in the photo
                    elif check_:
                        st.write("""
                        Monkeys were not there at the selected time.\n
                        Maybe they returned to the mountain?\n
                        Please double-check with the photo:
                        """)
                    # Else, there may be issues with the responses from the model
                    else:
                        st.write("""
                        Issue with the model's answer. Please rerun it.\n
                        Sorry for the inconvenience.\n
                        Here's the photo for you to check:
                        """)
                    st.write('')
                    st.image(url_imgs[0])
                # Else, if there is no "live" photo yet:
                else:
                    st.warning('Please try again later, there is no photo available yet.')
        # TODO: uncomment and implement when get_image_live2() gets fixed
        #elif cam == 'live2':
            #st.write('')
            #today_button = st.button('Run the summary')
            #if today_button:
                #st.write('')
                #live2 = get_image_live2()
                #st.write(live2)

    # Menu for Yesterday
    elif st.session_state.body_button == 'Yest':
        # If livecam1 up:
        if cam == 'live1':
            select_day = 'day1'
            # TODO: enable back when issue fixed by website (index.htm)
            # Check if Winter
            #if curr_month() in [1, 2, 3, 11, 12]:
                #selected_time_yest = st.selectbox('Select the timeslot:',
                                                  #['9am', '10am', '11am', '12pm',
                                                   #'1pm', '2pm', '3pm', '4pm'],
                                                  #index=None,
                                                  #placeholder='Please select...',
                                                  #key='time_yest')
            # Else, Summer
            #else:
                #selected_time_yest = st.selectbox('Select the timeslot:',
                                                  #['8am', '9am', '10am', '11am', '12pm',
                                                   #'1pm', '2pm', '3pm', '4pm', '5pm'],
                                                  #index=None,
                                                  #placeholder='Please select...',
                                                  #key='time_yest')
            st.write('')
            yest_button = st.button('Run the summary')
            if yest_button:
                st.write('')
                # TODO: enable back when issue fixed by website (index.htm)
                #if selected_time_yest:
                    #url_imgs, num_imgs, _ = get_image_live1(day=select_day,
                                                            #time=dict_time[selected_time_yest])
                #else:
                    #st.warning('No timeslot selected, showing for 9am.')
                    #url_imgs, num_imgs, _ = get_image_live1(day=select_day, time='09')
                url_imgs, num_imgs, _ = get_image_live1(day=select_day, time='09')
                if num_imgs == 1:
                    st.success('Correctly fetched the image.')
                else:
                    st.warning('Fetched more than one image, proceed with caution on the output!')
                # Run the model against the provided image
                with st.spinner("Analyzing the photo..."):
                    response_1 = model.generate_content(
                        [prompt, Image.open(requests.get(url_imgs[0], stream=True).raw)])
                    response_2 = model.generate_content(
                        [prompt, Image.open(requests.get(url_imgs[0], stream=True).raw)])
                    response_3 = model.generate_content(
                        [prompt, Image.open(requests.get(url_imgs[0], stream=True).raw)])
                check_, avg_resp = average_on_responses([response_1.text.strip(),
                                                         response_2.text.strip(),
                                                         response_3.text.strip()])
                # If avg_resp is True there are monkeys in the photo
                if avg_resp:
                    st.write('There were monkeys at the selected time!')
                # Else, if check_ is True there are no monkeys in the photo
                elif check_:
                    st.write("""
                        Monkeys were not there at the selected time.\n
                        Maybe they returned to the mountain?\n
                        Please double-check with the photo:
                        """)
                # Else, there may be issues with the responses from the model
                else:
                    st.write("""
                        Issue with the model's answer. Please rerun it.\n
                        Sorry for the inconvenience.\n
                        Here's the photo for you to check:
                        """)
                st.write('')
                st.image(url_imgs[0])
        # elif cam == 'live2':


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

