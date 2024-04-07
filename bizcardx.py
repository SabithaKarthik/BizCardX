import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io
import sqlite3


def image_to_text(path):

    input_img = Image.open(path)

    # converting image to array format
    image_arr = np.array(input_img)

    reader = easyocr.Reader(["en"])
    text = reader.readtext(image_arr, detail=0)

    return text, input_img


def extracted_text(texts):

    extrd_dict = {
        "NAME": [],
        "DESIGNATION": [],
        "COMPANY_NAME": [],
        "CONTACT": [],
        "EMAIL": [],
        "WEBSITE": [],
        "ADDRESS": [],
        "PINCODE": [],
    }

    extrd_dict["NAME"].append(texts[0])
    extrd_dict["DESIGNATION"].append(texts[1])

    for i in range(2, len(texts)):

        if texts[i].startswith("+") or (
            texts[i].replace("-", "").isdigit() and "-" in texts[i]
        ):

            extrd_dict["CONTACT"].append(texts[i])

        elif "@" in texts[i] and ".com" in texts[i]:
            extrd_dict["EMAIL"].append(texts[i])

        elif (
            "WWW" in texts[i]
            or "www" in texts[i]
            or "Www" in texts[i]
            or "wWw" in texts[i]
            or "wwW" in texts[i]
        ):
            small = texts[i].lower()
            extrd_dict["WEBSITE"].append(small)

        elif "Tamil Nadu" in texts[i] or "TamilNadu" in texts[i] or texts[i].isdigit():
            extrd_dict["PINCODE"].append(texts[i])

        elif re.match(r"^[A-Za-z]", texts[i]):
            extrd_dict["COMPANY_NAME"].append(texts[i])

        else:
            remove_colon = re.sub(r"[,;]", "", texts[i])
            extrd_dict["ADDRESS"].append(remove_colon)

    for key, value in extrd_dict.items():
        if len(value) > 0:
            concadenate = " ".join(value)
            extrd_dict[key] = [concadenate]

        else:
            value = "NA"
            extrd_dict[key] = [value]

    return extrd_dict


# Streamlit part

st.set_page_config(layout="wide")
st.markdown(
    "<h1 style='text-align: center; color: blue;'>BizCardX: Extracting Business Card Data with OCR</h1>",
    unsafe_allow_html=True,
)

# CREATING OPTION MENU
selected = option_menu(
    None,
    ["Home", "Upload & Extract", "Modify"],
    icons=["house", "cloud-upload", "pencil-square"],
    default_index=0,
    orientation="horizontal",
    styles={
        "nav-link": {
            "font-size": "25px",
            "text-align": "centre",
            "margin": "-2px",
            "--hover-color": "#6495ED",
        },
        "icon": {"font-size": "35px"},
        "container": {"max-width": "1000px"},
        "nav-link-selected": {"background-color": "#6495ED"},
    },
)

mydb = sqlite3.connect("bizcardx.db")
cursor = mydb.cursor()

# Table Creation

create_table_query = """CREATE TABLE IF NOT EXISTS bizcard_details(name varchar(225),
                                                                        designation varchar(225),
                                                                        company_name varchar(225),
                                                                        contact varchar(225),
                                                                        email varchar(225),
                                                                        website text,
                                                                        address text,
                                                                        pincode varchar(225),
                                                                        image text)"""

cursor.execute(create_table_query)
mydb.commit()

# HOME MENU
if selected == "Home":
    col1, col2 = st.columns(2)
    with col1:
        st.image(Image.open("/content/card.png"), width=400)
        st.markdown(
            "#### :green[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas"
        )
    with col2:
        st.write(
            "#### :green[**About :**] Bizcard is a Python application designed to extract information from business cards."
        )
        st.write(
            "#### The main purpose of Bizcard is to automate the process of extracting key details from business card images, such as the name, designation, company, contact information, and other relevant data. By leveraging the power of OCR (Optical Character Recognition) provided by EasyOCR, Bizcard is able to extract text from the images."
        )


if selected == "Upload & Extract":
    if st.button(":blue[Already stored data]"):
        cursor.execute(
            """SELECT NAME,DESIGNATION,COMPANY_NAME,CONTACT,EMAIL,WEBSITE,
                                                        ADDRESS,PINCODE FROM bizcard_details"""
        )
        table_df = pd.DataFrame(
            cursor.fetchall(),
            columns=(
                "NAME",
                "DESIGNATION",
                "COMPANY_NAME",
                "CONTACT",
                "EMAIL",
                "WEBSITE",
                "ADDRESS",
                "PINCODE",
            ),
        )
        st.write(table_df)

    st.subheader(":blue[Upload a Business Card]")
    uploaded_card = st.file_uploader(
        "upload here", label_visibility="collapsed", type=["png", "jpeg", "jpg"]
    )

    if uploaded_card is not None:
        st.markdown("#     ")
        st.markdown("#     ")
        st.markdown("### You have uploaded the card")
        st.image(uploaded_card)

        text_image, input_img = image_to_text(uploaded_card)

        text_dict = extracted_text(text_image)

        if text_dict:
             st.success("### Data Extracted!")

        df = pd.DataFrame(text_dict)

        # Converting Image to Bytes

        Image_bytes = io.BytesIO()
        input_img.save(Image_bytes, format="PNG")

        image_data = Image_bytes.getvalue()

        # Creating Dictionary
        data = {"IMAGE": [image_data]}

        df_1 = pd.DataFrame(data)

        concat_df = pd.concat([df, df_1], axis=1)

        st.write(concat_df)

        button_1 = st.button("Upload to Database")

        if button_1:

            # Insert Query

            insert_query = """INSERT INTO bizcard_details(name, designation, company_name,contact, email, website, address,
                                                    pincode, image)

                                                    values(?,?,?,?,?,?,?,?,?)"""

            datas = concat_df.values.tolist()[0]
            cursor.execute(insert_query, datas)
            mydb.commit()

            st.success("#### Uploaded to database successfully!")

            if st.button(":blue[View updated data]"):
                cursor.execute(
                    """SELECT NAME,DESIGNATION,COMPANY_NAME,CONTACT,EMAIL,WEBSITE,
                                                        ADDRESS,PINCODE FROM bizcard_details"""
                )
                table_df = pd.DataFrame(
                    cursor.fetchall(),
                    columns=(
                        "NAME",
                        "DESIGNATION",
                        "COMPANY_NAME",
                        "CONTACT",
                        "EMAIL",
                        "WEBSITE",
                        "ADDRESS",
                        "PINCODE",
                    ),
                )
                st.write(table_df)

