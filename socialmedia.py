#Step-1
import asyncio
import os
from youtube_transcript_api import YouTubeTranscriptApi
from agents import (
    Agent,
    Runner,
    WebSearchTool,
    function_tool,
    ItemHelpers,
    set_default_openai_client,
    set_default_openai_api,
    trace,
)
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List

#Step-2 (Claude API key and configure)
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1/"

#Step-3
anthropic_async_client = AsyncOpenAI(
    api_key=ANTHROPIC_API_KEY,
    base_url=ANTHROPIC_BASE_URL,
)
set_default_openai_client(anthropic_async_client)
set_default_openai_api("chat_completions")

#Synchronous client for tools
anthropic_client = OpenAI(
    api_key=ANTHROPIC_API_KEY,
    base_url=ANTHROPIC_BASE_URL,
)

#Step-4 (Defining Tools for the Agents)
@function_tool
def generate_content(video_transcript: str, social_media_platform: str):
    print(f"Generating social media content for {social_media_platform}...")

    response = anthropic_client.chat.completions.create(
        model="claude-haiku-4-5",
        messages=[
            {"role": "user", "content": f"Here is a new video transcript:\n{video_transcript}"
                                        f"generate a social media post on my {social_media_platform}"}
        ],
        max_tokens=2500,
    )
    return response.choices[0].message.content

#Step-5 (Defining the agent)
@dataclass
class Post:
    platform: str
    content: str

content_writer_agent = Agent(
    name="Content Writer Agent",
    instructions="""You are a talented content writer who writes engaging, humorous, informative, highly readable social media posts.
    You will be given a video transcript and social media platforms.
    You will generate a social media post based on the video transcript and the social media platforms.
    You may search the web for up-to-date information on the topic and fill in some useful details if needed.""",
    model="claude-haiku-4-5",
    tools=[generate_content],
    output_type=List[Post],
)

#Step-6 (define helper functions)
#Fetch transcript from a youtube video using the video id.
def get_transcript(video_id: str, languages: list = None) -> str:
    """
    Retrieves the transcript for a YouTube video.

    Args:
        video_id (str): The YouTube video ID.
        languages (list, optional): List of language codes to try, in order.
                                    Defaults to ["en"] if None.

    Returns:
        str: The concatenated transcript text.

    Raises:
        Exception: If transcript retrieval fails, with details about the error.
    """
    if languages is None:
        languages = ["en"]

    try:
        #use the youtube transcript API
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id, languages=languages)

        #more efficient way to concatenate all text snippets
        transcript_text = " ".join(snippet.text for snippet in fetched_transcript)

        return transcript_text

    except Exception as e:
        #Handle specific Youtube transcript API exceptions
        from youtube_transcript_api._errors import (
            CouldNotRetrieveTranscript,
            VideoUnavailable,
            InvalidVideoId,
            NoTranscriptFound,
            TranscriptsDisabled,
        )
        if isinstance(e, NoTranscriptFound):
            error_msg = f"No transcript found for video {video_id} in languages {languages}"
        elif isinstance(e, VideoUnavailable):
            error_msg = f"Video {video_id} is unavailable"
        elif isinstance(e, InvalidVideoId):
            error_msg = f"Invalid video ID: {video_id}"
        elif isinstance(e, TranscriptsDisabled):
            error_msg = f"Transcripts are disabled for video {video_id}"
        elif isinstance(e, CouldNotRetrieveTranscript):
            error_msg = f"Could not retrieve transcript: {str(e)}"
        else:
            error_msg = f"An unexpected error occurred: {str(e)}"

        print(f"Error: {error_msg}")
        raise Exception(error_msg) from e

#Step-7 (Run the agent)
async def main():
    video_id = "DfFoMhfYNLI"
    transcript = get_transcript(video_id)

    msg = f"Generate a LinkedIn post and an Instagram caption based on this video transcript: {transcript}"

    #package input for the agent
    input_items = [{"content": msg, "role": "user"}]

    #Run content writer agent
    with trace("Writing content"):
        result = await Runner.run(content_writer_agent, input_items)
        output = ItemHelpers.text_message_outputs(result.new_items)
        print("Generated Post:\n", output)

if __name__ == "__main__":
    asyncio.run(main())