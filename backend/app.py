from flask import Flask, jsonify, Response
from flask_pymongo import PyMongo
from flask_cors import CORS
import os
from dotenv import load_dotenv
import fitz  # pymupdf

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# MongoDB Connection
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

# Route: Get all syllabi
@app.route('/syllabi', methods=['GET'])
def get_syllabi():
    syllabi_collection = mongo.db.syllabi.find({}, {"_id": 0})  # Exclude _id
    return jsonify({"syllabi": list(syllabi_collection)})


# Route: Get syllabus by course_code
@app.route('/syllabi/<course_code>', methods=['GET'])
def get_syllabus_by_course_code(course_code):
    syllabus = mongo.db.syllabi.find_one({"course_code": course_code}, {"_id": 0})
    if syllabus:
        return jsonify(syllabus)
    else:
        return jsonify({"error": "Syllabus not found"}), 404


@app.route('/generate-pdf/<course_code>', methods=['GET'])
def generate_pdf(course_code):
    syllabus = mongo.db.syllabi.find_one({"course_code": course_code}, {"_id": 0})
    
    if not syllabus:
        return jsonify({"error": "Syllabus not found"}), 404

    # Create a PDF document
    pdf = fitz.open()
    page = pdf.new_page()

    # Initialize starting position for text
    text_position = 50  # Start 50 units down from the top of the page

    # Format syllabus content
    text = f"{syllabus['course_code']} "
    text += f"{syllabus['program']} - "
    text += f"{syllabus['year']}\n\n"
    
    # Title for Course Content
    text += "Course Content:\n\n"

    # Define a helper function to split long text into lines that fit on the page
    def wrap_text(text, max_length=100):
        lines = []
        while len(text) > max_length:
            # Find the last space within the max_length
            break_point = text.rfind(' ', 0, max_length)
            if break_point == -1:
                break_point = max_length
            lines.append(text[:break_point].strip())
            text = text[break_point:].strip()
        lines.append(text)  # Append the last chunk of text
        return lines

    # Loop through units and their details
    for index, (unit, details) in enumerate(syllabus["syllabus"].items(), 1):
        unit_title = details["title"]
        topics = ", ".join([f"{topic}" for topic in details["topics"]])
        experiential_learning = ", ".join([f"{exp}" for exp in details["experiential_learning"]])

        # Format the unit content
        text += f"Unit {index}: {unit_title}\n\n"  # Display unit number and title
        wrapped_topics = wrap_text(topics)  # Wrap the topics text
        for line in wrapped_topics:
            text += f"{line}\n"  # Add each line of wrapped topics
        
        # Wrap the experiential learning text
        wrapped_experiential_learning = wrap_text(experiential_learning)  # Wrap experiential learning
        text += f"\nExperiential learning:\n\n"
        for line in wrapped_experiential_learning:
            text += f"{line}\n"  # Add each line of wrapped experiential learning

        text += "\n"  # Add an extra newline after each unit

    # Add text to PDF
    page.insert_text((50, text_position), text, fontsize=10)

    # Save PDF to memory
    pdf_bytes = pdf.write()
    pdf.close()

    # Serve the PDF
    response = Response(pdf_bytes, content_type="application/pdf")
    response.headers["Content-Disposition"] = f"attachment; filename={course_code}.pdf"
    return response


# Route to generate a combined PDF from multiple syllabi
# @app.route('/combine-pdfs', methods=['POST'])
# def combine_pdfs():
#     # Get the course_codes from the request
#     course_codes = request.json.get("course_codes", [])
#     if not course_codes:
#         return jsonify({"error": "No course codes provided"}), 400

#     combined_pdf = fitz.open()  # Create a new empty PDF to store the combined result

#     for course_code in course_codes:
#         pdf_bytes = generate_pdf(course_code)  # Generate the PDF for each course_code
#         pdf = fitz.open(stream=pdf_bytes)  # Open the generated PDF from bytes
#         combined_pdf.insert_pdf(pdf)  # Append the PDF to the combined PDF

#     # Save the combined PDF to memory
#     combined_pdf_bytes = combined_pdf.write()
#     combined_pdf.close()

#     # Serve the combined PDF as a response
#     response = Response(combined_pdf_bytes, content_type="application/pdf")
#     response.headers["Content-Disposition"] = f"attachment; filename=combined_syllabi.pdf"
#     return response


@app.route('/combine-pdfs/<course_codes>', methods=['GET'])
def combine_pdfs(course_codes):
    # Convert the comma-separated course codes into a list
    course_codes_list = course_codes.split(',')

    # Retrieve syllabi for the selected courses
    syllabi = []
    for course_code in course_codes_list:
        syllabus = mongo.db.syllabi.find_one({"course_code": course_code}, {"_id": 0})
        if syllabus:
            syllabi.append(syllabus)
        else:
            return jsonify({"error": f"Syllabus not found for course {course_code}"}), 404

    # Create a new PDF document to combine all syllabi
    pdf = fitz.open()

    # Loop through each syllabus and add its content to the PDF
    for syllabus in syllabi:
        page = pdf.new_page()

        # Initialize starting position for text
        text_position = 50  # Start 50 units down from the top of the page

        # Format syllabus content
        text = f"{syllabus['course_code']} "
        text += f"{syllabus['program']} - "
        text += f"{syllabus['year']}\n\n"
        
        # Title for Course Content
        text += "Course Content:\n\n"

        # Define a helper function to wrap text
        def wrap_text(text, max_length=100):
            lines = []
            while len(text) > max_length:
                break_point = text.rfind(' ', 0, max_length)
                if break_point == -1:
                    break_point = max_length
                lines.append(text[:break_point].strip())
                text = text[break_point:].strip()
            lines.append(text)  # Append the last chunk of text
            return lines

        # Loop through units and their details
        for unit, details in syllabus["syllabus"].items():
            unit_title = details["title"]
            topics = ", ".join([f"{topic}" for topic in details["topics"]])
            experiential_learning = ", ".join([f"{exp}" for exp in details["experiential_learning"]])

            # Format the unit content
            text += f"Unit: {unit_title}\n\n"
            wrapped_topics = wrap_text(topics)
            for line in wrapped_topics:
                text += f"{line}\n"  # Add each wrapped line of topics
            
            text += f"\nExperiential learning:\n\n {experiential_learning}\n\n"

        # Add text to the page
        page.insert_text((50, text_position), text, fontsize=10)

    # Save the combined PDF to memory
    pdf_bytes = pdf.write()
    pdf.close()

    # Serve the combined PDF
    response = Response(pdf_bytes, content_type="application/pdf")
    response.headers["Content-Disposition"] = f"attachment; filename=combined_syllabi.pdf"
    return response


if __name__ == '__main__':
    app.run(debug=True)
