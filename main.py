# Dependencies
import streamlit as st
import os
from bs4 import BeautifulSoup
import requests
import google.generativeai as genai
from PIL import Image

# Define url to the website
web_monkey = 'http://www.jigokudani-yaenkoen.co.jp'

# Define the API KEY to access Gemini models
genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])

# Define the prompt to be used for Gemini Pro Vision
prompt = """
Analyze the provided image. The goal is to detect the presence of monkeys.
If there are monkeys in the image, respond True.
Otherwise, respond False.
You should format your response as a binary.
"""

# Dictionnary used to convert the selected timeslot
dict_time = {'8am':'08', '9am':'09', '10am':'10', '11am':'11', '12pm':'12',
             '1pm':'13', '2pm':'14', '3pm':'15', '4pm':'16', '5pm':'17'}


def get_image(day, time):
    """
    This function retrieves the image(s) for the selected day and time.
    :param day: 'day0' for today, 'day1' for yesterday
    :param time: '08', '09', ..., '17'
    :return: the url(s) to the image(s),
             the number of image(s) retrieved (should be 1 ideally),
             the presence of the correct title as a binary.
    """
    # Start by completing the url
    url_ = '{}/livecam/monkey/{}/{}/main.htm'.format(web_monkey, day, time)

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
    base_ = '{}/livecam/monkey/{}/{}/'.format(web_monkey, day, time)
    url_imgs = [base_ + img['src'] for img in img_tags]
    num_imgs = len(url_imgs)

    return url_imgs, num_imgs, title_bin


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


def main():
    st.title("Welcome to a Jigokudani Yaen-Koen monkey detector!")
    st.markdown('---')
    st.write('')

    # Load model
    with st.spinner(text="Gemini model loading..."):
        model = load_gemini_vision()
        if model:
            st.info('Gemini Pro Vision successfully connected!')
        else:
            st.warning('Gemini Pro Vision unavailable, working on a fix...')

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
        if model:
            if st.button('Detect for today', type='primary'):
                st.session_state.body_button = 'Today'
        else:
            st.button('Detect for today', disabled=True)
    with col3:
        if model:
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
        select_day = 'day0'
        selected_time_today = st.selectbox('Select the timeslot:',
                                           ['9am', '10am', '11am', '12pm', '1pm', '2pm', '3pm', '4pm'],
                                           index=None,
                                           placeholder='Please select...',
                                           key='time_today')
        st.write('')
        today_button = st.button('Run the summary')
        if today_button:
            st.write('')
            if selected_time_today:
                url_imgs, num_imgs, title_bin = get_image(day=select_day,
                                                          time=dict_time[selected_time_today])
            else:
                st.warning('No timeslot selected, showing for 9am.')
                url_imgs, num_imgs, title_bin = get_image(day=select_day)
            # If there is a "live" photo:
            if title_bin:
                if num_imgs == 1:
                    st.success('Correctly fetched the image.')
                else:
                    st.warning('Fetched more than one image, proceed with caution on the output!')
                # Run the model against the provided image
                with st.spinner("Analyzing the photo..."):
                    response = model.generate_content(
                        [prompt, Image.open(requests.get(url_imgs[0], stream=True).raw)], stream=True)
                    response.resolve()
                # If the model returns 'True' there are monkeys in the photo
                if response.text.strip() == 'True':
                    st.balloons()
                    st.write('There were monkeys at the selected time!')
                # If  the model returns 'False' there are no monkeys in the photo
                elif response.text.strip() == 'False':
                    st.write("""
                    Monkeys were not there at the selected time.\n
                    Maybe they returned to the mountain?\n
                    Please double-check with the photo:
                    """)
                # Issue with the response from the model (did not return 'True'/'False'
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
    # Menu for Yesterday
    elif st.session_state.body_button == 'Yest':
        select_day = 'day1'
        selected_time_yest = st.selectbox('Select the timeslot:',
                                          ['9am', '10am', '11am', '12pm', '1pm', '2pm', '3pm', '4pm'],
                                          index=None,
                                          placeholder='Please select...',
                                          key='time_yesterday')
        st.write('')
        yest_button = st.button('Run the summary')
        if yest_button:
            st.write('')
            if selected_time_yest:
                url_imgs, num_imgs, _ = get_image(day=select_day,
                                                  time=dict_time[selected_time_yest])
            else:
                st.warning('No timeslot selected, showing for 9am.')
                url_imgs, num_imgs, _ = get_image(day=select_day)
            if num_imgs == 1:
                st.success('Correctly fetched the image.')
            else:
                st.warning('Fetched more than one image, proceed with caution on the output!')
            # Run the model against the provided image
            with st.spinner("Analyzing the photo..."):
                response = model.generate_content(
                    [prompt, Image.open(requests.get(url_imgs[0], stream=True).raw)], stream=True)
                response.resolve()
            # If the model returns 'True' there are monkeys in the photo
            if response.text.strip() == 'True':
                st.balloons()
                st.write('There were monkeys at the selected time!')
            # If  the model returns 'False' there are no monkeys in the photo
            elif response.text.strip() == 'False':
                st.write("""
                Monkeys were not there at the selected time.\n
                Maybe they returned to the mountain?\n
                Please double-check with the photo:
                """)
            # Issue with the response from the model (did not return 'True'/'False'
            else:
                st.write("""
                Issue with the model's answer. Please rerun it.\n
                Sorry for the inconvenience.\n
                Here's the photo for you to check:
                """)
            st.write('')
            st.image(url_imgs[0])

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

