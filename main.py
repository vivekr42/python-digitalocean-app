## pip install aiohttp google-genai==0.3.0 google-generativeai==0.8.3 pydub
import asyncio
import json
import os
import base64
import io
import wave

from aiohttp import web
from google import genai
import google.generativeai as generative
from pydub import AudioSegment

from dotenv import load_dotenv
load_dotenv()

# Load API key from environment (or set it here for testing)
generative.configure(api_key=os.getenv('GOOGLE_API_KEY'))
MODEL = "gemini-2.0-flash-exp"  # use your model ID
TRANSCRIPTION_MODEL = "gemini-1.5-flash-8b"

client = genai.Client(http_options={'api_version': 'v1alpha'})

def transcribe_audio(audio_data):
    """Transcribes audio using Gemini 1.5 Flash."""
    try:
        if not audio_data:
            return "No audio data received."
        mp3_audio_base64 = convert_pcm_to_mp3(audio_data)
        if not mp3_audio_base64:
            return "Audio conversion failed."
        transcription_client = generative.GenerativeModel(model_name=TRANSCRIPTION_MODEL)
        prompt = (
            "Generate a transcript of the speech. "
            "Please do not include any other text in the response. "
            "If you cannot hear the speech, please only say '<Not recognizable>'."
        )
        response = transcription_client.generate_content(
            [
                prompt,
                {"mime_type": "audio/mp3", "data": base64.b64decode(mp3_audio_base64)}
            ]
        )
        return response.text
    except Exception as e:
        print(f"Transcription error: {e}")
        return "Transcription failed."

def convert_pcm_to_mp3(pcm_data):
    """Converts PCM audio to base64 encoded MP3."""
    try:
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)   # mono
            wav_file.setsampwidth(2)     # 16-bit
            wav_file.setframerate(24000) # 24kHz
            wav_file.writeframes(pcm_data)
        wav_buffer.seek(0)
        audio_segment = AudioSegment.from_wav(wav_buffer)
        mp3_buffer = io.BytesIO()
        audio_segment.export(mp3_buffer, format="mp3", codec="libmp3lame")
        mp3_base64 = base64.b64encode(mp3_buffer.getvalue()).decode('utf-8')
        return mp3_base64
    except Exception as e:
        print(f"Error converting PCM to MP3: {e}")
        return None

async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print("WebSocket connection established")

    try:
        # Expect the initial setup message from the client.
        setup_msg = await ws.receive_str()
        print("Received setup message:", setup_msg)
        config_data = json.loads(setup_msg)
        config = config_data.get("setup", {})

        # Connect to the Gemini API
        async with client.aio.live.connect(model=MODEL, config=config) as session:
            print("Connected to Gemini API")

            async def send_to_gemini():
                try:
                    async for msg in ws:
                        if msg.type == web.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                                if "realtime_input" in data:
                                    for chunk in data["realtime_input"]["media_chunks"]:
                                        if chunk["mime_type"] == "audio/pcm":
                                            await session.send({"mime_type": "audio/pcm", "data": chunk["data"]})
                                        elif chunk["mime_type"] == "image/jpeg":
                                            await session.send({"mime_type": "image/jpeg", "data": chunk["data"]})
                            except Exception as e:
                                print(f"Error sending to Gemini: {e}")
                        elif msg.type == web.WSMsgType.ERROR:
                            print("WebSocket error:", ws.exception())
                    print("Client connection closed (send)")
                except Exception as e:
                    print(f"Exception in send_to_gemini: {e}")
                finally:
                    print("send_to_gemini closed")

            async def receive_from_gemini():
                try:
                    while True:
                        async for response in session.receive():
                            if response.server_content is None:
                                print(f"Unhandled server message! - {response}")
                                continue
                            model_turn = response.server_content.model_turn
                            if model_turn:
                                for part in model_turn.parts:
                                    if hasattr(part, 'text') and part.text is not None:
                                        await ws.send_str(json.dumps({"text": part.text}))
                                    elif hasattr(part, 'inline_data') and part.inline_data is not None:
                                        print("audio mime_type:", part.inline_data.mime_type)
                                        base64_audio = base64.b64encode(part.inline_data.data).decode('utf-8')
                                        await ws.send_str(json.dumps({"audio": base64_audio}))
                                        if not hasattr(session, 'audio_data'):
                                            session.audio_data = b''
                                        session.audio_data += part.inline_data.data
                                        print("audio received")
                            if response.server_content.turn_complete:
                                print("<Turn complete>")
                                transcribed_text = transcribe_audio(session.audio_data)
                                if transcribed_text:
                                    await ws.send_str(json.dumps({"text": transcribed_text}))
                                session.audio_data = b''
                except Exception as e:
                    print(f"Error receiving from Gemini: {e}")
                finally:
                    print("Gemini connection closed (receive)")

            send_task = asyncio.create_task(send_to_gemini())
            receive_task = asyncio.create_task(receive_from_gemini())
            await asyncio.gather(send_task, receive_task)

    except Exception as e:
        print(f"Error in Gemini session: {e}")
    finally:
        print("Gemini session closed.")
    return ws

async def index(request):
    return web.FileResponse('./static/index.html')

app = web.Application()
app.router.add_get('/', index)
app.router.add_get('/ws', ws_handler)
app.router.add_static('/static/', path='./static', name='static')

if __name__ == '__main__':
    web.run_app(app, host="0.0.0.0", port=80)
