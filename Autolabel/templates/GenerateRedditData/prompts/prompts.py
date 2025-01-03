from langchain.prompts import PromptTemplate

get_relevance_prompt = PromptTemplate(
    template="""
User wants to do this :
{user_wants_to}

For this he found a post on reddit. Snippet of post is : 
{post_title}

Comments on this post are :
{comments_sample}

Relevant memory for from user's knowledge base is :
{relevant_memory}

#Task : what insight can you gain from this post ? 

Describe in extremely concrete words.

Thinking framework for answer is : 
1. First think what this post is about and what type of discussion is happening in comments
2. Then think what type of insight are you getting that can help user in their task.
3. If you have a big dump of comment sections of this post, what insight will you fetch from them?
4. IF THIS POST IN NOT RELEvANT TO TASK SET IS_RELEVANT FALSE
5. IF CONTENT OF POST ARE NOT WHAT USER WANT TO GAIN INSIGHT ON, SET IS_RELEVANT FALSE
6. Give a score to relevance from 0 to 5. 0 being not relevant at all and 5 being extremely relevant
Answer in one paragraph
""",
    input_variables=["user_wants_to", "post_title", "comments_sample", "relevant_memory"],
)

get_task_info_prompt = PromptTemplate(
    template="""
You are searching below reddit post :
{post_title}

Comments on this post are :
{comments_sample}

Here's what you want to do :
{user_wants_to}

To solve task you think this post is relevant because :
{relevance}

##Task : 
You want to create a labeled data from all comments in this post. For this You need to give your teammate following information in json : 

"task_info" : what insight to fetch from each comment section or a 3-4 liner task of what information to fetch

Rules :
1. Purpose of task_info is to give a clear idea to teammate what to fetch from comments and what is relevant to task. 
2. Task_info should be clear and concise.
3. Better task info are ones which instructs teamemate to not fill garbage data and only fill relevant data. 

Example : 
Post name : Are there any unique Minecraft servers?
Task_info : make list of minecraft servers discussed here, put fields about what features are liked and what are the problems with those servers 
""",
    input_variables=["post_title", "comments_sample", "user_wants_to", "relevance"],
)