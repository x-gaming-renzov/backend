import os, pathlib, json, dotenv
from termcolor import colored
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_openai import ChatOpenAI

from ....loader.reddit.XGReddit import XGReddit
from ....memory.XGMemoryClient import XGMemoryClient
from ..states.states import *
from ..prompts.prompts import *

dotenv.load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini")

#algorithmic nodes

def generate_reddit_data(GenerateRedditDataState : GenerateRedditDataState) -> GenerateRedditDataState:
    print(colored("Generating Reddit Data", "green"))
    
    reddit = XGReddit(
        GenerateRedditDataState.reddit_client_id,
        GenerateRedditDataState.reddit_client_secret,
        GenerateRedditDataState.reddit_user_agent
    )

    subreddits = []
    print(colored("Searching for subreddits...", "green"))
    with ThreadPoolExecutor() as executor:
        futures = []
        for subreddit in GenerateRedditDataState.subreddits:
            print(colored(f"Searching for subreddits related to '{subreddit}'...", "yellow"))
            future = executor.submit(reddit.search_subreddits, subreddit, 1)
            futures.append(future)
        
        for future in as_completed(futures):
            subreddits.extend(future.result())
    
    print(colored(f"Found {len(subreddits)} subreddits", "green"))
    
    print(colored("Fetching posts...", "green"))
    for subreddit in subreddits:
        print(colored(f"Fetching top posts from r/{subreddit.display_name} of all time", "yellow"))
        posts_all = subreddit.top(limit=20, time_filter="all")
        print(colored(f"Fetching top posts from r/{subreddit.display_name} of the week", "yellow"))
        posts_week = subreddit.top(limit=20, time_filter="week")
        print(colored(f"Fetching top posts from r/{subreddit.display_name} of the month", "yellow"))
        posts_month = subreddit.top(limit=20, time_filter="month")

        posts = []
        for post in posts_all:
            posts.append({
                "title": post.title,
                "post_id": post.id,
                "url": post.url,
                "text": post.selftext,
                "num_comments": post.num_comments,
                "upvotes": post.ups
            })
        for post in posts_week:
            posts.append({
                "title": post.title,
                "post_id": post.id,
                "url": post.url,
                "text": post.selftext,
                "num_comments": post.num_comments,
                "upvotes": post.ups
            })
        for post in posts_month:
            posts.append({
                "title": post.title,
                "post_id": post.id,
                "url": post.url,
                "text": post.selftext,
                "num_comments": post.num_comments,
                "upvotes": post.ups
            })

        # Save the posts to a file
        cache_path = GenerateRedditDataState.cache_path
        subreddit_path = os.path.join(cache_path, f"subreddit_data/{subreddit.display_name}/posts.json")

        # Create the directory if it doesn't exist
        pathlib.Path(os.path.dirname(subreddit_path)).mkdir(parents=True, exist_ok=True)

        with open(subreddit_path, "w") as f:
            json.dump(posts, f, indent=4)
        
        print(colored(f"Saved {len(posts)} posts to {subreddit_path}", "green"))

    GenerateRedditDataState.subreddits = [subreddit.display_name for subreddit in subreddits]

    print(colored("Reddit data generation complete", "green"))
    return GenerateRedditDataState

def generate_reddit_comments_from_subreddit(GenerateRedditDataState : GenerateRedditDataState) -> GenerateRedditDataState:
    print(colored("Generating Reddit Comments", "green"))
    
    reddit = XGReddit(
        GenerateRedditDataState.reddit_client_id,
        GenerateRedditDataState.reddit_client_secret,
        GenerateRedditDataState.reddit_user_agent
    )

    for subreddit in GenerateRedditDataState.subreddits:
        subreddit_path = os.path.join(GenerateRedditDataState.cache_path, f"subreddit_data/{subreddit}/posts.json")

        with open(subreddit_path, "r") as f:
            posts = json.load(f)

        for post in posts:
            post_id = post["post_id"]
            print(colored(f"Creating folder for post {post_id}", "yellow"))
            post_path = os.path.join(GenerateRedditDataState.cache_path, f"subreddit_data/{subreddit}/{post_id}")
            pathlib.Path(post_path).mkdir(parents=True, exist_ok=True)
            print(colored(f"Fetching comments for post {post_id}", "yellow"))
            comments = reddit.fetch_comments(post_id, 3, 1)
            print(colored(f"Saving comments for post {post_id}", "yellow"))
            with open(os.path.join(post_path, "comments.json"), "w") as f:
                json.dump(comments, f, indent=4)

    print(colored("Reddit data generation complete", "green"))
    return GenerateRedditDataState



#-----------------------------------------------------------------------------------------------------------------------#
#nodes using llm