if selected == "Modify":
    st.subheader(":blue[You can view , alter or delete the extracted data in this app]")
    select = option_menu(
        None,
        options=["ALTER", "DELETE"],
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"width": "100%"},
            "nav-link": {"font-size": "20px", "text-align": "center", "margin": "-2px"},
            "nav-link-selected": {"background-color": "#6495ED"},
        },
    )

    if select == "ALTER":
        st.markdown(":blue[Alter the data here]")

        try:
            cursor.execute("SELECT name FROM bizcard_details")
            result = cursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            options = ["None"] + list(business_cards.keys())
            selected_card = st.selectbox("**Select a card**", options)
            if selected_card == "None":
                st.write("No card selected.")
            else:
                st.markdown("#### Update or modify any data below")
                cursor.execute(f"""SELECT NAME,DESIGNATION,COMPANY_NAME,CONTACT,EMAIL,WEBSITE,
                     ADDRESS,PINCODE FROM bizcard_details WHERE name='{selected_card}'""")
                result = cursor.fetchone()

                # DISPLAYING ALL THE INFORMATIONS
                company_name = st.text_input("Company_Name", result[2])
                name = st.text_input("Card_Holder", result[0])
                designation = st.text_input("Designation", result[1])
                mobile_number = st.text_input("Mobile_Number", result[3])
                email = st.text_input("Email", result[4])
                website = st.text_input("Website", result[5])
                Address = st.text_input("Address", result[6])
                pin_code = st.text_input("Pin_Code", result[7])

                if st.button(":blue[Commit changes to DB]"):
                    # Update the information for the selected business card in the database
                    cursor.execute(f"""UPDATE bizcard_details SET company_name='{company_name}',name='{name}',designation='{designation}',
                                    contact='{mobile_number}',email='{email}',website='{website}',address='{Address}',pincode='{pin_code}' WHERE name='{name}'""")
                    mydb.commit()
                    st.success("Information updated in database successfully.")

            if st.button(":blue[View updated data]"):
                cursor.execute(
                    """SELECT NAME,DESIGNATION,COMPANY_NAME,CONTACT,EMAIL,WEBSITE,
                                                        ADDRESS,PINCODE FROM bizcard_details"""
                )
                table_df = pd.DataFrame(
                    cursor.fetchall(),
                    columns=(
                        "NAME",
                        "DESIGNATION",
                        "COMPANY_NAME",
                        "CONTACT",
                        "EMAIL",
                        "WEBSITE",
                        "ADDRESS",
                        "PINCODE",
                    ),
                )
                st.write(table_df)

        except Exception as e:
          st.write(e)

    if select == "DELETE":
        st.subheader(":blue[Delete the data]")
        try:
            cursor.execute("SELECT name FROM bizcard_details")
            result = cursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            options = ["None"] + list(business_cards.keys())
            selected_card = st.selectbox("**Select a card**", options)
            if selected_card == "None":
                st.write("No card selected.")
            else:
                st.write(
                    f"### You have selected :green[**{selected_card}'s**] card to delete"
                )
                st.write("#### Proceed to delete this card?")
                if st.button("Yes Delete Business Card"):
                    cursor.execute(
                        f"DELETE FROM bizcard_details WHERE name='{selected_card}'"
                    )
                    mydb.commit()
                    st.success("Business card information deleted from database.")

            if st.button(":blue[View updated data]"):
                cursor.execute(
                    """SELECT NAME,DESIGNATION,COMPANY_NAME,CONTACT,EMAIL,WEBSITE,
                                                        ADDRESS,PINCODE FROM bizcard_details"""
                )
                table_df = pd.DataFrame(
                    cursor.fetchall(),
                    columns=(
                        "NAME",
                        "DESIGNATION",
                        "COMPANY_NAME",
                        "CONTACT",
                        "EMAIL",
                        "WEBSITE",
                        "ADDRESS",
                        "PINCODE",
                    ),
                )
                st.write(table_df)

        except:
            st.warning("There is no data available in the database")
