import praw
from praw.models import Subreddit, Submission

import os, dotenv, json

dotenv.load_dotenv()

class XGReddit:
    def __init__(self, client_id, client_secret, user_agent):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

        self.subreddits = []

    def search_subreddits(self, query, limit=10) -> list[Subreddit]:
        """Search for subreddits related to the query

        Args:
            query (str): query to search for
            limit (int, optional): How many subreddits to fetch. Defaults to 10.

        Returns:
            list: list of subreddits
        """
        print(f"Searching for communities related to '{query}'...\n")
        try:
            # Search for subreddits related to the query
            results = self.reddit.subreddits.search(query, limit=limit)
            self.subreddits = [result for result in results]
            
        except Exception as e:
            print(f"An error occurred: {e}")
        return self.subreddits
    
    def fetch_post(self, post_url : str) -> Submission:
        """Fetch a Reddit post from the URL

        Args:
            post_url (str): URL of the Reddit post

        Returns:
            Submission: Reddit post object
        """
        try:
            # Get the submission (post) from the URL
            submission = self.reddit.submission(id=post_url)
            return submission
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return
    
    def fetch_comments(self, post_url : str, comment_limit=100, max_depth=10) -> list[dict]:
        """Fetch comments from a Reddit post in a structured format

        Args:
            post_url (str): _description_
            comment_limit (int, optional): _description_. Defaults to 100.
            max_depth (int, optional): _description_. Defaults to 10.
        """
        def parse_comment(comment, depth=0):
            if depth > max_depth:
                return None
            
            comment_data = {
                "body": comment.body,
                "replies": []
            }

            if hasattr(comment, "replies"):
                for reply in comment.replies:
                    parsed_reply = parse_comment(reply, depth=depth + 1)
                    if parsed_reply:
                        comment_data["replies"].append(parsed_reply)
            
            return comment_data

        # Get the submission (post) from the URL
        submission = self.reddit.submission(id=post_url)
        print(f"Fetching comments from post '{submission}'...\n")
        
        # Load all comments and replace MoreComments objects
        submission.comments.replace_more(limit=0)

        # Get the top-level comments
        top_comments = submission.comments[:comment_limit]

        # Parse each comment recursively
        parsed_comments = []
        for comment in top_comments:
            parsed_comment = parse_comment(comment)
            if parsed_comment:
                parsed_comments.append(parsed_comment)

        return parsed_comments
        
