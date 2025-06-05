import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from fpdf import FPDF
from io import BytesIO
from PIL import Image
import base64

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLAMA_MODEL = os.getenv("LLAMA_MODEL")
VISION_MODEL = os.getenv("VISION_MODEL")

# App Title
st.set_page_config(page_title="Smart Recipe App", layout="wide")
st.title("🍽️ Smart Recipe Generator")
st.markdown("Upload an image of food or ingredients, or search by dish name to get custom recipes!")

# Session state for storing results
if "last_recipe" not in st.session_state:
    st.session_state["last_recipe"] = ""

# --- TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📸 Dish Detection", 
    "🧪 Ingredients Detection", 
    "🔍 Generate Recipes", 
    "🍽️ Get Dish Recipe", 
    "📄 Export"
])

# --- TAB 1: DISH DETECTION (UPLOAD IMAGE OF A DISH) ---
with tab1:
    st.subheader("Upload an image of a dish")
    uploaded_file = st.file_uploader("Choose a dish image file", type=["jpg", "jpeg", "png"], key="dish_upload")

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Dish Image", use_column_width=True)

        # Convert image to base64
        img_bytes = BytesIO(uploaded_file.getvalue()).getbuffer()
        encoded_image = base64.b64encode(img_bytes).decode("utf-8")
        image_url = f"data:image/jpeg;base64,{encoded_image}"

        if st.button("Detect Dish & Generate Recipe"):
            with st.spinner("Analyzing image..."):

                # Step 1: Use vision model to detect dish name
                try:
                    response = requests.post(
                        url="https://openrouter.ai/api/v1/chat/completions", 
                        headers={
                            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        data=json.dumps({
                            "model": VISION_MODEL,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": "What dish or food is shown in this image?"},
                                        {"type": "image_url", "image_url": {"url": image_url}}
                                    ]
                                }
                            ],
                            "temperature": 0.5,
                            "max_tokens": 300
                        })
                    )

                    result = response.json()
                    if result.get("choices") and len(result["choices"]) > 0:
                        dish_name = result["choices"][0]["message"]["content"]

                        st.success("Detected Dish:")
                        st.write(dish_name)

                        # Step 2: Use LLaMA to generate recipe for the detected dish
                        prompt = f"""
You are an expert chef. Based on this dish name, generate a full recipe.

Dish Name: {dish_name}

Generate:
1. Name of the dish
2. List of required ingredients
3. Step-by-step instructions
4. Estimated cooking time
5. Dietary notes (e.g., vegan, gluten-free if applicable)

Make sure the recipe is safe to eat and matches the detected dish.
"""

                        try:
                            response = requests.post(
                                url="https://openrouter.ai/api/v1/chat/completions", 
                                headers={
                                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                                    "Content-Type": "application/json"
                                },
                                data=json.dumps({
                                    "model": LLAMA_MODEL,
                                    "messages": [{"role": "user", "content": prompt}],
                                    "temperature": 0.7,
                                    "max_tokens": 1200
                                })
                            )

                            data = response.json()
                            recipe_text = data["choices"][0]["message"]["content"]
                            st.session_state["last_recipe"] = recipe_text

                            st.subheader("Generated Recipe Based on Dish Image:")
                            st.markdown(recipe_text)

                        except Exception as e:
                            st.error(f"Error generating recipe: {str(e)}")

                    else:
                        st.warning("Could not identify dish from image.")

                except Exception as e:
                    st.error(f"Error analyzing image: {str(e)}")

# --- TAB 2: INGREDIENTS DETECTION (UPLOAD IMAGE OF INGREDIENTS) ---
with tab2:
    st.subheader("Upload an image of ingredients")
    uploaded_file = st.file_uploader("Choose ingredients image file", type=["jpg", "jpeg", "png"], key="ingredient_upload")

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Ingredients", use_column_width=True)

        # Convert image to base64
        img_bytes = BytesIO(uploaded_file.getvalue()).getbuffer()
        encoded_image = base64.b64encode(img_bytes).decode("utf-8")
        image_url = f"data:image/jpeg;base64,{encoded_image}"

        if st.button("Detect Ingredients & Generate Recipes"):
            with st.spinner("Analyzing image..."):

                # Step 1: Use vision model to detect ingredients
                try:
                    response = requests.post(
                        url="https://openrouter.ai/api/v1/chat/completions", 
                        headers={
                            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        data=json.dumps({
                            "model": VISION_MODEL,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": "List all visible ingredients in this image."},
                                        {"type": "image_url", "image_url": {"url": image_url}}
                                    ]
                                }
                            ],
                            "temperature": 0.5,
                            "max_tokens": 300
                        })
                    )

                    result = response.json()
                    if result.get("choices") and len(result["choices"]) > 0:
                        ingredients = result["choices"][0]["message"]["content"]
                        st.session_state["detected_ingredients"] = ingredients

                        st.success("Detected Ingredients:")
                        st.write(ingredients)

                        # Step 2: Use LLaMA to generate recipes from detected ingredients
                        dietary_preferences = ["Vegetarian", "Vegan", "Gluten-Free", "Low-Carb"]
                        preferences_str = ", ".join(dietary_preferences)

                        prompt = f"""
You are an expert chef. Based on these ingredients, generate 3 creative recipes.

Ingredients: {ingredients}
Dietary Preferences: {preferences_str}

For each recipe:
1. Name
2. Ingredients
3. Instructions
4. Cooking time
5. Substitution suggestions

Ensure recipes match dietary preferences and are safe to eat.
"""

                        try:
                            response = requests.post(
                                url="https://openrouter.ai/api/v1/chat/completions", 
                                headers={
                                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                                    "Content-Type": "application/json"
                                },
                                data=json.dumps({
                                    "model": LLAMA_MODEL,
                                    "messages": [{"role": "user", "content": prompt}],
                                    "temperature": 0.7,
                                    "max_tokens": 1200
                                })
                            )

                            data = response.json()
                            recipe_text = data["choices"][0]["message"]["content"]
                            st.session_state["last_recipe"] = recipe_text

                            st.subheader("Recipes You Can Make with These Ingredients:")
                            st.markdown(recipe_text)

                        except Exception as e:
                            st.error(f"Error generating recipes: {str(e)}")

                    else:
                        st.warning("No ingredients found in the image.")

                except Exception as e:
                    st.error(f"Error analyzing image: {str(e)}")

