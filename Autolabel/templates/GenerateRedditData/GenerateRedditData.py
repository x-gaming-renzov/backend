from langgraph.graph import StateGraph, START, END

import os, pathlib, json, dotenv
from termcolor import colored
import uuid

from .nodes.nodes import *
from .states.states import *

from ..ExtractJson import ExtractJson
from ...loader.reddit.XGReddit import XGReddit

from ...utils.llm_utils import LLM

import pandas as pd

dotenv.load_dotenv()

class RedditData:
    def __init__(self, subreddits, kb_data, reddit_client_id, reddit_client_secret, reddit_user_agent, status="Not started", user_id=None, reddit_posts_processed=[]):
        self.subreddits = subreddits
        self.kb_data = kb_data
        self.reddit_client_id = reddit_client_id
        self.reddit_client_secret = reddit_client_secret
        self.reddit_user_agent = reddit_user_agent
        self.user_id = user_id if user_id is not None else str(uuid.uuid4()) #"4f44875dcfc4487eb4a1d55ddc03c299" #uuid.uuid4().hex 
        self.cache_path = os.getcwd() + "/cache/generate_reddit_data/" + self.user_id
        self.status = status
        self.reddit_posts_processed = reddit_posts_processed

    def __str__(self):
        return f"GenerateRedditDataState(subreddits={self.subreddits}, kb_data={self.kb_data}, cache_path={self.cache_path}, reddit_client_id={self.reddit_client_id}, reddit_client_secret={self.reddit_client_secret}, reddit_user_agent={self.reddit_user_agent}, user_id={self.user_id})"

    def __repr__(self):
        return f"GenerateRedditDataState(subreddits={self.subreddits}, kb_data={self.kb_data}, cache_path={self.cache_path}, reddit_client_id={self.reddit_client_id}, reddit_client_secret={self.reddit_client_secret}, reddit_user_agent={self.reddit_user_agent}, user_id={self.user_id})"

    def to_dict(self):
        return {
            "subreddits": self.subreddits,
            "kb_data": self.kb_data,
            "cache_path": self.cache_path,
            "reddit_client_id": self.reddit_client_id,
            "reddit_client_secret": self.reddit_client_secret,
            "reddit_user_agent": self.reddit_user_agent,
            "user_id": self.user_id,
            "status": self.status,
            "reddit_posts_processed": self.reddit_posts_processed
        }

    @staticmethod
    def from_dict(data):
        return RedditData(
            subreddits=data["subreddits"],
            kb_data=data["kb_data"],
            reddit_client_id=data["reddit_client_id"],
            reddit_client_secret=data["reddit_client_secret"],
            reddit_user_agent=data["reddit_user_agent"],
            user_id=data["user_id"],
            status=data["status"],
            reddit_posts_processed=data["reddit_posts_processed"]
        )
    
    def save(self):
        with open(self.cache_path + "/state.json", "w") as f:
            json.dump(self.to_dict(), f)

    @staticmethod
    def load(cache_path):
        with open(cache_path + "/state.json", "r") as f:
            data = json.load(f)
        return RedditData.from_dict(data)

    def get_graph(self):
        graph = StateGraph(GenerateRedditDataState)

        graph.add_node("generate_reddit_data", generate_reddit_data)
        graph.add_node("generate_reddit_comments_from_subreddit", generate_reddit_comments_from_subreddit)
        graph.add_node("generate_relevance", generate_relevance)
        graph.add_node("generate_task_info", generate_task_info)

        graph.add_edge(START, "generate_reddit_data")
        graph.add_edge("generate_reddit_data", "generate_reddit_comments_from_subreddit")
        graph.add_edge("generate_reddit_comments_from_subreddit", "generate_relevance")
        graph.add_edge("generate_relevance", "generate_task_info")
        graph.add_edge("generate_task_info", END)

        compiled_graph = graph.compile()

        return compiled_graph

    def run_strategy(self):
        if self.status == "Completed":
            return "Already completed"
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)
        graph = self.get_graph()
        final_state = graph.invoke({
            "subreddits": self.subreddits,
            "kb_data": self.kb_data,
            "cache_path": self.cache_path,
            "reddit_client_id": self.reddit_client_id,
            "reddit_client_secret": self.reddit_client_secret,
            "reddit_user_agent": self.reddit_user_agent,
            "user_id": self.user_id
        })

        self.status = "Completed"
        return final_state
    
    def get_relevant_posts(self):
        dfs = {}
        for subreddit in self.subreddits:
            with open(self.cache_path + f"/subreddit_data/{subreddit}/posts.json", "r") as f:
                posts = json.load(f)
        
            df = pd.DataFrame(posts)
            #drop column text, url, relevance, num_comments and index by post_id
            df = df.drop(columns=["text", "url", "relevance"])
            df = df.set_index("post_id")
            df = df.sort_values(by=["num_comments"], ascending=False)
            dfs[subreddit] = df
        return dfs
    
    def generate(self, posts : List[str] = None, comment_limit : int = 100, max_comment_depth : int = 5):
        posts_from_subreddit = []

        for subreddit in self.subreddits:
            with open(self.cache_path + f"/subreddit_data/{subreddit}/posts.json", "r") as f:
                posts_data = json.load(f)
            for post in posts_data:
                if posts is None:
                    posts_from_subreddit.append(post)

                elif post["post_id"] in posts:
                    posts_from_subreddit.append(post)
        reddit = XGReddit(self.reddit_client_id, self.reddit_client_secret, self.reddit_user_agent)
        for post in posts_from_subreddit:
            comments = reddit.fetch_comments(post_url=post["post_id"], 
                                             comment_limit=comment_limit, 
                                             max_depth=max_comment_depth)
            comments = [str(comment) for comment in comments]
            post_data = ExtractJson.run(
                task_info=post["task_info"],
                user_id=self.user_id,
                chunk_context=f"""
Each chunk is a part of Comment section of a Reddit post about : {post["title"]}
It has {post["upvotes"]} upvotes and {post["num_comments"]} comments.
{post["relevance"]}
                            """,
                data=comments,
            )
            pathlib.Path(self.cache_path + f"/subreddit_data/{post['subreddit']}/{post['post_id']}/data").mkdir(parents=True, exist_ok=True)

            llm = LLM()
            response = llm.send_message(
                prompt=f"""
Create a name for the file that contains the data generated from the comments of the Reddit post.
name of post: {post['title']}
subreddit: {post['subreddit']}
What is collected: {post['task_info']}
Why is it collected: {post['relevance']}

Return only name of the file without any extension in json format.

Answer format: 

    "file_name": "name_of_file"

"""
            )
            

            with open(self.cache_path + f"/subreddit_data/{post['subreddit']}/{post['post_id']}/data/{json.loads(response)['file_name']}.json", "w") as f:
                f.write(json.dumps(post_data, indent=4))
            self.reddit_posts_processed.append([post["post_id"], post["subreddit"]])

        return "Data generated successfully"
    
    def run(self, num_posts=3):
        print(colored("Running GenerateRedditData", "cyan"))
        self.run_strategy()
        print(colored("GenerateRedditData completed", "cyan"))
        print("--------------------------------------------")
        print(colored("Saving progress", "cyan"))
        self.status = "Completed"
        self.save()
        print(colored("Progress saved", "cyan"))
        print("--------------------------------------------")
        print(colored("Generating comments", "cyan"))
        dfs = self.get_relevant_posts()
        for subreddit in dfs:
            print(colored(f"Generating data for {subreddit}", "blue"))
            print(dfs[subreddit].index.to_list())
            self.generate(posts=dfs[subreddit].index.to_list()[:num_posts])
            print(colored(f"Data generated for {subreddit}", "blue"))
        print("--------------------------------------------")
        print(colored("Saving progress", "cyan"))
        self.save()
        print(colored("Progress saved", "cyan"))
        print(colored("Data generated successfully", "cyan"))
    
    def get_reddit_posts_processed(self, zip_file_path):
        """create a zip file of all the files generated
        Structure of zip file:
        {subreddit_name}:
            {post_id}:
                {file_name}.json
        """
        import zipfile
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            for post_id, subreddit in self.reddit_posts_processed:
                data_dir = self.cache_path + f"/subreddit_data/{subreddit}/{post_id}/data"
                for file in os.listdir(data_dir):
                    zipf.write(data_dir + "/" + file, f"{subreddit}/{file}")
        return zip_file_path





        
        


            