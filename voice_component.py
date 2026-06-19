import streamlit as st
import speech_recognition as sr
import io
import tempfile
import os


def voice_input(key=None):
    """
    Voice input using st.audio_input (built-in Streamlit widget)
    + Google free speech recognition.
    No JavaScript or iframe needed.
    """
    audio_data = st.audio_input("🎤", key=key)

    if audio_data is not None:
        with st.spinner("Transcribing..."):
            try:
                recognizer = sr.Recognizer()

                # Read audio bytes
                audio_bytes = audio_data.read()
                audio_data.seek(0)

                # Save to temp WAV file for speech_recognition
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(audio_bytes)
                    tmp_path = tmp.name

                try:
                    with sr.AudioFile(tmp_path) as source:
                        audio = recognizer.record(source)

                    # Use Google's free speech recognition
                    text = recognizer.recognize_google(audio, language="en-US")
                    return text
                finally:
                    os.unlink(tmp_path)

            except sr.UnknownValueError:
                st.warning("Could not understand audio. Please try again.")
                return ""
            except sr.RequestError as e:
                st.error(f"Speech service error: {e}")
                return ""
            except Exception as e:
                st.error(f"Audio processing error: {str(e)}")
                return ""

    return ""