def generate_relevance(GenerateRedditDataState : GenerateRedditDataState) -> GenerateRedditDataState:
    print(colored("Generating Relevance", "green"))
    print(colored("Loading LLM memory", "blue"))
    memory = XGMemoryClient(user_name=GenerateRedditDataState.user_id)
    print(colored("Adding KB data to memory", "blue"))
    memory.add_kb_memory(GenerateRedditDataState.kb_data)

    user_wants_to = memory.chat("What does user want to do?")
    print(colored(f"User wants to - {user_wants_to}", "yellow"))

    generator_model = model.with_structured_output(RelevanceInfo)
    generator = get_relevance_prompt | generator_model


    for subreddit in GenerateRedditDataState.subreddits:
        subreddit_path = os.path.join(GenerateRedditDataState.cache_path, f"subreddit_data/{subreddit}/posts.json")

        with open(subreddit_path, "r") as f:
            posts = json.load(f)

        new_posts = []
        with ThreadPoolExecutor() as executor:
            futures = []
            for post in posts:
                post_id = post["post_id"]
                print(colored(f"Creating folder for post {post_id}", "yellow"))
                post_path = os.path.join(GenerateRedditDataState.cache_path, f"subreddit_data/{subreddit}/{post_id}")
                pathlib.Path(post_path).mkdir(parents=True, exist_ok=True)
                with open(os.path.join(post_path, "comments.json"), "r") as f:
                    comments = json.load(f)
                    comment_sample = []

                    for comment in comments:
                        body = {
                            "comment" : comment["body"],
                            "replies" : []
                        }
                        if "replies" in comment:
                            for reply in comment["replies"]:
                                if len(reply["replies"]) > 2:
                                    break
                                body["replies"].append(reply["body"])
                        comment_sample.append(body)
                    print(colored(f"Sampled comments for post {post_id}", "yellow"))
                
                print(colored(f"fetching relevant memeory...", "yellow"))
                relevant_memory = memory.get_memory(str(post["title"]) +  "\n" + str(comment_sample), user_name=GenerateRedditDataState.user_id)

                future = executor.submit(generator.invoke, {
                    "post_title": post["title"],
                    "comments_sample": str(comment_sample),
                    "user_wants_to": user_wants_to,
                    "relevant_memory": relevant_memory
                })

                futures.append(future)

            for future in as_completed(futures):
                continue

            for future_index, future in enumerate(futures):
                relevance = future.result()
                if isinstance(relevance, RelevanceInfo):
                    if relevance.is_relevant:
                        new_posts.append({
                            "title": posts[future_index]["title"],
                            "post_id": posts[future_index]["post_id"],
                            "url": posts[future_index]["url"],
                            "text": posts[future_index]["text"],
                            "num_comments": posts[future_index]["num_comments"],
                            "upvotes": posts[future_index]["upvotes"],
                            "relevance": relevance.relevance,
                            "relevance_score": relevance.relevance_score
                        })


            with open(subreddit_path, "w") as f:
                json.dump(new_posts, f, indent=4)
        
            print(colored(f"Deleted {len(posts) - len(new_posts)} posts from {subreddit_path}", "green"))

    print(colored("Reddit data generation complete", "green"))
    return GenerateRedditDataState

def generate_task_info(GenerateRedditDataState : GenerateRedditDataState) -> GenerateRedditDataState:
    print(colored("Generating Task Info", "green"))
    print(colored("Loading LLM memory", "blue"))
    memory = XGMemoryClient(user_name=GenerateRedditDataState.user_id)
    print(colored("Adding KB data to memory", "blue"))
    memory.add_kb_memory(GenerateRedditDataState.kb_data)

    user_wants_to = memory.chat("What does user want to do?")
    print(colored(f"User wants to - {user_wants_to}", "yellow"))

    generator_model = model.with_structured_output(TaskInfo)
    generator = get_task_info_prompt | generator_model


    for subreddit in GenerateRedditDataState.subreddits:
        subreddit_path = os.path.join(GenerateRedditDataState.cache_path, f"subreddit_data/{subreddit}/posts.json")

        with open(subreddit_path, "r") as f:
            posts = json.load(f)

        with ThreadPoolExecutor() as executor:
            futures = []

            for post in posts:
                post_id = post["post_id"]
                post["subreddit"] = subreddit
                print(colored(f"Creating folder for post {post_id}", "yellow"))
                post_path = os.path.join(GenerateRedditDataState.cache_path, f"subreddit_data/{subreddit}/{post_id}")
                pathlib.Path(post_path).mkdir(parents=True, exist_ok=True)
                with open(os.path.join(post_path, "comments.json"), "r") as f:
                    comments = json.load(f)
                    comment_sample = []

                    for comment in comments:
                        body = {
                            "comment" : comment["body"],
                            "replies" : []
                        }
                        if "replies" in comment:
                            for reply in comment["replies"]:
                                if len(reply["replies"]) > 2:
                                    break
                                body["replies"].append(reply["body"])
                        comment_sample.append(body)
                    print(colored(f"Sampled comments for post {post_id}", "yellow"))
                
                future = executor.submit(generator.invoke, {
                    "post_title": post["title"],
                    "comments_sample": str(comment_sample),
                    "user_wants_to": user_wants_to,
                    "relevance": post["relevance"]
                })
                futures.append(future)
            task_infos = []
            for future in as_completed(futures):
                continue

            print(colored(f"Task info for {subreddit} - {task_infos}", "yellow"))

            for future_index, future in enumerate(futures):
                task_info = future.result()
                if isinstance(task_info, TaskInfo):
                    posts[future_index]["task_info"] = task_info.task_info
            
            with open(subreddit_path, "w") as f:
                json.dump(posts, f, indent=4)

    print(colored("Reddit data generation complete", "green"))

    return GenerateRedditDataState

        