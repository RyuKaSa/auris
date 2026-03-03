"""stt.py -- RealtimeSTT wrapper functions."""
from RealtimeSTT import AudioToTextRecorder


def create_recorder():
    return AudioToTextRecorder(
        model="base",
        language="en",
        spinner=False,
        use_microphone=True,
        on_realtime_transcription_update=on_partial,
    )


def on_partial(text):
    print(f"  ... {text}", end="\r", flush=True)


def get_next_utterance(recorder, callback):
    recorder.text(callback)


def shutdown_recorder(recorder):
    recorder.shutdown()