# --- TAB 3: GENERATE RECIPES FROM TEXT INPUT ---
with tab3:
    st.subheader("Generate Recipes from Ingredients")
    ingredients = st.text_area("Available Ingredients", value=st.session_state.get("detected_ingredients", ""))
    dietary_preferences = st.multiselect(
        "Select dietary preferences:",
        ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Low-Carb", "Keto", "Paleo"]
    )
    preferences_str = ", ".join(dietary_preferences) if dietary_preferences else "No specific dietary preferences"

    if st.button("Generate Recipes"):
        if not ingredients.strip():
            st.error("Please enter at least one ingredient.")
        else:
            prompt = f"""
You are an expert chef and assistant. Based on these ingredients and dietary preferences, generate 3 recipes.

Ingredients: {ingredients}
Dietary Preferences: {preferences_str}

For each recipe:
1. Name of the dish
2. List of ingredients needed
3. Step-by-step instructions
4. Estimated cooking time
5. Notes on possible substitutions if ingredients are missing

Ensure all recipes match dietary preferences. If certain core ingredients are missing, adjust the recipe safely.
"""

            try:
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions", 
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    data=json.dumps({
                        "model": LLAMA_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 1200
                    })
                )
                data = response.json()
                recipe_text = data["choices"][0]["message"]["content"]
                st.session_state["last_recipe"] = recipe_text

                st.subheader("Here are your 3 recipe suggestions:")
                st.markdown(recipe_text)

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# --- TAB 4: GET RECIPE BY DISH NAME ---
with tab4:
    st.subheader("Get Recipe by Dish Name")
    dish_name = st.text_input("Enter the name of the dish you want the recipe for:", "")
    ingredients_override = st.text_input("What ingredients do you have available? (Optional)", "")

    if st.button("Get Recipe"):
        if not dish_name.strip():
            st.error("Please enter a dish name.")
        else:
            prompt = f"""
You are an expert chef and assistant. Provide a detailed recipe for '{dish_name}'.

Available ingredients: {ingredients_override or 'Assume full access'}

If key ingredients are missing, morph the recipe safely using common substitutes.
Always provide 3 variations of the recipe:
1. Original version
2. Adapted version using available ingredients
3. Alternate dish that can be made with similar flavor or theme

Include:
- Ingredients needed
- Step-by-step instructions
- Estimated cooking time
- Dietary notes if applicable
- Safety note if substitutions were made

Make sure none of the recipes would harm someone eating them.
"""

            try:
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions", 
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    data=json.dumps({
                        "model": LLAMA_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 1200
                    })
                )
                data = response.json()
                recipe_text = data["choices"][0]["message"]["content"]
                st.session_state["last_recipe"] = recipe_text

                st.subheader(f"Recipes related to '{dish_name}':")
                st.markdown(recipe_text)

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# --- TAB 5: EXPORT TO PDF ---
with tab5:
    st.subheader("Export Your Recipes")
    if st.session_state["last_recipe"]:
        st.markdown(st.session_state["last_recipe"])

        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 12)
                self.cell(0, 10, 'Generated Recipes', align='C', ln=1)
                self.ln(5)

        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        for line in st.session_state["last_recipe"].split('\n'):
            pdf.cell(0, 10, txt=line, ln=1)

        pdf_output = "recipes_export.pdf"
        pdf.output(pdf_output)

        with open(pdf_output, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name="recipes_export.pdf", mime="application/pdf")
    else:
        st.info("Generate some recipes first before exporting.")