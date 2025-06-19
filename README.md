# 🔳 Advanced QR Code Tool

An advanced QR code generator and scanner built with **Streamlit**. This web app allows users to create stylish and scannable QR codes with customizations like **dot shapes**, **colors**, **embedded images**, and **backgrounds**. It also supports **real-time QR code scanning** via webcam and static image decoding.
---

project live link - https://qr-code-generator-pnw7zcstumdxefiwrieh4m.streamlit.app/

## 🚀 Features

### ✅ Generate QR Codes
- **Styled QR Mode**:
  - Choose dot shape: Circle, Square, Rounded, Gapped Square
  - Select custom QR color
  - Option to add a background image with transparency handling
- **Embedded Image Mode**:
  - Embed images inside the QR matrix
  - Smart darkening algorithm for scan-friendly output
  - Preserves finder patterns for accuracy

### 📷 Live QR Scanner
- Real-time webcam scanner powered by `streamlit-webrtc`
- Highlights detected QR codes
- Displays decoded data instantly (URLs become clickable)

### 🖼️ Decode from Uploaded Images
- Upload images with QR codes to extract data
- Supports text and URLs with link preview

---

## 🛠️ Tech Stack

| Tool | Usage |
|------|-------|
| [Streamlit] | Web app framework |
| [qrcode] | QR generation |
| [OpenCV] | QR detection & decoding |
| [Pillow (PIL)] | Image processing |
| [NumPy] | Matrix operations |
| [streamlit-webrtc] | Real-time webcam feed |

---

## 🧩 Modular Architecture
  - Helper Functions:
    - generate_embedded_qr(data, image)
    - generate_styled_qr(data, color, shape, bg_image)
    - is_finder_pattern(x, y, size) to preserve QR functionality

  - Class: QRProcessor:
    - Handles video frame processing from webcam
    - Detects QR codes and overlays detection info

  - Tabbed Layout:
    - tab1: Generate QR
    - tab2: Upload + Decode
    - tab3: Webcam Scanner

--- 

## 📸 Screenshots

<!-- Optional: Add local or hosted screenshots -->
- **Styled QR Generation**
- **Embedded QR with image**
- **QR decoding from upload**
- **Live webcam scanner in action**

---

## 📦 Installation

### 🔧 Prerequisites
Make sure you have Python 3.7 or above.

### 🧪 Install Dependencies

pip install -r requirements.txt

---

## 💡 Tips
  - Use high-contrast images for better QR visibility

  - QR with embedded images may require larger size for reliability

  - Test your generated QR codes with different scanner apps

---

## 👥 Development Team

Contributors | LinkedIn

  1. Vaishnav M - www.linkedin.com/in/vaishnav-m-
  2. Aleena Pauly - www.linkedin.com/in/aleenapauly
  3. Sajin T S
  4. Farha

---

## 🙏 Acknowledgments

Special thanks to:

Mentor: Dixon Joy - https://www.linkedin.com/in/dixson-joy-527513173/

Academic Counselors:

Jasmine James - https://www.linkedin.com/in/jasmine-james-2-/

Eric Thomas - https://www.linkedin.com/in/eric-thomas-in/

Institution: Luminar Technolab, Kochi under Rahul Mohanakumar @ https://www.linkedin.com/company/luminartechnolab/posts/?feedView=all @ https://www.linkedin.com/in/rahulluminar/
