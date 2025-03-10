import pytest
import uuid
import os
import logging
import shutil
from backend.tasks.score import create_answer
from backend.utils import get_video_dir, get_audio_path

DIR_NAME = os.path.dirname(__file__)


def test_video_output():
    # Create test data directory if it doesn't exist
    os.makedirs(os.path.join(DIR_NAME, "data"), exist_ok=True)
    
    # Ensure test video is accessible
    test_video = os.path.join(DIR_NAME, "data", "test2.mp4")
    if not os.path.exists(test_video):
        raise FileNotFoundError(f"Test video file not found: {test_video}")
    
    # Copy the test video to our video directory for processing
    video_dir = get_video_dir()
    temp_video = os.path.join(video_dir, "test2.mp4")
    shutil.copy2(test_video, temp_video)
    
    # Generate a unique audio filename
    audio_filename = f"{uuid.uuid4()}.mp3"
    audio_path = get_audio_path(audio_filename)
    
    # Create content dictionary with the temp paths
    content = {
        "fname": temp_video,
        "rename": audio_filename,
    }
    
    # Run the processing
    result = create_answer(content)
    assert result is not None
    
    # Write result to log file
    log_path = os.path.join(DIR_NAME, "test.log")
    with open(log_path, "w") as f:
        f.write(str(result))
