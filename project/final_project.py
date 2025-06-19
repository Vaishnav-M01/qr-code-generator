import streamlit as st
import qrcode
import av
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageStat, ImageColor
from io import BytesIO
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    CircleModuleDrawer,
    SquareModuleDrawer,
    GappedSquareModuleDrawer,
    RoundedModuleDrawer
)
from qrcode.image.styles.colormasks import SolidFillColorMask
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import time
import re

# ------------------- PAGE CONFIG -------------------
st.set_page_config(
    page_title="Advanced QR Code Tool",
    layout="centered",
    page_icon="🔳"
)

# ------------------- CSS STYLING -------------------

# Apply custom CSS styling
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #1f4037, #99f2c8);
        background-attachment: fixed;
        background-size: cover;
        color: white;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(135deg, #1f4037, #99f2c8);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 0 15px rgba(0,0,0,0.5);
    }

    /* Sidebar title glow effect */
    .sidebar-title {
        font-size: 24px;
        font-weight: bold;
        color: #0ff;
        text-align: center;
        text-shadow: 0 0 5px #0ff, 0 0 10px #0ff;
        margin-bottom: 20px;
    }

    /* Sidebar card style */
    .sidebar-card {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        margin-top: 10px;
    }

    .css-1d391kg {  /* Sidebar text override */
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)


# ------------------- HELPER FUNCTIONS -------------------
def is_finder_pattern(x, y, size):
    """Check if coordinates are in QR finder pattern areas"""
    return ((x < 7 and y < 7) or
            (x >= size - 7 and y < 7) or
            (x < 7 and y >= size - 7))


def generate_embedded_qr(data, embedded_img, box_size=4):
    """Generate QR code with embedded image while maintaining scannability"""
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    size = len(matrix)
    img_size = size * box_size

    # Prepare images
    user_img = embedded_img.resize((img_size, img_size)).convert("RGB")
    user_np = np.array(user_img)
    final_np = np.ones((img_size, img_size, 3), dtype=np.uint8) * 255

    # Create QR with embedded image
    for y in range(size):
        for x in range(size):
            x0, y0 = x * box_size, y * box_size
            if matrix[y][x]:
                if is_finder_pattern(x, y, size):
                    final_np[y0:y0 + box_size, x0:x0 + box_size] = 0  # Black for finder patterns
                else:
                    block = user_np[y0:y0 + box_size, x0:x0 + box_size]
                    darkened = (block * 0.4).astype(np.uint8)  # Darken for better contrast
                    final_np[y0:y0 + box_size, x0:x0 + box_size] = darkened

    return Image.fromarray(final_np)


def generate_styled_qr(data, color, shape, bg_image=None):
    """Generate styled QR code with custom appearance"""
    # Create QRCode object
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4,
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Choose dot shape
    shape_drawers = {
        'Circle': CircleModuleDrawer(),
        'Square': SquareModuleDrawer(),
        'Rounded': RoundedModuleDrawer(),
        'Gapped Square': GappedSquareModuleDrawer()
    }
    drawer = shape_drawers.get(shape, SquareModuleDrawer())

    # Convert hex color to RGB
    rgb_color = ImageColor.getrgb(color)

    # Generate styled QR image
    qr_img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=drawer,
        color_mask=SolidFillColorMask(front_color=rgb_color, back_color=(255, 255, 255))
    ).convert('RGBA')

    # Make white background transparent
    datas = qr_img.getdata()
    new_data = []
    for item in datas:
        if item[:3] == (255, 255, 255):  # white
            new_data.append((255, 255, 255, 0))  # transparent
        else:
            new_data.append(item)
    qr_img.putdata(new_data)

    # Add background if provided
    ...
    if bg_image:
        bg = Image.open(bg_image).convert('RGBA')
        bg = bg.resize(qr_img.size)

        # Add overlay to boost contrast
        overlay = Image.new('RGBA', qr_img.size, (255, 255, 255, 150))
        bg_with_overlay = Image.alpha_composite(bg, overlay)

        # Check contrast
        bg_stat = ImageStat.Stat(bg)
        bg_brightness = sum(bg_stat.mean[:3]) / 3
        qr_brightness = sum(rgb_color) / 3
        contrast = abs(qr_brightness - bg_brightness)
        if contrast < 50:
            st.warning("⚠ Low contrast between QR and background. Try a darker or lighter QR color.")

        final_img = Image.alpha_composite(bg_with_overlay, qr_img)
    else:
        # Plain white background behind QR
        white_bg = Image.new("RGBA", qr_img.size, (255, 255, 255, 255))
        final_img = Image.alpha_composite(white_bg, qr_img)

    return final_img


