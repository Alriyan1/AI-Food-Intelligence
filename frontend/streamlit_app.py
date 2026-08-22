import streamlit as st
import requests
import base64
import json
from PIL import Image
import io
from typing import Dict,Any,List,Optional
from datetime import datetime

st.set_page_config(
    page_title="FoodVision AI",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = st.secrets.get('API_Base_URL','http://localhost:8000')

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .food-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        color: white;
    }
    .nutrition-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #2E86AB;
    }
    .recipe-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    .disclaimer {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 15px;
        margin: 20px 0;
        font-size: 0.9rem;
    }
    .chat-message {
        padding: 10px 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .user-message {
        background: #007bff;
        color: white;
        margin-left: 20%;
    }
    .assistant-message {
        background: #f1f1f1;
        color: #333;
        margin-right: 20%;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #2E86AB;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

if 'food_analysis' not in st.session_state:
    st.session_state.food_analysis = None
if "nutrition" not in st.session_state:
    st.session_state.nutrition = None
if 'recipes' not in st.session_state:
    st.session_state.recipes = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = {
        "diet": "non_vegetarian",
        "goal": "maintenance",
        "cuisine": "any",
        "max_calories": None,
        "max_prep_time": None,
        "allergies": []
    }


def encode_image_to_base64(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered,format='JPEG',quality=85)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def analyze_food_image(image: Image.Image) -> Dict[str,Any]:

    try:
        image_bytes = io.BytesIO()
        image.save(image_bytes,format='JPEG',quality=85)
        image_bytes.seek(0)

        files = {'image': ('image.jpg',image_bytes,'image/jpeg')}
        response = requests.post(
            f"{API_BASE_URL}/api/analyze-food",
            files=files,
            timeout=120
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            st.error(response.text)
            return None

    except requests.exceptions.Timeout:
        st.error("Request timeout. Please try again with a smaller image.")
        return None
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        return None

def generate_recipes_api(
        detected_foods: List[str],
        nutrition: Dict[str,Any],
        preferences: Dict[str,Any],
        num_recipes: int=3
) -> Optional[Dict[str,Any]]:

    try:
        request_data = {
            'detected_foods':detected_foods,
            'nutrition': nutrition,
            'preferences': preferences,
            'num_recipes': num_recipes
        }

        response = requests.post(
            f"{API_BASE_URL}/api/generate-recipes",
            json=request_data,
            timeout=60
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Recipe generation failed: {response.status_code}")
            return None

    except Exception as e:
        st.error(f"Recipe generation error: {str(e)}")
        return None


def chat_with_assistant(
    message: str,
    food_analysis: Optional[Dict] = None,
    nutrition: Optional[Dict] = None,
    preferences: Optional[Dict] = None,
    history: Optional[List[Dict]] = None
) -> Optional[Dict[str, Any]]:
    try:
        request_data = {
            "message": message,
            "food_analysis": food_analysis,
            "nutrition": nutrition,
            "preferences": preferences,
            "conversation_history": history or []
        }

        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json=request_data,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None

    except Exception as e:
        st.error(f"Chat error: {str(e)}")
        return None


def display_preferences_sidebar()->None:

    with st.sidebar:
        st.header("⚙️ Your Preferences")

        st.subheader('Diet')
        diet = st.selectbox(
            'Dietary Preference',
            ['vegetarian','non-vegetarian','vegan','eggetarian'],
            index=1,
            key='diet_select'
        )

        st.subheader("Goal")
        goal = st.selectbox(
            "Fitness Goal",
            ['weight_loss','muscle_gain','maintenance'],
            index=2,
            key='goal_select'
        )

        st.subheader('Cuisine')
        cuisine = st.selectbox(
            "Cuisine Preference",
            ["any", "indian", "chinese", "italian", "mexican"],
            index=0,
            key="cuisine_select"
        )


        st.subheader("Calories")
        max_calories = st.number_input(
            "Max Calories per Meal",
            min_value=200,
            max_value=1500,
            value=600,
            step=50,
            key="calories_input"
        )

        st.subheader("Time")
        max_prep_time = st.number_input(
            "Max Prep Time (minutes)",
            min_value=5,
            max_value=120,
            value=30,
            step=5,
            key="prep_time_input"
        )

        st.subheader("Allergies")
        allergies = st.multiselect(
            "Select Allergies",
            ["peanuts", "tree nuts", "dairy", "eggs", "soy", "wheat", "fish", "shellfish"],
            key="allergies_select"
        )

        st.session_state.user_preferences = {
            "diet": diet,
            "goal": goal,
            "cuisine": cuisine,
            "max_calories": max_calories,
            "max_prep_time": max_prep_time,
            "allergies": allergies
        }

        st.markdown("---")
        st.markdown("""
        ### ℹ️ About FoodVision AI
        FoodVision AI uses computer vision and AI to analyze your food photos and provide nutritional insights.
        
        **⚠️ Important:** Nutritional values are estimates and should not be used for medical purposes.
        """)


def main():
    