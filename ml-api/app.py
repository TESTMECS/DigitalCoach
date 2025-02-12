"""
Main Flask application as well as routes of the app.
"""

import uuid
import redis
from threading import Thread
from rq import Queue
from flask import Flask, jsonify, request
from flask_cors import CORS
from helpers.download_url import download_video
from helpers.score import create_answer
from db_monitor import poll_connection
import ffmpeg
import json

from models.BigFiveScores import BigFiveScores
from models.StarMethod import predict_star_scores, percentageFeedback

r = redis.Redis()
q = Queue(connection=r)


def launch_polling_script():
    Thread(target=poll_connection, args=(r,), daemon=True).start()
    print("Launched polling script in different thread.")


# initalize the Flask object
app = Flask(__name__)
with app.app_context():
    launch_polling_script()
CORS(app)


@app.route("/results/<job_id>", methods=["GET"])
def get_results(job_id):
    """
    GET route that returns results of a job.
    """
    # Fetch job status from Redis hash
    job_status = r.hget(f"rq:job:{job_id}", "status")
    if job_status is None:
        return jsonify(message="Job not found.")
    # Decode the job status
    job_status = job_status.decode("utf-8")
    if job_status == "finished":
        # Fetch job result from Redis hash
        result = r.hget(f"rq:job:{job_id}", "result")
        if result is None:
            return jsonify(message="Job result not found.")
        # Decode and process the result
        try:
            result = result.decode("utf-8")  # Decode bytes to string
            print(f"Raw result: {result}")
            e_result = eval(result)  # Caution: Evaluate the result
            json_string = json.dumps(e_result)  # Serialize as JSON string
            return jsonify(result=json.loads(json_string))  # Parse and return JSON
        except Exception as e:
            return jsonify(message="Error processing job result.", error=str(e))
    else:
        return jsonify(message="Job has not finished yet.")


@app.route("/predict", methods=["POST"])
def predict():
    """
    POST route that returns total text, audio and video predictions.
    """
    req = request.get_json()  # Video URL
    # Download the video from the firebase URL
    video_url = req["videoUrl"]
    if not video_url:
        return jsonify(errors="Required fields not in request body.")
    print("About to download video")
    download_video(video_url)  # Download video from URL, returns path to video
    input_path = "data/video.mp4"
    output_path = "data/output.mp4"
    try:
        input_stream = ffmpeg.input(input_path)
        audio_stream = input_stream.audio
        video_stream = input_stream.video.filter("fps", fps=30, round="up")
        output_stream = ffmpeg.output(video_stream, audio_stream, output_path)
        ffmpeg.run(output_stream)
    except Exception as e:
        return {"errors": e}
    content = {"fname": "output.mp4", "rename": str(uuid.uuid4()) + ".mp3"}
    job = q.enqueue(create_answer, content)
    message = (
        "Task " + str(job.get_id()) + " added to queue at " + str(job.enqueued_at) + "."
    )
    result = job.latest_result(timeout=600)
    if result.type == result.Type.SUCCESSFUL:
        print("Return Value", result.return_value)
        job_key = f"rq:job:{job.get_id()}"
        r.hset(job_key, "result", result.return_value)
    return jsonify(message=message)


@app.route("/big-five-feedback", methods=["POST"])
def get_big_five_feedback():
    data = request.get_json()
    scores = data
    big_five = BigFiveScores(
        scores["o"], scores["c"], scores["e"], scores["a"], scores["n"]
    )
    user_feedback = []
    # Ensure the correct mapping of traits to their attributes
    for trait, attr in zip(
        [
            "openness",
            "conscientiousness",
            "extraversion",
            "agreeableness",
            "neuroticism",
        ],
        ["o", "c", "e", "a", "n"],
    ):
        trait_level = big_five.determine_level(getattr(big_five, attr))
        user_feedback.append(BigFiveScores.FEEDBACK[trait][trait_level])
    return jsonify({"feedback": user_feedback})


@app.route("/star-feedback", methods=["POST"])
def get_star_feedback():
    """
    POST route that returns STAR feedback. Percentages of each part of the STAR method. And the breakdown of each sentence.
    """
    # takes in evaluation.text_analysis.output_text
    data = request.get_json()
    star_scores = predict_star_scores(data)
    classifications = star_scores["classifications"]
    percentages = star_scores["percentages"]
    feedback = percentageFeedback(percentages)
    # added classifications.
    return jsonify(
        {
            "feedback": feedback,
            "fufilledStar": star_scores["fufilledStar"],
            "classifications": classifications,
        }
    )


@app.route("/", methods=["GET"])
def index():
    """
    Home route.
    """
    return "Welcome to the ML API for Digital Coach"


if __name__ == "___main__":
    app.run(debug=True, host="0.0.0.0")
