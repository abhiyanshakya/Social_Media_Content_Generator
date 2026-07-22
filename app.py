import streamlit as st
import asyncio
from socialmedia import content_writer_agent, get_transcript, Runner, ItemHelpers
import json

#Set page Configuration
st.set_page_config(
    page_title="Social Media Content generation",
    page_icon="",
    layout="wide"
)

#App title and description
st.title("Social Media Content Generation")
st.markdown("""
This app generates social media content based on Youtube video transcripts.
Enter a Youtube Video ID and your query to generate content for different platforms.
""")

#Input Section
st.header("Input")
col1, col2 = st.columns(2)

with col1:
    video_id = st.text_input("Youtube Video ID", placeholder = "e.g., DfFoMhfYNLI")
    st.caption("The ID is the part after 'v=' in a Youtube URL. for example, in 'https://www.youtube.com/watch?v=DfFoMhfYNLI'")

with col2:
    query = st.text_area("Your Query",
                         placeholder = "e.g., Generate a LinkedIn post and an Instagram caption based on this video")

#Platform selection
st.subheader("Select Platforms")

col1, col2, col3 = st.columns(3)

with col1:
    linkedin = st.checkbox("LinkedIn", value=True)

with col2:
    instagram = st.checkbox("Instagram", value=True)

with col3:
    twitter = st.checkbox("Twitter")


# Function to run the agent
async def run_agent(video_id, query, platforms):
    try:
        # Get transcript
        transcript = get_transcript(video_id)

        # Prepare platforms string
        platforms_str = " and ".join(platforms)

        # Prepare message
        msg = f"Generate {platforms_str} posts based on this video transcript: {transcript}"
        if query:
            msg = f"{query} for {platforms_str} based on this video transcript: {transcript}"

        # Package input for the agent
        input_items = [{"content": msg, "role": "user"}]

        # Run content writer agent
        result = await Runner.run(content_writer_agent, input_items)
        return result, None

    except Exception as e:
        return None, str(e)

#Generate button
if st.button("Generate Content", type = "primary", disabled = not video_id):
        # Check if video ID is provided
        if not video_id:
            st.error("Please enter a YouTube Video ID")
        else:
            # Check if at least one platform is selected
            selected_platforms = []

            if linkedin:
                selected_platforms.append("LinkedIn")

            if instagram:
                selected_platforms.append("Instagram")

            if twitter:
                selected_platforms.append("Twitter")

            if not selected_platforms:
                st.error("Please select at least one social media platform")
            else:
                with st.spinner("Generating content... This may take a minute or two."):
                    # Run the agent
                    result, error = asyncio.run(
                        run_agent(video_id, query, selected_platforms)
                    )

                    if error:
                        st.error(f"Error: {error}")
                    else:
                        # Display results
                        st.header("Generated Content")
                        output = ItemHelpers.text_message_outputs(result.new_items)

                        # Parse the output correctly
                        parsed_output = json.loads(output)  # convert the JSON string to a Python dict

                        # Now access the list of posts
                        posts = parsed_output.get("response", [])

                        for post in posts:
                            platform = post.get("platform", "Unknown Platform")
                            content = post.get("content", "")

                            with st.expander(f"{platform} Post", expanded=True):
                                st.markdown(f"**Platform:** {platform}")
                                st.text_area(f"{platform} Content", content, height=200)

                                st.download_button(
                                    label=f"Download {platform} Content",
                                    data=content,
                                    file_name=f"{platform.lower()}_post.txt",
                                    mime="text/plain"
                                )
# Footer
st.markdown("---")
st.caption("Powered by OpenAI GPT-4o and YouTube Transcript API")