import re
import torch
import whisper
import threading

def clean_transcript(text):
    text = re.sub(r'[<|>{}\\~]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\b\w\b', '', text)
    return text.strip()

def remove_repetitions(text):
    text = re.sub(r'(\b\w+\b)( \1\b){3,}', r'\1', text)
    for phrase_len in range(3, 10):
        pattern = r'((?:\b\w+\b)(?: \b\w+\b){' + str(phrase_len-1) + r'})( \1\b){1,}'
        text = re.sub(pattern, r'\1', text)
    return text

def transcribe_with_whisper(audio_array, model_size="medium", progress_callback=None, segment_callback=None):
    try:
        if progress_callback:
            progress_callback(40, f"Loading model: {model_size}")
        
        model = whisper.load_model(model_size)
        
        if progress_callback:
            progress_callback(60, "Transcribing audio")
        
        options = {
            "beam_size": 5,
            "best_of": 5,
            "patience": 1.0,
            "length_penalty": 1.0,
            "fp16": torch.cuda.is_available()
        }
        
        # Transcribe with the callback to show real-time results
        result = model.transcribe(
            audio_array, 
            temperature=0.0,
            **options
        )
        
        if progress_callback:
            progress_callback(90, "Processing transcript")
            
        transcript = ""
        
        # Process each segment in real-time
        for i, segment in enumerate(result["segments"]):
            segment_text = segment["text"].strip()
            transcript += segment_text + " "
            
            # Send segment to UI immediately via callback
            if segment_callback:
                segment_callback(segment_text)
                
        transcript = clean_transcript(transcript)
        transcript = remove_repetitions(transcript)
        
        if progress_callback:
            progress_callback(100, "Transcription complete")
            
        return transcript
        
    except Exception as e:
        print(f"Transcription error: {e}")
        if progress_callback:
            progress_callback(0, f"Error: {str(e)}")
        return None

def process_long_audio(audio_array, model_size="medium", progress_callback=None, segment_callback=None):
    chunk_size = 16000 * 60 * 5  # 5 minutes of audio at 16kHz
    chunks = [audio_array[i:i+chunk_size] for i in range(0, len(audio_array), chunk_size)]
    
    if progress_callback:
        progress_callback(40, f"Processing {len(chunks)} chunks")
    
    full_transcript = ""
    
    for i, chunk in enumerate(chunks):
        if progress_callback:
            chunk_progress = 40 + (i / len(chunks) * 50)
            progress_callback(chunk_progress, f"Transcribing chunk {i+1}/{len(chunks)}")
        
        # Process this chunk and show results in real-time
        chunk_transcript = transcribe_with_whisper(
            chunk, 
            model_size=model_size,
            progress_callback=None,
            segment_callback=segment_callback
        )
        
        if chunk_transcript:
            full_transcript += chunk_transcript + " "
    
    full_transcript = clean_transcript(full_transcript)
    full_transcript = remove_repetitions(full_transcript)
    
    if progress_callback:
        progress_callback(100, "Transcription complete")
        
    return full_transcript