# ------------------- QR PROCESSOR CLASS -------------------
class QRProcessor(VideoProcessorBase):
    def __init__(self):
        super().__init__()
        self.qr_data = None
        self.last_detection_time = 0

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img)

        if bbox is not None and len(bbox) > 0:
            bbox = np.int32(bbox).reshape(-1, 2)
            for i in range(len(bbox)):
                pt1 = tuple(bbox[i])
                pt2 = tuple(bbox[(i + 1) % len(bbox)])
                cv2.line(img, pt1, pt2, (0, 255, 0), 2)

        if data:
            self.qr_data = data
            self.last_detection_time = time.time()
            cv2.putText(img, f"Data: {data}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
        elif time.time() - self.last_detection_time > 5:  # Clear after 5 seconds
            self.qr_data = None

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ------------------- MAIN APP -------------------
def main():
    st.title("🔳 Advanced QR Code Tool")
    st.markdown("Generate custom QR codes with embedded images or scan existing ones with your camera")

    tab1, tab2, tab3 = st.tabs(["Generate QR Code", "Decode QR Code", "Live Scanner"])

    with st.sidebar:
        st.markdown('<div class="sidebar-title">QR Customization</div>', unsafe_allow_html=True)

        generation_mode = st.radio(
            "Generation Mode:",
            ["Styled QR", "Embedded Image QR"],
            index=0,
            help="Choose between a styled QR code or one with an embedded image"
        )

        if generation_mode == "Styled QR":

            qr_color = st.color_picker('QR Color:', '#000000')
            shape = st.selectbox(
                "Dot Shape:",
                ['Circle', 'Square', 'Rounded', 'Gapped Square'],
                index=1
            )
            bg_image = st.file_uploader(
                'Background Image (optional)',
                type=['png', 'jpg', 'jpeg'],
                help="Add a background image to your QR code"
            )
        else:
            darken_factor = st.slider(
                "Image Darkness:",
                min_value=0.1,
                max_value=0.9,
                value=0.4,
                help="How much to darken the embedded image for better QR contrast"
            )

        st.markdown("---")
        st.markdown("""
            <div style="font-size: 0.9rem; color: #555;">
            <b>Tips:</b><br>
            • For embedded QR codes, use high-contrast images<br>
            • Test your QR codes with multiple scanners<br>
            • Larger QR codes work better with embedded images
            </div>
        """, unsafe_allow_html=True)

    # ------------------- GENERATE TAB -------------------
    with tab1:
        st.markdown('<div class="custom-card"><h2>Generate QR Code</h2></div>', unsafe_allow_html=True)

        data = st.text_input(
            "Enter text or URL to encode:",
            placeholder="https://example.com",
            help="The data that will be encoded in the QR code"
        )

        if generation_mode == "Embedded Image QR":
            embedded_img = st.file_uploader(
                "Upload image to embed inside QR",
                type=["jpg", "jpeg", "png"],
                help="This image will be embedded within the QR code modules"
            )
        else:
            embedded_img = None

        if st.button("Generate QR Code", key="generate_btn"):

            if data:
                if generation_mode == "Embedded Image QR" and embedded_img:
                    with st.spinner("Creating QR with embedded image..."):
                        qr_img = generate_embedded_qr(data, Image.open(embedded_img))
                else:
                    with st.spinner("Creating styled QR code..."):
                        qr_img = generate_styled_qr(data, qr_color, shape, bg_image)

                # Display QR code
                st.image(qr_img, caption="Your Custom QR Code", width=250)

                # Download button
                buf = BytesIO()
                qr_img.save(buf, format="PNG")
                st.download_button(
                    "Download QR Code",
                    data=buf.getvalue(),
                    file_name="custom_qr.png",
                    mime="image/png",
                    help="Download your custom QR code as a PNG file"
                )
            else:
                st.warning("Please enter some data to encode in the QR code")

    # ------------------- DECODE TAB -------------------
    with tab2:
        st.markdown('<div class="custom-card"><h2>Decode QR Code</h2></div>', unsafe_allow_html=True)

        uploaded_qr = st.file_uploader(
            "Upload an image with a QR code",
            type=["png", "jpg", "jpeg"],
            help="Upload an image containing a QR code to decode its contents"
        )

        if uploaded_qr:
            # Load and convert image
            pil_image = Image.open(uploaded_qr).convert("RGB")
            img_np = np.array(pil_image)
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

            st.image(pil_image, caption='Uploaded Image', width=250)

            # Detect and decode
            with st.spinner("Scanning for QR code..."):
                detector = cv2.QRCodeDetector()
                data, bbox, _ = detector.detectAndDecode(img_cv)

            if bbox is not None and data:
                st.success(f"✅ Decoded Data: {data}")

                # Check if it's a URL
                url_pattern = re.compile(r"^https?://[^\s]+$")
                if url_pattern.match(data.strip()):
                    st.markdown(f"[Visit this link]({data})")
            else:
                st.error("❌ No QR code found in the image. Try a clearer image.")

    # ------------------- LIVE SCANNER TAB -------------------
    with tab3:
        st.markdown('<div class="custom-card"><h2>Live QR Code Scanner</h2></div>', unsafe_allow_html=True)

        st.markdown("""
            <div style="margin-bottom: 1.5rem;">
            Point your camera at a QR code to scan it automatically. 
            Detected URLs will be clickable.
            </div>
        """, unsafe_allow_html=True)

        # Create scanner instance
        ctx = webrtc_streamer(
            key="qr-scanner",
            video_processor_factory=QRProcessor,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

        # Display results
        if ctx.video_processor:
            result_placeholder = st.empty()
            button_placeholder = st.empty()

            if hasattr(ctx.video_processor, 'qr_data') and ctx.video_processor.qr_data:
                result = ctx.video_processor.qr_data

                # Detect if the result is a URL
                url_pattern = re.compile(r"^https?://[^\s]+$")
                if url_pattern.match(result.strip()):
                    result_placeholder.markdown(
                        f"✅ Detected QR Code: [**{result}**]({result})",
                        unsafe_allow_html=True
                    )

                    if button_placeholder.button("🔗 Open URL in Browser"):
                        st.markdown(f'<meta http-equiv="refresh" content="0;url={result}">', unsafe_allow_html=True)
                else:
                    result_placeholder.success(f"✅ Detected QR Code: {result}")
            else:
                result_placeholder.info("📷 Point your camera at a QR code to scan...")


if __name__ == "__main__":
    main()